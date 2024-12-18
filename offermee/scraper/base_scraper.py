import requests
from bs4 import BeautifulSoup


class BaseScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    def fetch_page(self, url, params=None):
        """Sendet eine HTTP-Anfrage und gibt den Inhalt der Seite zurück."""
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def parse_html(self, html_content):
        """Parst HTML-Inhalt und gibt ein BeautifulSoup-Objekt zurück."""
        return BeautifulSoup(html_content, "html.parser")
