import json
import unittest
from unittest.mock import patch, MagicMock

import requests
from offermee.scraper.freelancermap import FreelanceMapScraper


class TestFreelanceMapScraper(unittest.TestCase):
    @patch("offermee.scraper.freelancermap.OpenAIClient")
    @patch("offermee.scraper.freelancermap.DatabaseManager")
    def test_process_project_success(self, mock_db_manager, mock_llm_client):
        # Mock LLM response
        mock_llm_instance = mock_llm_client.return_value
        mock_llm_instance.analyze_project.return_value = json.dumps(
            {
                "Location": "Remote",
                "Must-Have Requirements": ["Python", "SQL"],
                "Nice-To-Have Requirements": ["Docker", "Kubernetes"],
                "Tasks/Responsibilities": ["Develop database schema", "Implement API"],
                "Max Hourly Rate": 100.0,
                "Other conditions": ["Flexible hours"],
                "Contact Person": "Jane Doe",
                "Project Provider": "FreelancerMap",
                "Project Start Date": "2025-02-01",
                "Original Link": "https://www.freelancermap.de/project/123",
            }
        )

        # Mock database session
        mock_session = MagicMock()
        mock_db_manager.Session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        scraper = FreelanceMapScraper()
        project = {
            "title": "Test Project",
            "link": "https://www.freelancermap.de/project/123",
            "description": "A project requiring Python and SQL skills.",
        }

        scraper.process_rfp(project)

        # Assertions
        mock_llm_instance.analyze_project.assert_called_once_with(
            project["description"]
        )
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("offermee.scraper.freelancermap.OpenAIClient")
    @patch("offermee.scraper.freelancermap.DatabaseManager")
    def test_process_project_existing(self, mock_db_manager, mock_llm_client):
        # Mock LLM response
        mock_llm_instance = mock_llm_client.return_value
        mock_llm_instance.analyze_project.return_value = json.dumps(
            {
                "Location": "Remote",
                "Must-Have Requirements": ["Python", "SQL"],
                "Nice-To-Have Requirements": ["Docker", "Kubernetes"],
                "Tasks/Responsibilities": ["Develop database schema", "Implement API"],
                "Max Hourly Rate": 100.0,
                "Other conditions": ["Flexible hours"],
                "Contact Person": "Jane Doe",
                "Project Provider": "FreelancerMap",
                "Project Start Date": "2025-02-01",
                "Original Link": "https://www.freelancermap.de/project/123",
            }
        )

        # Mock database session with existing project
        mock_session = MagicMock()
        mock_db_manager.Session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            MagicMock()
        )

        scraper = FreelanceMapScraper()
        project = {
            "title": "Test Project",
            "link": "https://www.freelancermap.de/project/123",
            "description": "A project requiring Python and SQL skills.",
        }

        scraper.process_rfp(project)

        # Assertions
        mock_llm_instance.analyze_project.assert_called_once_with(
            project["description"]
        )
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()

    @patch("offermee.scraper.freelancermap.requests.get")
    def test_fetch_projects_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Netzwerkfehler")

        scraper = FreelanceMapScraper()
        projects = scraper.fetch_rfps(query="Test", max_results=5)

        self.assertEqual(projects, [])
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
