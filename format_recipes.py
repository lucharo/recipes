"""Normalise saved captions without inventing ingredients or cooking instructions.

Usage: uv run python format_recipes.py [--check] [content-directory]
The original captions remain in Git history. Unclassified prose stays in Notes.
"""

import argparse
import json
import re
from pathlib import Path

import yaml

CONTENT_DIR = Path(__file__).parent / "content" / "recipes"
FORMAT_VERSION = 1
MISSING_INGREDIENTS = "No separate ingredient list was identified. Check the notes and original source."
MISSING_METHOD = "No separate cooking method was identified. Check the notes and original source."
NUMBERED = re.compile(r"^(?:step\s+)?\d+[.)](?=\s|\D)\s*", re.I)
BULLET = re.compile(r"^[-•●▪◦*]+\s*")
QUANTITY = re.compile(r"^(?:\d|[¼½¾⅓⅔⅛⅜⅝⅞]|a\s+(?:pinch|knob|splash|handful)|"
                      r"(?:small\s+)?(?:pinch|handful|juice|zest)\b)", re.I)
ACTION = re.compile(
    r"^(?:(?:first|then|next|now|finally|carefully|gently|meanwhile|finely)\b[, :]*)?\s*"
    r"(?:add|heat|preheat|mix|stir|whisk|blend|combine|cook|bake|roast|fry|"
    r"saute|sauté|boil|simmer|bring|pour|drain|rinse|chop|slice|cut|dice|"
    r"peel|place|put|transfer|serve|season|toss|coat|spread|melt|fold|cover|"
    r"remove|let|leave|allow|set|take|start|wash|break|wrap|mash|squeeze|"
    r"roll|knead|freeze|refrigerate|soak|press|shred|grate|brush|top|line|sprinkle|"
    r"make|koche|if\b|once\b|enjoy\b|in a\b|in the\b|in another\b|to make\b)\b", re.I)
SECTION = re.compile(
    r"^(ingredients?|ingredienti|ingredientes|method|instructions?|directions?|"
    r"preparation|procedimento|procedimiento|what you[’']?ll need|you[’']?ll need)"
    r"\s*[:\-–—]?\s*([\[(][^\])]*[\])])?$", re.I)
PROMO = re.compile(r"^(?:follow\b|save\b|tag\b|find the full|full recipe|link in|"
                   r"check out|https?://|www\.|#|notes?\b|tips?\b|"
                   r"nutrition\b|macros\b)", re.I)


def clean_line(line: str) -> str:
    line = re.sub(r"[\u200b\u200c\u200d\u2060\u2063\ufeff\u2800]", "", line)
    return re.sub(r"\s+", " ", line).strip()


def list_text(line: str) -> str:
    line = re.sub(r"(\d)\ufe0f?\u20e3", r"\1. ", line)
    line = re.sub(r"[❶-❾①-⑨]", lambda m: str(
        ord(m[0]) - (ord('❶') if ord(m[0]) >= ord('❶') else ord('①')) + 1
    ) + '. ', line)
    line = BULLET.sub("", line.strip("*"))
    # Emoji bullets are decoration; keep letters, quantities and literal punctuation.
    return re.sub(r"^[^\w¼½¾⅓⅔⅛⅜⅝⅞(]+", "", line).strip()


def heading_text(line: str) -> str:
    # Strip decorative emoji/punctuation around headings, keeping their words.
    return re.sub(r"^[^\w(]+|[^\w):]+$", "", line).strip()


def is_noise(line: str) -> bool:
    return not re.search(r"\w", line) or bool(re.fullmatch(r"(?:#[\w]+\s*)+", line))


