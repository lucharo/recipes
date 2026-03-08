# Instagram Recipe Explorer

I love discovering recipes on Instagram, but they quickly add up and it becomes harder to explore the previously saved recipes.

In this repo and website we achieve the following:

* Fetch saved recipes from Instagram collections via `instagrapi`
* Turn each post into a markdown document using a `jinja2` template
* Build a minimalist searchable page with `mkdocs-material`

The main reason I did this is to get the search bar that mkdocs provides. If you want to explore the recipes I have saved, visit: <https://testkitchen.luischav.es>

## Setup

```sh
uv sync
```

## Fetch recipes

Set your Instagram credentials in `.env`:

```
IG_USER=your_username
IG_PSWD=your_password
```

Then fetch:

```sh
# Fetch from all saved collections (skips existing recipes)
uv run python fetch_recipes.py

# Fetch from a specific collection only
uv run python fetch_recipes.py --collection "Recipes"

# Overwrite all existing recipes
uv run python fetch_recipes.py --force

# Preview what would be fetched
uv run python fetch_recipes.py --dry-run

# Just rebuild the index without fetching
uv run python fetch_recipes.py --rebuild-index-only
```

## Build & publish site

**Build locally:**

```sh
uv run mkdocs build
```

**Preview locally:**

```sh
uv run mkdocs serve
```

**Publish to GitHub Pages:**

```sh
uv run mkdocs gh-deploy
```

## TODO

* Add tags to recipes that I have tried, perhaps as markdown metadata
* Add I'm feeling lucky button
* Add js/ts logic to easily scale recipes linearly
* Do more advanced parsing of recipes - maybe with an LLM
