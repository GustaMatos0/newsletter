import smtplib
import imaplib
import email
import os
import pandas as pd
import gdown
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# --- FUNÇÕES DE E-MAIL ---
def send_custom_email(recipient_address, subject, message_body):
    """Envia e-mail via SMTP."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_address
    msg.set_content(message_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print(f"E-mail enviado para {recipient_address}")
        return True
    except Exception as e:
        print(f" Erro ao enviar e-mail: {e}")
        return False

def send_confirmation_email(recipient, subject, body):
    return send_custom_email(recipient, subject, body)

# --- FUNÇÕES DE DOWNLOAD ---
def download_video_logic(url, name, redo=False):
    if not os.path.exists('downloads/videos'):
        os.makedirs('downloads/videos')
    
    path = f"downloads/videos/{name}.mp4"
    
    # Se o vídeo já existe e redo é False, pula o download
    if os.path.exists(path) and not redo:
        print(f" Vídeo '{name}' já existe. Pulando.")
        return path

    try:
        print(f" Baixando vídeo: {name}...")
        # fuzzy=True ajuda a baixar de links do Google Drive que não são diretos
        gdown.download(url, path, quiet=True, fuzzy=True)
        return path
    except Exception as e:
        print(f" Erro ao baixar vídeo {name}: {e}")
        return None

def download_image_logic(url, name):
    """
    Baixa imagem do Google Drive e salva como .jpg
    """
    if not os.path.exists('downloads/images'):
        os.makedirs('downloads/images')
    
    path = f"downloads/images/{name}.jpg"
    
    # Verifica se a imagem já existe para não baixar repetido
    if os.path.exists(path):
         print(f" Imagem '{name}' já existe. Pulando.")
         return path

    try:
        print(f" Baixando imagem: {name}...")
        gdown.download(url, path, quiet=True, fuzzy=True)
        return path
    except Exception as e:
        print(f" Erro ao baixar imagem {name}: {e}")
        return None

# --- FLUXO PRINCIPAL ---
def process_workflow():
    host = 'imap.gmail.com'
    if not os.path.exists('downloads'): os.makedirs('downloads')

    try:
        mail = imaplib.IMAP4_SSL(host, 993)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        # Busca mensagens recentes
        status, messages = mail.search(None, 'ALL')
        if not messages[0]: return [], None

        # Pega o último email
        for num in reversed(messages[0].split()[-5:]):
            status, data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            sender_email = email.utils.parseaddr(msg.get('From'))[1]

            for part in msg.walk():
                if part.get_filename() and part.get_filename().endswith(('.xlsx', '.xls')):
                    filename = part.get_filename()
                    excel_path = os.path.join('downloads', filename)
                    with open(excel_path, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    
                    print(f" Planilha '{filename}' recebida de: {sender_email}")
                    
                    df = pd.read_excel(excel_path)
                    scenes_processed = []

                    for _, row in df.iterrows():
                        # Captura dados das colunas (usando .get para evitar erro se a coluna não existir)
                        data = {
                            'name': str(row.get('item_name', '')),
                            'video_url': str(row.get('video_link', '')),
                            'image_url': str(row.get('image_link', '')),
                            'video_redo': str(row.get('video_redo', '')).upper() == 'TRUE',
                            'only_video': str(row.get('only_video', '')).upper() == 'TRUE',
                            # As colunas abaixo podem ser usadas depois, mas já lemos agora
                            'tts': str(row.get('tts', '')).upper() == 'TRUE',
                            'caption': str(row.get('caption', ''))
                        }

                        # 1. Baixar Vídeo (se houver link e for solicitado)
                        if data['video_url'] and data['video_url'] != 'nan' and data['only_video']:
                             download_video_logic(data['video_url'], data['name'], data['video_redo'])
                        
                        # 2. Baixar Imagem (se houver link)
                        if data['image_url'] and data['image_url'] != 'nan':
                             download_image_logic(data['image_url'], data['name'])

                        scenes_processed.append(data)

                    mail.close()
                    mail.logout()
                    return scenes_processed, sender_email
        return [], None
    except Exception as e:
        print(f" Erro crítico no Communication: {e}")
        return [], None