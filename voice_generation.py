import os
import requests
import mimetypes
from dotenv import load_dotenv
import logging as log
from pydub import AudioSegment

# Constants
DEFAULT_VOICE_ID = "b8jhBTcGAq4kQGWmKprT" 
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

load_dotenv()

def apply_noise_gate(audio_segment, threshold_db=-32.0, chunk_size_ms=10):
    """
    Applies a simple noise gate to the audio to remove breathing/silence.
    """
    ranges_to_silence = []
    current_silence_start = None
    
    # Scan audio loudness
    for i in range(0, len(audio_segment), chunk_size_ms):
        chunk = audio_segment[i:i+chunk_size_ms]
        
        if chunk.dBFS < threshold_db:
            if current_silence_start is None:
                current_silence_start = i
        else:
            if current_silence_start is not None:
                ranges_to_silence.append((current_silence_start, i))
                current_silence_start = None
                
    # Handle end of file
    if current_silence_start is not None:
        ranges_to_silence.append((current_silence_start, len(audio_segment)))
        
    if not ranges_to_silence:
        return audio_segment
        
    print(f"    -> Noise Gate: Detected {len(ranges_to_silence)} breath/silence segments.")
    
    cleaned_audio = audio_segment
    
    # Process in reverse order to maintain indices while constructing new audio
    for start, end in ranges_to_silence[::-1]:
        duration = end - start
        if duration < 50: # Ignore tiny micro-gaps (artifacts)
            continue
            
        silence_chunk = AudioSegment.silent(duration=duration)
        
        # Replace the breathy section with pure silence
        cleaned_audio = cleaned_audio[:start] + silence_chunk + cleaned_audio[end:]
        
    return cleaned_audio

def generate_speech(
    text, 
    output_path, 
    api_key=None, 
    voice_id=DEFAULT_VOICE_ID,
    title_pause=1.0,
    sentence_pause=0.2,
    noise_gate_threshold=-32.0
):
    """
    Generates Italian speech using ElevenLabs, then applies a noise gate 
    to remove breathing sounds before saving the final file.
    
    Args:
        text (str): The text to be spoken. First line is treated as Title.
        output_path (str): File path to save the final .mp3 audio.
        api_key (str): ElevenLabs API Key. Defaults to env variable.
        voice_id (str): The ElevenLabs Voice ID.
        title_pause (float): Seconds of silence after the first line.
        sentence_pause (float): Seconds of silence after each period.
        noise_gate_threshold (float): dB threshold for removing breath sounds.
    """
    # 1. Get API Key
    key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        print("Error: ELEVENLABS_API_KEY not found. Please set it or pass it as an argument.")
        return

    print(f"Generating speech for: \"{text[:30]}...\"")
    
    # 2. Process Text for Pauses (SSML Injection)
    break_tag = f" <break time=\"{sentence_pause}s\" />"

    def add_breaks(segment):
        # Replace all periods with period + break
        processed = segment.replace(".", "." + break_tag)
        # Remove the break if it's at the very end of the string (ignoring whitespace)
        if processed.rstrip().endswith(break_tag.strip()):
            processed = processed[:processed.rfind(break_tag)]
        return processed

    # Treat the first line as the "Header/Title"
    parts = text.strip().split('\n', 1)

    if len(parts) == 2:
        title = parts[0]
        body = parts[1]
        processed_body = add_breaks(body)
        final_text = f"{title} <break time=\"{title_pause}s\" /> {processed_body}"
    else:
        # If no newline, just process the whole text as body
        final_text = add_breaks(text)

    # 3. Prepare API Request
    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": key
    }

    data = {
        "text": final_text,
        "model_id": "eleven_multilingual_v2", 
        "voice_settings": {
            "stability": 0.3,       
            "similarity_boost": 0.75, 
            "style": 0.8,           
            "use_speaker_boost": True
        }
    }

    try:
        # 4. Call API
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # 5. Save Audio to Temp File
            temp_path = f"temp_{os.path.basename(output_path)}"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # 6. Apply Noise Gate
            try:
                print(f"  Applying noise gate (Threshold: {noise_gate_threshold}dB)...")
                audio = AudioSegment.from_mp3(temp_path)
                cleaned = apply_noise_gate(audio, threshold_db=noise_gate_threshold)
                
                # 7. Export Cleaned Audio
                cleaned.export(output_path, format="mp3")
                print(f"  Audio cleaned and saved to: {output_path}")
                
            except Exception as e:
                print(f"  Error during noise gate processing: {e}")
                # Fallback: Rename temp to output if pydub fails
                if os.path.exists(temp_path):
                    os.rename(temp_path, output_path)
                    print("  Saved original audio (uncleaned) due to error.")
            
            # 8. Cleanup Temp File
            if os.path.exists(temp_path):
                os.remove(temp_path)

        else:
            print(f"  Error: ElevenLabs API returned {response.status_code}")
            print(f"  Details: {response.text}")
            
    except Exception as e:
        print(f"  Exception during speech generation: {e}")




if __name__ == "__main__":

    sample_news_text = ("Giovani artisti dipingeranno i due drappelloni del Palio di Siena 2026. \n")
    
    generate_speech(sample_news_text, "saranno_audio.mp3")