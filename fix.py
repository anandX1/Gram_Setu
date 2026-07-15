import glob, re

for f in glob.glob('*.html') + glob.glob('pages/*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if we have an unclosed div issue.
    # The div we need to close is `<div style="display:flex; align-items:center;">`
    # We inserted it right before `<button class="mobile-menu-btn"`.
    # And we ended the insertion after `<div class="topbar-title">` but we never closed the flex div.
    # We should add `</div>` right after `</div>` of `topbar-title`.
    
    if '<button class="mobile-menu-btn"' in content:
        # Check if it already has the double </div> by looking at the occurrences.
        # But wait, earlier I might have already broken it or not.
        # Let's just find `<div class="topbar-title">...</div>` and if it's followed by `</div>`, we are good.
        # If it's followed by `<div class="lang-btn">` or `<div class="lang-switcher">` we need to insert `</div>` in between.
        
        content = re.sub(r'(<div class="topbar-title">.*?</div>)\s*(<div class="lang-(?:btn|switcher)")', r'\1\n    </div>\n    \2', content, flags=re.DOTALL)
        
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print('Done!')
