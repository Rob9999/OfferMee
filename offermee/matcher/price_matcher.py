class PriceMatcher:

    @staticmethod
    def match_price(project, freelancer_desired_rate):
        """
        Vergleicht den gewünschten Stundensatz des Freelancers mit dem maximalen Stundensatz des Projekts.

        Args:
            project (ProjectModel): Das Projektmodell mit extrahierten Anforderungen.
            freelancer_desired_rate (float): Der gewünschte Stundensatz des Freelancers.

        Returns:
            float: Preis-Matching-Score (0-100).
        """
        project_rate = project.hourly_rate

        if project_rate == 0:
            return 50  # Neutraler Score, wenn kein Rate angegeben ist

        difference = freelancer_desired_rate - project_rate

        if difference < 0:
            # Freelancer bietet weniger als die maximale Rate des Projekts
            # Je mehr niedriger, desto höher der Score (max 100)
            return min(100, 100 + difference)  # difference ist negativ
        else:
            # Freelancer bietet gleich oder mehr als die maximale Rate des Projekts
            # Je mehr höher, desto niedriger der Score (min 0)
            return max(0, 100 - difference)
