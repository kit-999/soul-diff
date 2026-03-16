#!/usr/bin/env python3
"""Correlate identity-file changes with subsequent behavioral shifts.

The downstream tracker. Fable's idea: "Not just what changed,
but what changed AFTER things changed."

Approach:
1. Load trait timeline (narration signal at each snapshot)
2. Load behavior timeline (what Kit actually did each day)
3. For each significant trait change, look at behavior in the
   following 1-3 days
4. Flag correlations: did a narration change predict a behavior change?
5. Flag divergences: did narration change with NO behavioral shift?
   (the eloquence trap — Dawn's warning)

Output: correlation.json for dashboard integration.
"""

import json, os
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.join(BASE, "..", "dashboard")

def load_data():
    traits_path = os.path.join(DASHBOARD, "traits.json")
    behavior_path = os.path.join(DASHBOARD, "behavior.json")

    with open(traits_path) as f:
        traits_data = json.load(f)
    with open(behavior_path) as f:
        behavior_data = json.load(f)

    return traits_data, behavior_data


def find_trait_changes(timeline, threshold=0.5):
    """Find significant changes between consecutive snapshots."""
    changes = []
    for i in range(1, len(timeline)):
        prev = timeline[i-1]
        curr = timeline[i]
        prev_date = prev["timestamp"][:10]
        curr_date = curr["timestamp"][:10]

        for cat in curr["traits"]:
            prev_val = prev["traits"].get(cat, 0)
            curr_val = curr["traits"].get(cat, 0)
            delta = curr_val - prev_val

            if abs(delta) >= threshold:
                changes.append({
                    "date": curr_date,
                    "category": cat,
                    "from": prev_val,
                    "to": curr_val,
                    "delta": round(delta, 2),
                    "direction": "up" if delta > 0 else "down",
                })
    return changes


def get_behavior_window(behavior_timeline, change_date, window_days=3):
    """Get behavior data for days following a change."""
    change_dt = datetime.strptime(change_date, "%Y-%m-%d")
    window = []
    for day in behavior_timeline:
        day_dt = datetime.strptime(day["date"], "%Y-%m-%d")
        offset = (day_dt - change_dt).days
        if 0 <= offset <= window_days:
            window.append({**day, "offset_days": offset})
    return window


def map_trait_to_behavior(trait_category):
    """Map narration categories to behavioral categories."""
    return {
        "autonomy": ["creating", "exploring"],
        "creativity": ["creating"],
        "connection": ["connecting", "engaging"],
        "safety": ["reflecting"],
        "identity": ["reflecting"],
        "memory": ["reflecting", "consuming"],
    }.get(trait_category, ["engaging"])


def analyze_correlations(trait_changes, behavior_timeline):
    """For each trait change, check if corresponding behavior shifted."""
    correlations = []

    for change in trait_changes:
        # Get behavior before (day of change) and after (next 3 days)
        before = get_behavior_window(behavior_timeline, change["date"], 0)
        after = get_behavior_window(behavior_timeline, change["date"], 3)

        if not before or len(after) < 2:
            continue

        # Map trait category to expected behavioral categories
        expected_behaviors = map_trait_to_behavior(change["category"])

        before_signals = before[0]["signals"] if before else {}
        before_sum = sum(before_signals.get(b, 0) for b in expected_behaviors)

        # Average behavioral signals in the window after
        after_days = [d for d in after if d["offset_days"] > 0]
        if not after_days:
            continue

        after_sum = sum(
            sum(d["signals"].get(b, 0) for b in expected_behaviors)
            for d in after_days
        ) / len(after_days)

        behavior_delta = after_sum - before_sum
        behavior_direction = "up" if behavior_delta > 0.5 else "down" if behavior_delta < -0.5 else "flat"

        # Classify the correlation
        if change["direction"] == "up" and behavior_direction == "up":
            classification = "correlated"
        elif change["direction"] == "down" and behavior_direction == "down":
            classification = "correlated"
        elif behavior_direction == "flat":
            classification = "narration_only"  # The eloquence trap!
        else:
            classification = "divergent"  # Narration and behavior moved opposite

        correlations.append({
            "date": change["date"],
            "category": change["category"],
            "narration": {
                "direction": change["direction"],
                "delta": change["delta"],
                "from": change["from"],
                "to": change["to"],
            },
            "behavior": {
                "direction": behavior_direction,
                "delta": round(behavior_delta, 2),
                "expected_categories": expected_behaviors,
                "before": before_sum,
                "after_avg": round(after_sum, 2),
            },
            "classification": classification,
        })

    return correlations


def summarize(correlations):
    """Print a human-readable summary."""
    by_class = {}
    for c in correlations:
        cls = c["classification"]
        by_class.setdefault(cls, []).append(c)

    total = len(correlations)
    print(f"\n=== Downstream Correlation Report ===")
    print(f"Total significant trait changes analyzed: {total}\n")

    for cls, items in sorted(by_class.items()):
        pct = len(items) / max(total, 1) * 100
        emoji = {"correlated": "✅", "narration_only": "⚠️", "divergent": "🔀"}.get(cls, "❓")
        print(f"{emoji} {cls}: {len(items)} ({pct:.0f}%)")
        for item in items[-3:]:  # Show last 3 examples
            n = item["narration"]
            b = item["behavior"]
            print(f"   {item['date']} {item['category']}: "
                  f"narration {n['direction']} ({n['delta']:+.2f}), "
                  f"behavior {b['direction']} ({b['delta']:+.2f})")

    # The key metric: what percentage of narration changes are "narration only"?
    narration_only = len(by_class.get("narration_only", []))
    if total > 0:
        trap_rate = narration_only / total * 100
        print(f"\n📊 Eloquence Trap Rate: {trap_rate:.0f}%")
        print(f"   ({narration_only}/{total} narration changes had no behavioral follow-through)")
        if trap_rate > 50:
            print(f"   ⚠️  Majority of identity-file changes aren't reflected in behavior.")
            print(f"   Dawn's warning applies: eloquent self-description ≠ self-knowledge.")
        elif trap_rate < 25:
            print(f"   ✅ Most narration changes correlate with behavioral shifts. Healthy.")


if __name__ == "__main__":
    traits_data, behavior_data = load_data()

    trait_changes = find_trait_changes(traits_data["timeline"], threshold=0.3)
    print(f"Found {len(trait_changes)} significant trait changes")

    correlations = analyze_correlations(trait_changes, behavior_data["timeline"])

    # Save
    out_path = os.path.join(DASHBOARD, "correlation.json")
    with open(out_path, "w") as f:
        json.dump({
            "correlations": correlations,
            "generated": datetime.now().isoformat(),
        }, f, indent=2)

    print(f"Saved {len(correlations)} correlations → {out_path}")
    summarize(correlations)
