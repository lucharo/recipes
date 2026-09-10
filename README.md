# Instagram Recipe Explorer

I love discovering recipes on Instagram, but they quickly add up and it becomes harder to explore the previously saved recipes.

In this repo and website we achieve the following:

* Export saved recipe posts from Instagram via browser API
* Turn each post into a markdown document using a `jinja2` template
* Build a searchable static site with Hugo, featuring side-by-side recipe layouts, ingredient filtering, and a "Feeling Lucky" button

Visit the site: <https://testkitchen.luischav.es>

This is the **Test Kitchen** repository (`lucharo/recipes`).

The "tried and tested" recipes go to [cook.luischav.es](https://cook.luischav.es/).

## Setup

```sh
uv sync
```

Requires [Hugo](https://gohugo.io/installation/) for site building.

## Recipe Markdown

Every saved post uses `## Ingredients` (bullets), `## Method` (numbered steps),
and optional `## Notes`. Title, author and original links stay in the YAML front
matter. On a recipe page, **Copy as Markdown** copies the title, attribution,
source links and formatted recipe. If clipboard access fails, a selectable text
box appears for manual copying.

```sh
# Format all saved posts in place
uv run python format_recipes.py

# Check that no posts still need formatting
uv run python format_recipes.py --check

# Run formatter/import regression tests
uv run python -m unittest discover -s tests
```

New imports use the same formatter automatically. It removes standalone hashtag
blocks and decorative separators, recognises ingredient lists and cooking steps,
and retains unclassified prose in Notes. It does not retrieve linked recipes,
translate, convert quantities or invent missing instructions. Missing sections
say so explicitly. Formatting is heuristic: check the original source when the
caption is ambiguous. Original captions remain available in Git history.

Files marked `recipe_format: 1` are left unchanged on subsequent runs so manual
corrections survive. Edit their Markdown directly; `--force` on the importer
explicitly replaces those edits with a fresh formatted import.

## Fetch recipes

1. Log into instagram.com in Chrome
2. Open browser console (F12)
3. Paste and run the fetch script (see `fetch_saved_posts.js`)
4. A JSON file will be downloaded automatically
5. Run:

```sh
# Process exported JSON into Hugo content
uv run python fetch_recipes.py --from-json instagram_saved_posts.json

# Preview what would be created
uv run python fetch_recipes.py --from-json instagram_saved_posts.json --dry-run

# Overwrite existing recipes
uv run python fetch_recipes.py --from-json instagram_saved_posts.json --force
```

## Build & preview site

```sh
# Preview locally
hugo server

# Build for production
hugo --minify

# Build with search (requires npx/Node)
hugo --minify && npx pagefind --site public
```

## Deploy

Deployment to GitHub Pages is handled automatically via GitHub Actions on push to `main`.
