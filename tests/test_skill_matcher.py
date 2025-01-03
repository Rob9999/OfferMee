import unittest
from offermee.matcher.skill_matcher import SkillMatcher
from offermee.database.models.base_project_model import BaseProjectModel


class TestSkillMatcher(unittest.TestCase):
    def setUp(self):
        self.project = BaseProjectModel(
            must_haves="Python, SQL", nice_to_haves="Docker, Kubernetes"
        )
        self.freelancer_skills = ["python", "django", "docker", "aws"]

    def test_match_skills(self):
        score, details = SkillMatcher.match_skills(self.project, self.freelancer_skills)
        self.assertGreater(score, 0)
        self.assertIn("python", details)
        self.assertIn("sql", details)
        self.assertIn("docker", details)
        self.assertIn("kubernetes", details)


if __name__ == "__main__":
    unittest.main()
