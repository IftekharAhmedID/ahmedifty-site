# Ifty Ahmed’s personal site

A small static website for ahmedifty.com. Plain HTML and CSS, with no dependencies or JavaScript. The layout follows the sparse serif-text reference supplied by Ifty; bio details came from the existing personal site and his current Translucid work.

## Preview

```sh
python3 -m http.server 8766 --bind 127.0.0.1 --directory public
```

Open http://127.0.0.1:8766. Edit `public/index.html` for the introduction and projects, the `index.html` files in `public/about/`, `public/research/`, and `public/press/` for the other pages, and `public/style.css` for the shared layout. Keep `public/sitemap.xml` up to date when adding pages. Pushes to main deploy automatically to Render.

## Render

Static Site in the Personal Portfolio project. Build command: `true`. Publish directory: `public`. No application server or secrets required. See DEPLOYMENT.md for domain setup and verification.

## Content sources

See [CONTENT-SOURCES.md](CONTENT-SOURCES.md) for the sources behind biographical details, publications, and press links. All pages are static HTML with directory indexes; no application routing or dependencies are needed. Preserve the Google ownership verification and IndexNow files.
