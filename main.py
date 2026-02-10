from communication import send_custom_email, download_and_process_latest_spreadsheet
import os

def run_workflow():
    print(" Starting Automation Process...")

    # Step 1: Download and Process the spreadsheet
    # This single call now handles: Connecting to Gmail, Downloading the .xlsx,
    # and converting it into a list of dictionaries (scenes).
    scenes = download_and_process_latest_spreadsheet()

    if scenes:
        # Step 2: Send Confirmation Email
        # In a real scenario, this could be dynamic
        client_email = "ellendsantos1@gmail.com"
        
        send_custom_email(
            client_email,
            "Confirmation: Processing Started",
            "Hello! We have successfully received and parsed your spreadsheet. Generating content now."
        )

        # Step 3: Logic for content generation (Audio/Video)
        print(f"  Loaded {len(scenes)} scenes. Starting generation...")
        
        for i, scene in enumerate(scenes):
            # Using .get() to avoid errors if the column name varies
            text = scene.get('scene_text', 'No text found')
            image = scene.get('Nome_Imagem', 'No image specified')
            
            print(f"\n--- Scene {i+1} ---")
            print(f"Text: {text}")
            print(f"Image Reference: {image}")
            
            # This is where you would call your audio/video generation functions
            # e.g., generate_speech(text, f"downloads/audio_{i}.mp3")

        # Step 4: Send Completion Email
        send_custom_email(
            client_email,
            "Process Finished",
            "Great news! All scenes have been processed and your content is ready."
        )
        
        print("\n Workflow finished successfully!")
    else:
        print(" No new spreadsheets found or error in processing.")

if __name__ == "__main__":
    run_workflow()