def split_caption(body: str) -> tuple[list[str], list[str], list[str]]:
    """Keep uncertain text in Notes; explicit sections and list context guide parsing."""
    ingredients, method, notes = [], [], []
    section = "notes"
    lines = [clean_line(raw) for raw in body.splitlines() if not is_noise(clean_line(raw))]
    group = ""
    method_group = ""
    day_group = False

    def add_step(text: str):
        nonlocal method_group
        if group and group != method_group:
            method.append(f"### {group}")
            method_group = group
        method.append(text)

    for index, line in enumerate(lines):
        text = list_text(line)
        heading = SECTION.fullmatch(heading_text(line))
        if heading:
            word, detail = heading.groups()
            section = "ingredients" if re.match(r"ingredient|what|you", word, re.I) else "method"
            group = method_group = ""
            day_group = False
            if detail:
                notes.append(detail.strip("()[]"))
            continue
        inline = re.match(r"^(?:method|instructions?|directions?|preparation):\s*(.+)", text, re.I)
        if inline:
            section = "method"
            group = method_group = ""
            day_group = False
            add_step(inline[1])
            continue
        if re.fullmatch(r"(?:the )?recipe\s*:?", heading_text(line), re.I):
            continue
        numbered = NUMBERED.match(text)
        action = ACTION.match(NUMBERED.sub("", text))
        following = list_text(lines[index + 1]) if index + 1 < len(lines) else ""
        is_day = bool(re.match(r"^(?:day|día)\s+\d+\s*$", text, re.I))
        is_group = (
            len(text) < 70 and not action and not QUANTITY.match(text)
            and QUANTITY.match(following)
            and (text.endswith(":") or text.isupper() or line.startswith("*"))
        )
        if is_day or is_group:
            group = text.rstrip(":*")
            day_group = is_day
            section = "ingredients"
            ingredients.append(f"### {group}")
            continue
        summary = re.match(
            r"^\d+(?:[-–/]\d+)?\s+(?:servings?|portions?)\s*$|"
            r"^\d+[- ]ingredients?\b|"
            r"^\d+(?:\.\d+)?\s*(?:k?cals?|calories|g\s+(?:protein|carbs|fat))\b", text, re.I
        )
        if PROMO.match(text) or summary:
            notes.append(line)
            section = "notes"
        elif numbered and (action or section == "method" or len(text) > 100):
            section = "method"
            add_step(NUMBERED.sub("", text))
        elif action and (section != "notes" or len(text) > 60):
            section = "method"
            add_step(text)
        elif QUANTITY.match(text) and not numbered and len(text) < 220:
            section = "ingredients"
            ingredients.append(text)
        elif section == "method" or day_group or (
            section == "ingredients" and re.match(r"^[A-ZÄÖÜ]{3,}(?:\s+\w|/)", text)
            and ("/" in text or len(text) > 70)
        ):
            # Preserve continuation order, including conditions and non-English prose.
            section = "method"
            add_step(NUMBERED.sub("", text))
        elif section == "ingredients" and len(text) < 150 and not re.search(
            r"https?://|www\.|#|@|\b(?:follow|recipe|blog|bio|enjoy|save|comment)\b", text, re.I
        ):
            ingredients.append(text)
        else:
            notes.append(line)
            section = "notes"
    return ingredients, method, notes


def short_title(title: str) -> tuple[str, str]:
    """Split only on an existing sentence/delimiter, never guess a dish name."""
    title = clean_line(title)
    if len(title) <= 100:
        return title, ""
    for match in re.finditer(r",\s|\s[-–—|]\s|[.!?]\s", title):
        prefix = title[:match.start()].strip()
        if 8 <= len(prefix) <= 100 and prefix.isupper():
            return prefix, title
    return title, ""


def render_body(ingredients: list[str], method: list[str], notes: list[str]) -> str:
    sections = ["## Ingredients", ""]
    for item in ingredients:
        if item.startswith("### "):
            sections += ["", item, ""]
        elif item.endswith(":") or (item.isupper() and not QUANTITY.match(item)):
            sections += ["", f"### {item.rstrip(':')}", ""]
        else:
            sections.append(f"- {item}")
    if not ingredients:
        sections.append(MISSING_INGREDIENTS)
    sections += ["", "## Method", ""]
    step = 0
    for item in method:
        if item.startswith("### "):
            sections += ["", item, ""]
        else:
            step += 1
            sections.append(f"{step}. {item}")
    if not method:
        sections.append(MISSING_METHOD)
    if notes:
        sections += ["", "## Notes", "", "\n\n".join(dict.fromkeys(notes))]
    return "\n".join(sections) + "\n"


def format_document(document: str) -> str:
    parts = re.split(r"^---[ \t]*$", document, maxsplit=2, flags=re.MULTILINE)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError("Expected YAML front matter")
    front, body = parts[1], parts[2]
    metadata = yaml.safe_load(front)
    if not isinstance(metadata, dict) or not isinstance(metadata.get("title"), str):
        raise ValueError("Expected a recipe title")
    if metadata.get("recipe_format") == FORMAT_VERSION:
        # Formatted files are human-editable; never reinterpret their sections.
        return document

    ingredients, method, notes = split_caption(body)
    title, description = short_title(metadata["title"])
    if description:
        notes.insert(0, description)
        # Dump the mapping only when changing the title: supports multiline YAML too.
        metadata["title"] = title
        front = "\n" + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    quality = "complete" if ingredients and method else "ingredients_only" if ingredients else "minimal"
    if not ingredients and not method and metadata.get("recipe_quality") == "video_only":
        quality = "video_only"
    if re.search(r"^recipe_quality:", front, re.MULTILINE):
        front = re.sub(r"^recipe_quality:.*$", f'recipe_quality: "{quality}"', front, flags=re.MULTILINE)
    else:
        front = front.rstrip() + f'\nrecipe_quality: "{quality}"\n'
    front = front.rstrip() + f"\nrecipe_format: {FORMAT_VERSION}\n"
    return f"---{front}---\n\n{render_body(ingredients, method, notes)}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=CONTENT_DIR)
    parser.add_argument("--check", action="store_true", help="Report pending changes without writing")
    args = parser.parse_args()
    files = sorted(p for p in args.directory.glob("*.md") if p.name != "_index.md")
    if not files:
        parser.error(f"No recipes found in {args.directory}")
    # Validate the whole batch before the first write.
    changes = []
    for file in files:
        original = file.read_text(encoding="utf-8")
        formatted = format_document(original)
        if formatted != original:
            changes.append((file, formatted))
    if not args.check:
        for file, formatted in changes:
            file.write_text(formatted, encoding="utf-8")
    print(json.dumps({"recipes": len(files), "pending" if args.check else "formatted": len(changes)}))
    return 1 if args.check and changes else 0


if __name__ == "__main__":
    raise SystemExit(main())
