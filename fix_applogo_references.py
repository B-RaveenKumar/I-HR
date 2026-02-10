"""Update all apple-touch-icon references from logo.png to applogo.png"""
import os
import re

templates_dir = 'templates'
files_updated = []

# Get all HTML files
for filename in os.listdir(templates_dir):
    if not filename.endswith('.html'):
        continue
    
    filepath = os.path.join(templates_dir, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace all apple-touch-icon references
        content = content.replace(
            "url_for('static', filename='images/logo.png')",
            "url_for('static', filename='images/applogo.png')"
        )
        
        # Also replace apple-touch-startup-image if present
        content = content.replace(
            'apple-touch-startup-image" href="{{ url_for(\'static\', filename=\'images/logo.png\'',
            'apple-touch-startup-image" href="{{ url_for(\'static\', filename=\'images/applogo.png\''
        )
        
        # Check if any changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            files_updated.append(filename)
            print(f"✓ Updated: {filename}")
    
    except Exception as e:
        print(f"✗ Error with {filename}: {e}")

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  Updated: {len(files_updated)} files")
print(f"{'='*60}")

if files_updated:
    print("\nUpdated files (logo.png → applogo.png):")
    for f in files_updated:
        print(f"  - {f}")

print("\n" + "="*60)
print("App logo fixed! Your installed app will now show applogo.png")
print("="*60)
