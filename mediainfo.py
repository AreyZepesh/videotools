from common import (
    subprocess, json, Path, 
    dataclass, field,
    run_subprocess, Config, str_to_int,
    )
from collections import defaultdict
from rich import print

# @dataclass
# class VideoTrack():
class MediaFileInfo():
    def __init__(self, path: Path|str, cfg: Config):
        self.cfg = cfg
        self.path = path
        self.output_path = cfg.build_output_path(self.path)

        self.check_files()

        all_tracks = self.get_all_info()

        self._video_need_convert: bool = self.is_video_need_convert(all_tracks.get("Video"))
        self._text_need_convert: bool = self.is_text_need_convert(all_tracks.get("Text"))
        self.need_convert: bool = self._video_need_convert or self._text_need_convert

        self.subtitles: list= self.get_simple_text_info(all_tracks.get("Text"))

    def __str__(self):
        return f'{self.path}   ->   {self.output_path}'

    def __setattr__(self, name, value):
        if name == "path":
            if value is None:
                raise ValueError("Не указан путь до видео файла")
            value = Path(value).absolute()
        super().__setattr__(name, value)

    def check_files(self):
        if not Path(self.cfg.mediainfo_path).exists():
            raise ValueError("MediaInfo.exe не найден")
        if not self.path.exists():
            raise ValueError("Файл не найден")
        if not self.path.is_file():
            raise ValueError("Переданный путь ведет не к одиночному файлу")

    def get_all_info(self) -> list[dict]:
        process = run_subprocess( [self.cfg.mediainfo_path, "--Output=JSON", self.path] )
        
        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip())

        json_data: dict = json.loads(process.stdout)
        data = defaultdict(list)
        if json_data and isinstance(json_data, dict):
            for track in json_data.get("media").get("track"):
                data[track.get("@type")].append(track)

        return data

    def is_video_need_convert(self, video_tracks: list[dict]) -> bool:
        if not video_tracks:
            raise ValueError(f"Не найдено видео потоков: {self.path}")
        
        needs_convert = False

        try:
            if len(video_tracks) > 1:
                raise ValueError(f"Более одного потока видео в файле: {self.path}")
            bit_depth = video_tracks[0].get("BitDepth")
            bit_depth = str_to_int(bit_depth)
            width = video_tracks[0].get("Width")
            width = str_to_int(width)
            height = video_tracks[0].get("Height")
            height = str_to_int(height)
        except Exception as e:
            print(f"Ошибка при чтении файла, пропускаем: {self.path}")
            print(e)
        
        if self.cfg.find_10bit:
            if bit_depth == 10:
                needs_convert = True
            elif bit_depth != 8:
                print(f"{self.path}: {bit_depth=}")

        if (self.cfg.width and width > self.cfg.width) or (self.cfg.height and height > self.cfg.height):
            needs_convert = True

        return needs_convert

    @staticmethod
    def _get_subtitle_extension(codec: str):
        d = {   "S_TEXT/UTF8": ".srt",
                "S_TEXT/ASS": ".ass",
                "S_TEXT/SSA": ".ssa",
                "S_TEXT/WEBVTT": ".vtt",
                "S_HDMV/PGS": ".sup",
                # "S_VOBSUB": ".sub", # (+ .idx рядом)
                "S_TEXT/USF": ".usf",
                "S_DVBSUB": ".sub",
                }
        return d.get(codec)
        

    def is_text_need_convert(self, subtitle_tracks: list[dict]) -> bool:
        return 
    
    def get_simple_text_info(self, subtitle_tracks: list[dict]) -> bool:
        subtitles = []
        if not subtitle_tracks:
            return subtitles
            # raise ValueError(f"Не найдено потоков субтитров: {self.path}")
        
        for track in subtitle_tracks:
            codecID = track.get("CodecID")
            # suffix = self._get_subtitle_extension(codecID)
            subtitles.append(dict(
                index = str_to_int(track.get("@typeorder"))-1,
                is_default = True if track.get("Default") in ["Yes", "Да", "True", True] else False,
                language = track.get("Language"),
                title = track.get("Title"),
                codecID = codecID,
                suffix = self._get_subtitle_extension(codecID),
                # path = Path(self.output_path.parent, self.output_path.stem+"_"+track.get("Language")+suffix),
                ))
            # print("ru" in track.get("Language") or "en" in track.get("Language"))

        # print(subtitles)
        return subtitles

def main():
    f = r"D:\Видео\_кинцо\Новое\Битва за битвой (2025) [One Battle After Another].mkv"
    f = r"D:\Видео\_маме\Unchosen_Отречённая.S01.1080p.WEB-DLRip.HEVC.H265.RUS.ENG.MultiSub\Unchosen_Отречённая.S01E01.1080p.WEB-DLRip.HEVC.H265.RUS.ENG.MultiSub.mkv"
    f = r"D:\Видео\_маме\Кафедра (нужна конвертация)\01. Кафедра.mkv"
    cfg = Config(Path(f).parent)
    cfg.load_cfg()
    data = MediaFileInfo(f, cfg)
    print(data.__dict__)

