import pandas as pd
import os

def excel_reading(archive_path):
    """
    Transforms Excel rows into a list of dictionaries (scenes).
    """
    if not os.path.exists(archive_path):
        print(f"Error: The file {archive_path} does not exist!")
        return []

    try:
        # Read the Excel file. Pandas automatically uses the first row as the header.
        df = pd.read_excel(archive_path)

        # Cleanup: remove rows that are completely empty
        df = df.dropna(how='all')

        # Convert to a list of dictionaries
        # Example: [{'Scene': 1, 'Text': 'Hello'}, {'Scene': 2, 'Text': 'World'}]
        scenes = df.to_dict(orient='records')
        
        print(f"Success! {len(scenes)} scenes processed from spreadsheet.")
        return scenes

    except Exception as e:
        print(f"Error processing Excel: {e}")
        return []

# Quick test (only runs if you execute this file directly)
if __name__ == "__main__":
    # Test with a file you've already downloaded in the downloads folder
    # Replace 'test_file.xlsx' with your actual file name for testing
    result = excel_reading("downloads/test_file.xlsx")
    print(result)