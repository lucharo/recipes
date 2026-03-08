"""Fetch saved Instagram recipes and generate markdown files + index.

Primary workflow:
  1. Export saved posts from Instagram via browser (see fetch_saved_posts.js)
  2. Process the JSON dump: uv run python fetch_recipes.py --from-json instagram_saved_posts.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import jinja2
import requests
import tqdm

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
POSTS_DIR = DOCS / "posts"
IMG_DIR = DOCS / "img"
RECIPE_TEMPLATE = ROOT / "recipe.md.jinja2"
INDEX_TEMPLATE = ROOT / "index.j2"
INDEX_OUT = DOCS / "index.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Instagram saved recipes")
    parser.add_argument(
        "--from-json",
        type=Path,
        help="Process a JSON dump of saved posts (from browser export)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing recipe files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fetched without writing anything",
    )
    parser.add_argument(
        "--rebuild-index-only",
        action="store_true",
        help="Skip fetching; just rebuild docs/index.md from existing posts",
    )
    return parser.parse_args()


def load_json_posts(json_path: Path) -> list[dict]:
    """Load posts from a JSON dump exported via browser."""
    with open(json_path) as f:
        posts = json.load(f)
    print(f"Loaded {len(posts)} posts from {json_path}")
    return posts


def make_filename(post: dict) -> str:
    """Generate filename from username and post timestamp."""
    taken_at = post["taken_at"]
    if isinstance(taken_at, (int, float)):
        dt = datetime.fromtimestamp(taken_at, tz=timezone.utc)
    else:
        dt = datetime.fromisoformat(str(taken_at))
    ts = dt.strftime("%d-%m-%Y_%H%M")
    return f"{post['username']}_{ts}"


def process_post(
    post: dict, template: jinja2.Template, *, force: bool, dry_run: bool
) -> str | None:
    """Process a single post. Returns filename if written, None if skipped."""
    fname = make_filename(post)
    md_path = POSTS_DIR / f"{fname}.md"
    img_path = IMG_DIR / f"{fname}.png"

    if md_path.exists() and not force:
        return None  # skip existing

    caption = post.get("caption_text") or ""
    caption_lines = caption.split("\n")
    title = caption_lines[0] if caption_lines else "(no caption)"

    if dry_run:
        print(f"  [dry-run] Would write: {fname}.md — {title[:60]}")
        return fname

    # Download image
    image_rel = f"img/{fname}.png"
    thumbnail_url = post.get("thumbnail_url")
    try:
        if thumbnail_url and (not img_path.exists() or force):
            img_data = requests.get(thumbnail_url, timeout=30).content
            img_path.write_bytes(img_data)
    except Exception:
        image_rel = "img/noimage.jpg"

    if not img_path.exists():
        image_rel = "img/noimage.jpg"

    # Parse caption
    body_lines = caption_lines[1:]
    text = "\n".join(f"{line}  " for line in body_lines)
    text = text.replace("#", "\\#")

    # Build post date
    taken_at = post["taken_at"]
    if isinstance(taken_at, (int, float)):
        post_date = datetime.fromtimestamp(taken_at, tz=timezone.utc)
    else:
        post_date = datetime.fromisoformat(str(taken_at))

    # Render markdown
    rendered = template.render(
        POST_DATE=post_date,
        TITLE=title,
        IMAGE_PATH=image_rel,
        AUTHOR_HANDLE=post["username"],
        AUTHOR_NAME=post.get("full_name", post["username"]),
        POST_URL=f"https://instagram.com/p/{post['code']}",
        RECIPE_BODY=text,
    )

    md_path.write_text(rendered, encoding="utf-8")
    return fname


def rebuild_index() -> int:
    """Rebuild docs/index.md from all existing post files. Returns recipe count."""
    posts = sorted(POSTS_DIR.glob("*.md"))
    cards = []
    for post_path in posts:
        fname = post_path.stem
        img_path = IMG_DIR / f"{fname}.png"
        image_rel = f"img/{fname}.png" if img_path.exists() else "img/noimage.jpg"

        # Read first heading line from the file for the title
        title = fname  # fallback
        for line in post_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract author handle from filename (everything before the date pattern)
        parts = fname.rsplit("_", 2)
        author = parts[0] if len(parts) >= 3 else fname

        card = (
            f'- [![]({image_rel}){{: style="width:100%;height:200px;'
            f'object-fit: cover;object-position: center;" }}](posts/{fname}.md)  \n'
            f"        **@{author}** - {title[:50]} [Read more...](posts/{fname}.md)"
        )
        cards.append(card)

    recipe_md = "\n".join(cards)

    template_text = INDEX_TEMPLATE.read_text(encoding="utf-8")
    template = jinja2.Template(template_text)
    index_content = template.render(RECIPE_MD=recipe_md, RECIPE_COUNT=len(cards))
    INDEX_OUT.write_text(index_content, encoding="utf-8")

    return len(cards)


def main():
    args = parse_args()

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    if args.rebuild_index_only:
        count = rebuild_index()
        print(f"Index rebuilt with {count} recipes.")
        return

    if not args.from_json:
        print("Usage: uv run python fetch_recipes.py --from-json instagram_saved_posts.json")
        print()
        print("To export saved posts from Instagram:")
        print("  1. Log into instagram.com in Chrome")
        print("  2. Open browser console (F12)")
        print("  3. Paste and run the fetch script (see fetch_saved_posts.js)")
        print("  4. A JSON file will be downloaded automatically")
        print("  5. Run this script with --from-json <path to json>")
        sys.exit(1)

    posts = load_json_posts(args.from_json)

    template_text = RECIPE_TEMPLATE.read_text(encoding="utf-8")
    template = jinja2.Template(template_text)

    new_count = 0
    skip_count = 0

    for post in tqdm.tqdm(posts, desc="Processing posts"):
        result = process_post(post, template, force=args.force, dry_run=args.dry_run)
        if result is not None:
            new_count += 1
        else:
            skip_count += 1

    if not args.dry_run:
        total = rebuild_index()
        print(f"\nDone! {new_count} new, {skip_count} skipped, {total} total in index.")
    else:
        print(f"\n[dry-run] Would fetch {new_count} new, {skip_count} already exist.")


if __name__ == "__main__":
    main()