if __name__ == "__main__":
    main()

if __name__ == None:
# def is_video_need_convert(path: str|Path, cfg: Config) -> list:
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

# def get_video_info(path: str|Path, cfg: Config) -> list[dict]:
#     path = Path(path)
#     check_files(path=path, cfg=cfg)
#     param = (
#         'Video;{""VideoID"":%StreamKindID%,""BitDepth"":%BitDepth%,""Width"":%Width%,""Height"":%Height%}\\n'
#             )
#     process = run_subprocess( [cfg.mediainfo_path, f"--Inform={param}", path] )
    
#     if process.returncode != 0:
#         raise RuntimeError(process.stderr.strip())

#     # NOTE: если будет падать, от того что одно из значение пустое - добавить кавычки в шаблоне, чтобы это были строки, а потом конвертировать в int|None
#     video_tracks = [ 
#         json.loads(r) for r in process.stdout.strip().splitlines() 
#         if r.strip() #защита от пустых строк
#                     ] 
#     return video_tracks

# def get_subtitles_info(path: str|Path, cfg: Config) -> list[dict]:
#     path = Path(path)
#     check_files(path=path, cfg=cfg)
#     param = (
#         'Text;{""TextID"":%StreamKindID%,""Language"":%Language%, ""Language/String"": %Language/String%, ""Format"": %Format%, ""Title"": %Title%}\\n'
#         # "Text;Track %StreamKindPos%: %Language/String% | %Format% | %Title%\n"
#             )
#     process = run_subprocess( [cfg.mediainfo_path, f"--Inform={param}", path] )
    
#     if process.returncode != 0:
#         raise RuntimeError(process.stderr.strip())

#     # NOTE: если будет падать, от того что одно из значение пустое - добавить кавычки в шаблоне, чтобы это были строки, а потом конвертировать в int|None
#     subtitles_tracks = [ 
#         json.loads(r) for r in process.stdout.strip().splitlines() 
#         if r.strip() #защита от пустых строк
#                     ] 
#     return subtitles_tracks


# def is_text(path: str|Path, cfg: Config) -> list:
#     return True

# def check_files(path: str|Path, cfg: Config):
#     if not Path(cfg.mediainfo_path).exists():
#         raise ValueError("MediaInfo.exe не найден")
#     if not path.exists():
#         raise ValueError("Файл не найден")
#     if not path.is_file():
#         raise ValueError("Переданный путь ведет не к одиночному файлу")

# def get_all_info(path: str|Path, cfg: Config) -> list[dict]:
#     path = Path(path)
#     check_files(path=path, cfg=cfg)
#     process = run_subprocess( [cfg.mediainfo_path, "--Output=JSON", path] )
    
#     if process.returncode != 0:
#         raise RuntimeError(process.stderr.strip())

#     json_data: dict = json.loads(process.stdout)
#     data = defaultdict(list)
#     if json_data and isinstance(json_data, dict):
#         for track in json_data.get("media").get("track"):
#             data[track.get("@type")].append(track)

#     return data
#     return dict(data)


# def is_video_need_convert(path: str|Path, cfg: Config, video_tracks: list) -> bool:
#     if not video_tracks:
#         raise ValueError("Не найдено видео потоков")
    
#     needs_convert = False
#     try:
#         # video_tracks = get_all_info(path, cfg).get("Video")
#         if len(video_tracks) > 1:
#             raise ValueError("Более одного потока видео в файле")
#         bit_depth = video_tracks[0].get("BitDepth")
#         bit_depth = str_to_int(bit_depth)
#         width = video_tracks[0].get("Width")
#         width = str_to_int(width)
#         height = video_tracks[0].get("Height")
#         height = str_to_int(height)
#     except Exception as e:
#         print(f"Ошибка при чтении файла, пропускаем: {path}")
#         print(e)
    
#     if cfg.find_10bit:
#         if bit_depth == 10:
#             needs_convert = True
#         elif bit_depth != 8:
#             print(f"{path}: {bit_depth=}")

#     if (cfg.width and width > cfg.width) or (cfg.height and height > cfg.height):
#         needs_convert = True

#     return needs_convert

# def is_subtitle_need_convert(path: str|Path, cfg: Config, subtitle_tracks: list) -> bool:
#     if not subtitle_tracks:
#         raise ValueError("Не найдено потоков субтитров")
    
#     print(len(subtitle_tracks))
#     print(subtitle_tracks[0])
#     for track in subtitle_tracks:
#         print(track.get("Language"), track.get("Title"), track.get("Default"))
    
#     # track.get("CodecID")
#     return

# def get_status(path: str|Path, cfg: Config) -> MediaInfoStatus:
#     all_tracks = get_all_info(path, cfg) 
#     need_video_convert = is_video_need_convert(path, cfg, all_tracks.get("Video"))
#     need_subtitle_convert = is_subtitle_need_convert(path, cfg, all_tracks.get("Text"))


#     return #MediaInfoStatus()
    pass