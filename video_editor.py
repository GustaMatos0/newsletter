import os
import textwrap
import math
import numpy as np
from moviepy import (
    VideoFileClip, 
    ImageClip, 
    TextClip, 
    CompositeVideoClip, 
    ColorClip, 
    AudioFileClip,
    concatenate_videoclips,
    vfx
)

# Helpers before main functionality
# Cropping function

def resize_and_crop(clip, target_w, target_h):
    """
    Resizes the clip to fill the target dimensions while maintaining aspect ratio,
    then center crops the excess. This prevents aspect ratio mismatches.
    """
    w, h = clip.w, clip.h
    
    # Avoid division by zero
    if h == 0 or target_h == 0:
        return clip

    target_ratio = target_w / target_h
    current_ratio = w / h
    
    if current_ratio > target_ratio:
        # Resize based on Height to fill vertically, then crop width.
        new_clip = clip.resized(height=target_h)
    else:
        # Resize based on Width to fill horizontally, then crop height.
        new_clip = clip.resized(width=target_w)
        
    # Center crop to exact target dimensions
    return new_clip.cropped(width=target_w, height=target_h, x_center=new_clip.w / 2, y_center=new_clip.h / 2)

def create_gradient_bar(width, height, direction='left', color=(0,0,0), max_opacity=0.8):
    """
    Creates a gradient bar (RGBA) for text background using numpy.
    Supports left, right, top, and bottom fade directions.
    """
    w, h = int(width), int(height)
    
    if w <= 0 or h <= 0:
        return ColorClip(size=(max(1, w), max(1, h)), color=(0,0,0,0))

    if direction in ['left', 'right']:
        x = np.linspace(0, 1, w)
        if direction == 'left':
            alpha_row = (1 - x) * 255 * max_opacity
        else: # right
            alpha_row = x * 255 * max_opacity
            
        alpha_row = alpha_row.reshape(1, w)
        alpha = np.tile(alpha_row, (h, 1))
    else:
        y = np.linspace(0, 1, h)
        if direction == 'top':
            alpha_col = (1 - y) * 255 * max_opacity
        else: # bottom
            alpha_col = y * 255 * max_opacity
            
        alpha_col = alpha_col.reshape(h, 1)
        alpha = np.tile(alpha_col, (1, w))
    
    r = np.full((h, w), color[0])
    g = np.full((h, w), color[1])
    b = np.full((h, w), color[2])
    
    img_array = np.dstack((r, g, b, alpha)).astype(np.uint8)
    
    return ImageClip(img_array)

def create_text_clip(text, font, fontsize, color, size, align='left', stroke_color=None, stroke_width=0):
    """
    Creates a TextClip with robust error handling for missing fonts and wrapping.
    Fonts have to be in the same folder and named explicitly. Function does not access system fonts.
    """
    if not text:
        return None

    safe_width_px = int(size[0]) if size[0] else 1000
    avg_char_width = fontsize * 0.5 
    max_chars_per_line = max(1, int(safe_width_px / avg_char_width))
    
    if len(text) > max_chars_per_line:
        final_text = textwrap.fill(text, width=max_chars_per_line)
    else:
        final_text = text
    
    final_text = final_text + "\n"

    try:
        clip = TextClip(
            text=final_text, 
            font_size=fontsize, 
            color=color, 
            font=font,
            method='label', 
            text_align=align, 
            stroke_color=stroke_color,
            stroke_width=stroke_width
        )
        
        if clip.w == 0 or clip.h == 0:
            print(f"[WARNING] Generated TextClip has 0 dimensions.")
            return None
            
        return clip

    except Exception as e:
        print(f"\n[ERROR] Failed to render text: '{text[:10]}...'")
        return None

