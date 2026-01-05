import asyncio
import os
import re
import httpx
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch
from ..logging import LOGGER

# Fonts loading with extra safety
def load_fonts():
    # Paths for fonts
    cfont_path = "PURVIMUSIC/assets/cfont.ttf"
    tfont_path = "PURVIMUSIC/assets/font.ttf"
    
    try:
        if os.path.exists(cfont_path) and os.path.exists(tfont_path):
            return {
                "title": ImageFont.truetype(tfont_path, 45), # Title bada kiya
                "artist": ImageFont.truetype(cfont_path, 30),
                "stats": ImageFont.truetype(cfont_path, 25),
            }
    except Exception as e:
        LOGGER.error(f"Font loading error: {e}")
    
    return {
        "title": ImageFont.load_default(),
        "artist": ImageFont.load_default(),
        "stats": ImageFont.load_default(),
    }

FONTS = load_fonts()
FALLBACK_IMAGE_PATH = "PURVIMUSIC/assets/controller.png"

async def fetch_image(url: str) -> Image.Image:
    async with httpx.AsyncClient() as client:
        try:
            # High Resolution image koshish karega
            response = await client.get(url, timeout=15)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return img.convert("RGBA")
        except Exception as e:
            LOGGER.error(f"Image fetch error: {e}")
            if os.path.exists(FALLBACK_IMAGE_PATH):
                return Image.open(FALLBACK_IMAGE_PATH).convert("RGBA")
            return Image.new("RGBA", (1280, 720), (20, 20, 20, 255))

def clean_text(text: str, limit: int = 30) -> str:
    if not text: return "Unknown"
    text = text.encode("ascii", "ignore").decode("ascii") # Non-english chars hatane ke liye
    return f"{text[:limit]}..." if len(text) > limit else text

async def create_modern_thumb(raw_img: Image.Image, title: str, artist: str, duration: str):
    # 1. Background: Blurred & Darkened
    bg = raw_img.resize((1280, 720), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=35))
    enhancer = ImageEnhance.Brightness(bg)
    bg = enhancer.enhance(0.6)

    # 2. Add a Glass Overlay (Central Box)
    draw = ImageDraw.Draw(bg, "RGBA")
    # Draw rounded main container
    draw.rounded_rectangle((50, 50, 1230, 670), radius=30, fill=(0, 0, 0, 100), outline=(255,255,255,30), width=2)

    # 3. Process Main Square Image (Front Image)
    front_img = raw_img.copy()
    front_img = ImageOps.fit(front_img, (450, 450), centering=(0.5, 0.5))
    
    # Rounded corners for front image
    mask = Image.new("L", (450, 450), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, 450, 450), radius=35, fill=255)
    front_img.putalpha(mask)
    
    # Paste Front Image
    bg.paste(front_img, (120, 135), front_img)

    # 4. Add Text (Title & Artist)
    safe_title = clean_text(title, 25)
    safe_artist = clean_text(f"Channel: {artist}", 30)
    
    # Title (Shadow effect)
    draw.text((620, 220), safe_title, (0, 0, 0, 100), font=FONTS["title"]) # Shadow
    draw.text((615, 215), safe_title, (255, 255, 255, 255), font=FONTS["title"]) # Main
    
    # Artist
    draw.text((615, 300), safe_artist, (200, 200, 200, 255), font=FONTS["artist"])
    
    # Duration / Status
    draw.text((615, 360), f"Duration: {duration}", (150, 150, 150, 255), font=FONTS["stats"])

    # 5. Simple Progress Bar Design (New Look)
    draw.rounded_rectangle((615, 450, 1100, 460), radius=5, fill=(255, 255, 255, 50))
    draw.rounded_rectangle((615, 450, 850, 460), radius=5, fill=(255, 0, 100, 200)) # Pink accent
    draw.ellipse((840, 445, 860, 465), fill=(255, 255, 255, 255)) # Knob

    return bg

async def get_thumb(videoid: str) -> str:
    if not videoid:
        return ""

    save_path = f"database/photos/{videoid}.png"
    if not os.path.exists("database/photos"):
        os.makedirs("database/photos", exist_ok=True)

    # Metadata fetching
    title, artist, thumb_url, duration = "Music", "Unknown", "", "00:00"
    
    try:
        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        resp = await search.next()
        if resp and resp.get("result"):
            res = resp["result"][0]
            title = res.get("title", "Unknown")
            artist = res.get("channel", {}).get("name", "Unknown")
            duration = res.get("duration", "04:00")
            # Sabse High Res Thumbnail nikalna
            thumbnails = res.get("thumbnails", [])
            if thumbnails:
                thumb_url = thumbnails[-1]["url"].split("?")[0] # Last one is usually maxres
    except Exception as e:
        LOGGER.error(f"Search Error: {e}")
        thumb_url = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"

    try:
        raw_img = await fetch_image(thumb_url)
        final_thumb = await create_modern_thumb(raw_img, title, artist, duration)
        
        final_thumb = final_thumb.convert("RGB")
        final_thumb.save(save_path, "JPEG", quality=90) # JPEG is faster & smaller
        
        raw_img.close()
        final_thumb.close()
        return save_path
    except Exception as e:
        LOGGER.error(f"Process Error: {e}")
        return ""
