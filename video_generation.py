import os
import fal_client
import requests
import mimetypes
from dotenv import load_dotenv
import logging as log 


DEFAULT_VISION_ENDPOINT = "openrouter/router/vision"
DEFAULT_VISION_MODEL = "google/gemini-2.5-flash" 
DEFAULT_VIDEO_ENDPOINT = "fal-ai/kandinsky5-pro/image-to-video"

load_dotenv()


def process_images(
    image_dict, 
    model_endpoint=DEFAULT_VIDEO_ENDPOINT, 
    duration="5s", 
    download_path="",
    test_mode="fully_working"
):
    """
    1. Uploads local images to Fal.
    2. Uses a Vision model to generate a custom cinematic prompt.
    3. Sends the image + generated prompt to the Video generation API.
    4. Downloads the result.

    Args:
        image_dict (dict): { "path/to/image.jpg": "Optional hint (or None)" }
        model_endpoint (str): The video generation model endpoint.
        duration (str): Duration (e.g., "5s"). Different models have different options, so check documentation.
        download_path (str): Folder to save downloaded videos.
    """
    
    if not os.environ.get("FAL_KEY"):
        log.critical("Error: FAL_KEY not found. Check .env")
        return

    if download_path and not os.path.exists(download_path):
        os.makedirs(download_path)

    total = len(image_dict)
    
    for i, (image_path, user_hint) in enumerate(image_dict.items(), 1):
        
        # Validation
        if not os.path.exists(image_path):
            log.info(f"Skipping [{i}/{total}]: {image_path} (File not found)")
            continue

        log.info(f"\nProcessing [{i}/{total}]: {image_path}")

        try:
            # Upload Image
            log.info("  [1/4] Uploading image to Fal.ai storage...")
            image_url = fal_client.upload_file(image_path)
            
            # Vision Model 
            log.info("  [2/4] Analyzing image with Vision model...")
            
            # Construct request for vision model
            vision_prompt = (
                "Describe this image in detail. Then, based on the description, "
                "write a single, creative, high-quality prompt for a cinematic video generation model. "
                "The video should have motion and life. "
                "Output ONLY the final video generation prompt, nothing else."
            )
            
            # add hint
            if test_mode == "fully_working":
                if user_hint:
                    vision_prompt += f" \nIMPORTANT style/context instruction: {user_hint}"

                vision_result = fal_client.subscribe(
                    DEFAULT_VISION_ENDPOINT,
                    arguments={
                        "image_urls": [image_url],
                        "prompt": vision_prompt,
                        "model": DEFAULT_VISION_MODEL
                    }
                )
            
            # Extract the generated text
                generated_prompt = vision_result.get('output', '').strip()
                log.info(f"  --> Generated Prompt: \"{generated_prompt}\"")

                if not generated_prompt:
                    log.error("  Error: Vision model returned empty prompt. Using fallback.")
                    generated_prompt = "A cinematic video of this scene, high quality, 4k"

            # Video Generation
            log.info(f"  [3/4] Generating video using {model_endpoint}...")

            result = None

            if test_mode == "fully_working":
            
                video_handler = fal_client.submit(
                    model_endpoint,
                    arguments={
                        "image_url": image_url,
                        "prompt": generated_prompt,
                        "duration": duration
                    }
                )
                result = video_handler.get()

        except Exception as e:
            log.error(f"  Error processing {image_path}: {e}")