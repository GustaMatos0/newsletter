from receiver import download_attachments_from_email
from mailer import send_custom_email

def run_workflow():
    print(" Starting Automation Process...")

    # Step 1: Check for new spreadsheets
    # This will look for unread emails and download .xlsx files to /downloads
    success_receiving = download_attachments_from_email()

    if success_receiving:
        # Step 2: Send Confirmation Email (First Email)
        # In a real scenario, you'd get the sender's email from the receiver module
        test_client_email = "seu-email-de-teste@gmail.com"
        
        send_custom_email(
            test_client_email,
            "Confirmation: File Received",
            "Hello! We received your spreadsheet. Our system is starting the analysis now."
        )

        # Step 3: (Logic for processing the spreadsheet would go here)
        print("⚙️ Processing data...")

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