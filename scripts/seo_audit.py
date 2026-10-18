#!/usr/bin/env python3
"""Read-only site, Search Console, and localized Google audit. See SEO.md."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timedelta
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urljoin, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

SITE = 'https://ahmedifty.com/'
NAMES = ['ifty ahmed', 'ahmed ifty', 'iftekhar ahmed']
QUALIFIED = ['iftekhar ahmed rice', 'ifty ahmed qube', 'iftekhar ahmed swingboard']


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def fetch(url, body=None, headers=None):
    request = Request(url, data=json.dumps(body).encode() if body is not None else None,
                      headers={'User-Agent': 'PortfolioSEOAudit/1.0', **(headers or {})})
    try:
        with urlopen(request, timeout=45) as response:
            return response.status, dict(response.headers), response.read(), response.url
    except HTTPError as error:
        return error.code, dict(error.headers), error.read(), error.url


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.h1, self.ids, self.links, self.assets = '', [], set(), [], []
        self.canonicals, self.robots, self.jsonld, self.json_errors = [], [], [], []
        self.in_title = self.in_h1 = self.in_json = False
        self.script = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'title':
            self.in_title = True
        if tag == 'h1':
            self.in_h1 = True
            self.h1.append('')
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])
        if tag == 'link' and 'canonical' in a.get('rel', '').split():
            self.canonicals.append(a.get('href'))
        if tag == 'meta' and a.get('name', '').lower() in ['robots', 'googlebot']:
            self.robots.append(a.get('content', '').lower())
        if tag in ['img', 'source', 'video', 'script'] and a.get('src'):
            self.assets.append(a['src'])
        if tag == 'video' and a.get('poster'):
            self.assets.append(a['poster'])
        if tag == 'link' and set(a.get('rel', '').split()) & {'stylesheet', 'icon'}:
            self.assets.append(a.get('href', ''))
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.in_json, self.script = True, ''

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'h1':
            self.in_h1 = False
        if tag == 'script' and self.in_json:
            try:
                self.jsonld.append(json.loads(self.script))
            except ValueError as error:
                self.json_errors.append(str(error))
            self.in_json = False

    def handle_data(self, value):
        if self.in_title:
            self.title += value
        if self.in_h1:
            self.h1[-1] += value
        if self.in_json:
            self.script += value


def identity(url):
    u = urlsplit(url)
    host, path = u.hostname or '', u.path.rstrip('/')
    if host in ['ahmedifty.com', 'www.ahmedifty.com']:
        return 'personal-site'
    if (host == 'linkedin.com' or host.endswith('.linkedin.com')) and path == '/in/iftekhar-ahmed-':
        return 'linkedin'
    if host == 'profiles.rice.edu' and path == '/student/iftekhar-ifty-ahmed':
        return 'rice'
    if host == 'scholar.google.com' and parse_qs(u.query).get('user') == ['drQ6MO4AAAAJ']:
        return 'scholar'
    return ''


def audit_site(base, output):
    status, _, body, _ = fetch(urljoin(base, 'sitemap.xml'))
    if status != 200:
        raise RuntimeError(f'Sitemap HTTP {status}')
    urls = [node.text for node in ET.fromstring(body).iter() if node.tag.endswith('}loc')]
    if not urls or any(not u.startswith(SITE) for u in urls):
        raise RuntimeError('Sitemap must contain canonical ahmedifty.com URLs')
    pages, rows, errors = {}, [], []
    for canonical in urls:
        path = urlsplit(canonical).path
        code, headers, html, final = fetch(urljoin(base, path))
        p = Page()
        p.feed(html.decode('utf-8', errors='replace'))
        pages[path] = p
        name = path.strip('/').replace('/', '-') or 'home'
        (output / (name + '.html')).write_bytes(html)
        xrobots = next((v for k, v in headers.items() if k.lower() == 'x-robots-tag'), '')
        issues = []
        if code != 200 or urlsplit(final).path != path:
            issues.append(f'HTTP/final path: {code} {final}')
        if p.canonicals != [canonical]:
            issues.append('Canonical mismatch')
        if not p.title or len(p.h1) != 1 or not p.h1[0].strip():
            issues.append('Missing title or single nonempty H1')
        if re.search(r'\b(noindex|none)\b', ' '.join(p.robots + [xrobots]).lower()):
            issues.append('Indexing blocked')
        if not p.jsonld or p.json_errors:
            issues.append('Missing/invalid structured-data JSON')
        rows.append({'url': canonical, 'status': code, 'title': p.title, 'h1': p.h1,
                     'canonical': p.canonicals, 'robots': p.robots, 'x_robots_tag': xrobots,
                     'jsonld': p.jsonld, 'bytes': len(html), 'issues': issues})
    assets = set()
    for path, p in pages.items():
        for href in p.links + p.assets:
            target = urlsplit(urljoin(urljoin(SITE, path), href))
            if target.netloc != 'ahmedifty.com':
                continue
            if target.path in pages:
                if target.fragment and target.fragment not in pages[target.path].ids:
                    errors.append(f'{path}: missing anchor {href}')
            elif target.path:
                assets.add(target.path)
            if href == '#':
                errors.append(f'{path}: nonfunctional link #')
    def check(path):
        try:
            code, _, _, _ = fetch(urljoin(base, path))
            return {'path': path, 'status': code}
        except (OSError, URLError) as error:
            return {'path': path, 'error': str(error)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        checked = list(pool.map(check, sorted(assets)))
    errors.extend(str(a) for a in checked if a.get('status') != 200)
    for row in rows:
        errors.extend(row['url'] + ': ' + issue for issue in row['issues'])
    robots_code, _, robots, _ = fetch(urljoin(base, 'robots.txt'))
    if robots_code != 200 or SITE + 'sitemap.xml' not in robots.decode():
        errors.append('Missing robots.txt or sitemap reference')
    result = {'base_url': base, 'urls': urls, 'pages': rows, 'assets': checked,
              'robots': robots.decode(), 'errors': errors}
    save(output / 'site.json', result)
    return urls, errors


def audit_gsc(urls, output, quota_project):
    token = subprocess.run(['gcloud', 'auth', 'application-default', 'print-access-token'],
                           capture_output=True, text=True, check=True, timeout=60).stdout.strip()
    headers = {'Authorization': 'Bearer ' + token, 'x-goog-user-project': quota_project,
               'Content-Type': 'application/json'}
    base = 'https://www.googleapis.com/webmasters/v3/sites/' + quote(SITE, safe='')
    tasks = [('sitemaps', base + '/sitemaps', None)]
    end = datetime.now(ZoneInfo('America/Chicago')).date() - timedelta(days=1)
    for days in [7, 28, 90]:
        for name, dims in [('totals', []), ('dates', ['date']), ('queries', ['query']),
                           ('pages', ['page']), ('countries', ['country']), ('devices', ['device']),
                           ('query-country-device-page', ['query', 'country', 'device', 'page'])]:
            body = {'startDate': str(end - timedelta(days=days - 1)), 'endDate': str(end),
                    'dimensions': dims, 'rowLimit': 25000, 'dataState': 'final', 'type': 'web'}
            tasks.append((f'{days}d-{name}', base + '/searchAnalytics/query', body))
    for url in urls:
        name = urlsplit(url).path.strip('/').replace('/', '-') or 'home'
        tasks.append(('inspection-' + name, 'https://searchconsole.googleapis.com/v1/urlInspection/index:inspect',
                      {'inspectionUrl': url, 'siteUrl': SITE, 'languageCode': 'en-US'}))
    def run(task):
        name, url, body = task
        try:
            code, _, data, _ = fetch(url, body, headers)
            value = json.loads(data)
            save(output / 'gsc' / (name + '.json'), value)
            return {'name': name, 'status': code, 'request': body,
                    'index': value.get('inspectionResult', {}).get('indexStatusResult')}
        except (OSError, ValueError) as error:
            return {'name': name, 'error': str(error)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, tasks))
    save(output / 'gsc-summary.json', results)
    return results


def audit_serps(output):
    jobs = [(q, c, 'desktop', p) for q in NAMES for c in ['us', 'bd'] for p in range(3)]
    jobs += [(q, c, 'mobile', 0) for q in NAMES for c in ['us', 'bd']]
    jobs += [(q, c, 'desktop', 0) for q in QUALIFIED for c in ['us', 'bd']]
    folder = output / 'serp'
    folder.mkdir(exist_ok=True)
    def run(job):
        query, country, device, page = job
        name = f'{query.replace(" ", "-")}-{country}-{device}-p{page+1}'
        path = folder / (name + '.json')
        cmd = ['brightdata-seo', 'search', query, '--engine', 'google', '--country', country,
               '--language', 'en', '--device', device, '--page', str(page), '--json', '-o', str(path)]
        error = ''
        for attempt in range(2):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    data = json.loads(path.read_text())
                    general = data.get('general', {})
                    actual_page = data.get('pagination', {}).get('current_page')
                    if (general.get('query', '').lower() != query or
                        general.get('country_code', '').lower() != country or
                        bool(general.get('mobile')) != (device == 'mobile') or
                        actual_page is not None and actual_page != page + 1 or
                        'organic' not in data):
                        raise ValueError('Provider returned mismatched or incomplete search metadata')
                    return {'query': query, 'country': country, 'device': device, 'page': page + 1,
                            'available': True, 'file': str(path), 'attempts': attempt + 1,
                            'timestamp': general.get('timestamp'), 'organic': data['organic']}
                error = (result.stderr + result.stdout)[-600:]
            except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                error = str(exc)
            if attempt == 0:
                time.sleep(16)
        return {'query': query, 'country': country, 'device': device, 'page': page + 1,
                'available': False, 'attempts': 2, 'error': error}
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(run, job) for job in jobs]):
            result = future.result()
            results.append(result)
            print('SERP', result['query'], result['country'], result['device'], result['page'],
                  'OK' if result['available'] else 'unavailable', flush=True)
    rows = []
    for result in results:
        for ordinal, item in enumerate(result.get('organic', []), 1):
            rows.append({**{k: result[k] for k in ['query', 'country', 'device', 'page', 'timestamp']},
                         'organic_ordinal': ordinal, 'url': item.get('link'), 'title': item.get('title'),
                         'identity': identity(item.get('link', ''))})
        result['matches'] = [{'organic_ordinal': i, 'url': x.get('link'),
                              'identity': identity(x.get('link', ''))}
                             for i, x in enumerate(result.pop('organic', []), 1) if identity(x.get('link', ''))]
    with (output / 'serp-results.csv').open('w') as f:
        keys = ['query', 'country', 'device', 'page', 'timestamp', 'organic_ordinal', 'url', 'title', 'identity']
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    save(output / 'serp-summary.json', sorted(results, key=lambda x: (x['query'], x['country'], x['device'], x['page'])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default=SITE)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--gsc', action='store_true')
    parser.add_argument('--quota-project', default='')
    parser.add_argument('--serp', action='store_true')
    args = parser.parse_args()
    if args.gsc and not args.quota_project:
        parser.error('--gsc requires --quota-project (an existing Search Console API-enabled project)')
    output = args.output_dir.expanduser().resolve()
    public = Path(__file__).resolve().parents[1] / 'public'
    if output.is_relative_to(public):
        parser.error('Keep private audit outputs outside public/')
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'run.json').exists():
        parser.error('Output directory already contains a run; use a new directory to preserve measurements')
    manifest = {'started_at': datetime.now().astimezone().isoformat(), 'base_url': args.base_url,
                'gsc': args.gsc, 'serp': args.serp}
    save(output / 'run.json', manifest)
    urls, errors = audit_site(args.base_url, output)
    if args.gsc:
        try:
            audit_gsc(urls, output, args.quota_project)
        except (OSError, subprocess.SubprocessError) as error:
            # Authentication errors never include token stdout/stderr in saved evidence.
            save(output / 'gsc-error.json', {'error': type(error).__name__, 'message': 'Search Console authentication/request failed'})
    if args.serp:
        audit_serps(output)
    manifest.update(finished_at=datetime.now().astimezone().isoformat(), site_errors=errors)
    save(output / 'run.json', manifest)
    print(json.dumps({'output': str(output), 'routes': len(urls), 'site_errors': errors}), flush=True)
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
