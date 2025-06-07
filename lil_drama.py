# pip install pynput pygame-ce mss screeninfo mido python-rtmidi 
# pip google-cloud-speech google-cloud-texttospeech google-cloud-translate pyaudio six screeninfo termcolor

import os
import sys
import mido
import signal
import socket
import pathlib
import threading
import subprocess
from pynput import keyboard, mouse
from screeninfo import get_monitors

# import submodules
from midi_listener import MidiListener
from desktop_feed.feedback import DesktopFeedback
from meme_deathmatch.player import MemeDeathmatch
from gameplay.player import GameplaySludge
from realtime_subs.display import SubtitleDisplay
from realtime_subs.transcript import SpeechTranslate

HERE = pathlib.Path(__file__).parent

class lil_drama:

	def __init__(self):
		# Subprocesses
		self.deathmatch_proc = None
		self.tunnel_proc = None
		self.subs_proc = None
		self.gameplay_proc = None
		self.subtitle_proc = None
		self.speech_proc = None
		self.ai_proc = None
		self.wheel_proc = None

		# Various vars
		self.host = "127.0.0.1"
		self.deathmatch_port = 6666
		self.gameplay_port = 6667
		self.tunnel_port = 6668
		self.secondary_screen = False

		# Keyboard & Mouse listener
		self.key_listener   = keyboard.GlobalHotKeys({
			# Not needed when using MIDI comntroller
			# 'b': self.deathmatch_kill_reel,
			# 'n': self.deathmatch_new_reel,
			# 'v': self.deathmatch_kill_all,
			# 'h': self.gameplay_kill_reel,
			# 'j': self.gameplay_new_reel,
			# 'g': self.gameplay_kill_all,
			# 'r': self.toggle_deathmatch,
			# 't': self.toggle_tunnel,
			# 'y': self.toggle_gameplay,
			# 's': self.toggle_subtitles,
			'q': self.on_exit
        })
		self.mouse_listener = mouse.Listener(
			on_scroll=self.on_scroll,
			on_click =self.on_click,
		)

		# Get screen dimensions
		monitor = get_monitors()[0]
		self.screen_offset = 0
		self.screen_width = monitor.width
		self.screen_height = monitor.height

		# MIDI listener
		port_name = self.open_default_port()
		print(f"Opening {port_name}")
		self.midi = MidiListener(self, port_name)
		self.midi.start()

		# Export Google API key
		os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "realtime_subs/alfred-2021-0b114e37a462.json"

	def open_default_port(self):
	    """Pick the first available MIDI‑IN port (quick & dirty)."""
	    names = mido.get_input_names()
	    if not names:
	        sys.exit("No MIDI input ports detected.")
	    for name in names:
	    	if "MIDI Mix" in name:
	    		return name
	    
	def toggle_secondary_screen(self):
		if self.secondary_screen:
			print("Disabling secondary screen")
			self.secondary_screen = False
			monitor = get_monitors()[0]
			self.screen_offset = 0
			self.screen_width = monitor.width
			self.screen_height = monitor.height
		else:
			print("Enabling secondary screen")
			self.secondary_screen = True
			monitor = get_monitors()[1]
			self.screen_offset = get_monitors()[0].width
			self.screen_width = monitor.width
			self.screen_height = monitor.height
		print(f"width: {self.screen_width}, height: {self.screen_height}")

	def toggle_deathmatch(self):
		if self.deathmatch_proc and self.deathmatch_proc.poll() is None:
			print("Stopping deathmatch ...")
			self.deathmatch_proc.terminate()
		else:
			print("Starting deathmatch ...")
			cmd = [sys.executable, "-m", "meme_deathmatch.player"]
			if self.secondary_screen:
				cmd.append("--secondary")
			self.deathmatch_proc = subprocess.Popen(cmd, cwd=HERE)

	def toggle_tunnel(self):
		if self.tunnel_proc and self.tunnel_proc.poll() is None:
			print("Stopping tunnel ...")
			self.tunnel_proc.kill()
		else:
			print("Starting tunnel ...")
			cmd = [sys.executable, "-m", "desktop_feed.feedback"]
			if self.secondary_screen:
				cmd.append("--secondary")
			self.tunnel_proc = subprocess.Popen(cmd, cwd=HERE)

	def toggle_gameplay(self):
		if self.gameplay_proc and self.gameplay_proc.poll() is None:
			print("Stopping gameplay ...")
			self.gameplay_proc.terminate()
		else:
			print("Starting gameplay ...")
			cmd = [sys.executable, "-m", "gameplay.player"]
			if self.secondary_screen:
				cmd.append("--secondary")
			self.gameplay_proc = subprocess.Popen(cmd, cwd=HERE)

	def toggle_subtitles(self):
		if self.subtitle_proc and self.subtitle_proc.poll() is None:
			print("Stopping subtitles ...")
			self.subtitle_proc.terminate()
		else:
			print("Starting subtitles ...")
			cmd = [sys.executable, "-m", "realtime_subs.display"]
			if self.secondary_screen:
				cmd.append("--secondary")
			self.subtitle_proc = subprocess.Popen(cmd, cwd=HERE)

	def toggle_speech(self):
		if self.speech_proc and self.speech_proc.poll() is None:
			print("Stopping speech-translate ...")
			self.speech_proc.terminate()
		else:
			print("Starting speech-translate ...")
			cmd = [sys.executable, "-m", "realtime_subs.transcript"]
			self.speech_proc = subprocess.Popen(cmd, cwd=HERE)

	def toggle_character_ai(self):
		if self.ai_proc and self.ai_proc.poll() is None:
			print("Stopping character.ai ...")
			self.ai_proc.terminate()
		else:
			print("Starting character.ai ...")
			self.ai_proc = self.start_chrome("https://character.ai", self.screen_width, 780, self.screen_offset)
		
	def toggle_wheelofnames(self):
		if self.wheel_proc and self.wheel_proc.poll() is None:
			print("Stopping Wheel Of Names ...")
			self.wheel_proc.terminate()
		else:
			print("Starting Wheel Of Names ...")
			self.wheel_proc = self.start_chrome("https://wheelofnames.com", self.screen_width, self.screen_height, self.screen_offset)

	def deathmatch_new_reel(self):
		self._send_async(self.deathmatch_port, b"new\n")

	def deathmatch_kill_reel(self):
		self._send_async(self.deathmatch_port, b"kill\n")

	def deathmatch_kill_all(self):
		self._send_async(self.deathmatch_port, b"killall\n")

	def gameplay_new_reel(self):
		self._send_async(self.gameplay_port, b"new\n")

	def gameplay_kill_reel(self):
		self._send_async(self.gameplay_port, b"kill\n")

	def gameplay_kill_all(self):
		self._send_async(self.gameplay_port, b"killall\n")

	def on_scroll(self, x, y, dx, dy):
		if   dy > 0: self._send_async(self.deathmatch_port, b"new\n")
		elif dy < 0: self._send_async(self.deathmatch_port, b"kill\n")

	def on_click(self, x, y, button, pressed):
		if button is mouse.Button.middle and not pressed:
			self._send_async(self.deathmatch_port, b"killall\n")

	def _send_async(self, port, payload: bytes):
		threading.Thread(target=self._send_worker, args=(port, payload), daemon=True).start()

	def _send_worker(self, port, payload: bytes):
		try:
			with socket.create_connection((self.host, port), timeout=1) as sock:
				sock.sendall(payload)
		except OSError as err:
			print(f"Connection failed: {err}")

	def start_chrome(self, url, width, height, offset):
		chromium = "/snap/bin/chromium"
		cmd = [
    		chromium,
		    f"--app={url}",
		    f"--window-size={width},{height}",
		    f"--window-position={offset},0",
		    "--disable-translate",
		    "--disable-infobars",
		    "--disable-features=TranslateUI",
		    "--no-first-run"
		]
		return subprocess.Popen(cmd)

	def on_exit(self):
		print("Received command to quit.")
		if self.midi:
			print("Stopping MIDI listener ...")
			self.midi.stop()
		if self.deathmatch_proc:
			print("Terminating deathmatch ...")
			self.deathmatch_proc.terminate()
		if self.tunnel_proc:
			print("Killing tunnel ...")
			self.tunnel_proc.kill()
		if self.gameplay_proc:
			print("Killing gameplay ...")
			self.gameplay_proc.kill()
		if self.subtitle_proc:
			print("Terminating subtitles ...")
			self.subtitle_proc.terminate()
		if self.speech_proc:
			print("Terminating speech-translate ...")
			self.speech_proc.terminate()
		print("Quitting ...")
		sys.exit(0)

	def run(self):
		self.key_listener.start()
		self.mouse_listener.start()
		try:
			self.key_listener.join()
		finally:
			self.mouse_listener.stop()

# Lil Drama
if __name__ == "__main__":
    lil_drama().run()