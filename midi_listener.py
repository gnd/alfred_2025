import mido, threading

class MidiListener(threading.Thread):
    def __init__(self, main_app, name, port_name: str | None = None):
        super().__init__(daemon=True)
        print("[midi] Starting listener ...")

        # The main app
        self.main_app = main_app
        self.name = name

        # MIDI ports
        self.inport = None
        self.outport = None
        
        # Various vars
        self.controls = {}
        self.led_state = {}

        # Connect to MIDI
        try:
            self.inport = mido.open_input(port_name, callback=self._handle)
            self.outport = mido.open_output(port_name) 
        except:
            print("[midi] Warning: Can't open MIDI.")
        self._closed = False

        # Reset all notes - for note numbers see below
        # Only if main app is lil_drama (not strobe)
        if (self.name == "lil_drama"):
            notes = [1, 3, 4, 6, 7, 9, 10, 13, 16, 19, 21, 22, 24]
            for note in notes:
                self.led_state[note] = False
                self._set_led(note, False)

    def stop(self):
        print("[midi] Cleaning up ...")
        if not self._closed:
            if self.outport:
                for note in self.led_state:
                    self._set_led(note, 0)
            if self.inport:        
                self.inport.close()
            if self.outport:
                self.outport.close()
            self._closed = True

    def _set_led(self, note, state: bool):
        vel = 127 if state else 0
        self.outport.send(mido.Message('note_on', note=note, velocity=vel))

    def _handle(self, msg):
        if msg.type == 'note_on' and msg.velocity > 0:
            note = msg.note
            #print(note)
            if note == 1:
                self.main_app.toggle_deathmatch()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 3:
                self.main_app.deathmatch_kill_all()
            if note == 4:
                self.main_app.toggle_tunnel()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 6:
                self.main_app.gameplay_new_reel()
            if note == 7:
                self.main_app.toggle_gameplay()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 9:
                self.main_app.gameplay_kill_all()
            if note == 10:
                self.main_app.toggle_subtitles()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 13:
                self.main_app.toggle_speech()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 16:
                self.main_app.toggle_character_ai()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 19:
                self.main_app.toggle_wheelofnames()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 21:
                self.main_app.toggle_gameplay_with_strobe()
                self.led_state[24] = True
                self._set_led(24, self.led_state[24])
                self.led_state[7] = True
                self._set_led(7, self.led_state[7])
            if note == 22:
                self.main_app.toggle_secondary_screen()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 24:
                self.main_app.toggle_strobe()
                if (self.name == "lil_drama"):
                    self.led_state[note] = not self.led_state.get(note, False)
                    self._set_led(note, self.led_state[note])
            if note == 18:
                self.main_app.toggle_smrt()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            
        if msg.type == 'control_change':
            cc_num  = int(msg.control)
            cc_val  = int(msg.value)
            #print(f"ccnum {cc_num} cc_val {cc_val}")
            if (cc_num not in self.controls):
                self.controls[cc_num] = 0
            else:
                if cc_num == 19:
                    if (cc_val > self.controls[cc_num]):
                        if self.main_app.deathmatch_proc:
                            self.main_app.deathmatch_new_reel()
                        self.controls[cc_num] = cc_val
                    else:
                        if self.main_app.deathmatch_proc:
                            self.main_app.deathmatch_kill_reel()
                        self.controls[cc_num] = cc_val
                if cc_num == 59:
                    self.main_app.adjust_greenblue((cc_val/127)*255)
                if cc_num == 60:
                    self.main_app.adjust_strobe_freq(cc_val/10)
                if cc_num == 61:
                    self.main_app.adjust_strobe_opacity(cc_val/127)