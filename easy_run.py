import sys
import tkinter as tk
from tkinter import filedialog
import replays
from pathlib import Path
import clicks
from pydub import AudioSegment
from tqdm import tqdm
from distutils.spawn import find_executable
import os

os.environ['PATH'] += os.pathsep + str(Path('./ffmpeg/bin').resolve())

if find_executable('ffmpeg') is None:
    from pyunpack import Archive
    import requests
    print('FFmpeg not found on path, downloading it')
    url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z'
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True, desc='Downloading ffmpeg')
    with open('ffmpeg.7z', 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    
    progress_bar.close()
    if total_size != 0 and progress_bar.n != total_size:
        print('ERROR, something went wrong')
        exit()
    
    Archive('ffmpeg.7z').extractall('.')
    try:
        ffmpeg_folder = next(Path('.').glob('ffmpeg-*'))
    except StopIteration:
        print('Extracted ffmpeg folder not found, rename it yourself to just ffmpeg and run this again')
        exit()
    ffmpeg_folder.rename('ffmpeg')


root = tk.Tk()
root.withdraw()

if len(sys.argv) < 2:
    replay_file = filedialog.askopenfile(title='Open the zbot macro', filetypes=('zBot\ Frame\ Based {.zbf}',), mode='rb')
    if replay_file is None:
        exit()
else:
    replay_file = open(sys.argv[1], 'rb')

data = replay_file.read()
replay_file.close()

print('Parsing replay')
replay = replays.parse_zbot_frame(data)

clicks_path = filedialog.askdirectory(mustexist=True, title='Open the clicks folder')
if clicks_path is None:
    exit()

clicks_path = Path(clicks_path)

print('Loading clicks')

click_sounds = clicks.load_clicks(clicks_path)
if len(click_sounds['hold']) == 0 or len(click_sounds['release']) == 0 or len(click_sounds['soft']) == 0:
    print('''Error loading clicks, make sure your clicks directory follows this structure
clicks
 |- holds
 |   |- 1.wav
 |   |- 2.wav
 |   |- s1.wav # these are soft clicks
 |
 |- releases
 |   |- 1.wav
 |   |- 2.wav
    ''')
    exit()

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

output_file = filedialog.asksaveasfilename(defaultextension='mp3', filetypes=('MP3 {.mp3}',), initialdir='.')
if output_file is None:
    print(':|')
    exit()
output.export(output_file)
