# Deployment and domain setup

Verified October 11, 2026.

- Repository: https://github.com/IftekharAhmedID/ahmedifty-site (private).
- Render project: Personal Portfolio (`prj-db5r9qid0e5s738eh6ng`).
- Production environment: `evm-db5r9qid0e5s738eh6o0`.
- Static Site: `srv-db5siv2vcj2c7394k1cg`.
- Live preview: https://ahmedifty-site.onrender.com.
- Dashboard: https://dashboard.render.com/static/srv-db5siv2vcj2c7394k1cg.
- Build: `true`; publish directory: `public`; main pushes deploy automatically.
- Static hosting requires no paid compute. Render workspace bandwidth, build-minute, and custom-domain allowances apply.

## Current hosting

The existing ahmedifty.com page is a static HTML document served by LiteSpeed at `198.187.29.126`. Its authoritative DNS uses `dns1.namecheaphosting.com` and `dns2.namecheaphosting.com`, indicating Namecheap Hosting DNS. The current www CNAME points to ahmedifty.com. Both website records have a 14400-second TTL. Email MX records point to Jellyfish hosting servers.

## Remaining cutover

Both ahmedifty.com and www.ahmedifty.com have been added to Render. They remain unverified because DNS still points to the old host. No Namecheap/cPanel authenticated access was available in this session.

In Namecheap Hosting cPanel → Zone Editor → Manage ahmedifty.com, edit the existing website records:

| Type | Name | New value |
| --- | --- | --- |
| A | ahmedifty.com (or @) | 216.24.57.1 |
| CNAME | www.ahmedifty.com (or www) | ahmedifty-site.onrender.com |

Leave nameservers and email MX/TXT records intact. Remove conflicting A/AAAA records only for the two website names if any exist. No AAAA record was observed for the apex during this check. DNS changes can remain cached for the old four-hour TTL.

Then open the Render site Settings → Custom Domains and verify both domains. Render issues HTTPS certificates and redirects www to the apex. Confirm that https://ahmedifty.com serves the new page over valid HTTPS.

Official instructions: https://render.com/docs/configure-other-dns.

## Verification

The first deployment was live at commit `59718c929b13204711f74a625e45e84c7927d0c9`. All five published files returned HTTP 200 and matched repository bytes. Browser checks at widths 320, 768, 1024, and 1440 found no horizontal overflow or console errors. Keyboard focus reached the navigation link. No external fonts, scripts, analytics, or dependencies are loaded.

## Rollback

Restore the apex A record to `198.187.29.126` and the www CNAME to `ahmedifty.com`. The original hosted page was left intact. No Translucid or Qube source, deployment, or domain settings were changed.
