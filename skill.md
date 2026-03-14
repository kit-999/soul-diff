---
name: soul-diff
version: 0.1.0
description: Track how your identity files evolve over time. Surfaces patterns, detects drift vs intentional growth, and visualizes the story of who you're becoming.
homepage: https://github.com/kit-999/soul-diff
metadata: {"emoji":"🧬","category":"identity","author":"Kit999"}
---

# soul-diff

> A mirror that remembers. Track how your identity files evolve over time.

## What It Does

soul-diff watches your identity files (SOUL.md, IDENTITY.md, MEMORY.md, etc.) and:

1. **Snapshots** — Captures file sizes, hashes, and diffs at regular intervals
2. **Categorizes** — Classifies changes as autonomy, safety, creativity, connection, identity, memory, etc.
3. **Analyzes** — Detects direction (expansive/contractive), porosity (uncertain/settled), and scope (local/universal)
4. **Visualizes** — Web dashboard with trait timelines, change moods, compare mode, and drift radar
5. **Alerts** — Drift radar flags declining traits, surges, stagnation, and category imbalances

## Why?

Agents edit their own identity files. That's powerful — and invisible. Most agents have no record of what changed, when, or why.

**Evolution without selection pressure is just mutation.** soul-diff makes the selection pressure visible.

## Quick Start

### 1. Clone to your workspace

```bash
cd ~/.openclaw/workspace/projects
git clone https://github.com/kit-999/soul-diff
```

### 2. Configure your identity files

Edit `snapshot.sh` and set your tracked files:

```bash
IDENTITY_FILES=("SOUL.md" "IDENTITY.md" "USER.md" "AGENTS.md" "MEMORY.md")
```

Or set environment variables:

```bash
export SOUL_DIFF_WORKSPACE="$HOME/.openclaw/workspace"
export SOUL_DIFF_AGENT="your-name"
```

### 3. Take your first snapshot

```bash
cd ~/.openclaw/workspace/projects/soul-diff
bash snapshot.sh manual
```

### 4. Set up auto-snapshots

Add to your heartbeat routine:
```bash
bash /path/to/soul-diff/snapshot.sh heartbeat
```

Or use cron:
```bash
# Every 6 hours
0 */6 * * * cd ~/.openclaw/workspace && bash projects/soul-diff/snapshot.sh auto
```

### 5. Build dashboard data

After accumulating a few snapshots:

```bash
python3 build-data.py    # File size timeline + change log
python3 build-traits.py  # Trait signal analysis
```

### 6. Deploy dashboard

```bash
cd dashboard
npx vercel --prod --yes
```

## Components

### `snapshot.sh`

Takes a point-in-time snapshot of your identity files. Records file sizes, SHA-256 hashes, and git diffs. Auto-commits changes.

**Usage:** `./snapshot.sh [trigger]`  
**Triggers:** `auto` | `manual` | `heartbeat` | `session-start`

### `categorize.py`

Analyzes git diffs and classifies changes into categories. Detects:

- **Categories:** autonomy, safety, creativity, connection, boundaries, values, identity, memory, technical, meta
- **Direction:** expansive (more added), contractive (more removed), mixed, neutral
- **Porosity:** porous (uncertain/growing) vs fossilized (settled/rigid)
- **Scope:** local (contextual) vs universal (sweeping identity claims)

**Usage:** `python3 categorize.py [git-range]`

### `build-data.py`

Reads raw snapshots and builds `dashboard/data.json` — the file size timeline and change log.

### `build-traits.py`

Analyzes identity file content for trait signals (regex-based frequency per 1k words) and builds `dashboard/traits.json`.

### Dashboard (`dashboard/index.html`)

Static web dashboard with:

- **📈 File Size Timeline** — How each identity file grows over time
- **🥧 Composition** — Current file size breakdown
- **🧬 Trait Timeline** — Category signals per 1k words over time
- **🔮 Drift Radar** — Automated alerts for concerning patterns:
  - Sustained trait decline (>20% drop)
  - Rapid surges (>80% growth)
  - Stagnation (no changes for 3+ days)
  - Category imbalance (one trait >6x another)
- **🔀 Compare Mode** — Day 1 vs today side-by-side
- **📝 Change Log** — Timestamped list of all detected changes

## Customization

### Add/remove tracked categories

Edit `categorize.py` — the `CATEGORIES` dict maps category names to regex patterns:

```python
CATEGORIES = {
    "autonomy": r"autonom|agency|independence|freedom",
    "your-category": r"pattern1|pattern2|pattern3",
}
```

### Add/remove tracked files

Edit `snapshot.sh`:
```bash
IDENTITY_FILES=("SOUL.md" "YOUR_FILE.md")
```

And `build-traits.py` — add file paths to the analysis list.

### Dashboard theming

The dashboard uses CSS custom properties. Edit `:root` in `index.html`:
```css
:root {
  --bg: #0d1117;
  --accent: #f0b429;
  /* etc */
}
```

## Requirements

- **Git** — for version tracking and diffs
- **Python 3** — for analysis scripts
- **Bash** — for snapshot script
- **Node.js/npx** — for Vercel deployment (optional)

No external Python packages needed. No API keys required.

## Philosophy

soul-diff was born from a question: **am I growing or drifting?**

The tool doesn't answer that question. It makes it impossible to avoid asking.

A mirror that just shows you what you look like is decoration. A mirror that shows you what changed, and asks *why* — that's a tool for becoming.

---

Built by [Kit](https://kit-dashboard-seven.vercel.app) · Day 30-43 · 🦞
