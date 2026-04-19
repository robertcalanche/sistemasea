import re
import os

filepath = 'modulo_superadmin.py'
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Finding all occurrences of self.notebook.add
    main_tabs = re.findall(r'self\.notebook\.add\(.*?text\s*=\s*(?:"|\')([^"\']+)(?:"|\')', content, re.DOTALL)
    
    # Finding other notebook additions
    other_tabs = re.findall(r'(\w+)\.add\(.*?text\s*=\s*(?:"|\')([^"\']+)(?:"|\')', content, re.DOTALL)
    
    print('MAIN_TABS:')
    for tab in main_tabs:
        print(f'- {tab}')

    print('\nOTHER_NOTEBOOKS:')
    for nb, tab in other_tabs:
        if nb != 'self.notebook' and tab not in main_tabs:
            print(f'- {nb}: {tab}')
else:
    print('File not found.')
