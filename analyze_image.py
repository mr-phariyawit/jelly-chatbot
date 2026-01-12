from PIL import Image
import sys

image_path = "/Users/mr.phariyawit/.gemini/antigravity/brain/2cc316a1-04c4-452b-a343-1f898a23d8e1/jvc_ai_logo_concept_thai_astro_1768122630249.png"
try:
    img = Image.open(image_path)
    print(f"Image Size: {img.size}")
    # Inspect corners to see where the favicon might be
    # Usually generated images are 1024x1024 or similar
except Exception as e:
    print(f"Error: {e}")
