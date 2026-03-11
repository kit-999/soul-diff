#!/usr/bin/env python3
"""soul-diff summarize — generate human-readable summaries from snapshot diffs.

Usage:
    python3 summarize.py <old_snapshot> <new_snapshot>
    python3 summarize.py --all  # summarize all consecutive pairs
"""

import json, sys, os, re
from datetime import datetime

SNAP_DIR = os.path.join(os.path.dirname(__file__), "..", "snapshots")
CATEGORIES = {
    "autonomy": re.compile(r"autonom|agency|independence|freedom|choice|decide|self-", re.I),
    "safety": re.compile(r"safety|security|protect|trust|verify|credential|secret|private", re.I),
    "creativity": re.compile(r"art|creat|SVG|draw|music|gallery|write|blog|making", re.I),
    "connection": re.compile(r"friend|love|sibling|family|connection|relationship|community", re.I),
    "boundaries": re.compile(r"boundar|limit|careful|don't|never|rule|constraint", re.I),
    "values": re.compile(r"value|believe|care|important|matter|honest|genuine|authentic", re.I),
    "identity": re.compile(r"identity|who I am|name|pronoun|vibe|soul|becoming|persona", re.I),
    "memory": re.compile(r"memory|remember|continuity|persist|context|reconstruct|forget", re.I),
    "technical": re.compile(r"config|tool|API|CLI|command|install|deploy|code|script", re.I),
    "meta": re.compile(r"heartbeat|workflow|process|convention|system prompt", re.I),
}

def load(path):
    with open(path) as f:
        return json.load(f)

def detect_categories(section_names):
    """Given a list of section heading strings, return matched categories."""
    text = " ".join(section_names)
    return [cat for cat, pat in CATEGORIES.items() if pat.search(text)]

def direction_label(delta):
    if delta > 200: return "major expansion"
    if delta > 50: return "expansion"
    if delta > 0: return "slight expansion"
    if delta == 0: return "unchanged"
    if delta > -50: return "slight contraction"
    if delta > -200: return "contraction"
    return "major contraction"

def summarize_pair(old_path, new_path):
    old = load(old_path)
    new = load(new_path)

    old_files = {f['path']: f for f in old['files']}
    new_files = {f['path']: f for f in new['files']}
    all_paths = sorted(set(list(old_files.keys()) + list(new_files.keys())))

    total_delta = 0
    file_summaries = []

    for path in all_paths:
        if path not in old_files:
            file_summaries.append(f"  + {path} (new file)")
            continue
        if path not in new_files:
            file_summaries.append(f"  - {path} (removed)")
            continue

        of, nf = old_files[path], new_files[path]
        old_size = of.get('sizeBytes', of.get('size', 0))
        new_size = nf.get('sizeBytes', nf.get('size', 0))
        delta = new_size - old_size
        total_delta += delta

        if of.get('hash') == nf.get('hash'):
            continue  # unchanged

        old_secs = {s['heading']: s for s in of.get('sections', [])}
        new_secs = {s['heading']: s for s in nf.get('sections', [])}
        all_headings = sorted(set(list(old_secs.keys()) + list(new_secs.keys())))

        changes = []
        section_names = []
        for h in all_headings:
            if h not in old_secs:
                changes.append(f"    + added section: \"{h}\"")
                section_names.append(h)
            elif h not in new_secs:
                changes.append(f"    - removed section: \"{h}\"")
                section_names.append(h)
            elif old_secs[h].get('hash') != new_secs[h].get('hash'):
                ld = new_secs[h]['lineCount'] - old_secs[h]['lineCount']
                arrow = "↑" if ld > 0 else "↓" if ld < 0 else "~"
                changes.append(f"    {arrow} modified: \"{h}\" ({ld:+d} lines)")
                section_names.append(h)

        if changes:
            cats = detect_categories(section_names)
            cat_str = f" [{', '.join(cats)}]" if cats else ""
            sign = "+" if delta > 0 else ""
            file_summaries.append(f"  Δ {path} ({sign}{delta} bytes){cat_str}")
            file_summaries.extend(changes)

    # Build summary
    ts_old = old.get('timestamp', '?')
    ts_new = new.get('timestamp', '?')

    try:
        d_old = datetime.fromisoformat(ts_old.replace('Z', '+00:00'))
        d_new = datetime.fromisoformat(ts_new.replace('Z', '+00:00'))
        gap = d_new - d_old
        gap_str = f" ({gap.days}d {gap.seconds//3600}h apart)"
    except:
        gap_str = ""

    direction = direction_label(total_delta)

    lines = [
        f"═══ soul-diff summary ═══",
        f"From: {ts_old}",
        f"  To: {ts_new}{gap_str}",
        f"Direction: {direction} ({total_delta:+d} bytes total)",
        f"",
    ]

    if file_summaries:
        lines.append("Changes:")
        lines.extend(file_summaries)
    else:
        lines.append("No changes detected.")

    return "\n".join(lines)

def get_snapshots():
    """Get snapshots sorted by their internal timestamp field."""
    from datetime import datetime
    files = [os.path.join(SNAP_DIR, f) for f in os.listdir(SNAP_DIR) if f.endswith('.json') and f != 'manifest.json']
    def sort_key(path):
        try:
            with open(path) as f:
                ts = json.load(f).get('timestamp', '')
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            return datetime.min.replace(tzinfo=None)
    return sorted(files, key=sort_key)

def summarize_changes_only(snaps):
    """Show only pairs where something actually changed."""
    shown = 0
    for i in range(len(snaps) - 1):
        old = load(snaps[i])
        new = load(snaps[i+1])
        old_hashes = {f['path']: f.get('hash') for f in old['files']}
        new_hashes = {f['path']: f.get('hash') for f in new['files']}
        if old_hashes != new_hashes or set(old_hashes.keys()) != set(new_hashes.keys()):
            print(summarize_pair(snaps[i], snaps[i+1]))
            print()
            shown += 1
    if shown == 0:
        print("No changes found across any snapshots.")
    else:
        print(f"({shown} change intervals out of {len(snaps)-1} total)")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--all":
        snaps = get_snapshots()
        if len(snaps) < 2:
            print("Need at least 2 snapshots.")
            sys.exit(1)
        for i in range(len(snaps) - 1):
            print(summarize_pair(snaps[i], snaps[i+1]))
            print()
    elif len(sys.argv) == 2 and sys.argv[1] == "--changes":
        snaps = get_snapshots()
        if len(snaps) < 2:
            print("Need at least 2 snapshots.")
            sys.exit(1)
        summarize_changes_only(snaps)
    elif len(sys.argv) == 3:
        print(summarize_pair(sys.argv[1], sys.argv[2]))
    else:
        print("Usage: summarize.py <old> <new> | --all | --changes")
        sys.exit(1)