def create_sidebar_clip(width, height, direction, title, caption, title_font='Arial', title_size=30, caption_font='Arial', caption_size=20):
    """
    Creates a composite clip containing the gradient background and text.
    Adapts layout dynamically to left, right, top, or bottom positioning.
    """
    # 1. Establish Layout based on orientation
    if direction in ['left', 'right']:
        bg_width = int(width * 1.2) 
        bg_height = height
        text_width = int(width * 0.8)
        padding_x = int(width * 0.1)
        padding_y = int(height * 0.1)
        txt_align = 'left'
    else: # top, bottom
        bg_width = width
        bg_height = int(height * 1.2)
        text_width = int(width * 0.8) # Constrain text to 80% of screen width
        padding_x = int(width * 0.03)
        padding_y = int(height * 0.1)
        txt_align = 'left'

    bg_clip = create_gradient_bar(bg_width, bg_height, direction=direction)
    layers = [bg_clip]
    
    # 2. Pre-create Text Clips to know their exact height
    t_clip = None
    c_clip = None
    total_text_h = 0
    
    if title:
        t_clip = create_text_clip(title, title_font, title_size, color='white', size=(text_width, None),
                                  align=txt_align, stroke_color='black', stroke_width=2)
        if t_clip: total_text_h += t_clip.h
        
    if caption:
        c_clip = create_text_clip(caption, caption_font, caption_size, color='yellow', size=(text_width, None),
                                  align=txt_align, stroke_color='black', stroke_width=1)
        if c_clip: total_text_h += c_clip.h
        
    if t_clip and c_clip:
        total_text_h += 20 # Padding between title and caption

    # 3. Determine starting vertical cursor
    if direction in ['left', 'right', 'top']:
        current_y = padding_y
    else: # bottom
        # Solid dark color is at the absolute bottom edge of bg_height
        current_y = bg_height - padding_y - total_text_h

    # 4. Apply Position and Compose
    if t_clip:
        if direction == 'left': x_pos = padding_x
        elif direction == 'right': x_pos = bg_width - t_clip.w - padding_x
        else: x_pos = padding_x # Left-aligned for top/bottom with padding
            
        t_clip = t_clip.with_position((x_pos, current_y))
        layers.append(t_clip)
        current_y += t_clip.h + 20
            
    if c_clip:
        if direction == 'left': x_pos = padding_x
        elif direction == 'right': x_pos = bg_width - c_clip.w - padding_x
        else: x_pos = padding_x # Left-aligned for top/bottom with padding

        c_clip = c_clip.with_position((x_pos, current_y))
        layers.append(c_clip)

    return CompositeVideoClip(layers, size=(bg_width, bg_height))

class VideoCompositor:
    def __init__(self, base_video_path):
        if not os.path.exists(base_video_path):
            raise FileNotFoundError(f"Video file not found: {base_video_path}")
            
        self.base_clip = VideoFileClip(base_video_path)
        self.elements = [self.base_clip]
        self.duration = self.base_clip.duration
        self.video_width = self.base_clip.w
        self.video_height = self.base_clip.h

    def apply_base_transitions(self, fade_in=0, fade_out=0, color=(0,0,0)):
        effects = []
        if fade_in > 0:
            effects.append(vfx.FadeIn(duration=fade_in, initial_color=color))
        if fade_out > 0:
            effects.append(vfx.FadeOut(duration=fade_out, final_color=color))
        
        if effects:
            self.elements[0] = self.elements[0].with_effects(effects)

    def add_image_overlay(self, image_path, start_time=0, duration=None, 
                          position=('center', 'center'), opacity=1.0, scale=1.0,
                          fade_in=0.0, fade_out=0.0):
        if not os.path.exists(image_path):
            print(f"Warning: Image path {image_path} not found.")
            return

        new_clip = ImageClip(image_path)
        final_duration = duration if duration else (self.duration - start_time)
        new_clip = new_clip.with_start(start_time).with_duration(final_duration)

        if scale != 1.0:
            new_clip = new_clip.resized(scale)
        new_clip = new_clip.with_opacity(opacity).with_position(position)

        effects = []
        if fade_in > 0: effects.append(vfx.CrossFadeIn(duration=fade_in))
        if fade_out > 0: effects.append(vfx.CrossFadeOut(duration=fade_out))
        if effects: new_clip = new_clip.with_effects(effects)

        self.elements.append(new_clip)

    def add_text_overlay(self, text, font='Arial', fontsize=50, color='white', 
                         start_time=0, duration=None, position=('center', 'bottom'), 
                         opacity=1.0, stroke_color=None, stroke_width=0,
                         fade_in=0.0, fade_out=0.0):
        
        txt_clip = create_text_clip(
            text, font, fontsize, color, (self.video_width, None), 
            align='center', stroke_color=stroke_color, stroke_width=stroke_width
        )
        
        if txt_clip:
            final_duration = duration if duration else (self.duration - start_time)
            txt_clip = txt_clip.with_start(start_time).with_duration(final_duration)
            txt_clip = txt_clip.with_opacity(opacity).with_position(position)

            effects = []
            if fade_in > 0: effects.append(vfx.CrossFadeIn(duration=fade_in))
            if fade_out > 0: effects.append(vfx.CrossFadeOut(duration=fade_out))
            if effects: txt_clip = txt_clip.with_effects(effects)

            self.elements.append(txt_clip)

    def render(self, output_path, fps=24):
        final_video = CompositeVideoClip(self.elements, size=self.base_clip.size)
        final_video.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', threads=4)

