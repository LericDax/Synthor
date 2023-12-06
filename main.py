import tkinter as tk
from tkinter import ttk
import pygame
import numpy as np
from enum import Enum
from scipy.signal import butter, lfilter, sawtooth, square

# Initialize Pygame for sound
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Constants
SAMPLE_RATE = 44100
MAX_VOLUME = 32767
NUM_VOICES = 8

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

# Filter Class
class Filter:
    def __init__(self, cutoff_frequency=1000):
        self.type = 'lowpass'  # Default filter type
        self.cutoff_frequency = cutoff_frequency  # Default cutoff frequency
        self.order = 2  # Filter order

    def butter_filter(self, cutoff, fs, order, filter_type):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype=filter_type, analog=False)
        return b, a

    def apply_filter(self, waveform):
        b, a = self.butter_filter(self.cutoff_frequency, SAMPLE_RATE, self.order, self.type)
        filtered_waveform = lfilter(b, a, waveform)
        return filtered_waveform

# LFO Class
class LFO:
    def __init__(self, rate=1):
        self.waveform = Waveform.SINE  # Default LFO waveform
        self.rate = rate  # Default rate in Hz

    def generate_lfo_wave(self, duration, rate):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        if self.waveform == Waveform.SINE:
            return np.sin(2 * np.pi * rate * t)
        # ... other waveform conditions
        return np.ones_like(t)  # Default to no modulation

    def apply_lfo(self, waveform, duration):
        lfo_wave = self.generate_lfo_wave(duration, self.rate)
        return waveform * lfo_wave

# Oscillator Class
class Oscillator:
    def __init__(self, waveform=Waveform.SINE):
        self.waveform = waveform
        self.active = True
        self.filter = Filter()
        self.lfo = LFO()

    def generate_wave(self, frequency, duration):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        if not self.active:
            return np.zeros(int(SAMPLE_RATE * duration))

        # Generate waveform based on selected type and frequency
        if self.waveform == Waveform.SINE:
            wave = np.sin(frequency * t * 2 * np.pi)
        elif self.waveform == Waveform.SAWTOOTH:
            wave = sawtooth(2 * np.pi * frequency * t)
        elif self.waveform == Waveform.TRIANGLE:
            wave = 2 * np.abs(sawtooth(2 * np.pi * frequency * t, width=0.5)) - 1
        elif self.waveform == Waveform.SQUARE:
            wave = square(2 * np.pi * frequency * t)
        elif self.waveform == Waveform.PULSE:
            wave = square(2 * np.pi * frequency * t, duty=0.1)
        elif self.waveform == Waveform.NOISE_WHITE:
            wave = np.random.normal(0, 1, int(SAMPLE_RATE * duration))
        else:
            wave = np.zeros(int(SAMPLE_RATE * duration))

        # Apply LFO and filter
        wave = self.lfo.apply_lfo(wave, duration)
        wave = self.filter.apply_filter(wave)

        return wave

# SynthPolyphony Class
class SynthPolyphony:
    def __init__(self):
        self.channels = [pygame.mixer.Channel(i) for i in range(NUM_VOICES)]
        self.active_notes = {}

    def play_sound(self, sound_array, key):
        stereo_sound_array = np.int16(np.column_stack([sound_array, sound_array]) * MAX_VOLUME)
        sound = pygame.sndarray.make_sound(stereo_sound_array)
        available_channel = next((ch for ch in self.channels if not ch.get_busy()), self.channels[0])
        available_channel.play(sound)
        self.active_notes[key] = available_channel

    def stop_sound(self, key):
        if key in self.active_notes:
            self.active_notes[key].stop()
            del self.active_notes[key]

# Frequency Mappings for Keys
key_frequencies = {
    # High keys (Q to P)
    'q': 1046.50, 'w': 1108.73, 'e': 1174.66, 'r': 1244.51, 't': 1318.51, 'y': 1396.91, 'u': 1479.98, 'i': 1567.98, 'o': 1661.22, 'p': 1760.00,
    # Mid keys (A to L)
    'a': 880.00, 's': 932.33, 'd': 987.77, 'f': 1046.50, 'g': 1108.73, 'h': 1174.66, 'j': 1244.51, 'k': 1318.51, 'l': 1396.91,
    # Bass keys (Z to M)
    'z': 440.00, 'x': 466.16, 'c': 493.88, 'v': 523.25, 'b': 554.37, 'n': 587.33, 'm': 622.25
}

