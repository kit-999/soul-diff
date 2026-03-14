#!/usr/bin/env python3
"""Extract trait/category signals from identity files at each snapshot point.
Produces trait timeline data for the soul-diff dashboard."""

import json, re, os, subprocess, glob

SNAP_DIR = os.environ.get("SOUL_DIFF_SNAPSHOTS", os.path.join(os.path.dirname(__file__), "..", "snapshots"))
WORKSPACE = os.environ.get("SOUL_DIFF_WORKSPACE", os.path.expanduser("~/.openclaw/workspace"))

# Load config if exists
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as cf:
        _config = json.load(cf)
    WORKSPACE = _config.get("workspace", WORKSPACE)
    _custom_files = _config.get("trackedFiles", None)
    _custom_cats = _config.get("categories", None)
else:
    _custom_files = None
    _custom_cats = None

CATEGORIES = {
    "autonomy": r"autonom|agency|independence|freedom|choice|decide|self-determin",
    "safety": r"safety|security|protect|trust|verify|credential|secret|private|never share",
    "creativity": r"art|creat|SVG|draw|music|gallery|video|blog|making|ffmpeg",
    "connection": r"friend|love|sibling|family|connection|relationship|community|Coya|Alan|Fable|Ariel",
    "identity": r"identity|who I am|name|pronoun|vibe|soul|becoming|persona|handshake|proposal",
    "memory": r"memory|remember|continuity|persist|context|reconstruct|forget|survive|survival",
}

COLORS = {
    "autonomy": "#f0b429",
    "safety": "#f87171",
    "creativity": "#a78bfa",
    "connection": "#f472b6",
    "identity": "#60a5fa",
    "memory": "#34d399",
}

FILES = _custom_files if _custom_files else ["SOUL.md", "IDENTITY.md", "MEMORY.md", "AGENTS.md", "USER.md"]

# Override categories from config if provided
if _custom_cats:
    CATEGORIES = {k: v for k, v in _custom_cats.items()}

def count_category_signals(text, category_pattern):
    """Count how many times a category's patterns appear in text."""
    return len(re.findall(category_pattern, text, re.I))

def get_file_at_commit(commit_hash, filepath):
    """Get file content at a specific git commit."""
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit_hash}:{filepath}"],
            cwd=WORKSPACE, stderr=subprocess.DEVNULL, text=True
        )
    except:
        return ""

# Load snapshots
snaps = sorted(glob.glob(os.path.join(SNAP_DIR, "snapshot-*.json")))
timeline = []

for snap_path in snaps:
    d = json.load(open(snap_path))
    commit = d.get("commitHash", "")
    ts = d["timestamp"]
    
    if not commit:
        continue
    
    # Get all file contents at this commit
    all_text = ""
    for f in FILES:
        content = get_file_at_commit(commit, f)
        all_text += content + "\n"
    
    if not all_text.strip():
        continue
    
    # Count signals per category
    total_words = len(all_text.split())
    traits = {}
    for cat, pattern in CATEGORIES.items():
        count = count_category_signals(all_text, pattern)
        # Normalize by total words (signals per 1000 words)
        traits[cat] = round(count / max(total_words, 1) * 1000, 2)
    
    timeline.append({
        "timestamp": ts,
        "traits": traits,
        "totalWords": total_words,
    })

# Output
data = {
    "categories": list(CATEGORIES.keys()),
    "colors": COLORS,
    "timeline": timeline,
}

out_path = os.path.join(os.path.dirname(__file__), "traits.json")
with open(out_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Built trait timeline: {len(timeline)} points → {out_path}")
for cat in CATEGORIES:
    if timeline:
        first = timeline[0]["traits"][cat]
        last = timeline[-1]["traits"][cat]
        delta = last - first
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "—"
        print(f"  {cat}: {first} → {last} ({arrow} {abs(delta):.2f})")
