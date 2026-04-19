import re
import os

filepath = 'modulo_superadmin.py'
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find tab names added to a ttk.Notebook
    # Use re.DOTALL to handle multiline .add calls
    tabs = re.findall(r'\.add\(.*?text\s*=\s*(?:"|\')([^"\']+)(?:"|\')', content, re.DOTALL)
    
    # Filter out empty or common non-tab names
    tabs = sorted(list(set(tabs)))
    
    print('ALL_TABS_FOUND:')
    for tab in tabs:
        print(tab)
else:
    print('File not found.')
