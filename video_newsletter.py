import os
import sys
import json
import argparse

# Import your custom modules
try:
    from video_generator import process_images
    from video_editor import StorySequencer
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure 'video_generator.py' and 'video_editor.py' are in the current directory.")
    sys.exit(1)

def load_config(config_path):
    """Loads and validates the JSON configuration."""
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_video_generation(config):
    """Step 1: Generates AI videos from images using Fal.ai."""
    print("\n=== STEP 1: Video Generation (Fal.ai) ===")
    
    video_folder = config.get("video_folder", "generated_videos")
    scenes = config.get("scenes", [])
    
    if not os.path.exists(video_folder):
        os.makedirs(video_folder)

    # Prepare dictionary for video_generator {image_path: prompt}
    images_to_process = {}
    
    for scene in scenes:
        img_path = scene.get("image_path")
        if not img_path or not os.path.exists(img_path):
            print(f"[Warning] Source image '{img_path}' not found. Skipping.")
            continue
            
        # Predict output filename
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        expected_video_path = os.path.join(video_folder, f"{base_name}_video.mp4")
        
        if not os.path.exists(expected_video_path):
            print(f"  [Queue] {img_path} -> Video will be generated.")
            images_to_process[img_path] = scene.get("video_hint")
        else:
            print(f"  [Skip] Video already exists: {expected_video_path}")

    if images_to_process:
        print(f"Generating {len(images_to_process)} videos...")
        process_images(
            images_to_process, 
            model_endpoint="fal-ai/kandinsky5-pro/image-to-video",
            duration="5s",
            download_path=video_folder
        )
    else:
        print("No new videos to generate.")

def run_editor(config):
    """Step 2: Assembles the final video using MoviePy."""
    print("\n=== STEP 2: Final Assembly (MoviePy) ===")
    
    output_res = config.get("output_resolution", [1280, 720])
    final_filename = config.get("final_filename", "final_story.mp4")
    video_folder = config.get("video_folder", "generated_videos")
    scenes = config.get("scenes", [])
    
    # Initialize Sequencer
    sequencer = StorySequencer(output_width=output_res[0], output_height=output_res[1])

    for scene in scenes:
        img_path = scene.get("image_path")
        if not img_path: continue

        # Resolve video path
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        video_path = os.path.join(video_folder, f"{base_name}_video.mp4")

        if os.path.exists(video_path):
            sequencer.add_scene(
                video_path=video_path,
                title=scene.get("title", ""),
                caption=scene.get("caption", ""),
                intro_duration=scene.get("intro_duration", 3.0),
                slide_duration=scene.get("slide_duration", 1.5),
                fade_duration=scene.get("fade_duration", 1.5),
                text_direction=scene.get("text_direction", "left")
            )
        else:
            print(f"[Error] Missing video file for scene: {video_path}")

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
        help="Which step of the pipeline to run."
    )
    
    parser.add_argument(
        "config_file", 
        help="Path to the .json configuration file."
    )

    args = parser.parse_args()

    # check environment variables
    missing_keys = []
    if args.action in ["video", "all"] and "FAL_KEY" not in os.environ:
        missing_keys.append("FAL_KEY")

    if missing_keys:
        print("WARNING: The following environment variables are missing:")
        for k in missing_keys: print(f" - {k}")
        print("Functionality relying on them will fail.\n")

    # Load Config
    config = load_config(args.config_file)

    # Execute Steps
    if args.action == "video" or args.action == "all":
        run_video_generation(config)
        
    if args.action == "edit" or args.action == "all":
        run_editor(config)