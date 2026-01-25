# Anand's Blog

Content and build pipeline for https://s-anand.net/

## Source files

Content:

- `pages/`: Standalone pages as Markdown (`pages/slug.md`).
  - [Home page](pages/s-anand.md)
  - Pages can be nested: `pages/lists/slug.md`
- `posts/`: Blog posts as Markdown (`posts/yyyy/slug.md`).
- `assets/`: Converted media files used by posts (WebP/OPUS). Served at `/blog/assets/`.

Configuration & Code:

- `metadata.yml` for taxonomies (categories, tags), and author info
- `hugo.toml`: Hugo site configuration
- `setup.sh`: Build script to generate content and build site
- `.github/workflows/deploy.yml`: Deployment workflow for GitHub Pages.
- `layouts/`: Hugo layout overrides for theme customizations.
- `static/`: Static files (CSS overrides, favicon assets).
- `themes/PaperMod/`: Hugo theme sources (vendored).
- `scripts/`: Conversion and utility scripts.

Auto-generated (DO NOT edit!):

- `content/`: Contains Hugo content (posts/pages + taxonomy and archive index pages).
- `public/`: Build output (deployed to GitHub Pages).

**After editing source files**, rebuild with:

```bash
bash setup.sh
```

This runs:

1. `scripts/build_content.py` - generates `content/` from `posts/`, `pages/`, and `metadata.yml`
2. `hugo` - builds static site to `public/blog/`
3. Post-processing scripts for comments and feed normalization
4. Copies special pages to `public/` root

## Frontmatter

- `build: { list: never, render: always }` ensures that posts/pages are not listed _anywhere_ blog index but are still rendered.
- `classes: wrap-code` adds the `wrap-code` class to the post's main `<article>` element, which applies CSS to wrap long code blocks.

## Notes

### Page Titles

The `<title>` tag generation in `layouts/partials/head.html` implements two behaviors:

1. **Capitalization**: Page titles are capitalized using Hugo's `title` function, so "blog" becomes "Blog"
2. **Deduplication**: When a page title equals the site title (e.g., "S Anand"), it only appears once instead of "S Anand | S Anand"

This ensures:
- The blog home page has title "Blog | S Anand"
- The site home page (pages/s-anand.md) has title "S Anand" (not duplicated)
