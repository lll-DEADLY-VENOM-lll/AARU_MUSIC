import asyncio, os, re, httpx, aiofiles.os
from io import BytesIO 
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from aiofiles.os import path as aiopath
from youtubesearchpython.__future__ import VideosSearch

from ..logging import LOGGER

# Fonts loading with extra safety
def load_fonts():
    try:
        # Check if font files exist before loading
        cfont_path = "PURVIMUSIC/assets/cfont.ttf"
        tfont_path = "PURVIMUSIC/assets/font.ttf"
        if os.path.exists(cfont_path) and os.path.exists(tfont_path):
            return {
                "cfont": ImageFont.truetype(cfont_path, 24),
                "tfont": ImageFont.truetype(tfont_path, 30),
            }
    except Exception as e:
        LOGGER.error(f"Font loading error: {e}")
    
    return {
        "cfont": ImageFont.load_default(),
        "tfont": ImageFont.load_default(),
    }

FONTS = load_fonts()

FALLBACK_IMAGE_PATH = "PURVIMUSIC/assets/controller.png"
YOUTUBE_IMG_URL = "https://i.ytimg.com/vi/default.jpg"

async def resize_youtube_thumbnail(img: Image.Image) -> Image.Image:
    target_width, target_height = 1280, 720
    img = img.convert("RGBA")
    
    # Aspect ratio maintenance
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        new_height = target_height
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_width
        new_height = int(new_width / img_ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    img = img.crop((left, top, left + target_width, top + target_height))
    
    return ImageEnhance.Sharpness(img).enhance(1.5)

async def fetch_image(url: str) -> Image.Image:
    async with httpx.AsyncClient() as client:
        try:
            if not url:
                raise ValueError("No URL")
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return await resize_youtube_thumbnail(img)
        except Exception as e:
            LOGGER.error(f"Image fetch error: {e}")
            # Try Local Fallback
            if os.path.exists(FALLBACK_IMAGE_PATH):
                img = Image.open(FALLBACK_IMAGE_PATH)
                return await resize_youtube_thumbnail(img)
            return Image.new("RGBA", (1280, 720), (20, 20, 20, 255))

def clean_text(text: str, limit: int = 25) -> str:
    if not text:
        return "Unknown"
    text = str(text).strip()
    return f"{text[:limit - 3]}..." if len(text) > limit else text

async def add_controls(img: Image.Image) -> Image.Image:
    # Blur background
    background = img.filter(ImageFilter.GaussianBlur(radius=40))
    background = ImageEnhance.Brightness(background).enhance(0.5)
    
    # Draw dark rounded box
    draw = ImageDraw.Draw(background)
    box = (305, 125, 975, 595)
    draw.rounded_rectangle(box, radius=25, fill=(0, 0, 0, 150))

    # Paste controls if exist
    try:
        if os.path.exists("PURVIMUSIC/assets/controls.png"):
            controls = Image.open("PURVIMUSIC/assets/controls.png").convert("RGBA")
            controls = controls.resize((600, 160), Image.Resampling.LANCZOS)
            background.paste(controls, (340, 415), controls)
            controls.close()
    except Exception:
        pass
        
    return background

def make_rounded_rectangle(image: Image.Image, size: tuple = (250, 250)) -> Image.Image:
    image = image.convert("RGBA")
    image = ImageOps.fit(image, size, centering=(0.5, 0.5))
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=30, fill=255)
    image.putalpha(mask)
    return image

async def get_thumb(videoid: str) -> str:
    if not videoid:
        return ""

    save_dir = f"database/photos/{videoid}.png"
    if not os.path.exists("database/photos"):
        os.makedirs("database/photos", exist_ok=True)

    # 1. Fetch Metadata Safely
    title, artist, thumbnail_url = "Unknown Title", "Unknown Artist", YOUTUBE_IMG_URL
    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        resp = await results.next()
        
        if resp and "result" in resp and len(resp["result"]) > 0:
            res = resp["result"][0]
            title = res.get("title", "Unknown Title")
            artist = res.get("channel", {}).get("name", "Unknown Artist")
            # Get best quality thumbnail
            if "thumbnails" in res and res["thumbnails"]:
                thumbnail_url = res["thumbnails"][0].get("url", "").split("?")[0]
    except Exception as e:
        LOGGER.error(f"Metadata error: {e}")

    # 2. Process Image
    try:
        raw_img = await fetch_image(thumbnail_url)
        bg = await add_controls(raw_img)
        
        # Square rounded thumbnail in the middle
        rounded_thumb = make_rounded_rectangle(raw_img, size=(200, 200))
        bg.paste(rounded_thumb, (340, 160), rounded_thumb)

        # 3. Add Text
        draw = ImageDraw.Draw(bg)
        safe_title = clean_text(title, limit=30)
        safe_artist = clean_text(artist, limit=35)
        
        draw.text((560, 170), safe_title, (255, 255, 255), font=FONTS["tfont"])
        draw.text((560, 220), safe_artist, (200, 200, 200), font=FONTS["cfont"])

        # 4. Save
        bg = bg.convert("RGB") # PNG se size badhta hai, RGB saves space
        bg.save(save_dir, "PNG", optimize=True)
        
        raw_img.close()
        rounded_thumb.close()
        bg.close()
        
        return save_dir
    except Exception as e:
        LOGGER.error(f"Thumbnail generation failed: {e}")
        return ""