# Synthesizer Application Class
class SynthesizerApp:
    def __init__(self, master):
        self.master = master
        master.title("Advanced Synthesizer")
        self.oscillators = [Oscillator() for _ in range(3)]
        self.synth_polyphony = SynthPolyphony()
        self.oscillator_waveform_vars = [tk.StringVar(master) for _ in range(3)]
        self.filter_cutoff_vars = [tk.DoubleVar(master, value=1000) for _ in range(3)]  # For filter cutoffs
        self.lfo_rate_vars = [tk.DoubleVar(master, value=1) for _ in range(3)]  # For LFO rates
        self.create_widgets()

    def create_widgets(self):
        waveform_options = [wf.name for wf in Waveform] + ['OFF']
        filter_options = ['lowpass', 'highpass', 'bandpass', 'notch']
        lfo_waveform_options = [wf.name for wf in Waveform]

        # Creating widgets for each oscillator
        for i in range(3):
            # Oscillator Waveform Selection
            osc_waveform_label = tk.Label(self.master, text=f'Oscillator {i+1} Waveform')
            osc_waveform_label.grid(row=i, column=0)
            osc_waveform_menu = ttk.Combobox(self.master, textvariable=self.oscillator_waveform_vars[i], values=waveform_options, state="readonly")
            osc_waveform_menu.current(0)
            osc_waveform_menu.grid(row=i, column=1)
            osc_waveform_menu.bind('<<ComboboxSelected>>', lambda event, index=i: self.update_oscillator_waveform(index, self.oscillator_waveform_vars[index].get()))

            # Filter Cutoff Frequency Slider
            filter_cutoff_slider = tk.Scale(self.master, from_=20, to=20000, orient='horizontal', label='Filter Cutoff', variable=self.filter_cutoff_vars[i])
            filter_cutoff_slider.grid(row=i, column=2)
            filter_cutoff_slider.bind('<Motion>', lambda event, index=i: self.update_filter_cutoff(index, self.filter_cutoff_vars[index].get()))

            # LFO Rate Slider
            lfo_rate_slider = tk.Scale(self.master, from_=0.1, to=10, orient='horizontal', label='LFO Rate', variable=self.lfo_rate_vars[i])
            lfo_rate_slider.grid(row=i, column=3)
            lfo_rate_slider.bind('<Motion>', lambda event, index=i: self.update_lfo_rate(index, self.lfo_rate_vars[index].get()))

            # Filter Type Selection
            filter_type_label = tk.Label(self.master, text=f'Filter {i+1} Type')
            filter_type_label.grid(row=i, column=4)
            filter_type_menu = ttk.Combobox(self.master, values=filter_options, state="readonly")
            filter_type_menu.current(0)
            filter_type_menu.grid(row=i, column=5)
            filter_type_menu.bind('<<ComboboxSelected>>', lambda event, index=i: self.update_filter_type(index, filter_type_menu.get()))

            # LFO Waveform Selection
            lfo_waveform_label = tk.Label(self.master, text=f'LFO {i+1} Waveform')
            lfo_waveform_label.grid(row=i, column=5)
            lfo_waveform_menu = ttk.Combobox(self.master, values=lfo_waveform_options, state="readonly")
            lfo_waveform_menu.current(0)
            lfo_waveform_menu.grid(row=i, column=6)
            lfo_waveform_menu.bind('<<ComboboxSelected>>', lambda event, index=i: self.update_lfo_waveform(index, lfo_waveform_menu.get()))

        # Additional settings for global controls
        # ...

        self.master.bind("<KeyPress>", self.on_key_press)
        self.master.bind("<KeyRelease>", self.on_key_release)

    # Update methods for oscillators, filters, and LFOs
    def update_oscillator_waveform(self, index, waveform_name):
        if waveform_name == 'OFF':
            self.oscillators[index].active = False
        else:
            self.oscillators[index].waveform = Waveform[waveform_name]
            self.oscillators[index].active = True
            
    def update_oscillator_frequency(self, index, frequency):
        self.oscillators[index].frequency = float(frequency)

    def update_filter_type(self, index, filter_type):
        self.oscillators[index].filter.type = filter_type

    def update_lfo_waveform(self, index, waveform_name):
        self.oscillators[index].lfo.waveform = Waveform[waveform_name]

    # Key press and release methods
   


    def on_key_press(self, event):
        key = event.char.lower()
        if key not in self.synth_polyphony.active_notes and key in key_frequencies:
            sound = self.generate_sound(key)
            self.synth_polyphony.play_sound(sound, key)

    def on_key_release(self, event):
        key = event.char.lower()
        if key in self.synth_polyphony.active_notes:
            self.synth_polyphony.stop_sound(key)

    def generate_sound(self, key):
        if key in key_frequencies:
            frequency = key_frequencies[key]
            duration = 1  # Duration in seconds for each note
            waves = [osc.generate_wave(frequency, duration) for osc in self.oscillators]
            combined_wave = np.sum(waves, axis=0) / len(self.oscillators)
            return combined_wave
        return np.zeros(int(SAMPLE_RATE * 1))

    def update_filter_cutoff(self, index, cutoff):
        self.oscillators[index].filter.cutoff_frequency = cutoff

    def update_lfo_rate(self, index, rate):
        self.oscillators[index].lfo.rate = rate

# Main Synthesizer Setup
if __name__ == "__main__":
    root = tk.Tk()
    app = SynthesizerApp(root)
    root.mainloop()
