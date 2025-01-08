import os
import subprocess


def main():
    # Define the relative path to the dashboard file
    dashboard_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../offermee/dashboard/app.py",  # Adjust path as needed
    )

    # Check if the dashboard file exists
    if not os.path.exists(dashboard_file):
        print(f"Dashboard file '{dashboard_file}' not found. Please check the path.")
        return

    # Start Streamlit in debug mode
    try:
        print("Starting the dashboard in debug mode...")
        subprocess.run(
            ["streamlit", "run", dashboard_file],
            check=True,
        )
    except FileNotFoundError:
        print(
            "Streamlit is not installed. Please install it with 'pip install streamlit'."
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting the dashboard: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
