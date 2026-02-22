import requests
import time
import base64
import json
import platform
import ollama
import webbrowser
import subprocess
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI_MODEL = "moondream"
OS       = platform.system()  # "Darwin" = Mac, "Windows" = Windows

FLAGGED_DIR = Path("training/flagged")
CLEAN_DIR   = Path("training/clean")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SETUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIG_FILE = Path("config.txt")

def load_config():
    config = {}
    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            config[key.strip()] = value.strip()
    return config

def save_config(place_id, webhook, cookie):
    CONFIG_FILE.write_text(
        f"# roblox-auto-mod config\n"
        f"# The cookie expires periodically — update it here when you get a new one\n"
        f"PLACE_ID={place_id}\n"
        f"DISCORD_WEBHOOK={webhook}\n"
        f"COOKIE={cookie}\n"
    )
    print("  Saved to config.txt for next time.\n")

config = load_config()

if config.get("PLACE_ID") and config.get("DISCORD_WEBHOOK") and config.get("COOKIE"):
    print(f"\nFound saved config:")
    print(f"  Place ID : {config['PLACE_ID']}")
    print(f"  Webhook  : {config['DISCORD_WEBHOOK'][:40]}...")
    print(f"  Cookie   : ...{config['COOKIE'][-10:]}")
    use_saved = input("\nUse saved config? [y]es / [n]o (enter new): ").strip().lower()
    if use_saved == "y":
        PLACE_ID        = config["PLACE_ID"]
        DISCORD_WEBHOOK = config["DISCORD_WEBHOOK"]
        COOKIE          = config["COOKIE"]
        print()
    else:
        PLACE_ID        = input("Roblox Place ID: ").strip()
        DISCORD_WEBHOOK = input("Discord Webhook URL: ").strip()
        COOKIE          = input("Roblox .ROBLOSECURITY cookie: ").strip()
        if "|_" in COOKIE:
            COOKIE = COOKIE.split("|_")[-1]
        COOKIE = COOKIE.strip()
        save_config(PLACE_ID, DISCORD_WEBHOOK, COOKIE)
else:
    print("\nNo saved config found. Enter your details below:\n")
    PLACE_ID        = input("Roblox Place ID: ").strip()
    DISCORD_WEBHOOK = input("Discord Webhook URL: ").strip()
    COOKIE          = input("Roblox .ROBLOSECURITY cookie: ").strip()
    if "|_" in COOKIE:
        COOKIE = COOKIE.split("|_")[-1]
    COOKIE = COOKIE.strip()
    save_config(PLACE_ID, DISCORD_WEBHOOK, COOKIE)

SESSION = requests.Session()
SESSION.cookies.set(".ROBLOSECURITY", COOKIE, domain=".roblox.com")
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

visited_servers = set()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BROWSER HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def open_url(url: str):
    webbrowser.open(url)
    time.sleep(0.8)

def close_browser_tab():
    if OS == "Darwin":
        subprocess.run(
            ['osascript',
             '-e', 'tell application "Firefox" to activate',
             '-e', 'delay 0.2',
             '-e', 'tell application "System Events" to keystroke "w" using command down'],
            capture_output=True
        )
        time.sleep(0.3)
        subprocess.run(
            ['osascript', '-e', 'tell application "Terminal" to activate'],
            capture_output=True
        )
    elif OS == "Windows":
        subprocess.run(
            ['powershell', '-Command',
             '$wshell = New-Object -ComObject wscript.shell;'
             '$wshell.AppActivate("Firefox");'
             'Start-Sleep -Milliseconds 300;'
             '$wshell.SendKeys("^w");'
             'Start-Sleep -Milliseconds 200;'
             '$wshell.AppActivate("Windows PowerShell")'],
            capture_output=True
        )
        time.sleep(0.3)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TRAINING EXAMPLES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_examples(folder: Path, limit=4) -> list[str]:
    images = []
    for f in sorted(folder.glob("*.png"))[-limit:]:
        images.append(base64.standard_b64encode(f.read_bytes()).decode("utf-8"))
    return images

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROMPT = """You are a Roblox game moderator checking if an avatar is wearing inappropriate clothing.

FLAG as inappropriate if you see:
- A skin-colored texture covering the whole body with no real clothing (looks naked)
- A shiny/latex/rubber suit showing every body curve
- Lingerie or underwear as the full outfit
- Any clothing with sexual imagery printed on it

DO NOT flag normal clothes, armour, animal costumes, sports outfits, or plain dark outfits.

Reply with ONLY this JSON, nothing else:
{"flagged": true, "reason": "one sentence description"}
or
{"flagged": false, "reason": null}"""

