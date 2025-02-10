from offermee.AI.ai_manager import AIManager
from offermee.scraper.freelancermap import FreelanceMapScraper


def main():
    print("Starte Freelancermap-Scraper...")
    ai_manager = AIManager("genai")
    scraper = FreelanceMapScraper()

    projects = scraper.fetch(
        query="C# OR C++ OR Java OR Python OR KI",
        contract_types=["contracting"],
        matching_skills=[
            "KSYWSPP48G0M2237B0DW",
            "KS0MUJGS1UTCN6QBYSB6",
            "KS1201Q6YZG5VR15ZJ0G",
        ],
        countries=[1, 2, 3, 39, 14, 106, 114, 4],
        states=[2905330, 2951839, 2842565, 2822542, 2872567],
        sort=1,
        page=1,
        max_results=5,
    )

    print("\nGefundene Projekte:")
    for idx, project in enumerate(projects, 1):
        print(f"{idx}. {project['title']}")
        print(f"   Link: {project['link']}")
        print(f"   Beschreibung: {project['description']}\n")

    print("Starte Freelancermap-Scraper paginated...")
    projects = scraper.fetch_paginated(
        query="Python OR Java",
        contract_types=["contracting"],
        countries=[1, 2, 3],
        max_pages=3,
        max_results=20,
    )

    print("\nGefundene Projekte:")
    for idx, project in enumerate(projects, 1):
        print(f"{idx}. {project['title']}")
        print(f"   Link: {project['link']}")
        print(f"   Beschreibung: {project['description']}\n")


if __name__ == "__main__":
    main()
