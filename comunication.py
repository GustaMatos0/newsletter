import smtplib
import imaplib
import email
import os
import pandas as pd
from email.message import EmailMessage
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# --- INTEGRATED PROCESSOR FUNCTIONS ---

def excel_reading(archive_path):
    """
    Transforms Excel rows into a list of dictionaries (scenes).
    """
    if not os.path.exists(archive_path):
        print(f" Error: The file {archive_path} does not exist!")
        return []

    try:
        # Read the Excel file using Pandas
        df = pd.read_excel(archive_path)
        # Cleanup: remove rows that are completely empty
        df = df.dropna(how='all')
        # Convert to a list of dictionaries
        scenes = df.to_dict(orient='records')
        
        print(f" Success! {len(scenes)} scenes processed from spreadsheet.")
        return scenes
    except Exception as e:
        print(f"Error processing Excel: {e}")
        return []

# --- COMMUNICATION FUNCTIONS ---

def send_custom_email(recipient_address, subject, message_body):
    """
    Sends an email using SMTP.
    Used for confirmation and completion alerts.
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_address
    msg.set_content(message_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print(f"Message sent to {recipient_address}")
        return True
    except Exception as e:
        print(f" Error sending email: {e}")
        return False

def download_and_process_latest_spreadsheet():
    """
    Scans the inbox for emails with spreadsheets, downloads the most recent one,
    and returns the processed data (scenes).
    """
    host = 'imap.gmail.com'
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        mail = imaplib.IMAP4_SSL(host, 993)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        # Search for all emails
        status, messages = mail.search(None, 'ALL')
        mail_ids = messages[0].split()
        
        if not mail_ids:
            print("📭 No messages found in inbox.")
            return []

        # Analyze the most recent emails in reverse order
        for num in reversed(mail_ids[-20:]): 
            status, data = mail.fetch(num, '(BODY.PEEK[])')
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart': continue
                        if part.get('Content-Disposition') is None: continue
                        
                        filename = part.get_filename()
                        if filename and filename.lower().endswith(('.xlsx', '.xls')):
                            filepath = os.path.join('downloads', filename)
                            
                            print(f" Spreadsheet found: {filename}")
                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            
                            # Log out before processing the data
                            mail.close()
                            mail.logout()
                            
                            # CALL PROCESSOR IMMEDIATELY
                            return excel_reading(filepath)

        mail.close()
        mail.logout()
        print(" No new spreadsheets found in recent emails.")
        return []

    except Exception as e:
        print(f"Critical error in workflow: {e}")
        return []

# --- INTEGRATED WORKFLOW TEST ---
if __name__ == "__main__":
    print(" Starting Integrated Workflow (Download + Processing)...")
    
    # This single command now handles the entire initial flow
    spreadsheet_data = download_and_process_latest_spreadsheet()
    
    if spreadsheet_data:
        print("\n--- DATA RECEIVED ---")
        for scene in spreadsheet_data:
            print(scene)
    else:
        print("\n No scenes were loaded.")