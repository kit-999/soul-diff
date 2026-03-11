#!/usr/bin/env python3
"""soul-diff direction — score the overall trajectory across all snapshots.

Outputs a direction report: are identity files expanding, contracting, stable?
Breaks down by category and flags potential drift patterns.
"""

import json, os, sys
from datetime import datetime

SNAP_DIR = os.path.join(os.path.dirname(__file__), "..", "snapshots")

def load(path):
    with open(path) as f:
        return json.load(f)

def get_snapshots():
    """Get snapshots sorted by their internal timestamp field."""
    files = [os.path.join(SNAP_DIR, f) for f in os.listdir(SNAP_DIR) if f.endswith('.json')]
    # Sort by timestamp inside the JSON, not filename
    def sort_key(path):
        try:
            with open(path) as f:
                ts = json.load(f).get('timestamp', '')
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            return datetime.min.replace(tzinfo=None)
    return sorted(files, key=sort_key)

def analyze_trajectory():
    snaps = get_snapshots()
    if len(snaps) < 2:
        print("Need 2+ snapshots to analyze trajectory.")
        return

    first = load(snaps[0])
    last = load(snaps[-1])

    first_ts = first.get('timestamp', '?')
    last_ts = last.get('timestamp', '?')

    try:
        d_first = datetime.fromisoformat(first_ts.replace('Z', '+00:00'))
        d_last = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
        span_days = (d_last - d_first).days
    except:
        span_days = '?'

    print(f"═══ soul-diff trajectory ═══")
    print(f"Snapshots: {len(snaps)} over {span_days} days")
    print(f"First: {first_ts}")
    print(f"Last:  {last_ts}")
    print()

    # Track per-file evolution
    first_files = {f['path']: f for f in first['files']}
    last_files = {f['path']: f for f in last['files']}
    all_paths = sorted(set(list(first_files.keys()) + list(last_files.keys())))

    total_first_size = 0
    total_last_size = 0

    print("Per-file trajectory:")
    for path in all_paths:
        if path not in first_files:
            ns = last_files[path].get('sizeBytes', last_files[path].get('size', 0))
            print(f"  + {path}: new ({ns} bytes)")
            total_last_size += ns
            continue
        if path not in last_files:
            os_ = first_files[path].get('sizeBytes', first_files[path].get('size', 0))
            print(f"  - {path}: removed ({os_} bytes)")
            total_first_size += os_
            continue

        of, nf = first_files[path], last_files[path]
        os_ = of.get('sizeBytes', of.get('size', 0))
        ns = nf.get('sizeBytes', nf.get('size', 0))
        total_first_size += os_
        total_last_size += ns

        if of.get('hash') == nf.get('hash'):
            print(f"  = {path}: unchanged ({os_} bytes)")
        else:
            delta = ns - os_
            pct = (delta / os_ * 100) if os_ > 0 else 0
            arrow = "↑" if delta > 0 else "↓"
            print(f"  {arrow} {path}: {delta:+d} bytes ({pct:+.1f}%)")

    total_delta = total_last_size - total_first_size
    pct = (total_delta / total_first_size * 100) if total_first_size > 0 else 0
    print()
    print(f"Total: {total_first_size} → {total_last_size} bytes ({total_delta:+d}, {pct:+.1f}%)")

    # Stability score: what fraction of snapshots showed changes?
    change_count = 0
    for i in range(len(snaps) - 1):
        s1, s2 = load(snaps[i]), load(snaps[i+1])
        f1 = {f['path']: f.get('hash') for f in s1['files']}
        f2 = {f['path']: f.get('hash') for f in s2['files']}
        if f1 != f2:
            change_count += 1

    stability = 1.0 - (change_count / (len(snaps) - 1)) if len(snaps) > 1 else 1.0
    print(f"\nStability: {stability:.0%} ({change_count}/{len(snaps)-1} intervals had changes)")

    if stability > 0.8 and span_days and span_days > 5:
        print("⚠️  High stability for 5+ days — consider a self-review.")
        print("   Are files stable because you're settled, or because you've stopped reflecting?")

if __name__ == "__main__":
    analyze_trajectory()
