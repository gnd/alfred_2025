import mido, threading

class MidiListener(threading.Thread):
    def __init__(self, lil_drama, port_name: str | None = None):
        super().__init__(daemon=True)
        print("[midi] Starting listener ...")

        # The main app
        self.lil_drama = lil_drama

        # Connect to MIDI
        self.port = mido.open_input(port_name, callback=self._handle)
        
        # Various vars
        self.controls = {}

    def _handle(self, msg):
        if msg.type == 'note_on' and msg.velocity > 0:
            note = msg.note
            if note == 1:
                self.lil_drama.toggle_deathmatch()
            if note == 3:
                self.lil_drama.deathmatch_kill_all()
            if note == 4:
                self.lil_drama.toggle_tunnel()
            if note == 6:
                self.lil_drama.gameplay_new_reel()
            if note == 7:
                self.lil_drama.toggle_gameplay()
            if note == 9:
                self.lil_drama.gameplay_kill_all()
        if msg.type == 'control_change':
            cc_num  = int(msg.control)
            cc_val  = int(msg.value)
            print(f"cnt change: {cc_num} {cc_val}")
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
                # if cc_num == 27:
                #     if (int(cc_val/10) >= self.controls[cc_num]):
                #         if self.lil_drama.gameplay_proc:
                #             self.lil_drama.gameplay_new_reel()
                #         self.controls[cc_num] = int(cc_val/10)
                #     else:
                #         if self.lil_drama.gameplay_proc:
                #             self.lil_drama.gameplay_kill_reel()
                #         self.controls[cc_num] = int(cc_val/10)