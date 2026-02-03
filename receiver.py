import imaplib
import email
import os
from dotenv import load_dotenv


def download_attachments_from_email():
    host = 'imap.gmail.com'
    username = 'ellendsantos1@gmail.com'
    password = 'ivxd gsky vdam hjcu'
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        mail = imaplib.IMAP4_SSL(host, 993)
        mail.login(username, password)
        print("Login realizado! Iniciando varredura completa...")
        
        mail.select("inbox")

        # Busca por todos os emails
        status, messages = mail.search(None, 'ALL')
        
       # ... (parte inicial do código igual até o mail.search)
        
        status, messages = mail.search(None, 'ALL')
        mail_ids = messages[0].split()
        
        if not mail_ids:
            print("ℹ️ Nenhuma mensagem encontrada.")
            return False

        # PEGAR APENAS OS ÚLTIMOS 10 EMAILS PARA NÃO TRAVAR
        last_emails = mail_ids[-100:] 
        print(f"🔎 Analisando os {len(last_emails)} e-mails mais recentes...")

        download_count = 0

        for num in last_emails:
            # BODY.PEEK[HEADER.FIELDS (SUBJECT)] - Primeiro lê só o assunto (mais rápido)
            status, data = mail.fetch(num, '(BODY.PEEK[])')
            
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg.get('Subject')
                    print(f"📦 Verificando e-mail: {subject}")
                    
                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue
                        
                        filename = part.get_filename()
                        if filename and filename.lower().endswith(('.xlsx', '.xls')):
                            filepath = os.path.join('downloads', filename)
                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            print(f"    DOWNLOAD CONCLUÍDO: {filename}")
                            download_count += 1 
        mail.close()
        mail.logout()
        
        if download_count > 0:
            print(f"\n Total de planilhas baixadas: {download_count}")
            return True
        else:
            print(" Nenhuma planilha encontrada nos emails.")
            return False

    except Exception as e:
        print(f" Erro crítico: {e}")
        return False

if __name__ == "__main__":
    download_attachments_from_email()