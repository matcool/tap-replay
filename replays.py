from dataclasses import dataclass
from typing import List
import struct

@dataclass
class TimeAction:
    time: float
    hold: bool

@dataclass
class Replay:
    actions: List[TimeAction]

def slice_per(l, n):
    yield from (l[i:i + n] for i in range(0, len(l), n))

def parse_zbot_frame(data: bytes) -> Replay:
    delta = struct.unpack('f', data[:4])[0]
    speed_hack = struct.unpack('f', data[4:8])[0]
    fps = 1 / delta * speed_hack
    actions = []
    for action_data in slice_per(data[8:], 6):
        if len(action_data) != 6:
            print('wtf', action_data)
        else:
            frame, hold, _ = struct.unpack('Ibb', action_data)
            actions.append(TimeAction(frame / fps, hold == 0x31))
    return Replay(actions)
