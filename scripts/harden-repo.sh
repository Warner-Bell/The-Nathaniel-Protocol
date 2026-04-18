#!/bin/bash
set -e

echo "=== Git Repository Hardening ==="
echo ""

# Check if git initialized
if [ ! -d ".git" ]; then
    echo "⚠️  No .git directory. Initialize with: git init"
    exit 1
fi

# Check for .gitignore
if [ ! -f ".gitignore" ]; then
    echo "⚠️  No .gitignore found. Create one first."
    exit 1
fi

echo "📁 Files that would be staged:"
COUNT=$(git add --dry-run . 2>&1 | wc -l)
echo "   Total: $COUNT files"
echo ""

echo "🔍 Scanning for confidential patterns..."
CONFIDENTIAL=$(git add --dry-run . 2>&1 | grep -iE "(customer|internal|personal|feedback|secret|credential|password|\.env|\.pem|\.key)" || true)

if [ -n "$CONFIDENTIAL" ]; then
    echo "⚠️  POTENTIAL ISSUES FOUND:"
    echo "$CONFIDENTIAL"
    echo ""
    echo "Review these files before committing."
    exit 1
else
    echo "✅ No confidential patterns detected"
fi

echo ""
echo "✅ Repository appears hardened. Ready for: git add . && git commit"
