from fuzzywuzzy import fuzz


class FuzzyMatcher:

    @staticmethod
    def fuzzy_match(a, b):
        """
        Bewertet die Ähnlichkeit zwischen zwei Strings.

        Args:
            a (str): Erster String.
            b (str): Zweiter String.

        Returns:
            int: Ähnlichkeits-Score (0-100).
        """
        return fuzz.token_set_ratio(a, b)