# --- New Story Sequencer ---
class StorySequencer:
    def __init__(self, output_width=1024, output_height=576):
        self.w = output_width
        self.h = output_height
        self.clips = [] 
        self.current_time = 0.0

    def add_scene(self, video_path, title, caption, title_font ='Arial',
                    caption_font = 'Arial',
                    effects_duration = 0.5,      # Fade animation length
                    text_direction='left',       # 'left', 'right', 'top', 'bottom'
                    audio_path=None              # Optional audio path
                    ):
        """
        Creates a composite scene with sliding intro, side-bar text, and optional audio.
        """

        intro_duration = effects_duration
        slide_duration = effects_duration
        fade_duration = effects_duration

        if not os.path.exists(video_path):
            print(f"Skipping scene: Missing {video_path}")
            return

        # Load Video
        # Resizing for good measure
        raw_clip = VideoFileClip(video_path)
        video_clip = resize_and_crop(raw_clip, self.w, self.h)
        
        # Extract first frame
        first_frame = video_clip.get_frame(0)
        intro_bg = ImageClip(first_frame)

        # Calculate Overlap and Start Time
        is_first_scene = (self.current_time == 0.0)
        overlap_time = slide_duration if not is_first_scene else 0.0
        scene_start_time = max(0, self.current_time - overlap_time)

        print(f"Adding scene '{title.strip() if title else 'Untitled'}' at t={scene_start_time:.2f}s (Overlap: {overlap_time}s)")

        # Intro 
        intro_bg = intro_bg.with_start(scene_start_time).with_duration(intro_duration)
        
        effects = []
        if fade_duration > 0:
            effects.append(vfx.CrossFadeIn(duration=fade_duration))
        if slide_duration > 0:
            effects.append(vfx.SlideIn(duration=slide_duration, side=text_direction))
        
        if effects:
            intro_bg = intro_bg.with_effects(effects)
        
        self.clips.append(intro_bg)

        # Main Video Logic (Audio Handling)
        video_start_time = scene_start_time + intro_duration
        
        # Handle Audio and Looping
        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)
            
            # If Audio is longer than Video, Loop the Video
            if audio_clip.duration > video_clip.duration:
                # Calculate required loops
                loops = math.ceil(audio_clip.duration / video_clip.duration)
                print(f"  [Looping] Audio ({audio_clip.duration:.2f}s) > Video ({video_clip.duration:.2f}s). Looping {loops} times.")
                
                # Loop by concatenating
                video_clip = concatenate_videoclips([video_clip] * loops)
                # Trim to exact audio length
                video_clip = video_clip.with_duration(audio_clip.duration)
            
            # Attach audio to video
            video_clip = video_clip.with_audio(audio_clip)
        
        # Set start time for video (now potentially looped)
        video_clip = video_clip.with_start(video_start_time)
        self.clips.append(video_clip)

        # Side-Bar Text Overlay
        if title or caption:
            # Orientation affects text boundaries
            if text_direction in ['top', 'bottom']:
                sidebar_width_target = self.w
                sidebar_height_target = int(self.h * 0.3)
            else:
                sidebar_width_target = int(self.w * 0.3)
                sidebar_height_target = self.h
            
            sidebar_clip = create_sidebar_clip(
                width=sidebar_width_target,
                height=sidebar_height_target,
                direction=text_direction,
                title=title,
                caption=caption,
                title_font = title_font,
                caption_font = caption_font
            )
            
            # Text starts when video starts and lasts for the full duration of the video
            text_dur = video_clip.duration
            sidebar_clip = sidebar_clip.with_start(video_start_time).with_duration(text_dur)
            
            # Positioning Logic (Manual 2D animation)
            if text_direction == 'left':
                start_x, final_x = -sidebar_clip.w, 0
                start_y, final_y = 0, 0
            elif text_direction == 'right':
                start_x, final_x = self.w, self.w - sidebar_clip.w
                start_y, final_y = 0, 0
            elif text_direction == 'top':
                start_x, final_x = 0, 0
                start_y, final_y = -sidebar_clip.h, 0
            elif text_direction == 'bottom':
                start_x, final_x = 0, 0
                start_y, final_y = self.h, self.h - sidebar_clip.h
            else:
                # Safety fallback
                start_x, final_x, start_y, final_y = 0, 0, 0, 0

            def slide_pos(t):
                if t < 1.0: 
                    progress = t / 1.0
                    x = start_x + (final_x - start_x) * progress
                    y = start_y + (final_y - start_y) * progress
                    return (int(x), int(y))
                else:
                    return (int(final_x), int(final_y))

            sidebar_clip = sidebar_clip.with_position(slide_pos)
            
            text_effects = [vfx.CrossFadeIn(duration=0.5)]
            sidebar_clip = sidebar_clip.with_effects(text_effects)
            
            self.clips.append(sidebar_clip)

        # Update Cursor
        self.current_time = video_start_time + video_clip.duration

    def render(self, output_path, fps=24):
        if not self.clips:
            print("No clips to render.")
            return

        print(f"Compositing {len(self.clips)} elements...")
        total_duration = self.current_time
        bg = ColorClip(size=(self.w, self.h), color=(0,0,0), duration=total_duration)
        final_movie = CompositeVideoClip([bg] + self.clips)
        
        print(f"Rendering full story to {output_path} (Duration: {total_duration:.2f}s)...")
        final_movie.write_videofile(
            output_path, 
            fps=fps, 
            codec='libx264', 
            audio_codec='aac',
            threads=4
        )
        print("Story render complete!")