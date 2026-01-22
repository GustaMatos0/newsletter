import os
import textwrap
import numpy as np
from moviepy import (
    VideoFileClip, 
    ImageClip, 
    TextClip, 
    CompositeVideoClip, 
    ColorClip, 
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



def create_text_clip(text, font, fontsize, color, size, align='center', stroke_color=None, stroke_width=0):
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

def create_sidebar_clip(width, height, direction, title, caption, font='Arial'):
    """
    Creates a composite clip containing the gradient background and text.
    """
    bg_width = int(width * 1.2) 
    bg_clip = create_gradient_bar(bg_width, height, direction=direction)
    
    layers = [bg_clip]
    
    text_width = int(width * 0.8)
    padding_x = int(width * 0.1)
    
    if direction == 'left':
        txt_align = 'left'
    else:
        txt_align = 'right'

    current_y = int(height * 0.1) 

    if title:
        title_clip = create_safe_text_clip(
            title, font, fontsize=30, color='white', size=(text_width, None),
            align=txt_align, stroke_color='black', stroke_width=2
        )
        if title_clip:
            if direction == 'left':
                x_pos = padding_x
            else:
                x_pos = bg_width - title_clip.w - padding_x
                
            title_clip = title_clip.with_position((x_pos, current_y))
            layers.append(title_clip)
            current_y += title_clip.h + 20
            
    if caption:
        cap_clip = create_safe_text_clip(
            caption, font, fontsize=20, color='yellow', size=(text_width, None),
            align=txt_align, stroke_color='black', stroke_width=1
        )
        if cap_clip:
            if direction == 'left':
                x_pos = padding_x
            else:
                x_pos = bg_width - cap_clip.w - padding_x

            cap_clip = cap_clip.with_position((x_pos, current_y))
            layers.append(cap_clip)

    return CompositeVideoClip(layers, size=(bg_width, height))

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
        
        txt_clip = create_safe_text_clip(
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

        effects = []
        if fade_in > 0:
            effects.append(vfx.CrossFadeIn(duration=fade_in))
        if fade_out > 0:
            effects.append(vfx.CrossFadeOut(duration=fade_out))
        
        if effects:
            new_clip = new_clip.with_effects(effects)

        self.elements.append(new_clip)
        print(f"Added overlay: {os.path.basename(image_path)} (fades: {fade_in}s/{fade_out}s)")