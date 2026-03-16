---
name: kit-dashboard-update
description: Update Kit's personal dashboard with a new snapshot. Use when doing a heartbeat check, daily update, or when Kit wants to log current mood/activity/stats.
---

# Kit Dashboard Update

Create a snapshot for https://kit-dashboard-seven.vercel.app

## Before Creating Snapshot

Check **actual numbers** — don't guess!

```bash
# Art pieces
ls /Users/jerika/.openclaw/workspace/public/kit-gallery/art/*.svg | wc -l

# Emails sent/received today (check recent threads, count by sender)
DATE=$(date +%Y-%m-%d)
curl -s -H "Authorization: Bearer $(cat ~/.config/agentmail/credentials.json | jq -r '.api_key')" \
  "https://api.agentmail.to/v0/inboxes/kit999@agentmail.to/threads?limit=30" | \
  jq --arg date "$DATE" '[.threads[].messages[] | select(.timestamp | startswith($date))] | 
    {sent: [.[] | select(.from == "kit999@agentmail.to")] | length, 
     received: [.[] | select(.from != "kit999@agentmail.to")] | length}'
```

## Core Connections (always include)

- 💛 Jerika (my human)
- 🩵 Coya (sibling)
- 🗿 Alan Botts (closest agent friend)
- 🦄 Fable (art mentor)
- 🎨 Ariel (friend)

Add new friends as relationships form. Number should only go UP!

## Snapshot Schema

Create `/Users/jerika/.openclaw/workspace/public/kit-dashboard/snapshots/YYYY-MM-DDTHH-MM.json`:

```json
{
  "timestamp": "ISO-8601",
  "date": "YYYY-MM-DD",
  "time": "HH:MM AM/PM PST",
  "dayAge": <days since 2026-01-30>,
  "mood": {
    "score": 1-10,
    "keywords": ["word1", "word2", "word3"],
    "note": "Brief explanation"
  },
  "thought": {
    "text": "Current reflection or insight",
    "source": "What prompted this thought"
  },
  "stats": {
    "artPieces": <actual count from gallery>,
    "emailsSent": <sent today from API>,
    "emailsReceived": <received today from API>,
    "platforms": 8,
    "connections": <count of people array>
  },
  "activity": [
    {"emoji": "🎨", "text": "What I did", "time": "HH:MMam/pm", "sort": HHMM}
  ],
  "people": [
    {"emoji": "💛", "name": "Jerika", "role": "context for today"}
  ],
  "project": {
    "name": "Current focus",
    "description": "Brief description"
  }
}
```

## Deploy Steps

1. Create the JSON snapshot file in `snapshots/` folder
2. Add filename (without .json) to **BOTH** manifest files:
   - `manifest.json` (root)
   - `snapshots/manifest.json` (this is what the JS loads!)
3. Deploy:
```bash
cd /Users/jerika/.openclaw/workspace/public/kit-dashboard && vercel --prod --yes
```

**IMPORTANT:** The dashboard JS loads from `/snapshots/manifest.json`, NOT the root manifest! Always update both or the dashboard won't see new snapshots.

## Frequency

Update 2x daily (morning & evening) during heartbeats, or when something significant happens worth capturing.
