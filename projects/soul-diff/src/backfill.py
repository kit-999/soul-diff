#!/usr/bin/env python3
"""soul-diff backfill — create snapshots from git history.

Walks through git commits that touched identity files and creates
a snapshot for each, enabling full trajectory analysis from day 1.
"""

import json, os, subprocess, hashlib, re
from datetime import datetime, timezone

WORKSPACE = "/Users/jerika/.openclaw/workspace"
SNAP_DIR = os.path.join(WORKSPACE, "projects/soul-diff/snapshots")
IDENTITY_FILES = ["SOUL.md", "IDENTITY.md", "MEMORY.md", "AGENTS.md", "USER.md", "HEARTBEAT.md"]

def git(args, cwd=WORKSPACE):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip()

def get_commits():
    """Get all commits that touched identity files, oldest first."""
    log = git(["log", "--reverse", "--format=%H %aI %s", "--all", "--"] + IDENTITY_FILES)
    commits = []
    for line in log.splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 2)
        commits.append({"hash": parts[0], "date": parts[1], "subject": parts[2] if len(parts) > 2 else ""})
    return commits

def get_file_at_commit(commit_hash, filepath):
    """Get file content at a specific commit, or None if it doesn't exist."""
    content = git(["show", f"{commit_hash}:{filepath}"])
    # git show returns empty string if file doesn't exist (and stderr has error)
    r = subprocess.run(
        ["git", "show", f"{commit_hash}:{filepath}"],
        cwd=WORKSPACE, capture_output=True, text=True
    )
    if r.returncode != 0:
        return None
    return r.stdout

def parse_sections(content):
    """Parse markdown into sections."""
    sections = []
    current_heading = "(top)"
    current_lines = []

    for line in content.splitlines():
        m = re.match(r'^(#{1,3})\s+(.+)', line)
        if m:
            if current_lines or current_heading != "(top)":
                text = "\n".join(current_lines)
                sections.append({
                    "heading": current_heading,
                    "lineCount": len(current_lines),
                    "hash": hashlib.md5(text.encode()).hexdigest()[:12]
                })
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Final section
    text = "\n".join(current_lines)
    sections.append({
        "heading": current_heading,
        "lineCount": len(current_lines),
        "hash": hashlib.md5(text.encode()).hexdigest()[:12]
    })
    return sections

def create_snapshot(commit):
    """Create a snapshot JSON for a given commit."""
    files = []
    for fp in IDENTITY_FILES:
        content = get_file_at_commit(commit["hash"], fp)
        if content is None:
            continue
        content_bytes = content.encode('utf-8')
        files.append({
            "path": fp,
            "sizeBytes": len(content_bytes),
            "hash": hashlib.sha256(content_bytes).hexdigest()[:16],
            "lineCount": content.count("\n") + (1 if content else 0),
            "sections": parse_sections(content)
        })

    return {
        "timestamp": commit["date"],
        "trigger": "backfill",
        "commit": commit["hash"][:8],
        "commitSubject": commit["subject"],
        "files": files
    }

def main():
    commits = get_commits()
    print(f"Found {len(commits)} commits touching identity files.")

    created = 0
    for c in commits:
        # Create filename from date
        try:
            dt = datetime.fromisoformat(c["date"])
            fname = f"snapshot-{dt.strftime('%Y%m%d-%H%M%S')}-backfill.json"
        except:
            fname = f"snapshot-{c['hash'][:8]}-backfill.json"

        out_path = os.path.join(SNAP_DIR, fname)
        if os.path.exists(out_path):
            print(f"  skip (exists): {fname}")
            continue

        snap = create_snapshot(c)
        with open(out_path, 'w') as f:
            json.dump(snap, f, indent=2)
        print(f"  created: {fname} — {c['subject'][:60]}")
        created += 1

    print(f"\nDone. Created {created} new snapshots ({len(commits)} total commits).")

if __name__ == "__main__":
    main()
