import os
import re
import aiofiles
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch, Video
from config import YOUTUBE_IMG_URL
from ..logging import LOGGER

# Function to resize images while maintaining quality
def resize_image(image, max_width, max_height):
    width_ratio = max_width / image.size[0]
    height_ratio = max_height / image.size[1]
    new_width = int(width_ratio * image.size[0])
    new_height = int(height_ratio * image.size[1])
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Function to split long titles into two lines
def truncate_title(text):
    words = text.split(" ")
    line1, line2 = "", ""    
    for word in words:
        if len(line1) + len(word) < 30:        
            line1 += " " + word
        elif len(line2) + len(word) < 30:       
            line2 += " " + word
    return [line1.strip(), line2.strip()]

# Function to create the circular thumbnail crop
def crop_to_circle(img, size, border_width, crop_scale=1.5):
    img = img.convert("RGBA")
    width, height = img.size
    
    # Square crop based on center
    shorter_side = min(width, height)
    larger_size = int(size * crop_scale)
    
    img = img.crop((
        (width - larger_size) // 2,
        (height - larger_size) // 2,
        (width + larger_size) // 2,
        (height + larger_size) // 2
    ))
    
    img = img.resize((size - 2 * border_width, size - 2 * border_width), Image.Resampling.LANCZOS)
    
    # Create transparent canvas for the circle
    circle_canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    # Create circular mask
    mask = Image.new("L", (size - 2 * border_width, size - 2 * border_width), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size - 2 * border_width, size - 2 * border_width), fill=255)
    
    # Paste image onto canvas using mask
    circle_canvas.paste(img, (border_width, border_width), mask)
    
    # Draw a thin white border around the circle
    draw_border = ImageDraw.Draw(circle_canvas)
    draw_border.ellipse((0, 0, size, size), outline="white", width=border_width)
    
    return circle_canvas

async def get_thumb(videoid):
    # Return cached image if exists
    cache_path = f"cache/{videoid}_v4.png"
    if os.path.isfile(cache_path):
        return cache_path

    if not os.path.exists("cache"):
        os.makedirs("cache")

    # Default Metadata placeholders
    title, duration, views, channel, thumb_url = "Unknown", "00:00", "0", "Unknown", YOUTUBE_IMG_URL
    
    # --- FETCH METADATA (FIX FOR "FAILED TO FETCH") ---
    try:
        # High-reliability method using Video ID directly
        video_data = await Video.getInfo(f"https://www.youtube.com/watch?v={videoid}")
        if video_data:
            title = video_data.get("title", "Unknown Title")
            duration = video_data.get("duration", {}).get("label", "00:00")
            views = video_data.get("viewCount", {}).get("short", "0 Views")
            channel = video_data.get("channel", {}).get("name", "Unknown Channel")
            # Get highest resolution thumbnail
            thumbnails = video_data.get("thumbnails", [])
            thumb_url = thumbnails[-1]["url"].split("?")[0] if thumbnails else f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
    except Exception as e:
        LOGGER.error(f"Metadata error for {videoid}: {str(e)}")
        # Fallback to search if GetInfo fails
        try:
            search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
            result = (await search.next())["result"][0]
            title = result["title"]
            duration = result.get("duration", "00:00")
            views = result.get("viewCount", {}).get("short", "0")
            channel = result.get("channel", {}).get("name", "Unknown")
            thumb_url = result["thumbnails"][0]["url"].split("?")[0]
        except:
            thumb_url = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"

    # Download the thumbnail image
    temp_thumb = f"cache/temp_{videoid}.png"
    async with aiohttp.ClientSession() as session:
        async with session.get(thumb_url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(temp_thumb, mode="wb")
                await f.write(await resp.read())
                await f.close()

    # --- IMAGE PROCESSING ---
    try:
        raw_image = Image.open(temp_thumb)
        
        # 1. Create Blurred Background
        bg_image = resize_image(raw_image, 1280, 720)
        background = bg_image.convert("RGBA").filter(ImageFilter.BoxBlur(25))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.5) # Darken background
        
        draw = ImageDraw.Draw(background)
        
        # Load Fonts (Fallback to default if not found)
        try:
            font_path = "PURVIMUSIC/assets/font.ttf"
            title_font = ImageFont.truetype(font_path, 45)
            subtitle_font = ImageFont.truetype(font_path, 30)
        except:
            title_font = subtitle_font = ImageFont.load_default()

        # 2. Add Circular Thumbnail
        circle_art = crop_to_circle(raw_image, 400, 10)
        background.paste(circle_art, (120, 160), circle_art)

        # 3. Draw Text (Title & Channel)
        text_x = 565
        clean_title = re.sub(r"\W+", " ", title).title()
        title_lines = truncate_title(clean_title)
        
        draw.text((text_x, 180), title_lines[0], fill="white", font=title_font)
        draw.text((text_x, 235), title_lines[1], fill="white", font=title_font)
        draw.text((text_x, 320), f"{channel}  |  {views}", fill="#CCCCCC", font=subtitle_font)

        # 4. Draw Modern Progress Bar
        bar_x_start = text_x
        bar_width = 580
        bar_y = 385
        
        # Background Bar (Gray)
        draw.line([(bar_x_start, bar_y), (bar_x_start + bar_width, bar_y)], fill="#444444", width=6)
        # Progress Bar (Red)
        draw.line([(bar_x_start, bar_y), (bar_x_start + 350, bar_y)], fill="#FF0000", width=6)
        # Slider Knob (White Circle)
        draw.ellipse([(bar_x_start + 345, bar_y - 7), (bar_x_start + 355, bar_y + 7)], fill="white")

        # 5. Draw Duration Text
        draw.text((bar_x_start, 405), "00:00", fill="white", font=subtitle_font)
        draw.text((bar_x_start + bar_width - 80, 405), duration, fill="white", font=subtitle_font)

        # 6. Paste Control Icons (If exists)
        icon_path = "PURVIMUSIC/assets/play_icons.png"
        if os.path.exists(icon_path):
            icons = Image.open(icon_path).convert("RGBA")
            icons = icons.resize((580, 62), Image.Resampling.LANCZOS)
            background.paste(icons, (text_x, 465), icons)

        # Save Final Image
        final_image = background.convert("RGB")
        final_image.save(cache_path, "PNG")
        
        # Cleanup temp files
        if os.path.exists(temp_thumb):
            os.remove(temp_thumb)
            
        return cache_path

    except Exception as e:
        LOGGER.error(f"Image generation failed: {e}")
        return YOUTUBE_IMG_URL 
