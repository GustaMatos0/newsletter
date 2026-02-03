import os
import argparse
from pydub import AudioSegment

def apply_noise_gate(audio_segment, threshold_db=-32.0, chunk_size_ms=10):
    """
    Applies a simple noise gate to the audio.
    
    How it works:
    It scans the audio in small chunks (e.g., 10ms).
    If a chunk's volume (dBFS) is lower than the threshold, it is considered 
    'silence' or 'breath' and is muted.
    
    Args:
        audio_segment (AudioSegment): The loaded audio.
        threshold_db (float): Volume level below which sounds are muted. 
                              -30 to -40 is typical for removing breaths vs speech.
        chunk_size_ms (int): Resolution of the check. 10ms provides smooth gating.
    
    Returns:
        AudioSegment: The cleaned audio.
    """
    
    # We iterate through the audio, identifying "silent" ranges
    # to create a non-destructive mask, avoiding clicky artifacts of simple chunk replacement.
    
    ranges_to_silence = []
    
    current_silence_start = None
    
    # Scan audio loudness
    # This is a bit computationally intensive for long files but very accurate
    for i in range(0, len(audio_segment), chunk_size_ms):
        chunk = audio_segment[i:i+chunk_size_ms]
        
        if chunk.dBFS < threshold_db:
            if current_silence_start is None:
                current_silence_start = i
        else:
            if current_silence_start is not None:
                # We found a silent block from current_silence_start to i
                ranges_to_silence.append((current_silence_start, i))
                current_silence_start = None
                
    # Handle end of file
    if current_silence_start is not None:
        ranges_to_silence.append((current_silence_start, len(audio_segment)))
        
    # Apply silence to detected ranges
    # We construct a new audio segment
    if not ranges_to_silence:
        return audio_segment
        
    print(f"    -> Detected {len(ranges_to_silence)} breath/silence segments.")
    
    # Create a mutable version (or apply overlay)
    # A simple way in pydub to "mute" sections is creating a silent chunk of that duration
    # and overlaying it, or constructing the file from non-silent parts.
    
    # Strategy: Silence the detected chunks in place
    # Since pydub objects are immutable, we process recursively or use overlay
    # Faster approach: just reduce gain significantly on those chunks
    
    cleaned_audio = audio_segment
    
    # We go in reverse so indexing doesn't shift (though length stays same for gain change)
    for start, end in ranges_to_silence:
        duration = end - start
        if duration < 50: # Ignore tiny micro-gaps (artifacts)
            continue
            
        silence_chunk = AudioSegment.silent(duration=duration)
        
        # We replace the breathy section with pure silence
        # (or you could overlay -100dB gain for a softer effect)
        cleaned_audio = cleaned_audio[:start] + silence_chunk + cleaned_audio[end:]
        
    return cleaned_audio

def clean_folder(folder_path, threshold=-32.0):
    """
    Iterates through all .mp3 files in the folder and removes breaths.
    Saves the result in a 'cleaned' subdirectory.
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return

    output_folder = os.path.join(folder_path, "cleaned")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".mp3")]
    
    if not files:
        print(f"No MP3 files found in {folder_path}")
        return

    print(f"Found {len(files)} files. Cleaning breaths (Threshold: {threshold} dB)...")

    for filename in files:
        input_path = os.path.join(folder_path, filename)
        output_path = os.path.join(output_folder, filename)
        
        print(f"Processing: {filename}")
        
        try:
            audio = AudioSegment.from_mp3(input_path)
            
            # Apply the gate
            cleaned = apply_noise_gate(audio, threshold_db=threshold)
            
            # Export
            cleaned.export(output_path, format="mp3")
            print(f"  Saved to: {output_path}")
            
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove breathing sounds from MP3s using a Noise Gate.")
    parser.add_argument("folder", help="Folder containing the MP3 files.")
    parser.add_argument("--threshold", type=float, default=-35.0, 
                        help="Volume threshold in dB. Sounds quieter than this are removed. Default: -35.0")
    
    args = parser.parse_args()
    
    clean_folder(args.folder, args.threshold)