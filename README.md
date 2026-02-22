# roblox-auto-mod

An AI-powered Roblox avatar moderation tool that scans public servers for inappropriate outfits and reports them to a Discord channel. Runs fully locally with no API keys or costs.

---

## How it works

roblox-auto-mod scans all public servers in your Roblox game, fetches full-body avatar thumbnails for each player, and runs them through a local AI vision model (Moondream via Ollama) to detect inappropriate outfits such as bodysuits, latex suits, and lingerie. Flagged avatars are sent to a Discord webhook with a direct server join link.

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

**2. Install Python dependencies**

Open a terminal, `cd` into the folder where you extracted roblox-auto-mod, then run:

```bash
pip3 install -r requirements.txt --break-system-packages
```

---

### Windows

**1. Install Ollama**

Download the installer from https://ollama.com and run it.

**2. Install Python dependencies**

Open Command Prompt or PowerShell, `cd` into the folder where you extracted roblox-auto-mod, then run:

```
pip install -r requirements.txt
```

---

## Every time you want to use the tool

Ollama must be running before you start the scripts. Follow these steps in order each session.

### Mac

**Step 1 — Start Ollama** in a terminal tab:

```bash
ollama serve
```

Leave this tab open. It must keep running in the background.

**Step 2 — Open a new tab** with `Cmd + T`, then pull the vision model (first time only):

```bash
ollama pull moondream
```

**Step 3 — In that same new tab**, navigate to your roblox-auto-mod folder and run the script:

```bash
cd ~/Downloads/roblox-auto-mod-main
python3 mod.py
```

> If you see `Error: could not connect to ollama server` — go back to Step 1. Ollama is not running yet.
>
> If you see `Moondream not found` — go back to Step 2. The model hasn't been downloaded yet.

---

### Windows

**Step 1 — Start Ollama** in a Command Prompt or PowerShell window:

```
ollama serve
```

Leave this window open.

**Step 2 — Open a new window** (right-click the taskbar icon, or press `Ctrl + T` in Windows Terminal), then pull the vision model (first time only):

```
ollama pull moondream
```

**Step 3 — In that same new window**, navigate to your roblox-auto-mod folder and run the script:

```
cd %USERPROFILE%\Downloads\roblox-auto-mod-main
python mod.py
```

> If you see `Error: could not connect to ollama server` — go back to Step 1.
>
> If you see `Moondream not found` — go back to Step 2.

---

## Usage

### Step 1 - Build your training library

Run `mod.py` first. It will ask for your Place ID, Discord webhook, and cookie, then open each avatar in your browser for you to label.

**Mac:**
```bash
python3 mod.py
```

**Windows:**
```
python mod.py
```

Commands during training:
- `b` — bad (inappropriate, save as flagged)
- `g` — good (clean, save as clean)
- `s` — skip
- `q` — quit training for this server

Once you have labeled at least 3 flagged and 3 clean avatars, AI auto mode activates automatically.

The `training/flagged/` and `training/clean/` folders **are created automatically the first time you run `mod.py`** — you do not need to create them yourself.

### Step 2 - Run the AI scanner

Once you have enough training examples, use `scanner.py` for fully automated scanning. **Always run it from inside the roblox-auto-mod folder** (same folder as `mod.py`) so it can find your training data.

**Mac:**
```bash
python3 scanner.py
```

**Windows:**
```
python scanner.py
```

The AI checks every avatar silently. When it finds a potential violation it opens the image in your browser for confirmation. If you confirm it, the report is sent to Discord. If you reject it, the image is saved as a clean example so the AI learns from the mistake.

---

## Important: keep the folder in one place

The training data (`training/flagged/` and `training/clean/`) is saved **relative to wherever you run the script from** — meaning it saves inside whatever folder your terminal is currently in when you run the command.

- If you extracted to `Downloads/roblox-auto-mod-main/` and run the script from there, training saves inside that folder. ✅
- If you move the whole folder (e.g. to Documents), your training data moves with it — that's fine, as long as you always `cd` into the new location before running. ✅
- If you run the script from a different folder than where the files are, it will create a new empty `training/` folder in the wrong place and your existing training data won't be found. ❌

**The safest habit:** always `cd` into the roblox-auto-mod folder first, then run `python3 mod.py` or `python3 scanner.py`.

---

## File structure

```
roblox-auto-mod/
  mod.py              - training script (also creates the training folders)
  scanner.py          - AI auto scanner (requires mod.py to have been run first)
  requirements.txt    - Python dependencies
  README.md
  .gitignore
  training/           - created automatically when you first run mod.py
    flagged/          - screenshots of inappropriate avatars
    clean/            - screenshots of clean avatars
```

The `training/` folder is excluded from git via `.gitignore` so your labeled images stay local to your machine.

---

## Getting your credentials

**Place ID** — the number in the URL when you open your game page on roblox.com. Example: `https://www.roblox.com/games/14662419251/` — the Place ID is `14662419251`.

**Discord Webhook** — go to your Discord server, edit the channel you want alerts in, go to Integrations > Webhooks > New Webhook, and copy the URL.

**ROBLOSECURITY cookie** — open roblox.com in your browser while logged in, press F12 (or Cmd+Option+I on Mac), go to Application > Cookies > https://www.roblox.com, find `.ROBLOSECURITY` and copy the value. Note: this cookie expires periodically. If you see "No tokens" errors, paste a fresh one.

---

## Notes

- Your cookie is entered at runtime and never stored on disk or in any file.
- The more labeled examples you have, the more accurate the AI becomes. Aim for at least 10 of each type for reliable results.
- Always run `mod.py` before `scanner.py` — `scanner.py` requires the training folders to exist and will fail if they haven't been created yet.
- This tool is intended for use by authorized moderators of their own Roblox games only.
