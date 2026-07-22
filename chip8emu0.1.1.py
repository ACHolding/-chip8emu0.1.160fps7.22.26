# ac_chip8_emu_0_1_1.py
# AC Chip 8 Emu 0.1.1
# Python 3.14+ (also runs on Python 3.10+)

import random
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox


WINDOW_TITLE = "AC Chip 8 Emu 0.1.1"
FPS = 60
CPU_HZ = 700
FRAME_TIME = 1.0 / FPS

DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
HIGH_DISPLAY_WIDTH = 128
HIGH_DISPLAY_HEIGHT = 64
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 320

BLUE_BG = "#001533"
BLUE_TEXT = "#66aaff"
BLACK_BTN = "#000000"
WHITE_TEXT = "#ffffff"

PROFILE_AUTO = "Auto"
PROFILE_CLASSIC = "Classic CHIP-8"
PROFILE_CHIP48 = "CHIP-48"
PROFILE_SCHIP = "Super-CHIP"

FONT_ADDRESS = 0x050
BIG_FONT_ADDRESS = 0x0A0
PROGRAM_ADDRESS = 0x200

# Standard 4x5 CHIP-8 font, stored as five bytes per hexadecimal digit.
FONT_DATA = bytes([
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
])

# Super-CHIP 8x10 font used by Fx30.
BIG_FONT_DATA = bytes([
    0x3C, 0x66, 0xC3, 0xC3, 0xC3, 0xC3, 0xC3, 0xC3, 0x66, 0x3C,
    0x18, 0x38, 0x78, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x7E,
    0x3E, 0x63, 0x03, 0x03, 0x06, 0x0C, 0x18, 0x30, 0x60, 0x7F,
    0x3E, 0x63, 0x03, 0x03, 0x1E, 0x03, 0x03, 0x03, 0x63, 0x3E,
    0x06, 0x0E, 0x1E, 0x36, 0x66, 0xC6, 0xFF, 0x06, 0x06, 0x0F,
    0x7F, 0x60, 0x60, 0x60, 0x7E, 0x03, 0x03, 0x03, 0x63, 0x3E,
    0x1E, 0x30, 0x60, 0x60, 0x7E, 0x63, 0x63, 0x63, 0x63, 0x3E,
    0x7F, 0x63, 0x03, 0x06, 0x06, 0x0C, 0x0C, 0x18, 0x18, 0x18,
    0x3E, 0x63, 0x63, 0x63, 0x3E, 0x63, 0x63, 0x63, 0x63, 0x3E,
    0x3E, 0x63, 0x63, 0x63, 0x63, 0x3F, 0x03, 0x03, 0x06, 0x3C,
    0x18, 0x3C, 0x66, 0xC3, 0xC3, 0xC3, 0xFF, 0xC3, 0xC3, 0xC3,
    0xFC, 0x66, 0x63, 0x66, 0x7C, 0x66, 0x63, 0x63, 0x66, 0xFC,
    0x1E, 0x33, 0x60, 0xC0, 0xC0, 0xC0, 0xC0, 0x60, 0x33, 0x1E,
    0xF8, 0x6C, 0x66, 0x63, 0x63, 0x63, 0x63, 0x66, 0x6C, 0xF8,
    0xFF, 0x63, 0x60, 0x64, 0x7C, 0x64, 0x60, 0x60, 0x63, 0xFF,
    0xFF, 0x63, 0x60, 0x64, 0x7C, 0x64, 0x60, 0x60, 0x60, 0xF0,
])


class Chip8Error(RuntimeError):
    """A readable error raised for malformed or unsupported ROM execution."""


