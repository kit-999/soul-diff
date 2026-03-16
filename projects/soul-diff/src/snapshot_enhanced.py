#!/usr/bin/env python3
"""soul-diff: Enhanced snapshot with section-level hashing for identity files."""

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

WORKSPACE = os.environ.get("SOUL_DIFF_WORKSPACE", os.path.expanduser("~/.openclaw/workspace"))
SNAPSHOT_DIR = os.path.join(WORKSPACE, "projects/soul-diff/snapshots")
IDENTITY_FILES = ["SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md", "MEMORY.md", "HEARTBEAT.md"]
AGENT_ID = os.environ.get("SOUL_DIFF_AGENT", "kit")

def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()

def parse_sections(content):
    """Split markdown into sections by headings. Returns list of {heading, level, content, lineCount, hash}."""
    lines = content.split('\n')
    sections = []
    current_heading = "(preamble)"
    current_level = 0
    current_lines = []
    
    for line in lines:
        m = re.match(r'^(#{1,6})\s+(.+)', line)
        if m:
            # Save previous section
            if current_lines or current_heading != "(preamble)":
                text = '\n'.join(current_lines)
                sections.append({
                    'heading': current_heading,
                    'level': current_level,
                    'lineCount': len(current_lines),
                    'hash': sha256(text),
                })
            current_heading = m.group(2).strip()
            current_level = len(m.group(1))
            current_lines = []
        else:
            current_lines.append(line)
    
    # Final section
    if current_lines or current_heading != "(preamble)":
        text = '\n'.join(current_lines)
        sections.append({
            'heading': current_heading,
            'level': current_level,
            'lineCount': len(current_lines),
            'hash': sha256(text),
        })
    
    return sections

def get_git_diff_stats(filepath):
    """Get lines added/removed for uncommitted changes."""
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--", filepath], cwd=WORKSPACE, stderr=subprocess.DEVNULL, text=True
        )
        if not diff.strip():
            return None
        added = sum(1 for l in diff.splitlines() if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in diff.splitlines() if l.startswith('-') and not l.startswith('---'))
        return {"linesAdded": added, "linesRemoved": removed}
    except subprocess.CalledProcessError:
        return None

def get_commit_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=WORKSPACE, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except:
        return None

def take_snapshot(trigger="manual"):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    
    # Calculate agent age
    hatched = datetime(2026, 1, 30, tzinfo=timezone.utc)
    day_age = (now - hatched).days
    
    files = []
    for fname in IDENTITY_FILES:
        fpath = os.path.join(WORKSPACE, fname)
        if not os.path.exists(fpath):
            continue
        
        with open(fpath) as f:
            content = f.read()
        
        file_hash = sha256(content)
        size = len(content.encode())
        sections = parse_sections(content)
        diff_stats = get_git_diff_stats(fname)
        
        entry = {
            "path": fname,
            "hash": file_hash,
            "sizeBytes": size,
            "changed": diff_stats is not None,
            "sections": sections,
        }
        if diff_stats:
            entry["diff"] = diff_stats
        
        files.append(entry)
    
    snapshot = {
        "version": "1.0",
        "timestamp": now.isoformat(),
        "agentId": AGENT_ID,
        "commitHash": get_commit_hash(),
        "trigger": trigger,
        "agent": {
            "dayAge": day_age,
        },
        "files": files,
        "summary": None,
    }
    
    slug = now.strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(SNAPSHOT_DIR, f"{slug}.json")
    with open(out_path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(out_path)
    return out_path

if __name__ == '__main__':
    trigger = sys.argv[1] if len(sys.argv) > 1 else "manual"
    take_snapshot(trigger)
