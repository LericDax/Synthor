import tkinter as tk
from tkinter import ttk
import pygame
import numpy as np
from enum import Enum
from scipy.signal import sawtooth, square

# Initialize Pygame for sound
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Constants
SAMPLE_RATE = 44100
MAX_VOLUME = 32767
NUM_VOICES = 8  # Number of polyphonic voices

# Waveform and Noise Types
class Waveform(Enum):
    SINE = 'sine'
    SAWTOOTH = 'sawtooth'
    TRIANGLE = 'triangle'
    SQUARE = 'square'
    PULSE = 'pulse'
    NOISE_WHITE = 'white'
    NOISE_PINK = 'pink'
    NOISE_BROWN = 'brown'
    # ... other noise colors

# Oscillator class
class Oscillator:
    def __init__(self, waveform=Waveform.SINE):
        self.waveform = waveform
        self.active = True  # Oscillator is active by default

    def generate_wave(self, frequency, duration):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)

        if not self.active:
            return np.zeros(int(SAMPLE_RATE * duration))

        if self.waveform == Waveform.SINE:
            return np.sin(frequency * t * 2 * np.pi)
        elif self.waveform == Waveform.SAWTOOTH:
            return sawtooth(2 * np.pi * frequency * t)
        elif self.waveform == Waveform.TRIANGLE:
            return 2 * np.abs(sawtooth(2 * np.pi * frequency * t, width=0.5)) - 1
        elif self.waveform == Waveform.SQUARE:
            return square(2 * np.pi * frequency * t)
        elif self.waveform == Waveform.PULSE:
            return square(2 * np.pi * frequency * t, duty=0.1)
        elif self.waveform == Waveform.NOISE_WHITE:
            return np.random.normal(0, 1, int(SAMPLE_RATE * duration))
        else:
            return np.zeros(int(SAMPLE_RATE * duration))

# Polyphony and Gating
class SynthPolyphony:
    def __init__(self):
        self.channels = [pygame.mixer.Channel(i) for i in range(NUM_VOICES)]
        self.active_notes = {}  # Format: {key: channel_index}

    def play_sound(self, sound_array, key):
        stereo_sound_array = np.int16(np.column_stack([sound_array, sound_array]) * MAX_VOLUME)
        sound = pygame.sndarray.make_sound(stereo_sound_array)
        available_channel = next((ch for ch in self.channels if not ch.get_busy()), self.channels[0])
        available_channel.play(sound)
        self.active_notes[key] = available_channel
        print(f"Playing sound for key: {key}")  # Debug

    def stop_sound(self, key):
        if key in self.active_notes:
            self.active_notes[key].stop()
            del self.active_notes[key]
            print(f"Stopped sound for key: {key}")  # Debug

# Frequency mappings for keys (octaves)
key_frequencies = {
    'q': 261.63, 'w': 277.18, 'e': 293.66, 'r': 311.13, 't': 329.63, 'y': 349.23, 'u': 369.99, 'i': 392.00, 'o': 415.30, 'p': 440.00,
    'a': 220.00, 's': 233.08, 'd': 246.94, 'f': 261.63, 'g': 277.18, 'h': 293.66, 'j': 311.13, 'k': 329.63, 'l': 349.23, ';': 369.99, "'": 392.00,
    'z': 174.61, 'x': 185.00, 'c': 196.00, 'v': 207.65, 'b': 220.00, 'n': 233.08, 'm': 246.94, ',': 261.63, '.': 277.18, '/': 293.66
}

# Main Application Class
class SynthesizerApp:
    def __init__(self, master):
        self.master = master
        master.title("Advanced Synthesizer")
        self.oscillators = [Oscillator() for _ in range(3)]
        self.synth_polyphony = SynthPolyphony()
        self.oscillator_waveform_vars = [tk.StringVar(master) for _ in range(3)]
        self.create_widgets()

    def create_widgets(self):
        waveform_options = [wf.name for wf in Waveform] + ['OFF']

        # Create dropdowns and labels for oscillators
        for i, osc_var in enumerate(self.oscillator_waveform_vars):
            label = tk.Label(self.master, text=f'Oscillator {i+1}')
            label.grid(row=i, column=0)
            osc_menu = ttk.Combobox(self.master, textvariable=osc_var, values=waveform_options, state="readonly")
            osc_menu.current(0)
            osc_menu.grid(row=i, column=1)
            osc_menu.bind('<<ComboboxSelected>>', lambda event, index=i: self.update_oscillator_waveform(index, osc_var.get()))

        self.master.bind("<KeyPress>", self.on_key_press)
        self.master.bind("<KeyRelease>", self.on_key_release)

    def update_oscillator_waveform(self, index, waveform_name):
        if waveform_name == 'OFF':
            self.oscillators[index].active = False
        else:
            self.oscillators[index].waveform = Waveform[waveform_name]
            self.oscillators[index].active = True
        print(f"Oscillator {index + 1} set to {waveform_name}")  # Debug

    def on_key_press(self, event):
        key = event.char.lower()
        print(f"Key pressed: {key}")  # Debug
        if key not in self.synth_polyphony.active_notes and key in key_frequencies:
            sound = self.generate_sound(key)
            self.synth_polyphony.play_sound(sound, key)

    def on_key_release(self, event):
        key = event.char.lower()
        print(f"Key released: {key}")  # Debug
        if key in self.synth_polyphony.active_notes:
            self.synth_polyphony.stop_sound(key)

    def generate_sound(self, key):
        frequency = key_frequencies[key]
        duration = 1  # Duration in seconds for each note
        waves = [osc.generate_wave(frequency, duration) for osc in self.oscillators]
        combined_wave = np.sum(waves, axis=0) / len(self.oscillators)  # Mix the waves
        return combined_wave

# Main Synthesizer Setup
if __name__ == "__main__":
    root = tk.Tk()
    app = SynthesizerApp(root)
    root.mainloop()
