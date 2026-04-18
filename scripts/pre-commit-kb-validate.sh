#!/bin/bash
# Pre-commit hook: validate intelligence store integrity
# Runs only when intelligence JSON files are staged

cd "$(git rev-parse --show-toplevel)" || exit 1

STAGED=$(git diff --cached --name-only | grep -E "Nate's-kb/(Intelligence|Memory)/.*\.json$")

if [ -z "$STAGED" ]; then
    exit 0  # No intelligence files staged, skip
fi

PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    # Try the cross-platform wrapper as last resort
    if [ -x "scripts/run-python.sh" ]; then
        PYTHON="scripts/run-python.sh"
    else
        echo "PRE-COMMIT WARNING: No python found, skipping KB validation"
        exit 0
    fi
fi

# JSON syntax check on all staged KB JSON files
echo "$STAGED" | while IFS= read -r f; do
    if [ -f "$f" ]; then
        $PYTHON -c "
import json, sys
try:
    json.load(open(sys.argv[1], encoding='utf-8'))
except Exception as e:
    print(f'JSON ERROR in {sys.argv[1]}: {e}', file=sys.stderr)
    sys.exit(1)
" "$f"
        if [ $? -ne 0 ]; then
            echo "PRE-COMMIT BLOCKED: Invalid JSON in $f"
            exit 1
        fi
    fi
done || exit 1

# Schema validation (errors only, warnings pass)
ERRORS=$($PYTHON scripts/validate-schemas.py --quiet 2>&1 | grep "ERROR")
if [ -n "$ERRORS" ]; then
    echo "PRE-COMMIT BLOCKED: Schema errors found:"
    echo "$ERRORS"
    exit 1
fi

# Index-store alignment check
$PYTHON -c "
import json, sys
checks = [
    ('Nate\\'s-kb/Intelligence/patterns.json', 'Nate\\'s-kb/Intelligence/patterns-index.json'),
    ('Nate\\'s-kb/Intelligence/knowledge.json', 'Nate\\'s-kb/Intelligence/knowledge-index.json'),
    ('Nate\\'s-kb/Intelligence/reasoning.json', 'Nate\\'s-kb/Intelligence/reasoning-index.json'),
]
ok = True
for store_path, index_path in checks:
    try:
        store = json.load(open(store_path, encoding='utf-8'))
        index = json.load(open(index_path, encoding='utf-8'))
        actual = len(store.get('entries', []))
        claimed = index.get('stats', {}).get('totalEntries', -1)
        if actual != claimed:
            print(f'MISALIGNED: {store_path} has {actual} entries but index claims {claimed}')
            ok = False
    except Exception as e:
        print(f'CHECK FAILED: {e}')
        ok = False
sys.exit(0 if ok else 1)
"
if [ $? -ne 0 ]; then
    echo "PRE-COMMIT BLOCKED: Index-store alignment failure"
    exit 1
fi

exit 0
