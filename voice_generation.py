import os
import fal_client
import requests
import mimetypes
from dotenv import load_dotenv
import logging as log 


DEFAULT_VOICE_ID = "b8jhBTcGAq4kQGWmKprT" 
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

load_dotenv()


def generate_speech(
    text, 
    output_path, 
    api_key=None, 
    voice_id=DEFAULT_VOICE_ID,
    title_pause=1.0,    # Time in seconds to wait after the Title (first line)
    sentence_pause=0.2  # Time in seconds to wait after every full stop
):
    """
    Generates Italian speech with a professional news tone using ElevenLabs.
    Automatically inserts SSML breaks for pacing, but avoids trailing silence.
    
    Args:
        text (str): The text to be spoken. First line is treated as Title.
        output_path (str): File path to save the .mp3 audio.
        api_key (str): ElevenLabs API Key. Defaults to env variable ELEVENLABS_API_KEY.
        voice_id (str): The ElevenLabs Voice ID. Defaults to "Sami - Italian News".
        title_pause (float): Seconds of silence after the first line (Title).
        sentence_pause (float): Seconds of silence after each period (.).
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
        title = text[0]
        body = " ".join(text[1:])
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

    print(final_text)
    
    data = {
        "text": final_text,
        # 'eleven_multilingual_v2' supports SSML <break> tags
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
            # 5. Save Audio
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"  Audio saved to: {output_path}")
        else:
            print(f"  Error: ElevenLabs API returned {response.status_code}")
            print(f"  Details: {response.text}")
            
    except Exception as e:
        print(f"  Exception during speech generation: {e}")




if __name__ == "__main__":

    sample_news_text = ("Giovani artisti dipingeranno i due drappelloni del Palio di Siena 2026. \n")
    
    generate_speech(sample_news_text, "saranno_audio.mp3")