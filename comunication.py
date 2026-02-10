import smtplib
import imaplib
import email
import os
from email.message import EmailMessage
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

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
        print(f" Message sent to {recipient_address}")
        return True
    except Exception as e:
        print(f" Error sending email: {e}")
        return False

def download_attachments_from_email():
    """
    Scans the inbox and downloads .xlsx files to the /downloads folder.
    """
    host = 'imap.gmail.com'
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        mail = imaplib.IMAP4_SSL(host, 993)
        mail.login(EMAIL_USER, EMAIL_PASS)
        print("🔓 Login successful! Scanning inbox...")
        
        mail.select("inbox")
        # Search for all emails
        status, messages = mail.search(None, 'ALL')
        mail_ids = messages[0].split()
        
        if not mail_ids:
            print("No messages found.")
            return False

        # Analyze the most recent emails
        last_emails = mail_ids[-100:] 
        print(f" Analyzing the {len(last_emails)} most recent emails...")

        download_count = 0

        for num in last_emails:
            status, data = mail.fetch(num, '(BODY.PEEK[])')
            
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg.get('Subject')
                    
                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue
                        
                        filename = part.get_filename()
                        if filename and filename.lower().endswith(('.xlsx', '.xls')):
                            print(f" Found spreadsheet in: {subject}")
                            filepath = os.path.join('downloads', filename)
                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            print(f"     DOWNLOAD COMPLETED: {filename}")
                            download_count += 1 

        mail.close()
        mail.logout()
        
        if download_count > 0:
            print(f"\n Total spreadsheets downloaded: {download_count}")
            return True
        else:
            print(" No spreadsheets found in the analyzed emails.")
            return False

    except Exception as e:
        print(f" Critical error during download: {e}")
        return False

# Unit Testing
if __name__ == "__main__":
    print("Running Communication Module Tests...")
    # download_attachments_from_email()