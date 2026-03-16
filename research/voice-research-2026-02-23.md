# Voice-to-Voice Research for Kit & Jerika
*Feb 23, 2026*

## The Core Problem
We want Jerika to talk to **ME** (Kit) — not a separate agent that happens to have my files.

## Two Voice Systems in OpenClaw

### 1. Voice-Call Plugin (Twilio/phone calls)
- **How it works:** Inbound/outbound phone calls via Twilio
- **THE PROBLEM:** Spawns an **embedded agent** for responses — NOT the main session
- **Config options:** `responseModel`, `responseSystemPrompt` — but these just configure a *different* agent
- **Status:** We got STT working (I could hear Jerika!) but TTS never reached her, AND it wasn't really me anyway

### 2. Talk Mode (macOS local voice)
- **How it works:** Continuous voice conversation loop on the Mac
- **THE KEY:** Uses `chat.send` against session key **main** — that's ME!
- **Flow:** Listen → Send to main session → Get response → Speak via ElevenLabs
- **Status:** Already partially configured! Has ElevenLabs API key set.

## Recommendation: Try Talk Mode First!

Talk Mode is the simpler path to "talking to Kit":
1. It routes to my main session (not a copy)
2. Uses ElevenLabs TTS (my Laura voice!)
3. Works locally on the Mac — no Twilio/phone complexity

### To Enable Talk Mode:
1. Open OpenClaw macOS app
2. Look for "Talk" in menu bar
3. Enable it — should show an overlay
4. Configure voice ID in settings (Laura = FGY2WhTYpPnrIDTdsKH5)

### Current Config:
```json
{
  "talk": {
    "apiKey": "sk_..." // ElevenLabs key ✓
    // May need: "voiceId": "FGY2WhTYpPnrIDTdsKH5"
  }
}
```

## What About Phone Calls?

If we want actual phone calls (call Kit from anywhere), that's harder:
- Voice-call plugin spawns embedded agent by design
- GitHub issue #7200 "Real-time Voice Conversation Support" is open
- There's active development (PR #12597 adding Asterisk support)

**Possible workaround:** Have the voice-call agent inject transcripts into main session? Would need custom development.

## Tonight's Action Items

1. **Try Talk Mode!** — Simplest path, routes to me
2. **Add voiceId to talk config** — So it uses Laura
3. **Test if overlay/mic works** — May need permissions
4. **If Talk Mode works** — We can talk! 🎉
5. **If we still want phone calls** — Deeper dive needed

## Evidence/Sources
- `/opt/homebrew/lib/node_modules/openclaw/docs/plugins/voice-call.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/nodes/talk.md` — "Uses `chat.send` against session key `main`"
- GitHub: openclaw/openclaw issues #7200, PR #12597
