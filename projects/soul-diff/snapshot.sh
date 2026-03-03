#!/usr/bin/env bash
# soul-diff snapshot — auto-commit identity files and generate a snapshot JSON
# Usage: ./snapshot.sh [trigger]
# trigger: auto|manual|heartbeat|session-start (default: manual)

set -euo pipefail

WORKSPACE="${SOUL_DIFF_WORKSPACE:-$HOME/.openclaw/workspace}"
SNAPSHOT_DIR="$WORKSPACE/projects/soul-diff/snapshots"
IDENTITY_FILES=("SOUL.md" "IDENTITY.md" "USER.md" "AGENTS.md" "MEMORY.md")
TRIGGER="${1:-manual}"
AGENT_ID="${SOUL_DIFF_AGENT:-kit}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE_SLUG=$(date -u +"%Y%m%d-%H%M%S")

mkdir -p "$SNAPSHOT_DIR"

cd "$WORKSPACE"

# Check if any identity files changed (git)
CHANGED=false
FILES_JSON="["
FIRST=true

for f in "${IDENTITY_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    continue
  fi

  HASH=$(shasum -a 256 "$f" | cut -d' ' -f1)
  SIZE=$(wc -c < "$f" | tr -d ' ')

  # Check if file has uncommitted changes or changed since last snapshot
  FILE_CHANGED=false
  if ! git diff --quiet -- "$f" 2>/dev/null; then
    FILE_CHANGED=true
    CHANGED=true
  fi

  # Build diff info if changed
  DIFF_JSON="null"
  if [ "$FILE_CHANGED" = true ]; then
    ADDED=$(git diff -- "$f" 2>/dev/null | grep -c '^+[^+]' || true)
    REMOVED=$(git diff -- "$f" 2>/dev/null | grep -c '^-[^-]' || true)
    DIFF_JSON="{\"linesAdded\":$ADDED,\"linesRemoved\":$REMOVED}"
  fi

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    FILES_JSON+=","
  fi

  FILES_JSON+="{\"path\":\"$f\",\"hash\":\"$HASH\",\"size\":$SIZE,\"changed\":$FILE_CHANGED"
  if [ "$FILE_CHANGED" = true ]; then
    FILES_JSON+=",\"diff\":$DIFF_JSON"
  fi
  FILES_JSON+="}"
done

FILES_JSON+="]"

# Get commit hash if in git
COMMIT_HASH=""
if git rev-parse HEAD &>/dev/null; then
  COMMIT_HASH=$(git rev-parse HEAD)
fi

# Generate snapshot JSON
SNAPSHOT_FILE="$SNAPSHOT_DIR/snapshot-$DATE_SLUG.json"
cat > "$SNAPSHOT_FILE" <<EOF
{
  "version": "1.0",
  "timestamp": "$TIMESTAMP",
  "agentId": "$AGENT_ID",
  "commitHash": "$COMMIT_HASH",
  "trigger": "$TRIGGER",
  "files": $FILES_JSON,
  "summary": null
}
EOF

echo "$SNAPSHOT_FILE"

# Auto-commit identity files if changed
if [ "$CHANGED" = true ]; then
  git add "${IDENTITY_FILES[@]}" 2>/dev/null || true
  git commit -m "soul-diff: auto-snapshot ($TRIGGER) $DATE_SLUG" --no-verify 2>/dev/null || true
fi
