# Ifty Ahmed’s personal site

A small static website for ahmedifty.com. Plain HTML and CSS, with no dependencies or JavaScript. The layout follows the sparse serif-text reference supplied by Ifty; bio details came from the existing personal site and his current Translucid work.

## Preview

```sh
python3 -m http.server 8766 --bind 127.0.0.1 --directory public
```

Open http://127.0.0.1:8766. Edit `public/index.html` for the introduction and and `public/style.css` for the layout. Pushes to main deploy automatically to Render.

## Render

Static Site in the Personal Portfolio project. Build command: `true`. Publish directory: `public`. No application server or secrets required. See DEPLOYMENT.md for domain setup and verification.
