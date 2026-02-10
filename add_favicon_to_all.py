"""Add favicon links to all HTML template files"""
import os
import re

# Favicon HTML to add
FAVICON_HTML = """    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
    <link rel="shortcut icon" type="image/x-icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
    <link rel="apple-touch-icon" href="{{ url_for('static', filename='images/logo.png') }}">
    """

templates_dir = 'templates'
files_updated = []
files_skipped = []

# Get all HTML files
for filename in os.listdir(templates_dir):
    if not filename.endswith('.html'):
        continue
    
    filepath = os.path.join(templates_dir, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has favicon
        if 'favicon.ico' in content:
            files_skipped.append(filename)
            continue
        
        # Skip if no <head> section
        if '<head>' not in content:
            files_skipped.append(filename)
            continue
        
        # Find the position after <title>...</title>
        title_match = re.search(r'<title>.*?</title>', content, re.DOTALL)
        
        if title_match:
            # Insert favicon after title
            insert_pos = title_match.end()
            new_content = content[:insert_pos] + '\n' + FAVICON_HTML + content[insert_pos:]
        else:
            # If no title, insert after <head>
            head_match = re.search(r'<head[^>]*>', content)
            if head_match:
                insert_pos = head_match.end()
                new_content = content[:insert_pos] + '\n' + FAVICON_HTML + content[insert_pos:]
            else:
                files_skipped.append(filename)
                continue
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        files_updated.append(filename)
        print(f"✓ Updated: {filename}")
    
    except Exception as e:
        print(f"✗ Error with {filename}: {e}")
        files_skipped.append(filename)

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  Updated: {len(files_updated)} files")
print(f"  Skipped: {len(files_skipped)} files")
print(f"{'='*60}")

if files_updated:
    print("\nUpdated files:")
    for f in files_updated:
        print(f"  - {f}")

if files_skipped:
    print("\nSkipped files (already have favicon or no <head>):")
    for f in files_skipped:
        print(f"  - {f}")
