import os, glob

for f in glob.glob('*.html') + glob.glob('pages/*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if viewport meta is present, if not add it
    if '<meta name="viewport"' not in content:
        content = content.replace('<head>', '<head>\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    # Add mobile-menu-btn
    if 'mobile-menu-btn' not in content:
        replacement = '''<div class="topbar">
    <div style="display:flex; align-items:center;">
      <button class="mobile-menu-btn" onclick="toggleMobileMenu()">
        <svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
      <div class="topbar-title">'''
        content = content.replace('<div class="topbar">\n    <div class="topbar-title">', replacement)
        content = content.replace('<div class="topbar">\n  <div class="topbar-title">', replacement)
        
        # Also need to close the div we opened! The original was:
        # <div class="topbar-title"><h1>...</h1><p>...</p></div>
        # Now it is <div style="...">...<div class="topbar-title">...</div>
        # We must add </div> after the topbar-title div.
        # Actually it's easier to just use regex:
        import re
        content = re.sub(r'(<div class="topbar">\s*<div class="topbar-title">.*?</div>)', 
                         r'<div style="display:flex; align-items:center;">\n      <button class="mobile-menu-btn" onclick="toggleMobileMenu()">\n        <svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>\n      </button>\n      \1\n    </div>', 
                         content, flags=re.DOTALL)

    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print('Done!')
