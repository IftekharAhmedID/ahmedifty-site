# SEO checks and measurement

The site remains static HTML/CSS. The audit uses Python 3.9+ standard-library modules; it does not add browser JavaScript, analytics, or an application server. Run commands from this repository.

## Validate the site

Use a fresh output directory outside `public/` and outside Git. The command discovers canonical routes from the sitemap and checks titles, one H1, canonicals, indexing directives, structured-data JSON, internal links/anchors, assets, and robots.txt.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/seo_audit.py \
  --output-dir "$HOME/Documents/SEO/ahmedifty/manual-site-check"
```

For local review, start `python3 -m http.server 8766 --bind 127.0.0.1 --directory public`, then add `--base-url http://127.0.0.1:8766/` to the audit. Canonicals must still identify the production URLs. A nonzero exit means site-validation errors; external measurement availability is recorded separately in the JSON outputs.

## Search Console and localized rankings

Prerequisites: an authorized `gcloud` Application Default Credentials login with Search Console access, an existing quota project with the Search Console API enabled, and the existing `brightdata-seo` CLI. Store credentials in their normal user configuration directories, never here. Set `SEO_QUOTA_PROJECT` to that existing project ID.

```sh
python3 scripts/seo_audit.py \
  --output-dir "$HOME/Documents/SEO/ahmedifty/manual-full-check" \
  --gsc --quota-project "$SEO_QUOTA_PROJECT" --serp
```

The audit is read-only. It does not submit a sitemap, request indexing, update profiles, or change authentication. Use a new output directory for each run; an existing `run.json` is rejected to preserve measurements. Provider requests use at most two concurrent SERP workers, with one retry after at least 16 seconds. A longer provider-required delay is honored up to 60 seconds; longer delays are recorded as deferred/unavailable instead of retried early. Inspect `serp-summary.json` for unavailable samples and `gsc-summary.json` / `gsc-error.json` for API/authentication failures. A failed provider request is not evidence of absence from Google.

The Google samples use US/Bangladesh country settings and English. Bare-name desktop searches cover three pages; mobile covers the first page. Qualified desktop searches cover the first page. Organic positions are page-relative, without treating provider global-rank fields as absolute rankings. Exact LinkedIn, Rice, and Scholar identifiers distinguish the author from namesakes. Country targeting is not a guarantee of a specific city or physical device location.

Search Console exports finalized 7-, 28-, and 90-day data through yesterday, including query/country/device/page dimensions and individual stored URL inspections. Google may not have finalized yesterday's data, and low-volume query rows may be omitted. Compare the actual returned dates; missing rows are not zero demand. The API does not return a complete backlink report or run Google's live inspection test.

Record profile connections separately when checking the public identity:

```sh
gh api user --jq '{login,name,blog,bio,location}'
```

Do not store tokens or full private account responses. GitHub's website should be `https://ahmedifty.com/`; the authorized bio is `Computer science at Rice University. Building Qube. Also known as Ifty Ahmed.` Public Rice, Scholar, and LinkedIn checks must record blocked/unknown states rather than invent missing links.

## Interpreting a release

Keep pre-release and post-release snapshots separate. Run Lighthouse 13.5.0 against the homepage three times per mobile/desktop condition, sequentially, and compare medians. Record version, settings, timestamps, LCP, TBT, CLS, warnings, and category scores. Lab measurements are not field Core Web Vitals or proof of ranking changes. Inspect actual failing audits before changing the design or media.

After a release, verify deployed bytes and canonical routes before submitting the sitemap once through Google's documented Sitemaps API and notifying IndexNow using the existing key. Record acceptance separately from indexing. IndexNow is not a Google indexing request. Google's URL Inspection API provides stored status; the Indexing API is restricted to eligible job/livestream pages and must not be used for this portfolio.

Rerun the full CLI audit 14 and 28 days after the release using fresh directories. Compare indexing/crawl dates first, then exact query/country/device impressions, clicks, position and first-page presence. The October 18 release's review dates are November 1 and November 15, 2026. No scheduled automation is installed.

## Sources

- [Search Analytics](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
- [Stored URL Inspection](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect)
- [Sitemap submission](https://developers.google.com/webmaster-tools/v1/sitemaps/submit)
- [Google recrawl guidance](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl)
- [Indexing API eligibility](https://developers.google.com/search/apis/indexing-api/v3/quickstart)
- [IndexNow](https://www.indexnow.org/documentation)
