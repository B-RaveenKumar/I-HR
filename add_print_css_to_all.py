"""Add print stylesheet to all HTML template files for logo visibility in downloads"""
import os
import re

# Print CSS link to add
PRINT_CSS = '    <link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/print.css\') }}" media="print">'

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
        
        # Skip if already has print.css
        if 'print.css' in content:
            files_skipped.append(filename)
            continue
        
        # Skip if no </head> tag
        if '</head>' not in content:
            files_skipped.append(filename)
            continue
        
        # Add print CSS before </head>
        new_content = content.replace('</head>', f'{PRINT_CSS}\n</head>')
        
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
    print("\nSkipped files (already have print.css or no </head>):")
    for f in files_skipped:
        print(f"  - {f}")
