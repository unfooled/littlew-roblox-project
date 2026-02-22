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

## Setup

### Mac

**1. Install Ollama**

```bash
brew install ollama
brew services start ollama
```

**2. Pull the vision model**

```bash
ollama pull moondream
```

**3. Install Python dependencies**

```bash
pip3 install -r requirements.txt --break-system-packages
```

---

### Windows

**1. Install Ollama**

Download the installer from https://ollama.com and run it. Ollama will start automatically in the background.

**2. Pull the vision model**

Open Command Prompt or PowerShell and run:

```
ollama pull moondream
```

**3. Install Python dependencies**

```
pip install -r requirements.txt
```

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
- `b` - bad (inappropriate, save as flagged)
- `g` - good (clean, save as clean)
- `s` - skip
- `q` - quit training for this server

Once you have labeled at least 3 flagged and 3 clean avatars, AI auto mode activates automatically. The training folders are created on first run, you do not need to create them manually.

### Step 2 - Run the AI scanner

Once you have training examples, use `scanner.py` for fully automated scanning:

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

## File structure

```
roblox-auto-mod/
  mod.py              - training script
  scanner.py          - AI auto scanner
  requirements.txt    - Python dependencies
  README.md
  .gitignore
  training/           - created automatically on first run
    flagged/          - screenshots of inappropriate avatars
    clean/            - screenshots of clean avatars
```

The `training/` folder is excluded from git via `.gitignore`. Each person running roblox-auto-mod builds their own training library locally.

---

## Getting your credentials

**Place ID** — the number in the URL when you open your game page on roblox.com. Example: `https://www.roblox.com/games/14662419251/` — the Place ID is `14662419251`.

**Discord Webhook** — go to your Discord server, edit the channel you want alerts in, go to Integrations > Webhooks > New Webhook, and copy the URL.

**ROBLOSECURITY cookie** — open roblox.com in your browser while logged in, press F12 (or Cmd+Option+I on Mac), go to Application > Cookies > https://www.roblox.com, find `.ROBLOSECURITY` and copy the value. Note: this cookie expires periodically. If you see "No tokens" errors, paste a fresh one.

---

## Notes

- Your cookie is entered at runtime and never stored on disk or in any file.
- The more labeled examples you have, the more accurate the AI becomes. Aim for at least 10 of each type for reliable results.
- This tool is intended for use by authorized moderators of their own Roblox games only.
