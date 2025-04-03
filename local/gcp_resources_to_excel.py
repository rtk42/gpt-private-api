import subprocess
import json
import pandas as pd
import os

# ---- Config ----
PROJECT_ID = "llm-chatbot-241025"  # <-- Replace this!
OUTPUT_JSON = "resources.json"
OUTPUT_XLSX = "resources.xlsx"

def fetch_gcp_resources(project_id):
    print(f"Fetching GCP resources for project: {project_id}")
    try:
        result = subprocess.run(
            ["gcloud", "asset", "search-all-resources", f"--project={project_id}", "--format=json"],
            check=True,
            capture_output=True,
            text=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error fetching resources from gcloud:")
        print(e.stderr)
        exit(1)

def save_to_excel(data, excel_file):
    print(f"Saving data to {excel_file}")
    df = pd.json_normalize(data)
    df.to_excel(excel_file, index=False)
    print(f"Saved {len(df)} resources to {excel_file}")

def main():
    if PROJECT_ID == "your-project-id":
        print("❗ Please set your Google Cloud project ID in the script.")
        return

    data = fetch_gcp_resources(PROJECT_ID)
    if not data:
        print("No resources found.")
        return

    save_to_excel(data, OUTPUT_XLSX)

if __name__ == "__main__":
    main()
