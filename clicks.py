from pathlib import Path
from dataclasses import dataclass
import glob
import random
from pydub import AudioSegment
import math

def load_clicks(base_path: Path):
    holds = glob.glob(str(base_path / 'holds' / '*.wav'))
    releases = glob.glob(str(base_path / 'releases' / '*.wav'))
    hold_sounds = [AudioSegment.from_wav(i) for i in holds]
    release_sounds = [AudioSegment.from_wav(i) for i in releases]
    soft_sounds = [sound for sound, file_path in zip(hold_sounds, holds) if Path(file_path).name[0] == 's']
    return {
        'hold': hold_sounds,
        'release': release_sounds,
        'soft': soft_sounds
    }

def db2mag(db):
    return 10 ** (db / 20.0)

def mag2db(mag):
    return 20.0 * math.log10(mag)

def nerve(x):
    return math.tanh(math.exp(0.1 * (x - 70.0) - 0.9)) / 2.0

class Click:
    def __init__(self, time: float, hold: bool, click_sounds):
        self.time = time
        self.hold = hold
        self.audio = random.choice(click_sounds['hold' if hold else 'release'])

    def mult_volume(self, amt: float):
        self.audio = self.audio.apply_gain(mag2db(db2mag(self.audio.dBFS) * amt) - self.audio.dBFS)

    def process(self, last_click: 'Click', full_Length: float, click_sounds):
        bias = random.uniform(0.8, 1.2)

        if self.time > full_Length * 0.5:
            bias += nerve(100 * self.time / full_Length)

        if last_click is None:
            self.mult_volume(bias)
            return

        time_since = self.time - last_click.time / 2 # why is it divided by two??

        if self.hold and time_since < 0.1:
            self.audio = random.choice(click_sounds['soft'])

        if time_since > 0.1 or not self.hold:
            self.mult_volume(bias)
        else:
            ret = (90.0 * time_since ** 2) + 0.0613 # tf is this
            self.mult_volume(ret * bias)

        octaves = random.uniform(-0.1, 0.1)
        self.audio = self.audio._spawn(
            self.audio.raw_data,
            overrides={'frame_rate': int(self.audio.frame_rate * (2.0 ** octaves))},
        )