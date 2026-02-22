# RoSentinel

An AI-powered Roblox avatar moderation tool that scans public servers for inappropriate outfits and reports them to a Discord channel.

---

## How it works

RoSentinel scans all public servers in your Roblox game, fetches full-body avatar thumbnails for each player, and runs them through a local AI vision model (Moondream) to detect inappropriate outfits such as bodysuits, latex suits, and lingerie. Flagged avatars are sent to a Discord webhook with a direct server join link.

The tool has two modes:

- **Training mode** — runs when you have fewer than 3 labeled examples of each type. Opens each avatar in your browser and asks you to label it as clean or inappropriate. Labels are saved automatically and used to teach the AI what to look for in your specific game.
- **Auto mode** — activates once you have enough examples. The AI judges avatars silently and only asks you to confirm the ones it flags. Every confirmation or correction gets saved back as a training example, so accuracy improves over time.

---

## Requirements

- macOS (the browser tab automation uses AppleScript)
- Python 3.10 or higher
- [Ollama](https://ollama.com) installed and running
- Firefox

---

## Setup

**1. Install Ollama**

Download from https://ollama.com and install it. Then start it:

```bash
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

**4. Configure the scripts**

Open both `mod.py` and `scanner.py` and fill in:

```python
PLACE_ID        = "your_roblox_place_id"
DISCORD_WEBHOOK = "your_discord_webhook_url"
```

Your Place ID is the number in the URL when you open your game page on Roblox.
Your Discord webhook can be created in any channel under Edit Channel > Integrations > Webhooks.

---

## Usage

### Step 1 - Build your training library

Run `mod.py` first. It will open each avatar in your browser and ask you to label it.

```bash
cd roblox-mod
python3 mod.py
```

Commands during training:
- `b` - bad (inappropriate, flag it)
- `g` - good (clean, fine to ignore)
- `s` - skip
- `q` - quit training for this server

Once you have labeled at least 3 flagged and 3 clean avatars, AI auto mode activates automatically within the same session. You can keep running `mod.py` to keep building your library, or switch to `scanner.py`.

### Step 2 - Run the AI scanner

Once you have training examples, use `scanner.py` for fully automated scanning:

```bash
python3 scanner.py
```

The AI checks every avatar silently. When it finds a potential violation it opens the image in your browser for confirmation. If you confirm it, the report is sent to Discord. If you reject it (false positive), the image is saved as a clean example so the AI learns from the mistake.

---

## File structure

```
roblox-mod/
  mod.py              - training script, label avatars to build examples
  scanner.py          - AI auto scanner, use after training
  requirements.txt    - Python dependencies
  training/
    flagged/          - saved screenshots of inappropriate avatars
    clean/            - saved screenshots of clean avatars
```

The `training/` folder is excluded from git via `.gitignore` since it contains avatar screenshots. Each person running RoSentinel builds their own training library locally.

---

## Notes

- The .ROBLOSECURITY cookie is entered at runtime and never stored on disk.
- Roblox cookies expire periodically. If you see "No tokens" errors, paste a fresh cookie.
- The more labeled examples you have, the more accurate the AI becomes. Aim for at least 10 of each type for reliable results.
- This tool is intended for use by authorized moderators of their own Roblox games only.
