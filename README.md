# Instagram Recipe Explorer

I love discovering recipes on Instagram, but they quickly add up and it becomes harder to explore the previously saved recipes.

In this repo and website we achieve the following:

* Export saved recipe posts from Instagram via browser API
* Turn each post into a markdown document using a `jinja2` template
* Build a searchable static site with Hugo, featuring side-by-side recipe layouts and ingredient filtering

Visit the site: <https://testkitchen.luischav.es>

The "tried and tested" recipes go to [cook.luischav.es](https://cook.luischav.es/).

## Setup

```sh
uv sync
```

Requires [Hugo](https://gohugo.io/installation/) for site building.

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
