"""
Institution Branding - Sample Logo Setup Script
Creates placeholder logos for testing dynamic branding feature
"""
import sqlite3
from PIL import Image, ImageDraw, ImageFont
import os

DB_PATH = 'vishnorex.db'
LOGO_DIR = 'static/uploads/logos'

def create_sample_logo(text, filename, bg_color, text_color):
    """Create a simple logo with institution initials"""
    # Create logo directory if it doesn't exist
    os.makedirs(LOGO_DIR, exist_ok=True)
    
    # Create image
    width, height = 200, 60
    image = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)
    
    # Try to use a nice font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position (center)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((width - text_width) / 2, (height - text_height) / 2)
    
    # Draw text
    draw.text(position, text, fill=text_color, font=font)
    
    # Save image
    filepath = os.path.join(LOGO_DIR, filename)
    image.save(filepath)
    print(f"✅ Created logo: {filepath}")
    return filepath

def update_school_logos():
    """Update schools in database with sample logos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all schools
        cursor.execute("SELECT id, name FROM schools")
        schools = cursor.fetchall()
        
        if not schools:
            print("⚠️  No schools found in database")
            return
        
        print(f"\n📋 Found {len(schools)} schools:")
        
        for school_id, school_name in schools:
            # Generate initials (first letter of each word)
            initials = ''.join([word[0].upper() for word in school_name.split()[:3]])
            
            # Create logo with different colors for each school
            colors = [
                ('#2E86AB', '#FFFFFF'),  # Blue
                ('#A23B72', '#FFFFFF'),  # Purple
                ('#F18F01', '#FFFFFF'),  # Orange
                ('#06A77D', '#FFFFFF'),  # Green
                ('#D62246', '#FFFFFF'),  # Red
            ]
            bg_color, text_color = colors[school_id % len(colors)]
            
            filename = f"{school_name.lower().replace(' ', '_')}_logo.png"
            logo_path = create_sample_logo(initials, filename, bg_color, text_color)
            
            # Update database
            relative_path = logo_path.replace('\\', '/')
            cursor.execute('''
                UPDATE schools 
                SET logo_path = ?, branding_enabled = 1 
                WHERE id = ?
            ''', (relative_path, school_id))
            
            print(f"   {school_name} (ID: {school_id}) → {relative_path}")
        
        conn.commit()
        print("\n✅ All schools updated with sample logos!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def create_default_logo():
    """Create a default VishnoRex logo"""
    os.makedirs('static/images', exist_ok=True)
    create_sample_logo('VR', 'default_logo.png', '#212529', '#FFFFFF')
    print("✅ Created default system logo")

if __name__ == '__main__':
    print("="*60)
    print("INSTITUTION BRANDING - SAMPLE LOGO SETUP")
    print("="*60)
    print()
    
    # Install Pillow if needed
    try:
        from PIL import Image
    except ImportError:
        print("⚠️  Pillow not installed. Installing...")
        os.system('pip install Pillow')
        print()
    
    # Create default logo
    create_default_logo()
    print()
    
    # Create sample logos for all schools
    update_school_logos()
    
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("   1. Restart Flask application")
    print("   2. Log in to test dynamic branding")
    print("   3. Upload real logos via school management interface")
    print("   4. Replace sample logos with actual institution logos")
    print()
