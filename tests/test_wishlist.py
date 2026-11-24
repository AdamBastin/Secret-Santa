import tempfile
import unittest
from pathlib import Path

from werkzeug.datastructures import MultiDict

from app import create_app
from app.spend_limit import format_spend_limit, parse_spend_limit
from app.wishlist import collect_wishlist_items


class WishlistValidationTests(unittest.TestCase):
    def test_requires_at_least_one_item(self):
        items, error = collect_wishlist_items(MultiDict([("items", "  ")]))

        self.assertEqual(items, [])
        self.assertEqual(error, "Add at least one item to your wishlist.")

    def test_rejects_more_than_five_items(self):
        form = MultiDict(("items", f"Gift {number}") for number in range(6))

        items, error = collect_wishlist_items(form)

        self.assertEqual(len(items), 6)
        self.assertEqual(error, "Your wishlist can contain up to 5 items.")


class SpendLimitTests(unittest.TestCase):
    def test_parses_and_formats_currency_without_float_rounding(self):
        self.assertEqual(parse_spend_limit("75.50"), 7550)
        self.assertEqual(format_spend_limit(7550), "$75.50")

    def test_rejects_non_positive_amounts(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            parse_spend_limit("0")


class WishlistFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        database_path = Path(self.temp_directory.name) / "test.sqlite"
        self.app = create_app(
            {"TESTING": True, "DATABASE": database_path, "SECRET_KEY": "test"}
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_directory.cleanup()

    def register(self, name, pin):
        return self.client.post(
            "/register",
            data={"name": name, "pin": pin},
            follow_redirects=True,
        )

    def save_wishlist(self, *items):
        return self.client.post(
            "/wishlist",
            data=MultiDict(("items", item) for item in items),
            follow_redirects=True,
        )

    def test_registration_leads_to_wishlist_and_saves_items(self):
        response = self.register("Alice", "1234")
        self.assertIn(b"Build your wishlist", response.data)
        self.assertIn(b"$50.00", response.data)

        response = self.save_wishlist("A novel", "Loose-leaf tea")
        self.assertIn(b"Your wishlist is saved", response.data)

        response = self.client.get("/admin")
        self.assertIn(b"<th>Wishlist</th>", response.data)
        self.assertIn(b"Complete", response.data)

    def test_questionnaire_url_redirects_to_wishlist(self):
        self.register("Alice", "1234")

        response = self.client.get("/questionnaire")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/wishlist"))

    def test_secret_santa_sees_their_recipient_wishlist(self):
        self.register("Alice", "1234")
        self.save_wishlist("A novel")
        response = self.client.post(
            "/admin",
            data={"spend_limit": "75.50"},
            follow_redirects=True,
        )
        self.assertIn(b"Spending limit updated", response.data)
        self.register("Bob", "5678")
        self.save_wishlist("Coffee beans", "Warm socks")

        self.register("Alice", "1234")
        self.client.post("/admin/assignments/start")
        admin_response = self.client.get("/admin/assignments")
        response = self.client.get("/waiting")

        self.assertIn(b'<details class="assignment-reveal">', admin_response.data)
        self.assertIn(b"Reveal assignment", admin_response.data)
        self.assertNotIn(b'<details class="assignment-reveal" open>', admin_response.data)
        self.assertIn(b"Bob", response.data)
        self.assertIn(b"$75.50", response.data)
        self.assertIn(b"Coffee beans", response.data)
        self.assertIn(b"Warm socks", response.data)


if __name__ == "__main__":
    unittest.main()
