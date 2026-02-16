import os
import sys
import json
import argparse
import shutil
from moviepy import AudioFileClip, VideoFileClip

# Import pandas for Excel support
try:
    import pandas as pd
except ImportError:
    print("Error: 'pandas' and 'openpyxl' libraries are required for Excel support.")
    print("Please install them: pip install pandas openpyxl")
    sys.exit(1)

# Import custom modules
try:
    from video_generation import generate_video_single, download_video
    from voice_generation import generate_speech
    from video_editor import StorySequencer
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure 'video_generation.py', 'voice_generation.py', and 'video_editor.py' are in the current directory.")
    sys.exit(1)

# --- Configuration Constants ---
IMAGE_INPUT_DIR = "image_input"
VIDEO_INPUT_DIR = "video_input"
GEN_VIDEO_DIR = "generated_videos"
GEN_AUDIO_DIR = "generated_audio"
DEFAULT_RES = [1280, 720]
DEFAULT_FILENAME = "final_story.mp4"

def load_config(config_path):
    """
    Loads configuration from JSON or Excel.
    Returns a dictionary with a 'scenes' list.
    """
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    
    ext = os.path.splitext(config_path)[1].lower()
    
    if ext == '.json':
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    elif ext in ['.xlsx', '.xls']:
        try:
            df = pd.read_excel(config_path)
            # Fill NaN values with empty strings or False for booleans
            df = df.fillna("")
            
            # Convert to list of dicts
            scenes = df.to_dict('records')
            
            # Normalize boolean columns
            bool_cols = ['video_redo', 'only_video', 'tts', 'tts_redo']
            for scene in scenes:
                for col in bool_cols:
                    if col in scene:
                        val = scene[col]
                        # Handle Excel True/False/1/0/"True"
                        if isinstance(val, str):
                            scene[col] = val.lower() in ['true', '1', 'yes']
                        else:
                            scene[col] = bool(val)
                            
            return {"scenes": scenes}
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            sys.exit(1)
    else:
        print("Unsupported file format. Use .json or .xlsx")
        sys.exit(1)

def run_content_generation(config):
    """Step 1: Generates Audio and Video assets based on flags."""
    print("\n=== STEP 1: Content Generation & Validation ===")
    
    scenes = config.get("scenes", [])
    
    # Ensure directories exist
    for d in [GEN_VIDEO_DIR, GEN_AUDIO_DIR, IMAGE_INPUT_DIR, VIDEO_INPUT_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)
    
    for i, scene in enumerate(scenes):
        item_name = scene.get("item_name")
        if not item_name:
            print(f"Skipping row {i+1}: Missing 'item_name'.")
            continue

        base_name = os.path.splitext(item_name)[0]
        print(f"\nProcessing Item: {item_name}")

        # --- 1. Audio Generation Logic ---
        audio_duration = 0
        audio_path = None
        
        should_tts = scene.get("tts", False)
        title_text = scene.get("title", "").strip()
        
        if should_tts and title_text:
            audio_filename = f"{base_name}_audio.mp3"
            audio_path = os.path.join(GEN_AUDIO_DIR, audio_filename)
            
            # Check Redo Flag
            if scene.get("tts_redo", False) and os.path.exists(audio_path):
                print(f"  [Audio] Redo requested. Removing old file.")
                os.remove(audio_path)
            
            if not os.path.exists(audio_path):
                print(f"  [Audio] Generating speech...")
                success = generate_speech(title_text, audio_path)
                if not success:
                    print("  [Error] Audio generation failed.")
            else:
                print(f"  [Audio] Found existing file.")
            
            # Get Duration
            if os.path.exists(audio_path):
                try:
                    with AudioFileClip(audio_path) as clip:
                        audio_duration = clip.duration
                except Exception as e:
                    print(f"  [Error] Could not measure audio: {e}")
        elif should_tts and not title_text:
            print("  [Audio] TTS is True but 'title' is empty. Skipping.")

        # --- 2. Video Logic ---
        only_video = scene.get("only_video", False)
        
        if only_video:
            # --- Case A: User Provided Video ---
            source_video = os.path.join(VIDEO_INPUT_DIR, item_name)
            if not os.path.exists(source_video):
                print(f"  [Error] only_video=True but file not found: {source_video}")
                continue
                
            # Validation: Audio longer than Video?
            if audio_duration > 0:
                try:
                    with VideoFileClip(source_video) as clip:
                        vid_duration = clip.duration
                    
                    if audio_duration > vid_duration:
                        print(f"  [CRITICAL ERROR] Audio ({audio_duration:.2f}s) is longer than input video ({vid_duration:.2f}s).")
                        print("  Stopping execution as requested.")
                        sys.exit(1) 
                except Exception as e:
                    print(f"  [Error] Could not validate video duration: {e}")

        else:
            # --- Case B: AI Generation ---
            source_image = os.path.join(IMAGE_INPUT_DIR, item_name)
            if not os.path.exists(source_image):
                print(f"  [Warning] Source image not found: {source_image}")
                continue
                
            target_video_path = os.path.join(GEN_VIDEO_DIR, f"{base_name}_video.mp4")
            
            # Check Redo Flag
            if scene.get("video_redo", False) and os.path.exists(target_video_path):
                print(f"  [Video] Redo requested. Removing old file.")
                os.remove(target_video_path)
                
            if not os.path.exists(target_video_path):
                # Calculate Duration: Audio + 1s (min 5s fallback if no audio)
                calc_duration = int(audio_duration) + 1 if audio_duration > 0 else 5
                
                print(f"  [Video] Generating AI Video (Duration: {calc_duration}s)...")
                generate_video_single(
                    image_path=source_image,
                    prompt=scene.get("video_hint", ""),
                    duration=calc_duration,
                    output_path=target_video_path,
                    model_endpoint="fal-ai/vidu/q3/image-to-video"
                )
            else:
                print(f"  [Video] Found existing generated video.")

