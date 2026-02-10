import os
import sys
import json
import argparse
from moviepy import AudioFileClip

# Import your custom modules
try:
    from video_generation import generate_video_single, download_video
    from voice_generation import generate_speech
    from video_editor import StorySequencer
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure 'video_generation.py' and 'video_editor.py' are in the current directory.")
    sys.exit(1)

def load_config(config_path):
    """Loads and validates the JSON configuration."""
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_content_generation(config):
    """Step 1: Generates Audio and Video assets."""
    print("\n=== STEP 1: Content Generation (Audio & Video) ===")
    
    video_folder = config.get("video_folder", "generated_videos")
    audio_folder = config.get("audio_folder", "generated_audio")
    scenes = config.get("scenes", [])
    
    # Create output directories
    if not os.path.exists(video_folder):
        os.makedirs(video_folder)
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)
    
    for i, scene in enumerate(scenes):
        print(f"\nProcessing Scene {i+1}...")

        # --- 1. Audio Generation ---
        # User requirement: Script is the 'title' parameter
        audio_text = scene.get("title", "")
        audio_duration = 0
        audio_path = None
        
        img_path = scene.get("image_path")
        base_name = f"scene_{i}"
        if img_path:
             base_name = os.path.splitext(os.path.basename(img_path))[0]
        
        if audio_text:
            audio_filename = f"{base_name}_audio.mp3"
            audio_path = os.path.join(audio_folder, audio_filename)
            
            if not os.path.exists(audio_path):
                print(f"  [Audio] Generating speech for: '{audio_text[:20]}...'")
                success = generate_speech(audio_text, audio_path)
                if not success:
                    print("  [Error] Audio generation failed.")
            else:
                print(f"  [Audio] Exists: {audio_filename}")
            
            # Get Duration for Video
            if os.path.exists(audio_path):
                try:
                    with AudioFileClip(audio_path) as clip:
                        audio_duration = clip.duration
                except Exception as e:
                    print(f"  [Error] Could not read audio duration: {e}")
                    audio_duration = 4 # Fallback
        else:
            print("  [Audio] No title text provided. Skipping audio.")
            audio_duration = 4 # Default fallback

        # --- 2. Video Generation ---
        if not img_path:
            continue
            
        if not os.path.exists(img_path):
            print(f"  [Warning] Source image '{img_path}' not found. Skipping video.")
            continue
            
        video_filename = f"{base_name}_video.mp4"
        video_path = os.path.join(video_folder, video_filename)
        
        if not os.path.exists(video_path):
            # User requirement: Duration = int(audio_duration + 1)
            video_duration_int = int(audio_duration) + 1
            print(f"  [Video] Generating based on audio length ({audio_duration:.2f}s) -> Video Duration: {video_duration_int}s")
            
            generate_video_single(
                image_path=img_path,
                prompt=scene.get("video_hint"),
                duration=video_duration_int, # Passing integer as requested
                output_path=video_path,
                model_endpoint="fal-ai/vidu/q3/image-to-video"
            )
        else:
            print(f"  [Video] Exists: {video_filename}")

def run_editor(config):
    """Step 2: Assembles the final video using MoviePy."""
    print("\n=== STEP 2: Final Assembly (MoviePy) ===")
    
    output_res = config.get("output_resolution", [1280, 720])
    final_filename = config.get("final_filename", "final_story.mp4")
    video_folder = config.get("video_folder", "generated_videos")
    audio_folder = config.get("audio_folder", "generated_audio")
    scenes = config.get("scenes", [])
    
    # Initialize Sequencer
    sequencer = StorySequencer(output_width=output_res[0], output_height=output_res[1])

    n = 0
    for i, scene in enumerate(scenes):
        # 1. Resolve Video Path
        video_path = scene.get("video_path")
        if not video_path and "image_path" in scene:
            img_path = scene["image_path"]
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            video_path = os.path.join(video_folder, f"{base_name}_video.mp4")

        # 2. Resolve Audio Path (Auto-detected from naming convention)
        audio_path = None
        if "image_path" in scene:
            img_path = scene["image_path"]
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            candidate_audio = os.path.join(audio_folder, f"{base_name}_audio.mp3")
            if os.path.exists(candidate_audio):
                audio_path = candidate_audio

        # 3. Validate and Add
        if not video_path:
            print(f"[Skipping Scene {i+1}] No video path found.")
            continue

        if os.path.exists(video_path):
            # First scene vs subsequent scenes logic (n==0 check from previous code)
            effects_dur = scene.get("effects_duration", 0 if n == 0 else 0.5)
            
            sequencer.add_scene(
                video_path=video_path,
                title=scene.get("title", ""),
                caption=scene.get("caption", ""),
                effects_duration=effects_dur,
                text_direction=scene.get("text_direction", "left"),
                audio_path=audio_path # Pass the auto-resolved audio path
            )
            n = 1
        else:
            print(f"[Error] Video file not found: {video_path}")

    if sequencer.clips:
        print(f"Rendering final movie to {final_filename}...")
        sequencer.render(final_filename, fps=24)
        print("Done!")
    else:
        print("No scenes were added. Nothing to render.")

if __name__ == "__main__":
    # Setup CLI Arguments
    parser = argparse.ArgumentParser(description="AI Video Story Generator CLI")
    
    parser.add_argument(
        "action", 
        choices=["video", "edit", "all"], 
        help="Which step of the pipeline to run. 'video' now runs both Audio and Video generation."
    )
    
    parser.add_argument(
        "config_file", 
        help="Path to the .json configuration file."
    )

    args = parser.parse_args()

    # check environment variables
    missing_keys = []
    if args.action in ["video", "all"]:
        if "FAL_KEY" not in os.environ: missing_keys.append("FAL_KEY")
        # ElevenLabs key is now required for generation
        if "ELEVENLABS_API_KEY" not in os.environ: missing_keys.append("ELEVENLABS_API_KEY")

    if missing_keys:
        print("WARNING: The following environment variables are missing:")
        for k in missing_keys: print(f" - {k}")
        print("Functionality relying on them will fail.\n")

    # Load Config
    config = load_config(args.config_file)

    # Execute Steps
    if args.action == "video" or args.action == "all":
        run_content_generation(config)
        
    if args.action == "edit" or args.action == "all":
        run_editor(config)