import socket
from pynput import keyboard

HOST = 'localhost'
PORT = 6666

def on_press(key):
    try:
        if key.char == 'n' or key.char == '2':
            conn.sendall(b'new\n')
        if key.char == 'b' or key.char == '1':
            conn.sendall(b'kill\n')
        if key.char == 'm' or key.char == '0':
            conn.sendall(b'killall\n')
    except AttributeError:
        pass  # Ignore special keys

# Connect to the player socket
try:
    conn = socket.create_connection((HOST, PORT))
    print(f"Controller connected to {HOST}:{PORT}")
except ConnectionRefusedError:
    print("Could not connect to the player. Make sure player.py is running.")
    exit(1)

# Start keyboard listener
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()