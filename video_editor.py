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