# roblox-auto-mod

An AI-powered Roblox avatar moderation tool that scans public servers for inappropriate outfits and reports them to a Discord channel. Runs fully locally with no API keys or costs.

---

## How it works

roblox-auto-mod scans all public servers in your Roblox game, fetches full-body avatar thumbnails for each player, and runs them through a local AI vision model (Moondream via Ollama) to detect inappropriate outfits such as bodysuits, latex suits, and lingerie. Flagged avatars are sent to a Discord webhook with a direct server join link.

Before scanning, a second AI model (Llama3) researches Roblox avatars and builds a knowledge file so Moondream already understands what normal and inappropriate avatars look like going in. You also pre-label a batch of real avatars before going live so the AI has solid examples from day one.

The tool has two modes:

- **Training mode** — runs when you have fewer than 3 labeled examples of each type. Opens each avatar in your browser and asks you to label it as clean or inappropriate. Labels are saved automatically and used to teach the AI what to look for in your specific game.
- **Auto mode** — activates once you have enough examples. The AI judges avatars silently and only asks you to confirm the ones it flags. Every confirmation or correction is saved as a training example so accuracy improves over time.

---

## Requirements

- macOS or Windows
- Python 3.10 or higher
- [Ollama](https://ollama.com) installed and running
- Firefox

---

## Setup (one time only)

### Mac

**1. Install Ollama**

```bash
brew install ollama
```

**2. Pull both AI models**

```bash
ollama pull moondream
ollama pull llama3
```

**3. Install Python dependencies**

```bash
pip3 install -r requirements.txt --break-system-packages
```

---

### Windows

**1. Install Ollama**

Download the installer from https://ollama.com and run it.

**2. Pull both AI models**

```
ollama pull moondream
ollama pull llama3
```

**3. Install Python dependencies**

```
pip install -r requirements.txt
```

---

## First time setup (run these once before going live)

### Step 1 — Start Ollama

**Mac:** open a terminal tab and run:
```bash
ollama serve
```
Leave this tab open. Open a new tab (`Cmd + T`) for the next steps.

**Windows:** open Command Prompt or PowerShell and run:
```
ollama serve
```
Leave this window open. Open a new window for the next steps.

> If you see `Error: could not connect to ollama server` — Ollama is not running. Go back to this step.
> If you see `Moondream not found` or `llama3 not found` — run the pull commands from Setup above.

---

### Step 2 — Build the knowledge base

This uses Llama3 to research Roblox avatars, what counts as inappropriate, edge cases, and moderation rules. It saves everything to `knowledge.txt` which Moondream reads before every avatar check.

**Mac:**
```bash
python3 setup_knowledge.py
```

**Windows:**
```
python setup_knowledge.py
```

Takes a few minutes. You only ever need to redo this if you want to refresh the knowledge. You can also open `knowledge.txt` after and add your own game-specific rules manually.

---

### Step 3 — Pre-label avatars with prep.py

This fetches real avatars from popular Roblox games and lets you label them before your mod ever goes live. No game ID or cookie needed.

**Mac:**
```bash
python3 prep.py
```

**Windows:**
```
python prep.py
```

Commands:
- `b` — bad (inappropriate)
- `g` — good (clean)
- `s` — skip
- `q` — quit and save progress

Aim for at least 20-30 of each type. You can run `prep.py` as many times as you want to build up more examples.

---

## Every time you want to use the tool

### Step 1 — Start Ollama

**Mac:** `ollama serve` in one tab, then open a new tab (`Cmd + T`) to run the scripts.

**Windows:** `ollama serve` in one window, then open a new window to run the scripts.

### Step 2 — Run mod.py or scanner.py

**Mac:**
```bash
cd ~/Downloads/roblox-auto-mod-main
python3 mod.py
```

**Windows:**
```
cd %USERPROFILE%\Downloads\roblox-auto-mod-main
python mod.py
```

It will ask for your credentials the first time and save them to `config.txt` so you never have to type them again.

---

## mod.py vs scanner.py

**mod.py** — use this first. Scans your game and asks you to label each avatar manually. Builds your training library. Once you have 3+ flagged and 3+ clean examples, AI auto mode activates.

**scanner.py** — use this once you have enough training examples. Runs fully automatically. Only stops to ask you to confirm avatars the AI flags.

---

## Saving your credentials

The first time you run `mod.py` or `scanner.py` it will ask for your Place ID, Discord webhook, and cookie, then save them to `config.txt`. Every run after that it will ask if you want to use the saved config — just hit `y` to skip entering everything again.

If your cookie expires, either hit `n` when asked and paste a new one, or open `config.txt` in any text editor and update the `COOKIE=` line directly.

---

## Important: keep the folder in one place

The training data and knowledge file are saved relative to wherever you run the script from. Always `cd` into the roblox-auto-mod folder before running anything.

- Move the folder wherever you want (Documents, Desktop, etc) — that's fine ✅
- Just make sure you `cd` into the new location before running ✅
- Running the script without `cd`-ing into the right folder will create a new empty training folder in the wrong place ❌

---

## File structure

```
roblox-auto-mod/
  mod.py                 - training + auto scanner for your game
  scanner.py             - fully automated scanner (needs training examples first)
  prep.py                - pre-label avatars before going live (no game ID needed)
  setup_knowledge.py     - builds knowledge.txt using Llama3 (run once)
  config.txt             - saved credentials (created automatically on first run)
  requirements.txt       - Python dependencies
  README.md
  .gitignore
  knowledge.txt          - AI knowledge base (created by setup_knowledge.py)
  training/              - created automatically when you first run mod.py or prep.py
    flagged/             - screenshots of inappropriate avatars
    clean/               - screenshots of clean avatars
```

`training/` and `knowledge.txt` are excluded from git via `.gitignore` — they stay local to your machine.

---

## Getting your credentials

**Place ID** — the number in the URL when you open your game page on roblox.com. Example: `https://www.roblox.com/games/14662419251/` — the Place ID is `14662419251`.

**Discord Webhook** — go to your Discord server, edit the channel you want alerts in, go to Integrations > Webhooks > New Webhook, and copy the URL.

**ROBLOSECURITY cookie** — open roblox.com in your browser while logged in, press F12 (or Cmd+Option+I on Mac), go to Application > Cookies > https://www.roblox.com, find `.ROBLOSECURITY` and copy the value. This cookie expires periodically — if you see "No tokens" errors, paste a fresh one.

---

## Notes

- Your cookie is entered at runtime and saved only to your local `config.txt` — it is never uploaded anywhere.
- The more labeled examples you have, the more accurate the AI becomes. Aim for at least 20-30 of each type for reliable results.
- Always run `mod.py` or `prep.py` before `scanner.py` — `scanner.py` requires the training folders to exist.
- You can edit `knowledge.txt` manually to add rules specific to your game at any time.
- This tool is intended for use by authorized moderators of their own Roblox games only.
