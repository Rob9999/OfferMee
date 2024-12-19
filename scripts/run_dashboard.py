import os
import subprocess


def main():
    # Dashboard-Datei
    dashboard_file = os.path.join("offermee", "dashboard", "app.py")

    # Prüfen, ob die Datei existiert
    if not os.path.exists(dashboard_file):
        print(f"Dashboard-Datei '{dashboard_file}' wurde nicht gefunden.")
        return

    # Streamlit starten
    try:
        print("Starte das Dashboard...")
        subprocess.run(["streamlit", "run", dashboard_file], check=True)
    except FileNotFoundError:
        print(
            "Streamlit ist nicht installiert. Installiere es mit 'pip install streamlit'."
        )
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Starten des Dashboards: {e}")


if __name__ == "__main__":
    main()
