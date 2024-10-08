# Instagram Recipe Explorer

I love discovering recipes on Instagram, but they quickly add up and it becomes harder to explore the previously saved recipes.

In this repo and website we achieve the following:

* Fetch saved recipes Instagram collection via `instagrapi` package (code not shown)
* Turn each post into a markdown document using a `jinja2` template
* Build minimalist page with `material-mkdocs`, usually a docs page but has an easy implementation of a search feature which is useful here.

The main reason I did this is to get the search bar that mkdocs provides. If you want to explore the recipes I have saved, visit: <https://testkitchen.luischav.es>

## Build & Publish site

First run `poetry shell` and execute the notebook that fetches, parses and saves the recipes (`jupyter nbconvert --to notebook --execute ig_api.ipynb`)

**Build locally:**

```sh
mkdocs build
```

**Publish:**

```sh
mkdocs gh-deploy
```

## TODO

* Add tags to recipes that I have tried, perhaps as markdown metadata (still don't know how mkdocs handles metadata)
* Add I'm feeling lucky button
* Add js/ts logic to easily scale recipes linearly
* Do more advanced parsing of recipes - maybe with an LLM
