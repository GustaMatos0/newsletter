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