def ai_check_avatar(img_b64: str) -> tuple[bool, str | None]:
    raw = ""
    try:
        messages = []
        for ex in load_examples(CLEAN_DIR):
            messages.append({"role": "user",     "content": "CLEAN example - do NOT flag:", "images": [ex]})
            messages.append({"role": "assistant", "content": '{"flagged": false, "reason": null}'})
        for ex in load_examples(FLAGGED_DIR):
            messages.append({"role": "user",     "content": "FLAGGED example - this IS inappropriate:", "images": [ex]})
            messages.append({"role": "assistant", "content": '{"flagged": true, "reason": "inappropriate outfit"}'})
        messages.append({"role": "user", "content": PROMPT, "images": [img_b64]})

        response = ollama.chat(model=AI_MODEL, messages=messages)
        raw = response["message"]["content"].strip()
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        result = json.loads(raw)
        return result.get("flagged", False), result.get("reason")

    except json.JSONDecodeError:
        flagged = any(w in raw.lower() for w in [
            "inappropriate", "flagged", "bodysuit", "naked", "nude", "latex", "lingerie"
        ])
        return flagged, "Manual review recommended" if flagged else None
    except Exception as e:
        print(f"  AI error: {e}")
        return False, None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ROBLOX HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_servers(cursor=""):
    url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/0?limit=100&cursor={cursor}"
    res = SESSION.get(url, timeout=10)
    if res.status_code == 200:
        return res.json()
    print(f"  Server fetch failed: {res.status_code}")
    return {}

def get_thumbnails(tokens):
    batch = [
        {"requestId": str(i), "token": t, "type": "Avatar",
         "size": "420x420", "format": "Png", "isCircular": False}
        for i, t in enumerate(tokens)
    ]
    res = SESSION.post("https://thumbnails.roblox.com/v1/batch", json=batch, timeout=15)
    if res.status_code == 200:
        return res.json().get("data", [])
    print(f"  Thumbnail fetch failed: {res.status_code}")
    return []

def download_image(url: str) -> bytes | None:
    try:
        r = requests.get(url, timeout=10)
        return r.content if r.status_code == 200 else None
    except:
        return None

def send_webhook(content=None, embed=None):
    payload = {}
    if content: payload["content"] = content
    if embed:   payload["embeds"]  = [embed]
    r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
    if r.status_code not in (200, 204):
        print(f"  Webhook error: {r.status_code}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STARTUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nChecking Ollama + Moondream...")
try:
    ollama.chat(model=AI_MODEL, messages=[{"role": "user", "content": "hi"}])
    print("Moondream ready.")
except:
    print("Moondream not found. Run: ollama pull moondream")
    exit(1)

flagged_count = len(list(FLAGGED_DIR.glob("*.png")))
clean_count   = len(list(CLEAN_DIR.glob("*.png")))
print(f"Training library: {flagged_count} flagged, {clean_count} clean")

if flagged_count == 0 or clean_count == 0:
    print("No training examples found. Run mod.py first to label some avatars.")
    exit(1)

print("AI auto mode active. Only flagged avatars will need your confirmation.")
print("\nroblox-auto-mod running.\n")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN LOOP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
while True:
    cursor = ""
    found_new = False

    while True:
        data = get_servers(cursor)
        servers = data.get("data", [])
        next_cursor = data.get("nextPageCursor")

        for server in servers:
            sid         = server["id"]
            playing     = server.get("playing", 0)
            max_players = server.get("maxPlayers", 12)
            tokens      = server.get("playerTokens", [])

            if sid in visited_servers or playing == 0 or playing >= max_players:
                visited_servers.add(sid)
                continue

            found_new = True
            visited_servers.add(sid)
            print(f"\nServer {sid} - {playing}/{max_players} players")

            if not tokens:
                print("  No tokens. Cookie may be expired.")
                continue

            thumbs = get_thumbnails(tokens)
            img_urls = [
                t.get("imageUrl") for t in thumbs
                if t.get("state") == "Completed" and t.get("imageUrl")
            ]
            if not img_urls:
                print("  No valid images.")
                continue

            print(f"  AI checking {len(img_urls)} avatars...")
            flagged_players = []

            for i, url in enumerate(img_urls):
                print(f"  Player {i+1}...", end=" ", flush=True)
                img_data = download_image(url)
                if not img_data:
                    print("skip")
                    continue
                img_b64 = base64.standard_b64encode(img_data).decode("utf-8")
                flagged, reason = ai_check_avatar(img_b64)
                if flagged:
                    print(f"FLAGGED - {reason}")
                    flagged_players.append((i+1, url, reason))
                else:
                    print("clean")

            if not flagged_players:
                print("  All clean.")
                continue

            print(f"\n  AI flagged {len(flagged_players)} player(s). Opening for review...")
            for num, url, reason in flagged_players:
                open_url(url)
                while True:
                    confirm = input(f"  Player {num} ({reason}) - report? [y]es / [n]o: ").strip().lower()
                    close_browser_tab()
                    if confirm == "y":
                        img_data = download_image(url)
                        if img_data:
                            path = FLAGGED_DIR / f"flagged_{int(time.time())}_{num}.png"
                            path.write_bytes(img_data)
                        send_webhook(content=f"[NSFW AVATAR] Server: {sid}\nroblox://experiences/start?placeId={PLACE_ID}&gameInstanceId={sid}")
                        send_webhook(embed={
                            "title": f"Player {num} - confirmed by moderator",
                            "description": f"AI reason: {reason}",
                            "image": {"url": url},
                            "color": 0xFF0000,
                        })
                        print("  Reported to Discord.\n")
                        break
                    elif confirm == "n":
                        img_data = download_image(url)
                        if img_data:
                            path = CLEAN_DIR / f"clean_{int(time.time())}_{num}.png"
                            path.write_bytes(img_data)
                            print("  Saved as clean example. AI will improve.\n")
                        break

        if not next_cursor:
            break
        cursor = next_cursor
        time.sleep(2)

    if not found_new:
        print("\nAll servers scanned. Waiting 5 minutes...")
        time.sleep(300)
        visited_servers.clear()
