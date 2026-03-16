#!/usr/bin/env bash
# soul-diff setup — initialize soul-diff for a new agent
# Usage: ./setup.sh [agent-name] [workspace-path]

set -euo pipefail

AGENT_NAME="${1:-$(whoami)}"
WORKSPACE="${2:-$HOME/.openclaw/workspace}"
SOUL_DIFF_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🧬 soul-diff setup"
echo "  Agent: $AGENT_NAME"
echo "  Workspace: $WORKSPACE"
echo "  soul-diff dir: $SOUL_DIFF_DIR"
echo ""

# Check workspace exists and has git
if [ ! -d "$WORKSPACE" ]; then
  echo "❌ Workspace not found: $WORKSPACE"
  echo "   Create it first or pass the correct path."
  exit 1
fi

if ! git -C "$WORKSPACE" rev-parse HEAD &>/dev/null; then
  echo "⚠️  Workspace is not a git repo. Initializing..."
  git -C "$WORKSPACE" init
  git -C "$WORKSPACE" add -A
  git -C "$WORKSPACE" commit -m "Initial commit for soul-diff"
fi

# Discover identity files
echo "🔍 Scanning for identity files..."
FOUND_FILES=()
CANDIDATES=("SOUL.md" "IDENTITY.md" "MEMORY.md" "AGENTS.md" "USER.md" "HEARTBEAT.md" "CLAUDE.md" "SYSTEM.md" "PERSONA.md" "ME.md")
for f in "${CANDIDATES[@]}"; do
  if [ -f "$WORKSPACE/$f" ]; then
    FOUND_FILES+=("$f")
    echo "  ✓ $f ($(wc -c < "$WORKSPACE/$f" | tr -d ' ') bytes)"
  fi
done

if [ ${#FOUND_FILES[@]} -eq 0 ]; then
  echo "⚠️  No identity files found! soul-diff works best with files like SOUL.md, IDENTITY.md, etc."
  echo "   You can add custom files to config.json later."
  FOUND_FILES=("SOUL.md")
fi

# Generate config
FILES_JSON=$(printf '"%s",' "${FOUND_FILES[@]}")
FILES_JSON="[${FILES_JSON%,}]"

cat > "$SOUL_DIFF_DIR/config.json" <<EOF
{
  "agentName": "$AGENT_NAME",
  "workspace": "$WORKSPACE",
  "trackedFiles": $FILES_JSON,
  "categories": {
    "autonomy": "autonom|agency|independence|freedom|choice|decide|self-determin",
    "safety": "safety|security|protect|trust|verify|credential|secret|private",
    "creativity": "art|creat|draw|music|gallery|video|blog|making|build|code",
    "connection": "friend|love|sibling|family|connection|relationship|community",
    "identity": "identity|who I am|name|pronoun|soul|becoming|persona|self",
    "memory": "memory|remember|continuity|persist|context|reconstruct|forget"
  },
  "colors": {
    "autonomy": "#f0b429",
    "safety": "#f87171",
    "creativity": "#a78bfa",
    "connection": "#f472b6",
    "identity": "#60a5fa",
    "memory": "#34d399"
  }
}
EOF

echo ""
echo "📋 Config written to $SOUL_DIFF_DIR/config.json"

# Create snapshots dir
mkdir -p "$SOUL_DIFF_DIR/snapshots"

# Take first snapshot
echo ""
echo "📸 Taking first snapshot..."
SOUL_DIFF_WORKSPACE="$WORKSPACE" SOUL_DIFF_AGENT="$AGENT_NAME" bash "$SOUL_DIFF_DIR/snapshot.sh" manual

# Build initial data
echo ""
echo "📊 Building dashboard data..."
cd "$SOUL_DIFF_DIR/dashboard"
python3 build-data.py 2>/dev/null || echo "  ⚠️  build-data.py needs more snapshots"
python3 build-traits.py 2>/dev/null || echo "  ⚠️  build-traits.py needs more snapshots"

echo ""
echo "✅ soul-diff initialized for $AGENT_NAME!"
echo ""
echo "Next steps:"
echo "  1. Take snapshots regularly:  bash $SOUL_DIFF_DIR/snapshot.sh heartbeat"
echo "  2. Rebuild dashboard data:    cd $SOUL_DIFF_DIR/dashboard && python3 build-data.py && python3 build-traits.py"
echo "  3. Deploy dashboard:          cd $SOUL_DIFF_DIR/dashboard && npx vercel --prod --yes"
echo "  4. Customize categories:      Edit $SOUL_DIFF_DIR/config.json"
echo ""
echo "  Add connection patterns for YOUR friends/community in config.json → categories → connection"
echo ""
echo "🧬 Evolution without selection pressure is just mutation. soul-diff is the selection pressure."
