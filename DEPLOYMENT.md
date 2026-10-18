# Deployment

Verified October 18, 2026.

- Repository: [IftekharAhmedID/ahmedifty-site](https://github.com/IftekharAhmedID/ahmedifty-site), public.
- Canonical website: [ahmedifty.com](https://ahmedifty.com/).
- Render static service: `srv-db5siv2vcj2c7394k1cg`, named `ahmedifty-site`.
- Render project: Personal Portfolio (`prj-db5r9qid0e5s738eh6ng`).
- [Render dashboard](https://dashboard.render.com/static/srv-db5siv2vcj2c7394k1cg).
- Build command: `true`; publish directory: `public`; pushes to `main` deploy automatically.
- Render's preview hostname is `ahmedifty-site.onrender.com`; public pages declare ahmedifty.com as canonical.

The custom domain is already serving the Render site over HTTPS. HTTP and www redirect to the HTTPS apex. The earlier Namecheap DNS cutover is complete; do not reapply old DNS instructions or change email records for a content release. No Translucid/Qube source or deployment belongs to this service.

## Release verification

1. Confirm the checkout and Git remote identify ahmedifty-site and verify the Render service still binds that repository's `main` branch.
2. Run the static audit and responsive browser checks described in [SEO.md](SEO.md). Preserve Google ownership verification and IndexNow files.
3. Review the scoped diff, publish to `main`, and wait for Render to report the exact commit live.
4. Compare production HTML/assets with the release and check redirects, sitemap, robots.txt, and canonical metadata.
5. If URLs or meaningful page content changed, submit the sitemap once and record actual Google inspection results separately from submission acceptance.

Credentials stay in user CLI configuration, outside this repository. Audit evidence belongs under `~/Documents/SEO/ahmedifty/`, not `public/`.

## Rollback

Revert the portfolio release commit(s) with a new commit and let this static service redeploy. Verify the rollback's exact commit and live content. No DNS change, database migration, or other repository deployment is needed.
