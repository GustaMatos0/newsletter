import os
import time
from voice_generation import generate_speech
from audio_cleaner import apply_noise_gate
from pydub import AudioSegment
from dotenv import load_dotenv



load_dotenv()

def run_audio_quality_check():
    print("🚀 Starting Production Audio Quality Test...")
    
    # Test cases: normal, long text, and special characters
    test_cases = [
        {"id": "normal", "text": "This is a standard quality check for the voice engine."},
        {"id": "long", "text": "This is a much longer sentence designed to test if the API timeout is handled correctly when the synthesis takes more time than usual to complete." * 3},
        {"id": "special", "text": "Wait! Is the engine handling dots... commas, and exclamation marks!?"}
    ]

    if not os.path.exists('test_output'):
        os.makedirs('test_output')

    for case in test_cases:
        print(f"\n--- Testing Case: {case['id'].upper()} ---")
        raw_path = f"test_output/{case['id']}_raw.mp3"
        clean_path = f"test_output/{case['id']}_clean.mp3"

        # 1. Stress test the API call
        start_time = time.time()
        try:
            success = generate_speech(case['text'], raw_path)
            elapsed = time.time() - start_time
            
            if success and os.path.exists(raw_path):
                print(f"✅ Generation Successful ({elapsed:.2f}s)")
                
                # 2. Test Audio Processing (Noise Gate)
                print(f"⚙️  Applying noise gate to {case['id']}...")
                audio_segment = AudioSegment.from_mp3(raw_path)
                
                # Verify if audio is not empty
                if len(audio_segment) > 0:
                    cleaned_audio = apply_noise_gate(audio_segment)
                    cleaned_audio.export(clean_path, format="mp3")
                    
                    if os.path.exists(clean_path):
                        print(f"✨ Quality Check Passed: {clean_path} created.")
                else:
                    print(f"❌ FAIL: {case['id']} generated an empty audio file.")
            else:
                print(f"❌ FAIL: API did not return a file for {case['id']}.")

        except Exception as e:
            print(f"🚨 CRITICAL FAILURE in production simulation: {e}")

if __name__ == "__main__":
    run_audio_quality_check()