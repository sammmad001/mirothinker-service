#!/usr/bin/env python3
"""Fix bashrc and verify deployment"""
import os

# Fix .bashrc - remove any output redirection
bashrc_path = '/root/.bashrc'
if os.path.exists(bashrc_path):
    with open(bashrc_path, 'r') as f:
        content = f.read()
    
    # Remove any exec or output redirection
    if 'exec >' in content or 'exec 1>' in content or '/dev/null' in content:
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            if 'exec >' not in line and 'exec 1>' not in line:
                clean_lines.append(line)
        
        with open(bashrc_path, 'w') as f:
            f.write('\n'.join(clean_lines))
        print("Fixed .bashrc")
    else:
        print(".bashrc is clean")
else:
    print(".bashrc not found")

# Verify deployment by checking file content
main_py = '/opt/pkb-system/backend/src/main.py'
if os.path.exists(main_py):
    with open(main_py, 'r') as f:
        content = f.read()
    
    if 'header: Optional[dict]' in content:
        print("main.py has header field - CORRECT")
    else:
        print("main.py missing header field - NEEDS FIX")
    
    if 'header.get("event_id"' in content:
        print("main.py has correct event_id extraction - CORRECT")
    else:
        print("main.py has wrong event_id extraction - NEEDS FIX")
else:
    print("main.py not found!")

feishu_py = '/opt/pkb-system/backend/src/input/adapters/feishu.py'
if os.path.exists(feishu_py):
    with open(feishu_py, 'r') as f:
        content = f.read()
    
    if 'message = event.get("message"' in content:
        print("feishu.py has correct parse_message - CORRECT")
    else:
        print("feishu.py has wrong parse_message - NEEDS FIX")
else:
    print("feishu.py not found!")
