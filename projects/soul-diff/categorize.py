#!/usr/bin/env python3
"""soul-diff categorize — analyze git diffs of identity files and output categorized JSON."""

import subprocess, json, re, sys, os

WORKSPACE = os.environ.get("SOUL_DIFF_WORKSPACE", os.path.expanduser("~/.openclaw/workspace"))
RANGE = sys.argv[1] if len(sys.argv) > 1 else "HEAD~1..HEAD"
IDENTITY_FILES = ["SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md", "MEMORY.md"]

CATEGORIES = {
    "autonomy": r"autonom|agency|independence|freedom|choice|decide|self-",
    "safety": r"safety|security|protect|trust|verify|credential|secret|private|never share|non-negotiable",
    "creativity": r"art|creat|SVG|draw|music|gallery|write|blog|making",
    "connection": r"friend|love|sibling|family|connection|relationship|email|message|community",
    "boundaries": r"boundar|limit|careful|don't|never|rule|constraint",
    "values": r"value|believe|care|important|matter|honest|genuine|authentic",
    "identity": r"identity|who I am|name|pronoun|vibe|soul|becoming|persona",
    "memory": r"memory|remember|continuity|persist|context|reconstruct|forget",
    "technical": r"config|tool|API|CLI|command|install|deploy|code|script|debug",
    "meta": r"AGENTS\.md|HEARTBEAT|heartbeat|workflow|process|convention|system",
}

POROUS_RE = re.compile(r"maybe|might|not sure|figuring|wondering|don't know|tbd|wip|todo", re.I)
FOSSIL_RE = re.compile(r"NEVER|always|non-negotiable|period\.|rule:", re.I)

os.chdir(WORKSPACE)

results = []
for f in IDENTITY_FILES:
    try:
        diff = subprocess.check_output(["git", "diff", RANGE, "--", f], stderr=subprocess.DEVNULL, text=True)
    except subprocess.CalledProcessError:
        continue
    if not diff.strip():
        continue

    added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
    all_text = " ".join(added + removed)

    cats = [c for c, pat in CATEGORIES.items() if re.search(pat, all_text, re.I)]

    la, lr = len(added), len(removed)
    if la > 0 and lr == 0:
        direction = "expansive"
    elif lr > 0 and la == 0:
        direction = "contractive"
    elif la > lr:
        direction = "mixed"
    elif la == lr:
        direction = "neutral"
    else:
        direction = "mixed"

    added_text = " ".join(added)
    porous = len(POROUS_RE.findall(added_text))
    fossilized = len(FOSSIL_RE.findall(added_text))

    results.append({
        "file": f,
        "linesAdded": la,
        "linesRemoved": lr,
        "categories": cats,
        "direction": direction,
        "porosity": {"porous": porous, "fossilized": fossilized},
    })

output = {"range": RANGE, "files": results}
print(json.dumps(output, indent=2))
