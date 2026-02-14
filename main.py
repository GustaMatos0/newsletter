from comunication import process_workflow, send_confirmation_email
import os

def run_main():
    print(" Iniciando Sistema de Downloads (Imagens e Vídeos)...")
    
    # Garante que as pastas existam
    if not os.path.exists('downloads/videos'): os.makedirs('downloads/videos')
    if not os.path.exists('downloads/images'): os.makedirs('downloads/images')

    # Executa o workflow: Baixa planilha -> Lê linhas -> Baixa Arquivos
    scenes, customer_email = process_workflow()

    if not scenes:
        print(" Nenhuma planilha nova encontrada.")
        return

    print(f"\n Processamento concluído!")
    print(f" Total de itens processados: {len(scenes)}")
    print(" Verifique as pastas 'downloads/videos' e 'downloads/images'.")

    # Envia e-mail de confirmação
    if customer_email:
        print(f"Enviando confirmação para: {customer_email}")
        send_confirmation_email(
            customer_email,
            "Arquivos Recebidos",
            f"Olá! Sua planilha foi processada. Baixamos os vídeos e imagens solicitados."
        )

if __name__ == "__main__":
    run_main()