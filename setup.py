# Setup script
from setuptools import setup, find_packages

setup(
    name="OfferMee",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4",
        "scrapy",
        "selenium",
        "python-dotenv",
        "openai",
        "google.generativeai",
        "streamlit",
        "sqlalchemy",
        "fuzzywuzzy",
        "PyPDF2",
        "pycryptodome",
        "streamlit-authenticator",
        "reportlab",
        "platformdirs",
        "babel",
        "polib",
    ],
)
