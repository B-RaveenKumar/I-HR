"""Create proper PWA icon files from applogo.png"""
from PIL import Image
import os

# Icon sizes needed for PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Source image
source_path = 'static/images/applogo.png'
output_dir = 'static/images'

try:
    # Open source image
    img = Image.open(source_path)
    print(f"Source image: {source_path}")
    print(f"Original size: {img.size}")
    print(f"Format: {img.format}")
    
    # Convert RGBA to RGB if needed (for better compatibility)
    if img.mode == 'RGBA':
        # Create white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
        img_rgb = background
    else:
        img_rgb = img.convert('RGB')
    
    # Create icons for each size
    for size in ICON_SIZES:
        # Resize image
        resized = img_rgb.resize((size, size), Image.Resampling.LANCZOS)
        
        # Save as PNG
        output_path = os.path.join(output_dir, f'icon-{size}x{size}.png')
        resized.save(output_path, 'PNG', optimize=True, quality=95)
        print(f"✓ Created: icon-{size}x{size}.png")
    
    # Also create a high-quality 512x512 maskable icon with padding
    maskable_size = 512
    # Add 20% padding for maskable icon (safe zone)
    padding = int(maskable_size * 0.1)
    canvas_size = maskable_size
    icon_size = maskable_size - (padding * 2)
    
    # Create white canvas
    canvas = Image.new('RGB', (canvas_size, canvas_size), (255, 255, 255))
    
    # Resize and paste logo in center
    logo_resized = img_rgb.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    canvas.paste(logo_resized, (padding, padding))
    
    maskable_path = os.path.join(output_dir, 'icon-512x512-maskable.png')
    canvas.save(maskable_path, 'PNG', optimize=True, quality=95)
    print(f"✓ Created: icon-512x512-maskable.png (with safe zone)")
    
    print("\n" + "="*60)
    print("PWA icons created successfully!")
    print("="*60)
    
except FileNotFoundError:
    print(f"Error: {source_path} not found!")
    print("Please ensure applogo.png exists in static/images/")
except Exception as e:
    print(f"Error: {e}")