def run_editor(config):
    """Step 2: Assembles the final video."""
    print("\n=== STEP 2: Final Assembly (MoviePy) ===")
    
    # Global Configs (JSON might provide these, Excel won't, so defaults apply)
    output_res = config.get("output_resolution", DEFAULT_RES)
    final_filename = config.get("final_filename", DEFAULT_FILENAME)
    scenes = config.get("scenes", [])
    
    sequencer = StorySequencer(output_width=output_res[0], output_height=output_res[1])
    
    scenes_added = 0

    for i, scene in enumerate(scenes):
        item_name = scene.get("item_name")
        if not item_name: continue
        
        base_name = os.path.splitext(item_name)[0]
        only_video = scene.get("only_video", False)
        
        # 1. Resolve Video Path
        if only_video:
            video_path = os.path.join(VIDEO_INPUT_DIR, item_name)
        else:
            video_path = os.path.join(GEN_VIDEO_DIR, f"{base_name}_video.mp4")
            
        if not os.path.exists(video_path):
            print(f"[Skipping] Video not found: {video_path}")
            continue

        # 2. Resolve Audio Path
        audio_path = None
        if scene.get("tts", False):
            cand_path = os.path.join(GEN_AUDIO_DIR, f"{base_name}_audio.mp3")
            if os.path.exists(cand_path):
                audio_path = cand_path

        # 3. Resolve Text
        title = str(scene.get("title", "")).strip()
        caption = str(scene.get("caption", "")).strip()
        
        # Logic: If both empty, pass empty strings (Sequencer handles "no black bar" logic)
        # Note: Sequencer.create_sidebar_clip checks `if title or caption`.
        
        # 4. Add to Sequencer
        print(f"Adding scene: {item_name}")
        sequencer.add_scene(
            video_path=video_path,
            title=title,
            caption=caption,
            effects_duration=float(scene.get("effects_duration", 0.5)),
            text_direction=scene.get("text_direction", "left"),
            audio_path=audio_path
        )
        scenes_added += 1

    if scenes_added > 0:
        print(f"Rendering {scenes_added} scenes to {final_filename}...")
        sequencer.render(final_filename, fps=24)
        print("Done!")
    else:
        print("No valid scenes found to render.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Excel-based AI Video Generator")
    
    parser.add_argument(
        "action", 
        choices=["video", "edit", "all"], 
        help="'video': Generate assets. 'edit': Combine them. 'all': Do both."
    )
    
    parser.add_argument(
        "config_file", 
        help="Path to .xlsx (Excel) or .json config file."
    )

    args = parser.parse_args()

    # Environment Check
    if args.action in ["video", "all"]:
        if "FAL_KEY" not in os.environ or "ELEVENLABS_API_KEY" not in os.environ:
            print("WARNING: FAL_KEY or ELEVENLABS_API_KEY missing in environment.")

    # Load Config
    config_data = load_config(args.config_file)

    # Execute
    if args.action == "video" or args.action == "all":
        run_content_generation(config_data)
        
    if args.action == "edit" or args.action == "all":
        run_editor(config_data)