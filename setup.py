from setuptools import setup, find_packages
setup(
    name="agent_extrator",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-dotenv",
        "pydantic",
        "langchain",
        "langchain-core",
        "langchain-community",
        "langchain-groq",
        "langchain-google-genai",
        "pypdf",
        "PyMuPDF",
    ],
    entry_points={
        "console_scripts": [
            "extract=agent_extrator.cli:main",
            "scrape=another_src.auction_scraper.cli:main", 
        ],
    },
)