class Chip8:
    def __init__(self):
        self.profile = PROFILE_AUTO
        self.active_profile = PROFILE_CHIP48
        self.rom_data = b""
        self.reset()

    @property
    def width(self):
        return HIGH_DISPLAY_WIDTH if self.high_resolution else DISPLAY_WIDTH

    @property
    def height(self):
        return HIGH_DISPLAY_HEIGHT if self.high_resolution else DISPLAY_HEIGHT

    @property
    def shift_uses_vy(self):
        return self.active_profile == PROFILE_CLASSIC

    @property
    def load_store_increments_i(self):
        return self.active_profile == PROFILE_CLASSIC

    @property
    def jump_uses_vx(self):
        return self.active_profile != PROFILE_CLASSIC

    @property
    def sprites_wrap(self):
        return self.active_profile == PROFILE_CLASSIC

    @property
    def logic_resets_vf(self):
        return self.active_profile == PROFILE_CLASSIC

    def reset(self):
        self.memory = bytearray(4096)
        self.memory[FONT_ADDRESS:FONT_ADDRESS + len(FONT_DATA)] = FONT_DATA
        self.memory[BIG_FONT_ADDRESS:BIG_FONT_ADDRESS + len(BIG_FONT_DATA)] = BIG_FONT_DATA
        self.V = [0] * 16
        self.I = 0
        self.pc = PROGRAM_ADDRESS
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [
            [0] * HIGH_DISPLAY_WIDTH for _ in range(HIGH_DISPLAY_HEIGHT)
        ]
        self.keys = [0] * 16
        self.rpl_flags = [0] * 8
        self.high_resolution = False
        self.running = False
        self.halted = False
        self.loaded = bool(self.rom_data)
        self.display_changed = True

        if self.rom_data:
            self.active_profile = self._detect_profile(self.rom_data)
            end = PROGRAM_ADDRESS + len(self.rom_data)
            self.memory[PROGRAM_ADDRESS:end] = self.rom_data
        else:
            self.active_profile = (
                PROFILE_CHIP48 if self.profile == PROFILE_AUTO else self.profile
            )

    def load_rom(self, data: bytes):
        data = bytes(data)
        if not data:
            raise ValueError("The selected ROM is empty.")
        maximum = len(self.memory) - PROGRAM_ADDRESS
        if len(data) > maximum:
            raise ValueError(
                f"ROM is {len(data)} bytes; this CHIP-8 core supports up to "
                f"{maximum} bytes."
            )
        self.rom_data = data
        self.reset()
        self.running = True

    def set_profile(self, profile):
        if profile not in {
            PROFILE_AUTO, PROFILE_CLASSIC, PROFILE_CHIP48, PROFILE_SCHIP
        }:
            raise ValueError(f"Unknown compatibility profile: {profile}")
        self.profile = profile
        self.reset()

    def _detect_profile(self, data):
        if self.profile != PROFILE_AUTO:
            return self.profile

        classic_score = 0
        chip48_score = 0
        for offset in range(0, len(data) - 1, 2):
            opcode = (data[offset] << 8) | data[offset + 1]
            if opcode in {0x00FB, 0x00FC, 0x00FD, 0x00FE, 0x00FF}:
                return PROFILE_SCHIP
            if opcode & 0xFFF0 == 0x00C0:
                return PROFILE_SCHIP
            if opcode & 0xF0FF in {0xF030, 0xF075, 0xF085}:
                return PROFILE_SCHIP
            if opcode & 0xF00F in {0x8006, 0x800E} and opcode & 0x00F0:
                classic_score += 2
            if opcode & 0xF000 == 0xB000 and opcode & 0x0F00:
                chip48_score += 2

        return PROFILE_CLASSIC if classic_score > chip48_score else PROFILE_CHIP48

    def _require_memory(self, address, size=1):
        if address < 0 or address + size > len(self.memory):
            raise Chip8Error(
                f"ROM accessed memory outside 0x000-0xFFF at 0x{address:04X}."
            )

    def _clear_display(self):
        for row in self.display:
            row[:] = [0] * HIGH_DISPLAY_WIDTH
        self.display_changed = True

    def _set_display_mode(self, high_resolution):
        self.high_resolution = high_resolution
        self._clear_display()

    def _scroll_down(self, amount):
        # Super-CHIP scroll distances are physical high-resolution pixels.
        if not self.high_resolution:
            amount = max(1, amount // 2) if amount else 0
        if amount:
            for y in range(self.height - 1, -1, -1):
                source = y - amount
                for x in range(self.width):
                    self.display[y][x] = self.display[source][x] if source >= 0 else 0
            self.display_changed = True

    def _scroll_horizontal(self, amount):
        if not self.high_resolution:
            amount //= 2
        if amount == 0:
            return
        for y in range(self.height):
            old_row = self.display[y][:self.width]
            for x in range(self.width):
                source = x - amount
                self.display[y][x] = old_row[source] if 0 <= source < self.width else 0
        self.display_changed = True

    def _draw_sprite(self, x_register, y_register, rows):
        origin_x = self.V[x_register] % self.width
        origin_y = self.V[y_register] % self.height
        wide_sprite = rows == 0
        row_count = 16 if wide_sprite else rows
        bytes_per_row = 2 if wide_sprite else 1
        self._require_memory(self.I, row_count * bytes_per_row)
        self.V[0xF] = 0

        for row in range(row_count):
            if wide_sprite:
                sprite = (self.memory[self.I + row * 2] << 8) | self.memory[self.I + row * 2 + 1]
                bit_count = 16
            else:
                sprite = self.memory[self.I + row]
                bit_count = 8

            for bit in range(bit_count):
                if not sprite & (1 << (bit_count - 1 - bit)):
                    continue
                pixel_x = origin_x + bit
                pixel_y = origin_y + row
                if self.sprites_wrap:
                    pixel_x %= self.width
                    pixel_y %= self.height
                elif pixel_x >= self.width or pixel_y >= self.height:
                    continue
                if self.display[pixel_y][pixel_x]:
                    self.V[0xF] = 1
                self.display[pixel_y][pixel_x] ^= 1

        self.display_changed = True

    def step(self):
        if not self.running or self.halted:
            return
        self._require_memory(self.pc, 2)
        instruction_address = self.pc
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2

        nnn = opcode & 0x0FFF
        nn = opcode & 0x00FF
        n = opcode & 0x000F
        x = (opcode >> 8) & 0x0F
        y = (opcode >> 4) & 0x0F
        family = opcode & 0xF000

        if opcode == 0x00E0:
            self._clear_display()
        elif opcode == 0x00EE:
            if not self.stack:
                raise Chip8Error("ROM returned with an empty call stack.")
            self.pc = self.stack.pop()
        elif opcode & 0xFFF0 == 0x00C0:
            self._scroll_down(n)
        elif opcode == 0x00FB:
            self._scroll_horizontal(4)
        elif opcode == 0x00FC:
            self._scroll_horizontal(-4)
        elif opcode == 0x00FD:
            self.halted = True
            self.running = False
        elif opcode == 0x00FE:
            self._set_display_mode(False)
        elif opcode == 0x00FF:
            self._set_display_mode(True)
            self.active_profile = PROFILE_SCHIP
        elif family == 0x0000:
            # 0nnn called RCA 1802 machine code and is safely ignored by
            # modern interpreters.
            pass
        elif family == 0x1000:
            self.pc = nnn
        elif family == 0x2000:
            if len(self.stack) >= 16:
                raise Chip8Error("ROM exceeded the 16-level CHIP-8 call stack.")
            self.stack.append(self.pc)
            self.pc = nnn
        elif family == 0x3000:
            if self.V[x] == nn:
                self.pc += 2
        elif family == 0x4000:
            if self.V[x] != nn:
                self.pc += 2
        elif family == 0x5000 and n == 0:
            if self.V[x] == self.V[y]:
                self.pc += 2
        elif family == 0x6000:
            self.V[x] = nn
        elif family == 0x7000:
            self.V[x] = (self.V[x] + nn) & 0xFF
        elif family == 0x8000:
            vx = self.V[x]
            vy = self.V[y]
            if n == 0x0:
                self.V[x] = vy
            elif n == 0x1:
                self.V[x] = vx | vy
                if self.logic_resets_vf:
                    self.V[0xF] = 0
            elif n == 0x2:
                self.V[x] = vx & vy
                if self.logic_resets_vf:
                    self.V[0xF] = 0
            elif n == 0x3:
                self.V[x] = vx ^ vy
                if self.logic_resets_vf:
                    self.V[0xF] = 0
            elif n == 0x4:
                total = vx + vy
                self.V[x] = total & 0xFF
                self.V[0xF] = 1 if total > 0xFF else 0
            elif n == 0x5:
                self.V[x] = (vx - vy) & 0xFF
                self.V[0xF] = 1 if vx >= vy else 0
            elif n == 0x6:
                value = vy if self.shift_uses_vy else vx
                self.V[x] = value >> 1
                self.V[0xF] = value & 1
            elif n == 0x7:
                self.V[x] = (vy - vx) & 0xFF
                self.V[0xF] = 1 if vy >= vx else 0
            elif n == 0xE:
                value = vy if self.shift_uses_vy else vx
                self.V[x] = (value << 1) & 0xFF
                self.V[0xF] = (value >> 7) & 1
            else:
                self._invalid_opcode(opcode, instruction_address)
        elif family == 0x9000 and n == 0:
            if self.V[x] != self.V[y]:
                self.pc += 2
        elif family == 0xA000:
            self.I = nnn
        elif family == 0xB000:
            if self.jump_uses_vx:
                self.pc = nnn + self.V[x]
            else:
                self.pc = nnn + self.V[0]
        elif family == 0xC000:
            self.V[x] = random.randrange(256) & nn
        elif family == 0xD000:
            self._draw_sprite(x, y, n)
        elif family == 0xE000 and nn == 0x9E:
            key = self.V[x]
            if key < 16 and self.keys[key]:
                self.pc += 2
        elif family == 0xE000 and nn == 0xA1:
            key = self.V[x]
            if key >= 16 or not self.keys[key]:
                self.pc += 2
        elif family == 0xF000:
            self._execute_f_opcode(opcode, instruction_address, x, nn)
        else:
            self._invalid_opcode(opcode, instruction_address)

    def _execute_f_opcode(self, opcode, instruction_address, x, nn):
        if nn == 0x07:
            self.V[x] = self.delay_timer
        elif nn == 0x0A:
            pressed = next((key for key, down in enumerate(self.keys) if down), None)
            if pressed is None:
                self.pc -= 2
            else:
                self.V[x] = pressed
        elif nn == 0x15:
            self.delay_timer = self.V[x]
        elif nn == 0x18:
            self.sound_timer = self.V[x]
        elif nn == 0x1E:
            total = self.I + self.V[x]
            if self.active_profile == PROFILE_CLASSIC:
                self.V[0xF] = 1 if total > 0x0FFF else 0
            self.I = total & 0x0FFF
        elif nn == 0x29:
            self.I = FONT_ADDRESS + (self.V[x] & 0x0F) * 5
        elif nn == 0x30:
            self.I = BIG_FONT_ADDRESS + (self.V[x] & 0x0F) * 10
        elif nn == 0x33:
            self._require_memory(self.I, 3)
            value = self.V[x]
            self.memory[self.I] = value // 100
            self.memory[self.I + 1] = (value // 10) % 10
            self.memory[self.I + 2] = value % 10
        elif nn == 0x55:
            self._require_memory(self.I, x + 1)
            self.memory[self.I:self.I + x + 1] = bytes(self.V[:x + 1])
            if self.load_store_increments_i:
                self.I = (self.I + x + 1) & 0x0FFF
        elif nn == 0x65:
            self._require_memory(self.I, x + 1)
            self.V[:x + 1] = self.memory[self.I:self.I + x + 1]
            if self.load_store_increments_i:
                self.I = (self.I + x + 1) & 0x0FFF
        elif nn == 0x75:
            last = min(x, 7)
            self.rpl_flags[:last + 1] = self.V[:last + 1]
        elif nn == 0x85:
            last = min(x, 7)
            self.V[:last + 1] = self.rpl_flags[:last + 1]
        else:
            self._invalid_opcode(opcode, instruction_address)

    @staticmethod
    def _invalid_opcode(opcode, address):
        raise Chip8Error(f"Unsupported opcode 0x{opcode:04X} at 0x{address:03X}.")

    def tick_timers(self, ticks=1):
        for _ in range(max(0, ticks)):
            if self.delay_timer > 0:
                self.delay_timer -= 1
            if self.sound_timer > 0:
                self.sound_timer -= 1


class ACChip8EmuApp:
    KEY_MAP = {
        "1": 0x1, "2": 0x2, "3": 0x3, "4": 0xC,
        "q": 0x4, "w": 0x5, "e": 0x6, "r": 0xD,
        "a": 0x7, "s": 0x8, "d": 0x9, "f": 0xE,
        "z": 0xA, "x": 0x0, "c": 0xB, "v": 0xF,
    }

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.configure(bg=BLUE_BG)
        self.root.resizable(False, False)

        self.chip8 = Chip8()
        self.profile_var = tk.StringVar(value=PROFILE_AUTO)
        self.error_pending = False

        menubar = tk.Menu(self.root, bg=BLUE_BG, fg=BLUE_TEXT, tearoff=0)

        file_menu = tk.Menu(menubar, tearoff=0, bg=BLUE_BG, fg=BLUE_TEXT)
        file_menu.add_command(label="Open ROM...", command=self.open_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        emu_menu = tk.Menu(menubar, tearoff=0, bg=BLUE_BG, fg=BLUE_TEXT)
        emu_menu.add_command(label="Reset", command=self.reset_emu)
        emu_menu.add_command(label="Run", command=self.run_emu)
        emu_menu.add_command(label="Pause", command=self.pause_emu)
        compatibility_menu = tk.Menu(
            emu_menu, tearoff=0, bg=BLUE_BG, fg=BLUE_TEXT
        )
        for profile in (
            PROFILE_AUTO, PROFILE_CLASSIC, PROFILE_CHIP48, PROFILE_SCHIP
        ):
            compatibility_menu.add_radiobutton(
                label=profile,
                value=profile,
                variable=self.profile_var,
                command=self.change_profile,
            )
        emu_menu.add_cascade(label="Compatibility", menu=compatibility_menu)
        menubar.add_cascade(label="Emulator", menu=emu_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=BLUE_BG, fg=BLUE_TEXT)
        help_menu.add_command(label="Keypad", command=self.show_keypad)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=BLUE_BG,
            highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=(10, 4))

        self.status_var = tk.StringVar(value="Open a .ch8 ROM to begin")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=BLUE_BG,
            fg=BLUE_TEXT,
            anchor="w",
        ).pack(fill="x", padx=10)

        btn_frame = tk.Frame(self.root, bg=BLUE_BG)
        btn_frame.pack(pady=7)

        self.btn_run = tk.Button(
            btn_frame, text="Run", command=self.run_emu,
            bg=BLACK_BTN, fg=WHITE_TEXT, width=8,
        )
        self.btn_run.grid(row=0, column=0, padx=5)

        self.btn_pause = tk.Button(
            btn_frame, text="Pause", command=self.pause_emu,
            bg=BLACK_BTN, fg=WHITE_TEXT, width=8,
        )
        self.btn_pause.grid(row=0, column=1, padx=5)

        self.btn_reset = tk.Button(
            btn_frame, text="Reset", command=self.reset_emu,
            bg=BLACK_BTN, fg=WHITE_TEXT, width=8,
        )
        self.btn_reset.grid(row=0, column=2, padx=5)

        self.root.bind_all("<KeyPress>", self.key_down)
        self.root.bind_all("<KeyRelease>", self.key_up)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        self.last_time = time.perf_counter()
        self.cpu_accumulator = 0.0
        self.timer_accumulator = 0.0
        self.draw_accumulator = 0.0
        self.sound_was_active = False
        self.draw_display()
        self.root.after(0, self.main_loop)

    def draw_display(self):
        self.canvas.delete("all")
        scale_x = CANVAS_WIDTH // self.chip8.width
        scale_y = CANVAS_HEIGHT // self.chip8.height
        scale = min(scale_x, scale_y)
        for y in range(self.chip8.height):
            for x in range(self.chip8.width):
                if self.chip8.display[y][x]:
                    self.canvas.create_rectangle(
                        x * scale,
                        y * scale,
                        (x + 1) * scale,
                        (y + 1) * scale,
                        fill=BLUE_TEXT,
                        outline=BLUE_TEXT,
                    )
        self.chip8.display_changed = False

    def main_loop(self):
        now = time.perf_counter()
        dt = min(now - self.last_time, 0.1)
        self.last_time = now

        if self.chip8.running:
            self.cpu_accumulator += dt
            self.timer_accumulator += dt
            cycle_time = 1.0 / CPU_HZ
            cycles = min(int(self.cpu_accumulator / cycle_time), 100)
            if cycles:
                self.cpu_accumulator -= cycles * cycle_time
            try:
                for _ in range(cycles):
                    self.chip8.step()
                    if not self.chip8.running:
                        break

                timer_ticks = int(self.timer_accumulator / FRAME_TIME)
                if timer_ticks:
                    self.timer_accumulator -= timer_ticks * FRAME_TIME
                    self.chip8.tick_timers(timer_ticks)
            except (Chip8Error, IndexError) as error:
                self.chip8.running = False
                self.report_emulation_error(str(error))
        else:
            self.cpu_accumulator = 0.0
            self.timer_accumulator = 0.0

        sound_active = self.chip8.sound_timer > 0 and self.chip8.running
        if sound_active and not self.sound_was_active:
            self.root.bell()
        self.sound_was_active = sound_active

        self.draw_accumulator += dt
        if self.draw_accumulator >= FRAME_TIME:
            self.draw_accumulator %= FRAME_TIME
            if self.chip8.display_changed:
                self.draw_display()

        self.root.after(1, self.main_loop)

    def open_rom(self):
        path = filedialog.askopenfilename(
            title="Open CHIP-8 ROM",
            filetypes=[
                ("CHIP-8 ROM", "*.ch8"),
                ("Super-CHIP ROM", "*.sc8"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            with open(path, "rb") as rom_file:
                self.chip8.load_rom(rom_file.read())
            self.error_pending = False
            self.reset_timing()
            self.status_var.set(
                f"Running {Path(path).name} — {self.chip8.active_profile}"
            )
        except (OSError, ValueError) as error:
            messagebox.showerror("ROM error", f"Failed to load ROM:\n{error}")

    def reset_timing(self):
        self.last_time = time.perf_counter()
        self.cpu_accumulator = 0.0
        self.timer_accumulator = 0.0

    def reset_emu(self):
        self.chip8.reset()
        self.chip8.running = self.chip8.loaded
        self.error_pending = False
        self.reset_timing()
        if self.chip8.loaded:
            self.status_var.set(f"Reset — {self.chip8.active_profile}")
        else:
            self.status_var.set("Open a .ch8 ROM to begin")

    def run_emu(self):
        if not self.chip8.loaded:
            messagebox.showinfo("No ROM", "Open a .ch8 ROM first.")
            return
        if self.chip8.halted:
            self.reset_emu()
        self.chip8.running = True
        self.reset_timing()
        self.status_var.set(f"Running — {self.chip8.active_profile}")

    def pause_emu(self):
        self.chip8.running = False
        self.status_var.set(f"Paused — {self.chip8.active_profile}")

    def change_profile(self):
        was_loaded = self.chip8.loaded
        self.chip8.set_profile(self.profile_var.get())
        self.chip8.running = was_loaded
        self.error_pending = False
        self.reset_timing()
        if was_loaded:
            self.status_var.set(
                f"Restarted — {self.chip8.active_profile} compatibility"
            )

    def key_down(self, event):
        key = self.KEY_MAP.get(event.keysym.lower())
        if key is not None:
            self.chip8.keys[key] = 1

    def key_up(self, event):
        key = self.KEY_MAP.get(event.keysym.lower())
        if key is not None:
            self.chip8.keys[key] = 0

    def report_emulation_error(self, text):
        self.status_var.set("Paused because the ROM hit an emulation error")
        if not self.error_pending:
            self.error_pending = True
            self.root.after_idle(
                lambda: messagebox.showerror("Emulation error", text)
            )

    @staticmethod
    def show_keypad():
        messagebox.showinfo(
            "CHIP-8 Keypad",
            "CHIP-8     Keyboard\n"
            "1 2 3 C     1 2 3 4\n"
            "4 5 6 D     Q W E R\n"
            "7 8 9 E     A S D F\n"
            "A 0 B F     Z X C V",
        )

    @staticmethod
    def show_about():
        messagebox.showinfo(
            "About",
            "AC Chip 8 Emu 0.1.1\n"
            "Python 3.14, 60 Hz timers, 700 Hz CPU.\n"
            "CHIP-8, CHIP-48 and Super-CHIP compatibility.",
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = ACChip8EmuApp(root)
    root.mainloop()
