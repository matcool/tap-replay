from dataclasses import dataclass
from typing import List, Union
import struct
from gd import Level
from gd.api import get_length_from_x
from gd.api.enums import Speed

@dataclass
class Action:
    x: float
    hold: bool

@dataclass
class TimeAction:
    time: float
    hold: bool

@dataclass
class Replay:
    actions: List[Union[Action, TimeAction]]

def slice_per(l, n):
    yield from (l[i:i + n] for i in range(0, len(l), n))

def parse_replaybot(data: bytes) -> Replay:
    # not needed for this lol
    fps = struct.unpack('f', data[:4])[0]
    actions = []
    for action_data in slice_per(data[4:], 6):
        if len(action_data) != 6:
            print('wtf', action_data)
        else:
            x, hold, _ = struct.unpack('fbb', action_data)
            actions.append(Action(x, bool(hold)))
    return Replay(actions)

def convert_to_time(replay: Replay, level: Level) -> Replay:
    editor = level.open_editor()
    start_speed = editor.get_header().speed or Speed.NORMAL
    speeds = editor.get_speed_portals()
    for i, action in enumerate(replay.actions):
        # TODO: this doesn't account for scaled or rotated speed portals
        time = get_length_from_x(action.x, start_speed, speeds)
        replay.actions[i] = TimeAction(time, action.hold)
    return replay