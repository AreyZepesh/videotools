from common import (
    subprocess, json, Path, 
    # dataclass, field,
    run_subprocess, Config, str_to_int,
    )
from collections import defaultdict

# @dataclass
# class MediaInfoStatus():
#     need_conver: bool = field(default=False)
#     subtitles: list[str] = field(default_factory=list)
#     # basic_subtitles: list[str] = field(default_factory=list)
#     # additional_subtitles: list[str] = field(default_factory=list)


def check_files(path: str|Path, cfg: Config):
    if not Path(cfg.mediainfo_path).exists():
        raise ValueError("MediaInfo.exe не найден")
    if not path.exists():
        raise ValueError("Файл не найден")
    if not path.is_file():
        raise ValueError("Переданный путь ведет не к одиночному файлу")

def get_all_info(path: str|Path, cfg: Config) -> list[dict]:
    path = Path(path)
    check_files(path=path, cfg=cfg)
    process = run_subprocess( [cfg.mediainfo_path, "--Output=JSON", path] )
    
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip())

    json_data: dict = json.loads(process.stdout)
    data = defaultdict(list)
    if json_data and isinstance(json_data, dict):
        for track in json_data.get("media").get("track"):
            data[track.get("@type")].append(track)
    
    return data
    return dict(data)

def get_video_info(path: str|Path, cfg: Config) -> list[dict]:
    path = Path(path)
    check_files(path=path, cfg=cfg)
    param = (
        'Video;{""VideoID"":%StreamKindID%,""BitDepth"":%BitDepth%,""Width"":%Width%,""Height"":%Height%}\\n'
            )
    process = run_subprocess( [cfg.mediainfo_path, f"--Inform={param}", path] )
    
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip())

    # NOTE: если будет падать, от того что одно из значение пустое - добавить кавычки в шаблоне, чтобы это были строки, а потом конвертировать в int|None
    video_tracks = [ 
        json.loads(r) for r in process.stdout.strip().splitlines() 
        if r.strip() #защита от пустых строк
                    ] 
    return video_tracks

def is_video_need_convert(path: str|Path, cfg: Config) -> list:
    needs_convert = False
    try:
        video_tracks = get_all_info(path, cfg).get("Video")
        if len(video_tracks) > 1:
            raise ValueError("Более одного потока видео в файле")
        bit_depth = video_tracks[0].get("BitDepth")
        bit_depth = str_to_int(bit_depth)
        width = video_tracks[0].get("Width")
        width = str_to_int(width)
        height = video_tracks[0].get("Height")
        height = str_to_int(height)
    except Exception as e:
        print(f"Ошибка при чтении файла, пропускаем: {path}")
        print(e)
    
    if cfg.find_10bit:
        if bit_depth == 10:
            needs_convert = True
        elif bit_depth != 8:
            print(f"{path}: {bit_depth=}")

    if (cfg.width and width > cfg.width) or (cfg.height and height > cfg.height):
        needs_convert = True

    return needs_convert

    # needs_convert = False
    # try:
    #     tracks = get_video_info(path, cfg)
    #     if len(tracks) > 1:
    #         raise ValueError("Более одного потока видео в файле")
    #     bit_depth = tracks[0].get("BitDepth")
    #     width = tracks[0].get("Width")
    #     height = tracks[0].get("Height")
    # except Exception as e:
    #     print(f"Ошибка при чтении файла, пропускаем: {path}")
    #     print(e)
    
    # if cfg.find_10bit:
    #     if bit_depth == 10:
    #         needs_convert = True
    #     elif bit_depth != 8:
    #         print(f"{path}: {bit_depth=}")

    # if (cfg.width and width > cfg.width) or (cfg.height and height > cfg.height):
    #     needs_convert = True

    # return needs_convert

# TODO: def get_subtitles_info(path: str|Path, cfg: Config) -> list[dict]:
# """Для определения количества субтитров, и возможно сохранения их отдельно снаружи"""
# NOTE: возможно стоит получать единоразово полный json инфы, 
# а потом уже из него возрвращать тольно нужное, меньше запросов к фс

def get_subtitles_info(path: str|Path, cfg: Config) -> list[dict]:
    path = Path(path)
    check_files(path=path, cfg=cfg)
    param = (
        'Text;{""TextID"":%StreamKindID%,""Language"":%Language%, ""Language/String"": %Language/String%, ""Format"": %Format%, ""Title"": %Title%}\\n'
        # "Text;Track %StreamKindPos%: %Language/String% | %Format% | %Title%\n"
            )
    process = run_subprocess( [cfg.mediainfo_path, f"--Inform={param}", path] )
    
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip())

    # NOTE: если будет падать, от того что одно из значение пустое - добавить кавычки в шаблоне, чтобы это были строки, а потом конвертировать в int|None
    subtitles_tracks = [ 
        json.loads(r) for r in process.stdout.strip().splitlines() 
        if r.strip() #защита от пустых строк
                    ] 
    return subtitles_tracks


def is_text(path: str|Path, cfg: Config) -> list:
    return True


def main():
    from rich import print
    c = Config()
    c.load_cfg()
    f = r"D:\Видео\_маме\Unchosen_Отречённая.S01.1080p.WEB-DLRip.HEVC.H265.RUS.ENG.MultiSub\Unchosen_Отречённая.S01E01.1080p.WEB-DLRip.HEVC.H265.RUS.ENG.MultiSub.mkv"

    # x = Track()
    # x.
    data = get_all_info(f, c)
    print(data)
    # for k, v in data.items():
    #     print(k, v)
        # if track.get("@type") == "Video":
        #     print(track)
        # if track.get("@type") == "Text":
        #     print(track)


if __name__ == "__main__":
    main()