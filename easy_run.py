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

def promptExit():
    input('Press enter to close...')
    sys.exit()

os.environ['PATH'] += os.pathsep + str(Path('./ffmpeg/bin').resolve())

CWD = Path.cwd()

print('Tap by Camden314, zBot Frame Beta port by mat')

try:
    root = tk.Tk()
    root.withdraw()

    if find_executable('ffmpeg') is None:
        print('FFmpeg was not found on path, please download it from the link below, and extract it.')
        print('https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z')
        input('Press enter after you\'ve extracted ffmpeg...')

        ffmpeg_folder = filedialog.askdirectory(mustexist=True, title='Open the extracted ffmpeg folder')
        if not ffmpeg_folder:
            print('why did you press cancel')
            promptExit()
        ffmpeg_folder = Path(ffmpeg_folder)
        
        for path in ffmpeg_folder.glob('ffmpeg-*'):
            ffmpeg_folder = path
            break

        if not (ffmpeg_folder / 'bin' / 'ffmpeg.exe').exists():
            print('No ffmpeg.exe found, make sure you select the folder with the following structure')
            print('bin/\ndoc/\npresets/\nLICENSE\nREADME.txt')
            promptExit()
        
        ffmpeg_folder.rename(CWD / 'ffmpeg')

    if len(sys.argv) < 2:
        replay_file = filedialog.askopenfile(title='Open the .zbf macro', filetypes=('zBot\ Frame\ Based {.zbf}',), mode='rb')
        if not replay_file:
            promptExit()
    else:
        replay_file = open(sys.argv[1], 'rb')

    data = replay_file.read()
    replay_file.close()

    print('Parsing replay')
    replay = replays.parse_zbot_frame(data)

    clicks_path = filedialog.askdirectory(mustexist=True, title='Open the clicks folder')
    if not clicks_path:
        promptExit()

    clicks_path = Path(clicks_path)

    print('Loading clicks')

    click_sounds = clicks.load_clicks(clicks_path)
    if len(click_sounds['hold']) == 0 or len(click_sounds['release']) == 0:
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
        promptExit()

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
    if not output_file:
        print(':|')
        promptExit()
    output.export(output_file)

    promptExit()
except:
    import traceback
    if sys.exc_info()[0] != SystemExit:
        traceback.print_exc()
        promptExit()