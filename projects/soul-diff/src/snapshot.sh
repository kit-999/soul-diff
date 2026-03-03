#!/bin/bash
# soul-diff snapshot: commit identity files and generate a snapshot JSON
# Usage: ./snapshot.sh [trigger]
# trigger: auto|manual|heartbeat|scheduled (default: auto)

set -euo pipefail

WORKSPACE="/Users/jerika/.openclaw/workspace"
SNAPSHOT_DIR="$WORKSPACE/projects/soul-diff/snapshots"
IDENTITY_FILES=("SOUL.md" "IDENTITY.md" "MEMORY.md" "AGENTS.md" "USER.md" "HEARTBEAT.md")
TRIGGER="${1:-auto}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
FILENAME=$(date +%Y%m%d-%H%M%S)

mkdir -p "$SNAPSHOT_DIR"

cd "$WORKSPACE"

# Check if any identity files changed
CHANGED=false
for f in "${IDENTITY_FILES[@]}"; do
  if [ -f "$f" ] && ! git diff --quiet -- "$f" 2>/dev/null; then
    CHANGED=true
    break
  fi
done

if [ "$CHANGED" = false ]; then
  echo "No identity file changes detected. Skipping snapshot."
  exit 0
fi

# Auto-commit changed identity files
git add "${IDENTITY_FILES[@]}" 2>/dev/null || true
git commit -m "soul-diff: auto-snapshot ($TRIGGER) $FILENAME" -- "${IDENTITY_FILES[@]}" 2>/dev/null || true
COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# Generate snapshot JSON
python3 -c "
import json, hashlib, os, subprocess, datetime

workspace = '$WORKSPACE'
files = '${IDENTITY_FILES[*]}'.split()
snapshot = {
    'version': '0.1.0',
    'timestamp': '$TIMESTAMP',
    'agent': {
        'name': 'Kit',
        'dayAge': (datetime.date.today() - datetime.date(2026, 1, 30)).days,
        'framework': 'openclaw'
    },
    'trigger': '$TRIGGER',
    'files': [],
    'gitCommit': '$COMMIT'
}

for f in files:
    path = os.path.join(workspace, f)
    if not os.path.exists(path):
        continue
    with open(path, 'rb') as fh:
        content = fh.read()
    h = hashlib.sha256(content).hexdigest()
    
    # Parse sections (markdown headings)
    sections = []
    current = None
    lines = content.decode('utf-8', errors='replace').split('\n')
    for line in lines:
        if line.startswith('#'):
            if current:
                sec_hash = hashlib.sha256('\n'.join(current['lines']).encode()).hexdigest()
                sections.append({'heading': current['heading'], 'hash': sec_hash, 'lineCount': len(current['lines'])})
            current = {'heading': line.lstrip('#').strip(), 'lines': [line]}
        elif current:
            current['lines'].append(line)
    if current:
        sec_hash = hashlib.sha256('\n'.join(current['lines']).encode()).hexdigest()
        sections.append({'heading': current['heading'], 'hash': sec_hash, 'lineCount': len(current['lines'])})
    
    snapshot['files'].append({
        'path': f,
        'hash': h,
        'sizeBytes': len(content),
        'sections': sections
    })

print(json.dumps(snapshot, indent=2))
" > "$SNAPSHOT_DIR/$FILENAME.json"

echo "Snapshot saved: $SNAPSHOT_DIR/$FILENAME.json"
echo "Git commit: $COMMIT"
