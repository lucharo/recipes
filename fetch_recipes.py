"""Fetch saved Instagram recipes and generate Hugo content.

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
CONTENT_DIR = ROOT / "content" / "recipes"
IMG_DIR = ROOT / "static" / "img"
RECIPE_TEMPLATE = ROOT / "recipe.md.jinja2"


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
    md_path = CONTENT_DIR / f"{fname}.md"
    img_path = IMG_DIR / f"{fname}.png"

    if md_path.exists() and not force:
        return None

    caption = post.get("caption_text") or ""
    caption_lines = caption.split("\n")
    title = caption_lines[0] if caption_lines else "(no caption)"

    if dry_run:
        print(f"  [dry-run] Would write: {fname}.md — {title[:60]}")
        return fname

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

    body_lines = caption_lines[1:]
    text = "\n".join(body_lines)

    taken_at = post["taken_at"]
    if isinstance(taken_at, (int, float)):
        post_date = datetime.fromtimestamp(taken_at, tz=timezone.utc)
    else:
        post_date = datetime.fromisoformat(str(taken_at))

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


def main():
    args = parse_args()

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

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

    print(f"\nDone! {new_count} new, {skip_count} skipped.")


if __name__ == "__main__":
    main()
