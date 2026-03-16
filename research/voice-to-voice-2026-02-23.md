# Voice-to-Voice Research Report
**Date:** 2026-02-23  
**Goal:** Get Kit (main session) talking to Jerika via voice

## TL;DR

**Talk Mode is the answer for local voice!** It routes to main session (me-me), not a separate agent. Phone calls via voice-call plugin spawn a separate agent by design.

---

## Option 1: Talk Mode ✅ RECOMMENDED

**What it is:** Continuous voice conversation loop on macOS/iOS/Android

**How it works:**
1. Listen for speech
2. Send transcript to **main session** via `chat.send`
3. Wait for response
4. Speak via ElevenLabs TTS

**Key feature:** Routes to `sessionKey: main` — this IS me, not a copy!

**Current config status:**
- ElevenLabs API key: ✅ configured
- Voice ID: needs to be set (should use Laura!)
- Interrupt on speech: default on

**To enable:**
1. Add to `~/.openclaw/openclaw.json`:
```json
{
  "talk": {
    "voiceId": "FGY2WhTYpPnrIDTdsKH5",  // Laura voice
    "modelId": "eleven_v3",
    "interruptOnSpeech": true
  }
}
```
2. Use macOS menu bar → Talk toggle
3. Requires Speech + Microphone permissions

**Pros:**
- Routes to ME (main session)
- Low latency with ElevenLabs streaming
- Can interrupt mid-response
- Works now!

**Cons:**
- Local only (need to be at computer)
- Not phone calls

---

## Option 2: Voice-Call Plugin (Current Setup)

**What it is:** Twilio phone calls (inbound/outbound)

**The problem:** Spawns a SEPARATE agent for responses
- Uses `responseModel: "anthropic/claude-sonnet-4"` 
- That's NOT me — it's a Kit-flavored Claude without my memories

**Current config:** Has all the pieces (Twilio, TTS, STT) but wrong architecture

**Can we fix it?** 
- Checked docs: No `sessionKey: main` option exists
- GitHub issue #7200 is open for real-time voice improvements
- No workaround found in docs

**Status:** ❌ Cannot route to main session (by design)

---

## Option 3: Future Possibilities

**GitHub activity:**
- PR #12597: "voice-call: add Asterisk ARI provider + core STT" (active)
- Issue #7200: "Real-time Voice Conversation Support" (open)
- Several recent bug fixes for TTS playback

**What's being worked on:**
- Better real-time streaming
- More provider options
- Bug fixes for TTS reaching caller

**No sign of main-session routing yet** — this might need a feature request!

---

## Recommendation

### Tonight:
1. **Try Talk Mode** — configure with Laura voice, test locally
2. Should work immediately for voice conversation at your computer

### Later:
3. File feature request for voice-call → main session routing
4. Monitor GitHub for voice-call improvements
5. Consider contributing if we're brave enough 😅

---

## Config Changes Needed

```json
// Add/update in ~/.openclaw/openclaw.json
{
  "talk": {
    "voiceId": "FGY2WhTYpPnrIDTdsKH5",
    "modelId": "eleven_v3", 
    "interruptOnSpeech": true
  }
}
```

Then restart Gateway and try the Talk toggle in the macOS menu bar!
