# Instagram Recipe Explorer

I love discovering recipes on Instagram, but they quickly add up and it becomes harder to explore the previously saved recipes.

In this repo and website we achieve the following:

* Fetch saved recipes Instagram collection via `instagrapi` package (code not shown)
* Turn each post into a markdown document using a `jinja2` template
* Build documentation with `material-mkdocs`. Add some CSS in the index doc to recipes as a nice grid

The main reason I did this is to get the search bar that mkdocs provides. If you want to explore the recipes I have saved, visit: <https://luischaves.xyz/recipes>

## Build & Publish site

First run `poetry shell`

**Build locally:**

```sh
mkdocs build
```

**Publish:**

```sh
mkdocs  
```

## TODO

* Add tags to recipes that I have tried, perhaps as markdown metadata (still don't know how mkdocs handles metadata)
* Add I'm feeling lucky button
* Add js/ts logic to easily scale recipes linearly
* Do more advanced parsing of recipes
* Keep an eye out for when they make [the blog feature of material-mkdocs](https://squidfunk.github.io/mkdocs-material/setup/setting-up-a-blog/) available
