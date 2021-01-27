import argparse
import replays
import gd
from pathlib import Path
import clicks
from pydub import AudioSegment
from tqdm import tqdm

parser = argparse.ArgumentParser(description='Generate clicks')
parser.add_argument('replay', help='Path to the replay/macro file', type=argparse.FileType('rb'))
parser.add_argument('level', help='Level ID', type=int)
parser.add_argument('output', help='Path to the output mp3 file')
parser.add_argument('--clicks', default='clicks', required=False, help='Path to the clicks folder')

args = parser.parse_args()

data = args.replay.read()
args.replay.close()

print('Parsing replay')
replay = replays.parse_replaybot(data)

client = gd.Client()
print('Downloading level')
lvl = client.run(client.get_level(args.level))

print('Converting replay')
replays.convert_to_time(replay, lvl)

clicks_path = Path(args.clicks)

print('Loading clicks')

click_sounds = clicks.load_clicks(clicks_path)

print('Generating clicks')

clicks = [clicks.Click(action.time, action.hold, click_sounds) for action in replay.actions]
full_length = clicks[-1].time + 1

output = AudioSegment.silent(duration=full_length * 1000)

last_click = None
last_click_hold = None
for click in tqdm(clicks, desc='Mapping clicks'):
    if last_click is None or click.hold != last_click.hold:
        click.process(last_click_hold, full_length, click_sounds)
        if click.hold: last_click_hold = click
        last_click = click
        output = output.overlay(click.audio, position=click.time * 1000)

output.export(args.output)
