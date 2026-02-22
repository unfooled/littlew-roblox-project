import subprocess
import time
import pyautogui
import pytesseract
from PIL import Image, ImageEnhance
import requests
import re
import sys
import os

IS_WINDOWS = sys.platform == "win32"

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PLACE_ID = input("Enter your Roblox Place ID: ").strip()
DISCORD_WEBHOOK = input("Enter your Discord Webhook URL: ").strip()
GAME_LOAD_WAIT = 20

BODYSUIT_KEYWORDS = [
    "bodysuit", "body suit", "catsuit", "latex suit",
    "nude", "nsfw", "naked", "underwear", "lingerie", "belly button"
]

visited_servers = set()
globally_checked_users = set()  # never recheck same user across servers
# ──────────────────────────────────────────────────────────────────────────────

def get_servers():
    url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?limit=100&sortOrder=Desc"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json().get("data", [])
    except Exception as e:
        print(f"  Error fetching servers: {e}")
    return []

def join_server(server_id):
    print(f"\n→ Joining server: {server_id}")
    url = f"roblox://experiences/start?placeId={PLACE_ID}&gameInstanceId={server_id}"
    if IS_WINDOWS:
        os.startfile(url)
    else:
        subprocess.Popen(["open", url])
    print(f"  Waiting {GAME_LOAD_WAIT}s for game to load...")
    time.sleep(GAME_LOAD_WAIT)

def open_people_tab():
    print("  Opening ESC menu...")
    pyautogui.press("escape")
    time.sleep(2)
    screen = pyautogui.screenshot()
    data = pytesseract.image_to_data(screen, output_type=pytesseract.Output.DICT)
    for i, word in enumerate(data["text"]):
        if "People" in word:
            x = data["left"][i] + data["width"][i] // 2
            y = data["top"][i] + data["height"][i] // 2
            pyautogui.click(x, y)
            time.sleep(1.5)
            return True
    print("  Could not find People tab")
    return False

def is_valid_username(u):
    if len(u) < 3 or len(u) > 20:
        return False
    if not re.match(r'^[A-Za-z0-9_]+$', u):
        return False
    garbage = {
        "use", "usernames", "usernanes", "people", "settings", "report",
        "help", "mute", "all", "invite", "connections", "roblox", "captures"
    }
    if u.lower() in garbage:
        return False
    # Filter things that are clearly not usernames (short random letters, server IDs etc)
    if re.match(r'^[0-9a-f]{6,}$', u.lower()):  # hex-like strings
        return False
    return True

def screenshot_and_ocr():
    screen = pyautogui.screenshot()
    enhancer = ImageEnhance.Contrast(screen)
    screen = enhancer.enhance(2.0)
    text = pytesseract.image_to_string(screen)
    return text

def extract_usernames(text):
    found = re.findall(r'@([A-Za-z0-9_]+)', text)
    return [u for u in found if is_valid_username(u)]

def scroll_down_in_menu():
    screen_width, screen_height = pyautogui.size()
    pyautogui.scroll(-3, x=screen_width // 2, y=screen_height // 2)
    time.sleep(1)

def get_user_id(username):
    try:
        res = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username], "excludeBannedUsers": False},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                return data[0]["id"], data[0]["name"]
    except Exception as e:
        print(f"    API error: {e}")
    return None, None

def get_avatar_image_url(user_id):
    try:
        res = requests.get(
            f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false",
            timeout=10
        )
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                return data[0].get("imageUrl")
    except Exception as e:
        print(f"    Thumbnail error: {e}")
    return None

def check_bodysuit(user_id):
    try:
        res = requests.get(
            f"https://avatar.roblox.com/v1/users/{user_id}/avatar",
            timeout=10
        )
        if res.status_code != 200:
            return False, None
        assets = res.json().get("assets", [])
        flagged = []
        for asset in assets:
            name = asset.get("name", "").lower()
            for keyword in BODYSUIT_KEYWORDS:
                if keyword in name:
                    flagged.append(asset.get("name"))
                    break
        if flagged:
            return True, ", ".join(flagged)
        return False, None
    except Exception as e:
        print(f"    Avatar check error: {e}")
        return False, None

def send_discord_alert(username, user_id, server_id, avatar_url, reason):
    profile_url = f"https://www.roblox.com/users/{user_id}/profile"
    try:
        requests.post(DISCORD_WEBHOOK, json={
            "embeds": [{
                "title": f"🚨 NSFW Detected: @{username}",
                "description": f"**Flagged item(s):** {reason}\n**Profile:** {profile_url}\n**Server ID:** `{server_id}`",
                "image": {"url": avatar_url},
                "color": 0xff0000,
                "footer": {"text": f"User ID: {user_id}"}
            }]
        }, timeout=10)
        print(f"  🚨 ALERT sent for @{username} — {reason}")
    except Exception as e:
        print(f"  Webhook error: {e}")

def leave_game():
    print("  Leaving game...")
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/F", "/IM", "RobloxPlayerBeta.exe"], capture_output=True)
    else:
        subprocess.run(["pkill", "-x", "RobloxPlayer"])
    time.sleep(3)

def process_server(server_id):
    join_server(server_id)

    opened = open_people_tab()
    if not opened:
        pyautogui.press("escape")
        time.sleep(1)
        open_people_tab()

    all_usernames = set()
    scroll_attempts = 0

    while scroll_attempts < 2:
        text = screenshot_and_ocr()
        usernames = extract_usernames(text)
        new_usernames = set(usernames) - all_usernames
        if new_usernames:
            print(f"  New usernames: {list(new_usernames)}")
            all_usernames.update(new_usernames)
            scroll_down_in_menu()
            scroll_attempts = 0
        else:
            scroll_attempts += 1
            print(f"  No new usernames, scrolling... ({scroll_attempts}/2)")
            scroll_down_in_menu()

    print(f"\n  Total usernames collected: {list(all_usernames)}")

    for username in all_usernames:
        if username.lower() in globally_checked_users:
            print(f"  Skipping @{username} (already checked before)")
            continue

        print(f"  Checking @{username}...")
        user_id, real_username = get_user_id(username)

        if not user_id:
            print(f"    Not a real user (OCR error likely)")
            continue

        globally_checked_users.add(username.lower())

        avatar_url = get_avatar_image_url(user_id)
        detected, reason = check_bodysuit(user_id)

        if detected and avatar_url:
            send_discord_alert(real_username, user_id, server_id, avatar_url, reason)
        elif detected:
            send_discord_alert(real_username, user_id, server_id, "", reason)
        else:
            print(f"    @{real_username} — clean ✅")

        time.sleep(0.5)

    leave_game()

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
print("\n🚀 Roblox Moderation Scanner started!")
print("⚠️  Don't touch your mouse while it's running!\n")
time.sleep(3)

while True:
    servers = get_servers()
    if not servers:
        print("No servers found, retrying in 30s...")
        time.sleep(30)
        continue

    found_new = False
    for server in servers:
        sid = server["id"]
        if sid not in visited_servers:
            found_new = True
            visited_servers.add(sid)
            playing = server.get("playing", 0)
            if playing == 0:
                print(f"  Skipping empty server {sid}")
                continue
            print(f"\n📡 Server {sid} — {playing} players")
            try:
                process_server(sid)
            except Exception as e:
                print(f"  Error processing server: {e}")
                try:
                    leave_game()
                except:
                    pass
            time.sleep(5)

    if not found_new:
        print("\nAll servers checked! Waiting 5 mins for new ones...")
        time.sleep(300)
