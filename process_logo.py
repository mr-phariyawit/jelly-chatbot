from PIL import Image
import os

source_path = "/Users/mr.phariyawit/.gemini/antigravity/brain/2cc316a1-04c4-452b-a343-1f898a23d8e1/jvc_ai_logo_concept_thai_astro_1768122630249.png"
dest_dir = "/Users/mr.phariyawit/Documents/ai-support/admin-dashboard/public"

try:
    img = Image.open(source_path)
    
    # 1. Main Logo (Top part mostly)
    # Crop top 700px to capture Symbol + Text
    logo_crop = img.crop((0, 0, 1024, 720))
    logo_path = os.path.join(dest_dir, "logo.png")
    logo_crop.save(logo_path)
    print(f"Saved Logo to {logo_path}")

    # 2. Favicon (Bottom Right corner)
    # The generator usually puts the favicon variation in the bottom right quadrant
    # roughly 720, 720 to 1024, 1024
    favicon_crop = img.crop((730, 730, 1010, 1010)) 
    
    # Resize for standard favicon
    favicon_ico = favicon_crop.resize((32, 32), Image.Resampling.LANCZOS)
    favicon_ico_path = os.path.join(dest_dir, "favicon.ico")
    favicon_ico.save(favicon_ico_path)
    print(f"Saved Favicon to {favicon_ico_path}")

    # Resize for Apple Icon / Modern
    favicon_png = favicon_crop.resize((192, 192), Image.Resampling.LANCZOS)
    icon_path = os.path.join(dest_dir, "text-icon.png") # Dashboard seems to use file.svg, let's add png
    favicon_png.save(icon_path)
    print(f"Saved Icon to {icon_path}")
    
    # Also save as apple-touch-icon
    apple_icon_path = os.path.join(dest_dir, "apple-touch-icon.png")
    favicon_png.resize((180, 180)).save(apple_icon_path)
    print(f"Saved Apple Icon to {apple_icon_path}")

except Exception as e:
    print(f"Error processing image: {e}")
