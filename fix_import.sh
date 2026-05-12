#!/bin/bash
# Fix the webhook debug logging

FILE="/opt/pkb-system/backend/src/main.py"

# Add import sys if not present
if ! head -5 "$FILE" | grep -q "import sys"; then
    sed -i '1i import sys' "$FILE"
fi

# Fix the debug print line
sed -i 's/print(f"DEBUG: Received body: {body}", file=sys.stderr)/print("DEBUG:", str(body)[:300])/' "$FILE"

echo "Fixed"
systemctl restart pkb
sleep 3
echo "Done"
