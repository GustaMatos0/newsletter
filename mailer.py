import smtplib
from email.message import EmailMessage

def send_custom_email(recipient_address, subject, message_body):
    """
    General function to send emails. 
    Can be used for confirmation or process completion alerts.
    """
    # Configuration - Replace with your credentials
    sender_email = "ellendsantos1@gmail.com"
    app_password = "cfpv gyce uqar ssgg" # 16-character Google App Password

    # Creating the email structure
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_address
    msg.set_content(message_body)

    try:
        # Connecting to the SMTP server (Gmail example)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print(f"✅ Message sent to {recipient_address}")
        return True
    except Exception as e:
        print(f"Error sending email to {recipient_address}: {e}")
        return False

# Example of how to call the function for different purposes:
if __name__ == "__main__":
    # 1. Confirmation Email
    send_custom_email(
        "client@example.com", 
        "Confirmation: We received your file", 
        "Hello! This is a confirmation that your spreadsheet has been received and is being processed."
    )
    
    # 2. Completion Email
    # send_custom_email("client@example.com", "Process Finished", "The analysis is complete.")