import os
import textwrap
from moviepy import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, vfx

class VideoCompositor:
    def __init__(self, base_video_path):
        """
        Initializes the editor with a base video file.
        """
        if not os.path.exists(base_video_path):
            raise FileNotFoundError(f"Video file not found: {base_video_path}")
            
        self.base_clip = VideoFileClip(base_video_path)
        # The base clip is always the first element
        self.elements = [self.base_clip] 
        self.duration = self.base_clip.duration
        self.video_width = self.base_clip.w
        self.video_height = self.base_clip.h

    def apply_base_transitions(self, fade_in=0, fade_out=0, color=(0,0,0)):
        """
        Applies fade in/out to the main background video (fades to/from a color, default black).
        """
        effects = []
        if fade_in > 0:
            effects.append(vfx.FadeIn(duration=fade_in, initial_color=color))
        if fade_out > 0:
            effects.append(vfx.FadeOut(duration=fade_out, final_color=color))
        
        if effects:
            # Update the base clip (first element) with effects
            self.elements[0] = self.elements[0].with_effects(effects)
            print(f"Applied base video fade-in: {fade_in}s, fade-out: {fade_out}s")

    def render(self, output_path, fps=24, codec='libx264'):
        """
        Composites all layers and saves the final video file.
        """
        print(f"Rendering {len(self.elements)} elements to {output_path}...")
        final_video = CompositeVideoClip(self.elements, size=self.base_clip.size)
        
        final_video.write_videofile(
            output_path, 
            fps=fps, 
            codec=codec, 
            audio_codec='aac',
            threads=4
        )
        print("Render complete!")

    def add_image_overlay(self, image_path, start_time=0, duration=None, 
                          position=('center', 'center'), opacity=1.0, scale=1.0,
                          fade_in=0.0, fade_out=0.0):
        """
        Adds an image overlay with optional transitions.
        """
        if not os.path.exists(image_path):
            print(f"Warning: Image path {image_path} not found. Skipping.")
            return

        # Load Image
        new_clip = ImageClip(image_path)

        # Handle Duration
        final_duration = duration if duration else (self.duration - start_time)
        new_clip = new_clip.with_start(start_time).with_duration(final_duration)

        # Apply Resize & Opacity
        if scale != 1.0:
            new_clip = new_clip.resized(scale)
        new_clip = new_clip.with_opacity(opacity)
        new_clip = new_clip.with_position(position)

        # Apply Transitions (CrossFade affects opacity)
        effects = []
        if fade_in > 0:
            effects.append(vfx.CrossFadeIn(duration=fade_in))
        if fade_out > 0:
            effects.append(vfx.CrossFadeOut(duration=fade_out))
        
        if effects:
            new_clip = new_clip.with_effects(effects)

        self.elements.append(new_clip)
        print(f"Added overlay: {os.path.basename(image_path)} (fades: {fade_in}s/{fade_out}s)")