import requests
import time
import random
import platform
import webbrowser
import subprocess
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OS          = platform.system()
FLAGGED_DIR = Path("training/flagged")
CLEAN_DIR   = Path("training/clean")
FLAGGED_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# Popular social Roblox games to pull random players from
# These are large public games with lots of active players and varied avatar styles
SAMPLE_GAMES = [
    "142823291",   # Adopt Me
    "606849621",   # Brookhaven
    "189707",      # Welcome to Bloxburg
    "3233893879",  # Royale High
    "2753915549",  # Piggy
]

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
#  ROBLOX HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_servers(place_id: str):
    try:
        url = f"https://games.roblox.com/v1/games/{place_id}/servers/0?limit=10"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json().get("data", [])
    except:
        pass
    return []

def get_thumbnails(tokens: list):
    if not tokens:
        return []
    try:
        batch = [
            {"requestId": str(i), "token": t, "type": "Avatar",
             "size": "420x420", "format": "Png", "isCircular": False}
            for i, t in enumerate(tokens)
        ]
        res = requests.post(
            "https://thumbnails.roblox.com/v1/batch",
            json=batch,
            timeout=15
        )
        if res.status_code == 200:
            return res.json().get("data", [])
    except:
        pass
    return []

def download_image(url: str):
    try:
        r = requests.get(url, timeout=10)
        return r.content if r.status_code == 200 else None
    except:
        return None

def fetch_avatar_urls(count: int = 50) -> list:
    """Fetch avatar thumbnail URLs from random servers across popular games."""
    urls = []
    print(f"Fetching {count} avatars from popular Roblox games...")

    games = SAMPLE_GAMES.copy()
    random.shuffle(games)

    for place_id in games:
        if len(urls) >= count:
            break
        print(f"  Sampling game {place_id}...", end=" ", flush=True)
        servers = get_servers(place_id)
        if not servers:
            print("no servers found, skipping")
            continue

        # Pick a few random servers
        sampled = random.sample(servers, min(3, len(servers)))
        batch_urls = []
        for server in sampled:
            tokens = server.get("playerTokens", [])
            if not tokens:
                continue
            thumbs = get_thumbnails(tokens)
            for t in thumbs:
                if t.get("state") == "Completed" and t.get("imageUrl"):
                    batch_urls.append(t["imageUrl"])

        random.shuffle(batch_urls)
        urls.extend(batch_urls)
        print(f"got {len(batch_urls)} avatars")
        time.sleep(1)

    # Deduplicate and cap
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)

    return unique[:count]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LABELING SESSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def count_examples():
    return (
        len(list(FLAGGED_DIR.glob("*.png"))),
        len(list(CLEAN_DIR.glob("*.png")))
    )

def label_avatars(urls: list):
    flagged_count, clean_count = count_examples()
    print(f"\nStarting labeling session — {len(urls)} avatars to review")
    print(f"Current library: {flagged_count} flagged, {clean_count} clean\n")
    print("Controls:")
    print("  b = bad (inappropriate) — flag it")
    print("  g = good (clean)        — save as clean")
    print("  s = skip")
    print("  q = quit and save progress\n")
    print("━" * 50)

    labeled = 0
    for i, url in enumerate(urls):
        print(f"\n[{i+1}/{len(urls)}] Opening avatar...")
        open_url(url)

        while True:
            answer = input(f"  [{i+1}/{len(urls)}] b / g / s / q: ").strip().lower()
            close_browser_tab()

            if answer == "q":
                flagged_count, clean_count = count_examples()
                print(f"\nStopped. Library now: {flagged_count} flagged, {clean_count} clean")
                return

            elif answer == "s":
                print("  Skipped.")
                break

            elif answer in ("b", "g"):
                img_data = download_image(url)
                if not img_data:
                    print("  Could not download image, skipping.")
                    break
                timestamp = int(time.time())
                if answer == "b":
                    path = FLAGGED_DIR / f"flagged_{timestamp}_{i}.png"
                    path.write_bytes(img_data)
                    print(f"  Saved as FLAGGED ✓")
                else:
                    path = CLEAN_DIR / f"clean_{timestamp}_{i}.png"
                    path.write_bytes(img_data)
                    print(f"  Saved as CLEAN ✓")
                labeled += 1
                break

            else:
                print("  Type b, g, s, or q")

    flagged_count, clean_count = count_examples()
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Session complete! Labeled {labeled} avatars.")
    print(f"Training library: {flagged_count} flagged, {clean_count} clean")
    if flagged_count >= 3 and clean_count >= 3:
        print("AI auto mode is unlocked. You can now run mod.py or scanner.py.")
    else:
        still_need = max(0, 3 - flagged_count) + max(0, 3 - clean_count)
        print(f"Need {still_need} more labeled avatars to unlock AI auto mode.")
        print("Run prep.py again to label more.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  roblox-auto-mod — Prep Training Session")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("\nThis script fetches real Roblox avatars for you to label.")
print("No game ID or cookie needed — it uses popular public games.")
print("\nTip: aim for at least 20-30 of each type for good accuracy.")
print("You can run this as many times as you want to build up examples.\n")

try:
    raw = input("How many avatars do you want to review? (default 50): ").strip()
    count = int(raw) if raw.isdigit() else 50
except:
    count = 50

urls = fetch_avatar_urls(count)

if not urls:
    print("\nCould not fetch any avatars. Check your internet connection.")
else:
    print(f"\nFetched {len(urls)} avatars. Starting labeling session...")
    label_avatars(urls)
