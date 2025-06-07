import mido, threading

class MidiListener(threading.Thread):
    def __init__(self, lil_drama, port_name: str | None = None):
        super().__init__(daemon=True)
        print("[midi] Starting listener ...")

        # The main app
        self.lil_drama = lil_drama

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
            if note == 1:
                self.lil_drama.toggle_deathmatch()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 3:
                self.lil_drama.deathmatch_kill_all()
            if note == 4:
                self.lil_drama.toggle_tunnel()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 6:
                self.lil_drama.gameplay_new_reel()
            if note == 7:
                self.lil_drama.toggle_gameplay()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 9:
                self.lil_drama.gameplay_kill_all()
            if note == 10:
                self.lil_drama.toggle_subtitles()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 13:
                self.lil_drama.toggle_speech()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 16:
                self.lil_drama.toggle_character_ai()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 19:
                self.lil_drama.toggle_wheelofnames()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 22:
                self.lil_drama.toggle_secondary_screen()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
            if note == 24:
                self.lil_drama.toggle_strobe()
                self.led_state[note] = not self.led_state.get(note, False)
                self._set_led(note, self.led_state[note])
        if msg.type == 'control_change':
            cc_num  = int(msg.control)
            cc_val  = int(msg.value)
            if (cc_num not in self.controls):
                self.controls[cc_num] = 0
            else:
                if cc_num == 19:
                    if (cc_val > self.controls[cc_num]):
                        if self.lil_drama.deathmatch_proc:
                            self.lil_drama.deathmatch_new_reel()
                        self.controls[cc_num] = cc_val
                    else:
                        if self.lil_drama.deathmatch_proc:
                            self.lil_drama.deathmatch_kill_reel()
                        self.controls[cc_num] = cc_val
                if cc_num == 60:
                    self.lil_drama.adjust_strobe_freq(cc_val/10)
                if cc_num == 59:
                    self.lil_drama.adjust_strobe_opacity(cc_val/127)