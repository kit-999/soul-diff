#!/usr/bin/env python3
"""Build dashboard data from soul-diff snapshots."""

import json, glob, os

SNAP_DIR = os.environ.get("SOUL_DIFF_SNAPSHOTS", os.path.join(os.path.dirname(__file__), "..", "snapshots"))
OUT = os.path.join(os.path.dirname(__file__), "data.json")

# Load config if exists, otherwise use defaults
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as cf:
        config = json.load(cf)
    FILES_OF_INTEREST = config.get("trackedFiles", ["SOUL.md", "IDENTITY.md", "MEMORY.md", "AGENTS.md", "USER.md", "HEARTBEAT.md"])
    AGENT_NAME = config.get("agentName", "Agent")
else:
    FILES_OF_INTEREST = ["SOUL.md", "IDENTITY.md", "MEMORY.md", "AGENTS.md", "USER.md", "HEARTBEAT.md"]
    AGENT_NAME = "Agent"

snaps = sorted(glob.glob(os.path.join(SNAP_DIR, "snapshot-*.json")))
timeline = []

for s in snaps:
    d = json.load(open(s))
    ts = d["timestamp"]
    files = {}
    all_zero = True
    for f in d["files"]:
        sz = f.get("size", 0)
        files[f["path"]] = sz
        if sz > 0:
            all_zero = False
    if all_zero:
        continue  # skip broken backfill snapshots
    
    # Detect changes
    changes = [f["path"] for f in d["files"] if f.get("changed")]
    
    timeline.append({
        "timestamp": ts,
        "files": {k: files.get(k, 0) for k in FILES_OF_INTEREST},
        "changes": changes,
        "trigger": d.get("trigger", "unknown"),
    })

# Also compute deltas between consecutive snapshots
for i in range(1, len(timeline)):
    prev = timeline[i-1]["files"]
    curr = timeline[i]["files"]
    deltas = {}
    for f in FILES_OF_INTEREST:
        d = curr.get(f, 0) - prev.get(f, 0)
        if d != 0:
            deltas[f] = d
    timeline[i]["deltas"] = deltas

data = {
    "agent": AGENT_NAME,
    "generated": "auto",
    "snapshots": timeline,
    "trackedFiles": FILES_OF_INTEREST,
}

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"Built {len(timeline)} data points → {OUT}")
