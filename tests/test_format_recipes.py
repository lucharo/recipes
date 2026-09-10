import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import jinja2
import yaml

import fetch_recipes
from format_recipes import (
    CONTENT_DIR, MISSING_INGREDIENTS, MISSING_METHOD, format_document, main, split_caption,
)

FIXTURES = Path(__file__).parent / "fixtures"


class RecipeFormattingTests(unittest.TestCase):
    def test_beans_keeps_quantities_and_every_cooking_paragraph(self):
        original = (FIXTURES / "carolinagelen_06-01-2023_2101.md").read_text()

        result = format_document(original)

        self.assertIn("title: BEANS ALLA VODKA\n", result)
        body = result.split("## Ingredients", 1)[1]
        self.assertEqual(len(re.findall(r"^- ", body, re.M)), 13)
        self.assertEqual(len(re.findall(r"^\d+\. ", result, re.M)), 4)
        self.assertIn("- 1 x 15 oz (500 g) can butter beans, drained and rinsed", result)
        self.assertIn("3. Add the freshly grated cheese, a knob of butter", result)
        self.assertNotIn("#penneallavodka", result)

    def test_inline_method_and_decimal_quantities(self):
        caption = "Ingredients:\n1.5 cups flour\n1/2 tsp salt\nDirections: Mix well.\nBake for 20 minutes."

        result = split_caption(caption)

        self.assertEqual(result, (["1.5 cups flour", "1/2 tsp salt"],
                                  ["Mix well.", "Bake for 20 minutes."], []))

    def test_emoji_numbers_are_steps_not_ingredients(self):
        original = (FIXTURES / "foodypopz_01-11-2021_0711.md").read_text()

        result = format_document(original)

        self.assertEqual(len(re.findall(r"^\d+\. ", result, re.M)), 4)
        self.assertIn("4. Finish with a splash of olive oil", result)
        self.assertNotIn("- 1️⃣", result)

    def test_unlabelled_method_preserves_middle_paragraph_order(self):
        original = (FIXTURES / "rgveganfood_09-04-2023_1304.md").read_text()

        result = format_document(original)

        self.assertIn("3. In another shallow bowl, mix together", result)
        self.assertIn("4. Place the cauliflower florets", result)

    def test_multipart_recipe_keeps_broth_and_gravy_ingredients(self):
        original = (FIXTURES / "veganrecipesideas_26-11-2021_1711.md").read_text()

        result = format_document(original)

        ingredients, method = result.split("## Ingredients", 1)[1].split("## Method", 1)
        self.assertIn("### Broth\n\n- 4 cups (1 L) veg stock", ingredients)
        self.assertIn("- 1 cup (250ml) plant milk", ingredients)
        self.assertIn("### Broth\n\n2. COOK the steaks for 15mins/FRY them afterwards", method)
        self.assertNotIn("4 cups (1 L) veg stock", method)
        self.assertNotIn("KOCHE die cremig.", ingredients)
        self.assertIn("KOCHE die cremig.", method)

    def test_first_preparation_is_not_an_ingredient(self):
        original = (FIXTURES / "woon.heng_28-10-2021_1410.md").read_text()

        result = format_document(original)

        ingredients, method = result.split("## Ingredients", 1)[1].split("## Method", 1)
        self.assertNotIn("First, whisk", ingredients)
        self.assertIn("1. First, whisk together soy sauce", method)

    def test_sourdough_preserves_day_groups_and_spanish_instructions(self):
        original = (FIXTURES / "abeautifulmess.es_13-03-2025_1127.md").read_text()

        result = format_document(original)

        ingredients, method = result.split("## Ingredients", 1)[1].split("## Method", 1)
        self.assertIn("### DÍA 1", ingredients)
        self.assertIn("### DÍA 1\n\n1. Mezcla", method)
        self.assertIn("Descarta la mitad", method)
        self.assertNotIn(MISSING_METHOD, method)

    def test_conditional_preparation_and_final_freeze_stay_in_order(self):
        original = (FIXTURES / "crowded_kitchen_12-06-2023_1406.md").read_text()

        result = format_document(original)

        method = result.split("## Method", 1)[1].split("## Notes", 1)[0]
        self.assertIn("1. If you want to serve", method)
        self.assertIn("2. Add all ingredients", method)
        self.assertIn("3. Enjoy right away", method)
        self.assertIn("(2-3 hours)", method)

    def test_incomplete_caption_keeps_source_and_uncertain_text(self):
        original = '---\ntitle: Dinner\npost_url: https://instagram.com/p/example\n---\nSee my blog for the recipe.\n#dinner #food\n'

        result = format_document(original)

        self.assertIn(MISSING_INGREDIENTS, result)
        self.assertIn(MISSING_METHOD, result)
        self.assertIn("See my blog for the recipe.", result)
        self.assertIn("post_url: https://instagram.com/p/example", result)

    def test_formatted_manual_edits_survive_second_pass(self):
        original = (FIXTURES / "carolinagelen_06-01-2023_2101.md").read_text()
        edited = format_document(original).replace("## Notes", "## Notes\n\nMy own cooking note.")

        result = format_document(edited)

        self.assertEqual(result, edited)

    def test_cli_checks_before_writing_and_includes_underscore_author(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recipe = root / "__author.md"
            original = '---\ntitle: Toast\n---\nIngredients:\n2 slices bread\nMethod:\nToast the bread.\n'
            recipe.write_text(original)
            (root / "_index.md").write_text("untouched index")

            with patch("sys.argv", ["format_recipes.py", "--check", directory]), contextlib.redirect_stdout(io.StringIO()):
                check = main()

            self.assertEqual(check, 1)
            self.assertEqual(recipe.read_text(), original)
            with patch("sys.argv", ["format_recipes.py", directory]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
            self.assertIn("## Ingredients", recipe.read_text())
            self.assertEqual((root / "_index.md").read_text(), "untouched index")

    def test_malformed_batch_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = '---\ntitle: Toast\n---\n2 slices bread\n'
            (root / "a.md").write_text(original)
            (root / "z.md").write_text("no front matter")

            with patch("sys.argv", ["format_recipes.py", directory]):
                with self.assertRaises(ValueError):
                    main()

            self.assertEqual((root / "a.md").read_text(), original)

    def test_importer_writes_formatted_recipe(self):
        post = {"username": "cook", "taken_at": 1700000000, "code": "example",
                "caption_text": "Beans\nIngredients:\n1 tin beans\nMethod:\nHeat the beans."}
        template = jinja2.Template(fetch_recipes.RECIPE_TEMPLATE.read_text())
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(fetch_recipes, "CONTENT_DIR", Path(directory)), patch.object(fetch_recipes, "IMG_DIR", Path(directory)):
                filename = fetch_recipes.process_post(post, template, force=False, dry_run=False)

            written = (Path(directory) / f"{filename}.md").read_text()
            self.assertIn("## Ingredients\n\n- 1 tin beans", written)
            self.assertIn("## Method\n\n1. Heat the beans.", written)

    def test_entire_collection_has_consistent_sections_and_valid_metadata(self):
        recipes = [p for p in CONTENT_DIR.glob("*.md") if p.name != "_index.md"]
        self.assertGreater(len(recipes), 600)
        for recipe in recipes:
            with self.subTest(recipe=recipe.name):
                text = recipe.read_text()
                metadata = yaml.safe_load(re.split(r"^---[ \t]*$", text, maxsplit=2, flags=re.M)[1])
                self.assertEqual(metadata["recipe_format"], 1)
                self.assertEqual(text.count("\n## Ingredients\n"), 1)
                self.assertEqual(text.count("\n## Method\n"), 1)
                self.assertEqual(format_document(text), text)
