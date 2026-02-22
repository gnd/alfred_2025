import socket
from pynput import keyboard
from pynput import mouse 

HOST = 'localhost'
PORT = 6667

try:
    conn = socket.create_connection((HOST, PORT))
    print(f"Controller connected to {HOST}:{PORT}")
except ConnectionRefusedError:
    print("Could not connect to the player. Make sure player.py is running.")
    exit(1)

# handle keyboard keys pressed
def on_press(key):
    try:
        if key.char in ('n', '2'):
            conn.sendall(b'new\n')
        elif key.char in ('b', '1'):
            conn.sendall(b'kill\n')
        elif key.char in ('v', '0'):
            conn.sendall(b'killall\n')
    except AttributeError:
        # special keys (Ctrl, Alt …) don’t have .char
        pass

# handle mouse scrolling
def on_scroll(x, y, dx, dy):
    if dy > 0:
        conn.sendall(b'new\n')
    elif dy < 0:
        conn.sendall(b'kill\n')

# handle mouse clicks
def on_click(x, y, button, pressed):
    if button is mouse.Button.middle:
        if pressed:
            pass
        else:
            conn.sendall(b'killall\n')


# start both listeners in parallel threads
keyboard_listener = keyboard.Listener(on_press=on_press, daemon=True)
mouse_listener    = mouse.Listener(on_scroll=on_scroll, on_click=on_click, daemon=True)
keyboard_listener.start()
mouse_listener.start()

# join main
keyboard_listener.join()
mouse_listener.join()