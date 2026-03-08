"""One-time migration: convert MkDocs recipe posts to Hugo format."""

import re
import shutil
from pathlib import Path

DOCS_POSTS = Path("docs/posts")
DOCS_IMG = Path("docs/img")
DOCS_CNAME = Path("docs/CNAME")
CONTENT_RECIPES = Path("content/recipes")
STATIC_IMG = Path("static/img")
STATIC_CNAME = Path("static/CNAME")


def parse_mkdocs_post(md_path: Path) -> dict:
    """Parse a MkDocs recipe markdown file into components."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Extract front matter
    date = ""
    i = 0
    if lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            line = lines[i].strip()
            if line.startswith("posted on:"):
                date = line.split("posted on:", 1)[1].strip()
            i += 1
        i += 1  # skip closing ---

    # Skip blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Title (# line)
    title = ""
    if i < len(lines) and lines[i].startswith("# "):
        title = lines[i][2:].strip()
        i += 1

    # Skip blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Attribution (> recipe by ...)
    author_handle = ""
    author_name = ""
    post_url = ""
    if i < len(lines) and lines[i].startswith(">"):
        attr_line = lines[i]
        # Next line may be continuation
        if i + 1 < len(lines) and not lines[i + 1].startswith(">") and lines[i + 1].strip().startswith("("):
            attr_line += " " + lines[i + 1]
            i += 1
        elif i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith("#") and not lines[i + 1].startswith("!"):
            attr_line += " " + lines[i + 1]
            i += 1

        handle_match = re.search(r"@(\w[\w.]*)", attr_line)
        if handle_match:
            author_handle = handle_match.group(1)

        name_match = re.search(r"\(([^)]+)\)\s*-\s*\[", attr_line)
        if name_match:
            author_name = name_match.group(1)

        url_match = re.search(r"\[see original post\]\((https?://[^)]+)\)", attr_line)
        if url_match:
            post_url = url_match.group(1)
        i += 1

    # Skip blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Image line ![](../img/...)
    image = ""
    if i < len(lines) and lines[i].startswith("!["):
        img_match = re.search(r"\.\./img/([^)]+)", lines[i])
        if img_match:
            image = f"img/{img_match.group(1)}"
        i += 1

    # Rest is body
    body = "\n".join(lines[i:]).strip()
    # Clean up escaped hashtags
    body = body.replace("\\#", "#")

    return {
        "title": title,
        "date": date,
        "author_handle": author_handle,
        "author_name": author_name,
        "post_url": post_url,
        "image": image,
        "body": body,
    }


def write_hugo_post(data: dict, out_path: Path):
    """Write a Hugo-format recipe markdown file."""
    # Escape quotes in title for YAML
    safe_title = data["title"].replace('"', '\\"')

    lines = [
        "---",
        f'title: "{safe_title}"',
        f'date: {data["date"]}',
        f'author_handle: "{data["author_handle"]}"',
        f'author_name: "{data["author_name"]}"',
        f'post_url: "{data["post_url"]}"',
        f'image: "{data["image"]}"',
        'recipe_quality: ""',
        "---",
        "",
        data["body"],
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    CONTENT_RECIPES.mkdir(parents=True, exist_ok=True)
    STATIC_IMG.mkdir(parents=True, exist_ok=True)

    # Migrate posts
    posts = sorted(DOCS_POSTS.glob("*.md"))
    print(f"Migrating {len(posts)} recipe posts...")

    for md_path in posts:
        data = parse_mkdocs_post(md_path)
        slug = md_path.stem
        out_path = CONTENT_RECIPES / f"{slug}.md"
        write_hugo_post(data, out_path)

    print(f"Wrote {len(posts)} Hugo posts to {CONTENT_RECIPES}/")

    # Copy images
    images = list(DOCS_IMG.glob("*"))
    print(f"Copying {len(images)} images...")
    for img in images:
        dest = STATIC_IMG / img.name
        if not dest.exists():
            shutil.copy2(img, dest)

    # Copy CNAME
    if DOCS_CNAME.exists():
        shutil.copy2(DOCS_CNAME, STATIC_CNAME)
        print("Copied CNAME")

    print("Done!")


if __name__ == "__main__":
    main()
