from receiver import download_attachments_from_email
from mailer import send_custom_email
from processor import excel_reading
import glob
import os

def run_workflow():
    print("Starting Automation Process...")

    # Step 1: Check for new spreadsheets
    # This will look for unread emails and download .xlsx files to /downloads
    success_receiving = download_attachments_from_email()

    if success_receiving:
        # Step 2: Send Confirmation Email (First Email)
        # In a real scenario, you'd get the sender's email from the receiver module
        test_client_email = "ellendsantos1@gmail.com"
        
        send_custom_email(
            test_client_email,
            "Confirmation: File Received",
            "Hello! We received your spreadsheet. Our system is starting the analysis now."
        )

        # Step 3: Logic for processing the spreadsheet
        print("⚙️ Processing data...")
        
        # Search for the most recent Excel file in the downloads folder 
        archive_list = glob.glob("downloads/*.xlsx")
        
        if archive_list:
            # Get the file with the most recent modification date
            spreadsheet_path = max(archive_list, key=os.path.getmtime)
            print(f"Reading file: {spreadsheet_path}")

            # Call your processor function here
            scenes = excel_reading(spreadsheet_path)

            if scenes:
                for i, scene in enumerate(scenes):
                    # Printing the content of each row for testing purposes
                    # Note: 'scene_text' must match the column name in your Excel
                    print(f"Scene {i+1} loaded: {scene.get('scene_text', 'No text')}")
            else:
                print("The spreadsheet was found, but returned no data.")
        else:
            print("No .xlsx files found in the downloads folder.")

        # Step 4: Send Completion Email (Second Email)
        send_custom_email(
            test_client_email,
            "Process Finished",
            "Great news! The process is complete and your data has been updated."
        )
        
        print("\n Workflow finished successfully!")
    else:
        print("No new files found or error in connection.")

if __name__ == "__main__":
    run_workflow()