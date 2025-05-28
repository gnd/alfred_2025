from instagrapi import Client
import requests
import os
import configparser

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    username = config.get('instagram', 'username')
    password = config.get('instagram', 'password')
    thread_name = config.get('instagram', 'thread_name')
    download_folder = config.get('instagram', 'download_folder')
    return username, password, thread_name, download_folder

def login(username, password):
    cl = Client()
    cl.login(username, password)
    return cl

def get_video_url(msg):
    if msg.media_share and hasattr(msg.media_share, 'video_url'):
        return msg.media_share.video_url
    if msg.clip and hasattr(msg.clip, 'video_url'):
        return msg.clip.video_url
    if msg.reel_share and msg.reel_share.media and hasattr(msg.reel_share.media, 'video_url'):
        return msg.reel_share.media.video_url
    return None

def download_reel(url, download_folder, index):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    file_name = os.path.join(download_folder, f"reel_{index}.mp4")
    response = requests.get(url)

    with open(file_name, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded: {file_name}")

def fetch_all_thread_messages(cl, thread_id):
    messages = cl.direct_messages(thread_id, 300)
    print(f"Fetched {len(messages)} messages (latest available).")
    return messages

def fetch_chat_and_download_reels():
    username, password, thread_name, download_folder = load_config()
    cl = login(username, password)

    threads = cl.direct_threads()
    target_thread = next((t for t in threads if t.thread_title == thread_name), None)

    if not target_thread:
        print(f"Thread '{thread_name}' not found.")
        return

    thread_history_file = 'thread.history'

    if not os.path.exists(thread_history_file):
        with open(thread_history_file, 'w') as file:
            file.write('0')

    with open(thread_history_file, 'r') as file:
        previous_message_count = int(file.read().strip())

    thread_messages = fetch_all_thread_messages(cl, target_thread.id)

    reel_messages = [msg for msg in thread_messages if get_video_url(msg) is not None]
    current_message_count = len(reel_messages)

    new_message_count = current_message_count - previous_message_count

    if new_message_count <= 0:
        print("No new video messages to download.")
        return

    print(f"New video messages found: {new_message_count}")

    with open(thread_history_file, 'w') as file:
        file.write(str(current_message_count))

    new_reel_messages = reel_messages[:new_message_count]

    if not new_reel_messages:
        print("No new videos to download.")
        return

    print("Downloading new reels...")
    for index, msg in enumerate(new_reel_messages, start=previous_message_count):
        video_url = get_video_url(msg)
        if video_url:
            download_reel(video_url, download_folder, index)

    print("All new reels downloaded.")

if __name__ == "__main__":
    fetch_chat_and_download_reels()
