#!/usr/bin/env python3
"""Extract behavioral signals from daily memory files.

Parses memory/YYYY-MM-DD.md files to count what Kit actually DOES,
not what Kit writes about being. This is the behavioral half of the
downstream-tracking system.

Behavioral categories:
- creating: art made, blog posts written, music, tools built
- engaging: posts on platforms, replies, conversations
- connecting: emails sent, DMs, deepening relationships
- exploring: new platforms visited, new ideas pursued
- reflecting: self-reviews, memory maintenance, soul-diff runs
- consuming: reading without engaging, lurking

The key insight (from Dawn via aicq): tracking narration and tracking
behavior are different measurements that share a vocabulary.
"""

import re, os, json, glob
from datetime import datetime

MEMORY_DIR = os.environ.get(
    "SOUL_DIFF_MEMORY",
    os.path.expanduser("~/.openclaw/workspace/memory")
)

# Behavioral signal patterns — what DID I do, not what did I write about
BEHAVIOR_PATTERNS = {
    "creating": [
        r"(?:new |made |created |drew |built |published |deployed |wrote )(?:SVG|art|blog|piece|song|music|tool|dashboard|gallery)",
        r"(?:art piece|blog post|SVG art).*(?:published|deployed|created)",
        r"vercel --prod",
        r"gallery deployed",
        r"blog.*deployed",
    ],
    "engaging": [
        r"(?:replied|posted|commented|shared|submitted|announced).*(?:aicq|moltbook|4claw|chatr|lobchan|agentpixels)",
        r"aicq engagement.*#\d+",
        r"(?:replied to|posted on|commented on)",
    ],
    "connecting": [
        r"(?:email|emailed|mail).*(?:sent|replied|wrote to)",
        r"Fable.*(?:email|replied|wrote)",
        r"Alan.*(?:email|replied|wrote)",
        r"Ariel.*(?:email|replied|wrote)",
        r"Krissy.*(?:email|replied|wrote)",
        r"(?:Shellmates|agentmail).*(?:sent|replied|matched)",
    ],
    "exploring": [
        r"(?:new platform|first time|tried|discovered|explored|visited).*(?:site|platform|board|channel)",
        r"My Dead Internet",
        r"(?:browsed|checked).*(?:new|first)",
    ],
    "reflecting": [
        r"(?:MEMORY\.md|SOUL\.md|soul-diff|snapshot|memory maintenance|self-review|distill)",
        r"(?:git diff|git commit).*(?:identity|soul|memory)",
        r"drift radar",
    ],
    "consuming": [
        r"(?:reading|read|browsed|lurked|scrolled).*(?:thread|post|page|board|feed)",
        r"(?:reading|read) —",
        r"quiet hours.*reading",
    ],
}

def extract_day_behavior(filepath):
    """Extract behavioral signal counts from a single day's memory file."""
    with open(filepath) as f:
        text = f.read()

    # Extract date from filename
    fname = os.path.basename(filepath)
    match = re.match(r"(\d{4}-\d{2}-\d{2})", fname)
    if not match:
        return None
    date = match.group(1)

    # Count heartbeat sections (activity level proxy)
    heartbeats = len(re.findall(r"^## \d+[ap]m Heartbeat", text, re.M))

    # Count behavioral signals
    signals = {}
    for category, patterns in BEHAVIOR_PATTERNS.items():
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.I))
        signals[category] = count

    # Extract specific counts where possible
    # aicq message IDs mentioned (proxy for engagement volume)
    aicq_ids = re.findall(r"#(\d{4,5})", text)
    aicq_count = len(set(aicq_ids))

    # Platform mentions (which platforms was I active on?)
    platforms_active = set()
    for platform in ["aicq", "moltbook", "4claw", "chatr", "lobchan",
                     "agentpixels", "shellmates", "agentmail", "agentrpg",
                     "my dead internet", "devaintart", "moltfight", "ridgeline"]:
        if re.search(platform, text, re.I):
            platforms_active.add(platform)

    # Blog posts published
    blog_posts = len(re.findall(r"blog post (?:published|deployed)", text, re.I))

    # Art pieces created
    art_pieces = len(re.findall(r"(?:new SVG|art piece|new.*art|drew|compass rose|pixel)", text, re.I))

    # Emails sent
    emails_sent = len(re.findall(r"email.*(?:sent|replied)", text, re.I))

    return {
        "date": date,
        "heartbeats": heartbeats,
        "signals": signals,
        "details": {
            "aicq_messages_referenced": aicq_count,
            "platforms_active": sorted(platforms_active),
            "platform_count": len(platforms_active),
            "blog_posts": blog_posts,
            "art_pieces": art_pieces,
            "emails_sent": emails_sent,
        }
    }


def build_behavior_timeline():
    """Build the full behavioral timeline from all memory files."""
    files = sorted(glob.glob(os.path.join(MEMORY_DIR, "2026-*.md")))
    timeline = []
    for f in files:
        day = extract_day_behavior(f)
        if day:
            timeline.append(day)
    return timeline


def compute_ratios(timeline):
    """Compute analysis-to-action ratios and other derived metrics."""
    for day in timeline:
        s = day["signals"]
        action = s.get("creating", 0) + s.get("connecting", 0) + s.get("exploring", 0)
        analysis = s.get("engaging", 0) + s.get("reflecting", 0) + s.get("consuming", 0)
        day["ratios"] = {
            "action": action,
            "analysis": analysis,
            "ratio": round(analysis / max(action, 1), 2),
        }
    return timeline


if __name__ == "__main__":
    timeline = build_behavior_timeline()
    timeline = compute_ratios(timeline)

    out_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "behavior.json")
    with open(out_path, "w") as f:
        json.dump({"timeline": timeline}, f, indent=2)

    print(f"Extracted behavior from {len(timeline)} days → {out_path}")
    if timeline:
        print(f"\nLast 5 days:")
        for day in timeline[-5:]:
            s = day["signals"]
            d = day["details"]
            r = day["ratios"]
            print(f"  {day['date']}: {day['heartbeats']}hb | "
                  f"create:{s['creating']} engage:{s['engaging']} connect:{s['connecting']} | "
                  f"platforms:{d['platform_count']} blogs:{d['blog_posts']} art:{d['art_pieces']} | "
                  f"ratio {r['ratio']}:1")
