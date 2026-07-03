from common import (
    subprocess, json, os, Path,
    run_subprocess,
    )

CONFIG_PATH = './config.json'

def _is_ffmeg(ffmpeg_path: Path) -> bool:
    try:
        process = run_subprocess([ffmpeg_path.absolute(), '-version'])
        if 'ffmpeg' in process.stdout.strip().split():
            return True
    except:
        return False

def _is_mediainfo(mediainfo_path: Path) -> bool:
    try:
        # NOTE: таймаут выкидывает прогу если она долго отвечает, мини защита от открытого гуя
        process = run_subprocess([mediainfo_path.absolute(), '--Version'], 
                                **dict(timeout = 10)
                                )
        if 'MediaInfo' in process.stdout.strip().split():
            return True
    except:
        return False

def find_exes():
    ffmpeg = None
    mediainfo = None
    pathes = list(Path('.').rglob('*.exe'))
    for path in pathes[:]:
        if ffmpeg and mediainfo:
            break
        if not ffmpeg and path.name.lower() == 'ffmpeg.exe':
            if _is_ffmeg(path):
                ffmpeg = str(path.absolute())
        if not mediainfo and path.name.lower() == 'mediainfo.exe':
            if _is_mediainfo(path):
                mediainfo = str(path.absolute())
    
    return (ffmpeg, mediainfo)

def create_cfg(ffmpeg, mediainfo):
    config = dict(
        ffmpeg = ffmpeg,
        mediainfo = mediainfo,
        )
    with open(CONFIG_PATH, 'w', encoding='utf-8-sig') as file:
        json.dump(config, file, indent=0)
        
def load_cfg():
    if not Path(CONFIG_PATH).exists():
        ffmpeg, mediainfo = find_exes()
        # print(ffmpeg, mediainfo)
        create_cfg(ffmpeg, mediainfo)
    with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as file:
        config = json.load(file)
    return config


def main():
    ffmpeg, mediainfo = find_exes()
    print(ffmpeg, mediainfo)
    # if not Path(CONFIG_PATH).exists():
    #     ffmpeg, mediainfo = find_exes()
    #     # print(ffmpeg, mediainfo)
    #     create_cfg(ffmpeg, mediainfo)
    # else:
    #     print(load_cfg())
    # pass


if __name__ == "__main__":
    main()
