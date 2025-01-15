import unittest
from offermee.database.models.main_models import ProjectModel
from offermee.matcher.price_matcher import PriceMatcher


class TestPriceMatcher(unittest.TestCase):
    def setUp(self):
        self.project = ProjectModel(hourly_rate=100.0)

    def test_price_matcher_under(self):
        score = PriceMatcher.match_price(self.project, 90.0)
        self.assertEqual(
            score, 100 + (90.0 - 100.0)
        )  # 90 - 100 = -10; 100 + (-10) = 90

    def test_price_matcher_equal(self):
        score = PriceMatcher.match_price(self.project, 100.0)
        self.assertEqual(score, 100 - 0.0)  # 100 - 100 = 0; 100 - 0 = 100

    def test_price_matcher_over(self):
        score = PriceMatcher.match_price(self.project, 110.0)
        self.assertEqual(score, 100 - (110.0 - 100.0))  # 110 - 100 = 10; 100 - 10 = 90


if __name__ == "__main__":
    unittest.main()
