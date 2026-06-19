import subprocess
import json
from pathlib import Path

VIDEO_SUFFIXES = {".mp4", ".mkv", ".avi", ".mov", ".ts", '.m4v'}
MEDIAINFO = r'D:\_python\.video_cli\MediaInfo\MediaInfo.exe'
FFMPEG = r'D:\_python\.video_cli\ffmpeg\bin\ffmpeg.exe'

def run_subprocess(args: list, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8-sig",
        **kwargs
        )

def get_list_codecs(data: str, filter: str) ->list[str]:
    def get_codec_from_line(line: str) -> str:
        # NOTE: не будет работать без фильтра, так как в выводе есть строки не подходящие по шаблону
        parts = line.strip().split("  ")
        return parts[0].split()[-1]
    if not filter:
        raise ValueError("Небходимо указать фильтр для кодеков")
    lines = [ line for line in data.splitlines() if filter in line.lower()]
    return [ get_codec_from_line(line) for line in lines ]

def get_ffmpeg_nv_support(ffmpeg_path = FFMPEG) -> dict:
    # NOTE: специально захардкодил функцию, для получение информации именно для nvidia
    if not Path(ffmpeg_path).exists():
        raise ValueError("ffmpeg.exe не найден")
    result_encoders = run_subprocess( [ffmpeg_path, '-hide_banner', '-encoders'] ).stdout.strip()
    encoders = get_list_codecs(result_encoders, "nvenc")
    result_decoders = run_subprocess( [ffmpeg_path, '-hide_banner', '-decoders'] ).stdout.strip()
    decoders = get_list_codecs(result_decoders, "cuvid")
    return {"encoders": encoders, "decoders": decoders}

def get_media_info(path: str|Path, mediainfo_path: str|Path = MEDIAINFO) -> list[dict]:
    if not Path(mediainfo_path).exists():
        raise ValueError("MediaInfo.exe не найден")
    if not Path(path).exists():
        raise ValueError("Файл не найден")
    if not Path(path).is_file():
        raise ValueError("Переданный путь ведет не к одиночному файлу")

    param = (
        'Video;'
        '{""Video%StreamKindID%"":'
        '{""BitDepth"":%BitDepth%,""Width"":%Width%,""Height"":%Height%}}\\n'
            )
    param = (
        'Video;{""VideoID"":%StreamKindID%,""BitDepth"":%BitDepth%,""Width"":%Width%,""Height"":%Height%}\\n'
            )
    process = run_subprocess( [mediainfo_path, f"--Inform={param}", path] )
    
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip())
    # print(result.stdout.strip().split())
    video_tracks = [ json.loads(r) for r in process.stdout.strip().splitlines() ]
    return video_tracks

def scan_dir(dir_path: str|Path, find_10bit: bool = True, max_width: int = 1920, max_height: int = 1080, video_suffixes: set|list|tuple = VIDEO_SUFFIXES) -> list:
    files_to_convert = []
    for filepath in Path(dir_path).glob("**/*"):
        if filepath.is_dir():
            continue
        if filepath.suffix.lower() not in video_suffixes:
            continue
        needs_convert = False
        try:
            tracks = get_media_info(filepath)
            if len(tracks) > 1:
                raise ValueError("Более одного потока видео в файле")
            bit_depth = tracks[0].get("BitDepth")
            width = tracks[0].get("Width")
            height = tracks[0].get("Height")
        except Exception as e:
            print(f"Ошибка при чтении файла, пропускаем: {filepath}")
            print(e)
            continue
        
        if find_10bit:
            if bit_depth == 10:
                needs_convert = True
            elif bit_depth != 8:
                print(f"{filepath}: {bit_depth=}")

        if width > max_width or height > max_height:
            needs_convert = True
        
        if needs_convert:
            files_to_convert.append(filepath)

    return files_to_convert

def convert_video(input_path: str|Path, output_path: str|Path, width: int = None, height: int = None):
    pass

def main():
    # Блок тестирования получения mediainfo
    # vfile_path = r'D:\Видео\_маме\Кафедра (нужна конвертация)\01. Кафедра.mkv'
    # vfile_path = r'D:\_python\videotools\codex\two_video_streams_sample.mkv'
    # vfile_path = r'D:\Видео\_маме\Анора.mkv'
    # results = get_media_info(vfile_path)
    # print(type(results))
    # print(results)
    # for result in results:
    #     print(type(result))
    #     print(result)


    # Блок тестирования сканирования директорий
    # data = scan_dir(r"G:")
    # data = scan_dir(r"D:\_python\videotools\codex")
    # data = scan_dir(r"D:\Видео\_маме", 
    #                 # find_10bit=False, 
    #                 # max_width=800, max_height=600
    #                 )
    # for x in data:
    #     print(x)

    # Тест получения совместивых кодеков
    # print(get_ffmpeg_nv_support())

    pass


if __name__ == "__main__":
    main()