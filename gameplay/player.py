import os
import subprocess
import random
import time
import socket
from screeninfo import get_monitors

# Configuration
REEL_WIDTH = 600
REEL_ANOMALY = 100
REELS_FOLDER = 'gameplay'
PORT = 6666
HOST = 'localhost'
LOUD = "10"
KILL_TIMEOUT = 3
PLAYER = "mplayer"  # Options: 'mplayer' or 'ffplay'

# List of processes
process_list = []

reel_files = [f for f in os.listdir(REELS_FOLDER) if (f.endswith('sludge.mp4') and f)]
reel_count = len(reel_files)

if reel_count == 0:
    print("No reels found in folder.")
    exit(1)

# Screen dimensions
monitor = get_monitors()[0]
screen_width, screen_height = monitor.width, monitor.height
current_reel_index = 0
main_vid_fullscreen = True

def launch_mainvid(file_path):
    window_title = f"mplayer_0"
    
    cmd = [
        "mplayer",
        "-fs",
        "-xy", "1920,1080",
        "-vo", "x11",
        "-loop", "0",
        "-really-quiet",
        "-noborder",
        "-nomouseinput",
        "-hardframedrop",
        "-double",
        "-nosub",
        # more quiet
        "-af", f"volume=-{LOUD}",
        "-title",
        window_title,
        file_path
    ]

    print(" ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )

    process_list.append(proc)

def launch_player(file_path, index):
    actual_reel_width = REEL_WIDTH

    # open first 3 videos at predetrmined positions
    match current_reel_index:
        case 1:
            pos_x = 0
            pos_y = 780
        case _:
            pos_x = random.randint(0, max(0, screen_width - actual_reel_width))
            pos_y = random.randint(0, max(0, screen_height - 500))
    
    window_title = f"mplayer_{index}"

    cmd = [
        "nice", "-n", "19",
        "mplayer",
        "-xy", str(actual_reel_width),
        "-geometry", f"{pos_x}:{pos_y}",
        "-loop", "0",
        "-really-quiet",
        "-noborder",
        "-nomouseinput",
        # some stuff to speed up
        #"-vo", "xv",
        "-hardframedrop",
        "-double",
        "-nosub",
        # more quiet
        "-af", f"volume=-{LOUD}",
        "-aspect", "4:3",
        "-title",
        window_title,
        file_path
    ]

    print(" ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )

    process_list.append(proc)


def toggle_fullscreen(title, fullscreen):
    if (fullscreen):
        # Remove fullscreen
        wmctrl_cmd = ["wmctrl", "-r", title, "-b", "remove,fullscreen"]
        subprocess.run(wmctrl_cmd, check=True)
    else:
        # Add fullscreen
        wmctrl_cmd = ["wmctrl", "-r", title, "-b", "add,fullscreen"]
        subprocess.run(wmctrl_cmd, check=True)


def move_window(title, x, y, width, height):
    """
    Uses wmctrl to move and resize a window by title.
    """
    try:
        
        # Then make it a bit smaller to make place for other videos
        wmctrl_cmd = ["wmctrl", "-r", title, "-e", f"0,{x},{y},{width},{height}"]
        #print(wmctrl_cmd)
        subprocess.run(wmctrl_cmd, check=True)
        print(f"Moved and resized '{title}' to {x},{y} ({width}x{height})")
    except subprocess.CalledProcessError as e:
        print(f"wmctrl failed: {e}")


def kill_player(proc):
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=KILL_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
        finally:
            proc = None


# Socket server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    launch_mainvid(os.path.join(REELS_FOLDER, 'gameplay.mp4'))

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Player ready. Listening on {HOST}:{PORT} using {PLAYER}...")

    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            command = data.decode().strip()
            if command == 'new':
                print("Launching new process.")
                current_reel_index = (current_reel_index + 1) % reel_count
                match current_reel_index:
                    case 1:
                        toggle_fullscreen("mplayer_0", main_vid_fullscreen)
                        main_vid_fullscreen = not main_vid_fullscreen
                        move_window("mplayer_0", 0, 0, 1920, 780)
                        launch_player(os.path.join(REELS_FOLDER, reel_files[current_reel_index]), current_reel_index)
                        print(f"{len(process_list)} processes running..")                
                    case _:
                        launch_player(os.path.join(REELS_FOLDER, reel_files[current_reel_index]), current_reel_index)
                        print(f"{len(process_list)} processes running..")
            if command == 'kill' and process_list:
                kill_player(process_list.pop())
                if (len(process_list) == 1):
                    toggle_fullscreen("mplayer_0", main_vid_fullscreen)
                    main_vid_fullscreen = not main_vid_fullscreen
                    move_window("mplayer_0", 0, 0, 1920, 1080)
                print("Killing last process.")
                print(f"{len(process_list)} processes left..")
            if command == 'killall':
                print("Killing all processes.")
                while process_list:
                    kill_player(process_list.pop())
                print(f"{len(process_list)} processes left..")
