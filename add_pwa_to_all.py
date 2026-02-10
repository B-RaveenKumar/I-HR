"""Add PWA manifest and meta tags to all HTML template files"""
import os
import re

# PWA meta tags and manifest to add
PWA_TAGS = """    <!-- PWA Meta Tags -->
    <meta name="theme-color" content="#0d6efd">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="VishnoRex">
    <link rel="manifest" href="{{ url_for('static', filename='manifest.json') }}">
    <link rel="apple-touch-icon" href="{{ url_for('static', filename='images/logo.png') }}">
    <link rel="apple-touch-startup-image" href="{{ url_for('static', filename='images/logo.png') }}">
    """

# Service Worker registration script
SW_SCRIPT = """
    <script>
        // Register Service Worker for PWA
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register("{{ url_for('static', filename='sw.js') }}")
                    .then(reg => console.log('Service Worker registered'))
                    .catch(err => console.log('Service Worker registration failed:', err));
            });
        }
    </script>"""

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
        
        # Skip if already has manifest
        if 'manifest.json' in content:
            files_skipped.append(filename)
            continue
        
        # Skip if no </head> tag
        if '</head>' not in content:
            files_skipped.append(filename)
            continue
        
        # Add PWA tags before </head>
        new_content = content.replace('</head>', f'{PWA_TAGS}\n</head>')
        
        # Add service worker script before </body> if body exists
        if '</body>' in new_content and 'serviceWorker' not in new_content:
            new_content = new_content.replace('</body>', f'{SW_SCRIPT}\n</body>')
        
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
    print("\nSkipped files (already have PWA or no </head>):")
    for f in files_skipped:
        print(f"  - {f}")

print("\n" + "="*60)
print("PWA Setup Complete!")
print("Your site can now be installed as an app with logo visible")
print("="*60)
