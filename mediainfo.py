from common import (
    subprocess, json, Path,
    run_subprocess, Config
    )


# MEDIAINFO BLOCK
def get_video_info(path: str|Path, cfg: Config) -> list[dict]:
    path = Path(path)
    if not Path(cfg.mediainfo_path).exists():
        raise ValueError("MediaInfo.exe не найден")
    if not path.exists():
        raise ValueError("Файл не найден")
    if not path.is_file():
        raise ValueError("Переданный путь ведет не к одиночному файлу")

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

# TODO: def get_subtitles_info(path: str|Path, cfg: Config) -> list[dict]:
# """Для определения количества субтитров, и возможно сохранения их отдельно снаружи"""
# NOTE: возможно стоит получать единоразово полный json инфы, 
# а потом уже из него возрвращать тольно нужное, меньше запросов к фс

def is_need_convert(path: str|Path, cfg: Config) -> list:
    needs_convert = False
    try:
        tracks = get_video_info(path, cfg)
        if len(tracks) > 1:
            raise ValueError("Более одного потока видео в файле")
        bit_depth = tracks[0].get("BitDepth")
        width = tracks[0].get("Width")
        height = tracks[0].get("Height")
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
