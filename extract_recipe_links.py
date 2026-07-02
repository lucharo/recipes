"""Extract external recipe URLs from recipe markdown files.

Finds URLs embedded in recipe captions that link to the actual recipe
on the author's website (not Instagram links).

Usage:
    uv run python extract_recipe_links.py
    uv run python extract_recipe_links.py --update  # Add links to front matter
"""

import argparse
import json
import re
from pathlib import Path

CONTENT_DIR = Path(__file__).parent / "content" / "recipes"
OUTPUT = Path(__file__).parent / "recipe_links.json"

URL_PATTERN = re.compile(r'https?://[^\s<>")\]\\]+')
SKIP_DOMAINS = {
    "instagram.com",
    "www.instagram.com",
    "bit.ly",
    "linktr.ee",
    "amzn.to",
    "amazon.com",
    "www.amazon.com",
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "tiktok.com",
    "www.tiktok.com",
    "facebook.com",
    "www.facebook.com",
    "twitter.com",
    "x.com",
}


def extract_links() -> dict[str, list[str]]:
    """Extract external URLs from recipe body text."""
    results = {}

    for f in sorted(CONTENT_DIR.glob("*.md")):
        if f.name == "_index.md":
            continue

        text = f.read_text()
        # Split on front matter delimiter lines only, so "---" inside
        # front matter values or body text can't break the parse.
        parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
        if len(parts) < 3:
            continue

        body = parts[2]
        urls = URL_PATTERN.findall(body)

        # Clean trailing punctuation and filter
        external = []
        for u in urls:
            # Strip invisible Unicode characters (Instagram captions often
            # end lines with U+2063) and trailing punctuation.
            u = re.sub("[\\u2028\\u2029\\u200b\\u200c\\u200d\\u2060\\u2063\\ufeff]", "", u)
            u = u.rstrip(".,:;!?*")
            domain = u.split("//", 1)[-1].split("/", 1)[0].split("?", 1)[0]
            if domain not in SKIP_DOMAINS:
                external.append(u)

        # Deduplicate preserving order
        seen = set()
        unique = []
        for u in external:
            if u not in seen:
                seen.add(u)
                unique.append(u)

        if unique:
            results[f.stem] = unique

    return results


def update_front_matter(links: dict[str, list[str]]) -> int:
    """Add recipe_link field to front matter for recipes with external URLs."""
    count = 0
    for stem, urls in links.items():
        f = CONTENT_DIR / f"{stem}.md"
        if not f.exists():
            continue

        text = f.read_text()
        if "recipe_link:" in text:
            continue

        # Use the first URL as the primary recipe link
        link = urls[0]
        # Replace only the first occurrence (the front matter field), so a
        # "recipe_quality:" string in the body can't get YAML injected.
        text = text.replace(
            'recipe_quality:',
            f'recipe_link: "{link}"\nrecipe_quality:',
            1,
        )
        f.write_text(text)
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="Add links to front matter")
    args = parser.parse_args()

    links = extract_links()
    print(f"Found {len(links)} recipes with external URLs")

    # Save to JSON
    OUTPUT.write_text(json.dumps(links, indent=2))
    print(f"Saved to {OUTPUT}")

    if args.update:
        count = update_front_matter(links)
        print(f"Updated {count} recipe front matter files")


if __name__ == "__main__":
    main()
