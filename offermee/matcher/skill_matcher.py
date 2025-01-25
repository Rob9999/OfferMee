from fuzzywuzzy import fuzz
from fuzzywuzzy import process


class SkillMatcher:
    @staticmethod
    def match_skills(project, freelancer_skills):
        """
        Vergleicht die Fähigkeiten des Freelancers mit den Must-Have und Nice-To-Have Skills des Projekts.

        Args:
            project (ProjectModel): Das Projektmodell mit extrahierten Anforderungen.
            freelancer_skills (list): Liste der Fähigkeiten des Freelancers.

        Returns:
            float: Gesamt-Matching-Score (0-100).
            dict: Detaillierte Matching-Scores für jede Fähigkeit.
        """
        must_haves = (
            [skill.strip().lower() for skill in project.get("must_haves").split(", ")]
            if project.get("must_haves")
            else []
        )
        nice_to_haves = (
            [
                skill.strip().lower()
                for skill in project.get("nice_to_haves").split(", ")
            ]
            if project.get("nice_to_haves")
            else []
        )

        total_must_haves = len(must_haves)
        total_nice_to_haves = len(nice_to_haves)
        matched_must_haves = 0
        matched_nice_to_haves = 0

        skill_details = {}

        for skill in must_haves:
            match = process.extractOne(
                skill, freelancer_skills, scorer=fuzz.partial_ratio
            )
            if match and match[1] >= 80:
                matched_must_haves += 1
                skill_details[skill] = {"matched": True, "score": match[1]}
            else:
                skill_details[skill] = {
                    "matched": False,
                    "score": match[1] if match else 0,
                }

        for skill in nice_to_haves:
            match = process.extractOne(
                skill, freelancer_skills, scorer=fuzz.partial_ratio
            )
            if match and match[1] >= 70:
                matched_nice_to_haves += 1
                skill_details[skill] = {"matched": True, "score": match[1]}
            else:
                skill_details[skill] = {
                    "matched": False,
                    "score": match[1] if match else 0,
                }

        # Gewichtung: 70% Must-Have, 30% Nice-To-Have
        must_have_score = (
            (matched_must_haves / total_must_haves) * 70 if total_must_haves > 0 else 0
        )
        nice_to_have_score = (
            (matched_nice_to_haves / total_nice_to_haves) * 30
            if total_nice_to_haves > 0
            else 0
        )
        total_score = must_have_score + nice_to_have_score

        return total_score, skill_details
