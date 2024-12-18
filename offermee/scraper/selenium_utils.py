from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time


def setup_browser(driver_path="chromedriver"):
    """Initialisiert einen Selenium-Browser."""
    service = Service(driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    return webdriver.Chrome(service=service, options=options)


def fetch_dynamic_page(url, wait_time=3):
    """Lädt eine Seite mit Selenium und gibt den HTML-Inhalt zurück."""
    browser = setup_browser()
    browser.get(url)
    time.sleep(wait_time)  # Warten, bis die Seite geladen ist
    content = browser.page_source
    browser.quit()
    return content
