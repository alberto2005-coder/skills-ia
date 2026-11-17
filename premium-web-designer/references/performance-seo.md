# PERFORMANCE AND SEO STANDARD

## PERFORMANCE

- Optimize image formats and dimensions; declare width and height to avoid layout shifts.
- Lazy-load non-critical images; never lazy-load the hero.
- Avoid unnecessary JavaScript and third-party scripts.
- Optimize font loading with preload and `font-display`.
- Use caching appropriately and version local assets (`styles.css?v=3`).
- Measure actual performance, never estimate it.

## SEO MINIMUM FOR A PUBLIC PAGE

Every shipped page must carry:

- `lang` on the root element and a single, unique `<title>` of 15–65 characters.
- Meta description of 70–165 characters that matches the visible copy.
- Canonical URL, absolute and self-referencing.
- Open Graph with `og:title`, `og:description` and `og:image` (1200×630), plus a Twitter card.
- One `h1` and a heading hierarchy without skipped levels.
- Descriptive alternative text on every meaningful image; empty `alt` for decorative ones.
- JSON-LD that describes only what is visible on the page.
- `robots.txt` that declares the sitemap, and a `sitemap.xml` with the published URLs.
- `llms.txt` when the site answers AI surfaces, with a short description and its key pages.

## HEADERS AND SECURITY AT DEPLOY

Static hosting does not fix these for you. Ship a headers file or configure the platform with:

- `Content-Security-Policy` without `unsafe-inline` where possible.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
- `X-Content-Type-Options: nosniff`, `Referrer-Policy` and `Permissions-Policy`.
- Compression (brotli or gzip) enabled by the host; verify with the response headers.

`delivery_check.py --public` looks for `_headers`, `netlify.toml` or `vercel.json`, reads the CSP and HSTS declarations and warns when either is missing or HSTS lacks `max-age`.

## CONTENT

Avoid duplicate titles, empty metadata, keyword stuffing, misleading structured data and automatically generated meaningless copy.

## VERIFICATION

`py premium-web-designer/scripts/delivery_check.py <folder>` checks the static half of this list before delivery. Pass `--public` for a folder that is actually going live: canonical, Open Graph with image, `robots.txt` and `sitemap.xml` then become `must` instead of advice. Then:

- Measure in a browser: transferred weight, request count, TTFB and layout shifts.
- Inspect the rendered page at 360, 390, 768, 1024 and 1440 px.
- For a full technical audit, hand over to the `seo-auditor` package.

Never invent performance scores or indexing results.
