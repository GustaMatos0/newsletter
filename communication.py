import smtplib
import imaplib
import email
import os
import pandas as pd
from email.message import EmailMessage
from dotenv import load_dotenv

import mimetypes






# Load credentials from .env file
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

PROCESSED_LOG_FILE = "processed_emails.txt"


def load_processed_ids():
    """Loads the list of processed email IDs from a file."""
    if not os.path.exists(PROCESSED_LOG_FILE):
        return set()
    with open(PROCESSED_LOG_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_id(message_id):
    """Appends a new processed email ID to the file."""
    if not message_id:
        return
    with open(PROCESSED_LOG_FILE, 'a') as f:
        f.write(f"{message_id}\n")

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

def send_custom_email(recipient_address, subject, message_body, attachment_path=None):
    """
    Sends an email using SMTP with optional attachment support.
    
    Args:
        recipient_address (str): The email address of the recipient.
        subject (str): The subject of the email.
        message_body (str): The body text of the email.
        attachment_path (str, optional): The file path of the attachment. Defaults to None.
        
    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        print("Error: EMAIL_USER or EMAIL_PASS environment variables not set.")
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_address
    msg.set_content(message_body)

    # Handle Attachment
    if attachment_path and os.path.exists(attachment_path):
        # Guess the MIME type or default to binary
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        
        maintype, subtype = ctype.split('/', 1)

        try:
            with open(attachment_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(attachment_path)
                
            msg.add_attachment(
                file_data,
                maintype=maintype,
                subtype=subtype,
                filename=file_name
            )
            print(f"Attachment added: {file_name}")
        except Exception as e:
            print(f"Error reading attachment file: {e}")
            # Depending on requirements, we might want to fail or just send without attachment
            # For now, we proceed sending the email without the attachment if read fails
    elif attachment_path:
        print(f"Warning: Attachment path '{attachment_path}' does not exist. Sending email without attachment.")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print(f"Message sent to {recipient_address}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def download_and_process_latest_spreadsheet():
    """
    Scans the inbox for emails with spreadsheets, downloads the most recent one
    that hasn't been processed yet, and returns the sender's email.
    """
    host = 'imap.gmail.com'
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    processed_ids = load_processed_ids()

    try:
        mail = imaplib.IMAP4_SSL(host, 993)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        # Search for all emails
        status, messages = mail.search(None, 'ALL')
        mail_ids = messages[0].split()
        
        if not mail_ids:
            # print("📭 No messages found in inbox.") # Optional: reduce log spam
            return None

        # Analyze the most recent 5 emails in reverse order
        for num in reversed(mail_ids[-2:]): 
            # Fetch headers first to check Message-ID without downloading attachments
            status, header_data = mail.fetch(num, '(BODY.PEEK[HEADER])')
            
            msg_header = email.message_from_bytes(header_data[0][1])
            message_id = msg_header.get("Message-ID", "").strip()
            
            if message_id in processed_ids:
                # print(f"Skipping already processed email: {message_id}")
                continue

            # If not processed, fetch the full body
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

                            sender = msg.get("From")
                            
                            # Mark as processed immediately
                            save_processed_id(message_id)
                            
                            # Log out before processing the data
                            mail.close()
                            mail.logout()
                            
                            # Return sender to trigger workflow
                            return sender

        mail.close()
        mail.logout()
        # print(" No new spreadsheets found in recent emails.")
        return None

    except Exception as e:
        print(f"Critical error in workflow: {e}")
        return None

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