from collections import defaultdict

from common import (
    json,
    Path, # from pathlib import
    dataclass, # from dataclasses import
    str_to_int, str_to_float,
    )

from config import Config
from proc import run_subprocess


@dataclass(frozen=True)
class SubtitleInfo():
    index: int
    is_default: bool
    language: str
    title: str
    codecID: str
    codec: str
    suffix: str
    out_path: Path

    def is_basic(self):
        if self.is_default:
            return True
        for l in ['ru', 'RU']:
            if l in self.language:
                return True
        return False


class MediaFileInfo():
    def __init__(self, path: Path|str, cfg: Config):
        self.cfg = cfg
        self.path = path
        self.output_path = cfg.build_output_path(self.path)

        self.check_files()

        all_tracks = self.get_all_info()

        self.duration_us = self.get_duration_us(all_tracks.get("General"))

        self.subtitles: list[SubtitleInfo] = self.get_simple_text_info(all_tracks.get("Text"))
        self.subtitle_count_exceeded: bool = True if len(self.subtitles) > 3 else False 
        #self.is_text_need_convert(all_tracks.get("Text"))

        self.video_need_convert: bool = self.is_video_need_convert(all_tracks.get("Video"))
        # if self._text_need_convert:
        #     print(len(self.subtitles))
        self.need_convert: bool = self.video_need_convert or self.subtitle_count_exceeded

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

        # try:
        if len(video_tracks) > 1:
            # raise ValueError(f"Более одного потока видео в файле: {self.path}")
            print(f"ВНИМАНИЕ! Более одного потока видео в файле: {self.path}.\
                  \n   Видеопотоки кроме первого будут проигнорированы")
        bit_depth = video_tracks[0].get("BitDepth")
        bit_depth = str_to_int(bit_depth)
        width = video_tracks[0].get("Width", 0)
        width = str_to_int(width)
        height = video_tracks[0].get("Height", 0)
        height = str_to_int(height)
        # except Exception as e:
        #     print(f"Ошибка при чтении файла, пропускаем: {self.path}")
        #     print(e)
        #     raise e
        
        if self.cfg.find_10bit:
            if bit_depth == 10:
                needs_convert = True
            elif bit_depth != 8:
                print(f"{self.path}: {bit_depth=}")

        _width  = self.cfg.width  and width  and width  > self.cfg.width
        _height = self.cfg.height and height and height > self.cfg.height
        if _width or _height:
            needs_convert = True

        return needs_convert

    @staticmethod
    def _get_sub_suffix_and_codec(codec: str) -> tuple[str]|None:
        d = {   "S_TEXT/UTF8": (".srt", "subrip"),
                "S_TEXT/ASS": (".ass", "ass"),
                "S_TEXT/SSA": (".ssa", "ssa"),
                "S_TEXT/WEBVTT": (".vtt", "webvtt"),
                "S_HDMV/PGS": (".sup", "hdmv_pgs_subtitle"),
                "S_VOBSUB": (".sub", "dvd_subtitle"), # (+ .idx рядом)
                "S_TEXT/USF": (".usf", "usf"),
                "S_DVBSUB": (".sub", "dvbsub"),
                }
        return d.get(codec)
         
    def get_simple_text_info(self, subtitle_tracks: list[dict]) -> list[SubtitleInfo]:
        subtitles = []
        if not subtitle_tracks:
            return subtitles
            # raise ValueError(f"Не найдено потоков субтитров: {self.path}")
        
        for track in subtitle_tracks:
            try:
                index = str_to_int(track.get("@typeorder"))-1
                codecID = track.get("CodecID")
                suffix, codec = self._get_sub_suffix_and_codec(codecID)
                language = track.get("Language") or ""
                subtitles.append(SubtitleInfo(
                    index = index,
                    is_default = True if track.get("Default") in ["Yes", "Да", "True", True] else False,
                    language = language,
                    title = track.get("Title"),
                    codecID = codecID,
                    codec = codec,
                    suffix = suffix,
                    out_path = Path(self.output_path.parent, self.output_path.stem+"."+language+str(index)+suffix),
                    ))
                # print("ru" in track.get("Language") or "en" in track.get("Language"))
            except Exception as ex:
                print(f"Ошибка в mediainfo.get_simple_text_info: {self.path} \n {track}")
                print(ex)
                print() # TODO: logs

        # print(subtitles)
        return subtitles

    def get_duration_us(self, general_tracks: list[dict]) -> float | int | None:
        if not general_tracks:
            raise ValueError(f"Не найдено потоков General: {self.path}")
        if len(general_tracks)>1:
            print(f"ВНИМАНИЕ! Более одного потока General: {self.path}.\
                  \n   Потоки кроме первого будут проигнорированы")
        duration = str_to_float(general_tracks[0].get('Duration'))
        if duration:
            duration *= 1000000
        return duration

def main():
    # f = r"D:\Видео\_кинцо\Новое\Битва за битвой (2025) [One Battle After Another].mkv"
    # f = r"D:\Видео\_маме\Отречённая\Unchosen_Отречённая.S01E01.1080p.WEB-DLRip.HEVC.H265.RUS.ENG.MultiSub.mkv"
    f = r"D:\Видео\_маме\Кафедра\01. Кафедра.mkv"
    cfg = Config(Path(f).parent)
    cfg.load_cfg()
    data = MediaFileInfo(f, cfg)
    # print(data.__dict__)
    print(
        data._get_sub_suffix_and_codec("S_TEXT/UTF8")
        )

if __name__ == "__main__":
    main()
