import os
import subprocess
import random
import time
import socket
from screeninfo import get_monitors

# Configuration
REEL_WIDTH = 600
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
reel_files.sort()
print(reel_files)

if reel_count == 0:
    print("No reels found in folder.")
    exit(1)

# Screen dimensions
monitor = get_monitors()[0]
screen_width, screen_height = monitor.width, monitor.height
current_reel_index = 0
main_vid_fullscreen = True

# Video dimensions
width_half = int(screen_width / 2)
width_smaller = int(screen_width / 2.66666)
height_half = int(screen_height / 2)

def launch_mainvid(file_path):
    window_title = f"mplayer_main"
    
    cmd = [
        "mplayer",
        "-fs",
        "-xy", f"{screen_width},{screen_height}",
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

def launch_sidevid(file_path, index, x, y, width, height):
    window_title = f"mplayer_{index}"

    cmd = [
        "nice", "-n", "19",
        "mplayer",
        "-xy", f"{width},{height}",
        "-geometry", f"{x}:{y}",
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
                match len(process_list):
                    # Second video layer
                    case 1:
                        launch_sidevid(os.path.join(REELS_FOLDER, reel_files[current_reel_index]), current_reel_index, 0, 0, width_smaller, screen_height)
                        print(f"{len(process_list)} processes running..")
                    # Third video layer
                    case 2:
                        toggle_fullscreen("mplayer_main", main_vid_fullscreen)
                        main_vid_fullscreen = not main_vid_fullscreen
                        move_window("mplayer_main", width_half, 0, width_half, 1080)
                        move_window("mplayer_0", 0, 0, width_half, height_half)
                        # launch third video
                        launch_sidevid(os.path.join(REELS_FOLDER, reel_files[current_reel_index]), current_reel_index, 0, height_half, width_half, height_half)
                        print(f"{len(process_list)} processes running..")
                    # All others
                    case _:
                        pos_x = random.randint(0, max(0, screen_width - REEL_WIDTH))
                        pos_y = random.randint(0, max(0, screen_height - 500))
                        launch_sidevid(os.path.join(REELS_FOLDER, reel_files[current_reel_index]), current_reel_index, pos_x, pos_y, REEL_WIDTH, 0)
                        print(f"{len(process_list)} processes running..")
                # increase reel index
                current_reel_index = (current_reel_index + 1) % reel_count
            if command == 'kill' and process_list:
                kill_player(process_list.pop())
                if (len(process_list) == 1):
                    toggle_fullscreen("mplayer_main", main_vid_fullscreen)
                    main_vid_fullscreen = not main_vid_fullscreen
                    move_window("mplayer_main", 0, 0, screen_width, screen_height)
                print("Killing last process.")
                print(f"{len(process_list)} processes left..")
            if command == 'killall':
                print("Killing all processes.")
                while process_list:
                    kill_player(process_list.pop())
                print(f"{len(process_list)} processes left..")
