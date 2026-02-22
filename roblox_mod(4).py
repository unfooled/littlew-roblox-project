import subprocess
import time
import pyautogui
import pydirectinput
pydirectinput.PAUSE = 0
import pytesseract
from PIL import Image, ImageEnhance
import requests
import re
import sys
import os

IS_WINDOWS = sys.platform == "win32"

# ─── Tesseract path (Windows) ─────────────────────────────────────────────────
if IS_WINDOWS:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PLACE_ID = "14662419251"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1475225559318663200/4XO4gkXZZsU85F249qWvLHB-_w1jnzWfeSICRsKdT4VCnKBAp0vQXsf3upGCjl62_MSZ"
GAME_LOAD_WAIT = 25  # slightly longer on Windows

BODYSUIT_KEYWORDS = [
    "bodysuit", "body suit", "catsuit", "latex suit",
    "nude", "nsfw", "naked", "underwear", "lingerie", "belly button"
]

visited_servers = set()
globally_checked_users = set()
# ──────────────────────────────────────────────────────────────────────────────

def focus_roblox():
    """Bring Roblox window to front on Windows"""
    if not IS_WINDOWS:
        return
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle("Roblox")
        if windows:
            win = windows[0]
            win.restore()
            win.activate()
            time.sleep(1.5)
            print("  Roblox window focused!")
        else:
            print("  Could not find Roblox window - is the game open?")
    except Exception as e:
        print(f"  Could not focus Roblox window: {e}")

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
    print("  Focusing Roblox window...")
    focus_roblox()
    time.sleep(1.5)
    print("  Opening ESC menu...")
    # Move mouse to center of screen and click game to ensure focus
    cx, cy = pyautogui.size()[0] // 2, pyautogui.size()[1] // 2
    pyautogui.moveTo(cx, cy)
    time.sleep(0.3)
    pyautogui.click(cx, cy)
    time.sleep(1.5)
    pydirectinput.keyDown("escape")
    time.sleep(0.15)
    pydirectinput.keyUp("escape")
    time.sleep(3.5)
    # Check if ESC menu opened by looking for People tab
    screen = pyautogui.screenshot()
    data = pytesseract.image_to_data(screen, output_type=pytesseract.Output.DICT)
    for i, word in enumerate(data["text"]):
        if "People" in word:
            x = data["left"][i] + data["width"][i] // 2
            y = data["top"][i] + data["height"][i] // 2
            print(f"  Found People tab, clicking...")
            pyautogui.click(x, y)
            time.sleep(2)
            return True
    print("  ESC menu did not open or People tab not found")
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
    if re.match(r'^[0-9a-f]{6,}$', u.lower()):
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
    list_x = int(screen_width * 0.5)
    list_y = int(screen_height * 0.6)
    pyautogui.moveTo(list_x, list_y)
    time.sleep(0.3)
    if IS_WINDOWS:
        import ctypes
        # Send scroll wheel directly via ctypes - much more reliable in games
        MOUSEEVENTF_WHEEL = 0x0800
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, -120 * 3, 0)
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, -120 * 3, 0)
    else:
        pyautogui.scroll(-5)
    time.sleep(1.2)

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
        subprocess.run(["taskkill", "/F", "/IM", "RobloxPlayer.exe"], capture_output=True)
        time.sleep(3)
        # Flush any stray keypresses from the keyboard buffer
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    else:
        subprocess.run(["pkill", "-x", "RobloxPlayer"])
        time.sleep(3)

def process_server(server_id):
    join_server(server_id)

    opened = open_people_tab()
    if not opened:
        print("  Retrying - clicking People tab again...")
        time.sleep(2)
        # Don't press ESC again! Just try to find and click People tab
        screen = pyautogui.screenshot()
        data = pytesseract.image_to_data(screen, output_type=pytesseract.Output.DICT)
        for i, word in enumerate(data["text"]):
            if "People" in word:
                x = data["left"][i] + data["width"][i] // 2
                y = data["top"][i] + data["height"][i] // 2
                pyautogui.click(x, y)
                time.sleep(2)
                opened = True
                break

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
            print(f"  Skipping @{username} (already checked)")
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
            max_players = server.get("maxPlayers", 12)
            if playing == 0:
                print(f"  Skipping empty server {sid}")
                continue
            if playing >= max_players:
                print(f"  Skipping full server {sid} ({playing}/{max_players})")
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
