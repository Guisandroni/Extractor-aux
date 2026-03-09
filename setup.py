from setuptools import setup, find_packages

setup(
    name="auction_scraper",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        "beautifulsoup4",
        "pandas",
        "pdfplumber",
        "google-generativeai"
    ],
    entry_points={
        "console_scripts": [
            "scrape=auction_scraper.cli:main",
        ],
    },
)
