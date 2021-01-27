from pathlib import Path
from dataclasses import dataclass
import glob
import random
from pydub import AudioSegment
import math

def get_random_click_path(path: Path, type_: str):
    if type_ == 'hold':
        paths = glob.glob(str(path / 'holds' / '*.wav'))
    elif type_ == 'soft':
        paths = glob.glob(str(path / 'holds' / 's*.wav'))
    elif type_ == 'release':
        paths = glob.glob(str(path / 'releases' / '*.wav'))
    return random.choice(paths)

def db2mag(db):
    return 10 ** (db / 20.0)

def mag2db(mag):
    return 20.0 * math.log10(mag)

def nerve(x):
    return math.tanh(math.exp(0.1 * (x - 70.0) - 0.9)) / 2.0

class Click:
    def __init__(self, time: float, hold: bool, base_path: Path):
        self.base_path = base_path
        self.time = time
        self.hold = hold
        self.audio = AudioSegment.from_wav(get_random_click_path(base_path, 'hold' if hold else 'release'))

    def mult_volume(self, amt: float):
        self.audio = self.audio.apply_gain(mag2db(db2mag(self.audio.dBFS) * amt) - self.audio.dBFS)

    def process(self, last_click: 'Click', full_Length: float):
        bias = random.uniform(0.8, 1.2)

        if self.time > full_Length * 0.5:
            bias += nerve(100 * self.time / full_Length)

        if last_click is None:
            self.mult_volume(bias)
            return

        time_since = self.time - last_click.time / 2 # why is it divided by two??

        if self.hold and time_since < 0.1:
            self.audio = AudioSegment.from_wav(get_random_click_path(self.base_path, 'soft'))

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