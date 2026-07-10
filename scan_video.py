from common import (
    subprocess, json, Path,
    run_subprocess, Config
    )

from ffmpeg import FFmpegCmdBuilder, get_ffmpeg_kwargs

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

# RUN FFMPEG CONVERT
# def convert_video(input_path: str|Path, output_path: str|Path, ffmpeg_kwargs: dict[str, list[str]]):
#     args = []
#     args += ffmpeg_kwargs.get('ffmpeg_path')
#     args += ffmpeg_kwargs.get('global_options')
#     args += ffmpeg_kwargs.get('input_options')
#     args += ['-i', input_path]
#     args += ffmpeg_kwargs.get('output_options')
#     args += [output_path]

#     process = subprocess.run(args)
#     # process = run_subprocess(args)
#     if process.returncode != 0:
#         raise RuntimeError(f"Процесс завершился неверно")
#         # raise RuntimeError(f"Процесс завершился неверно\n{process.stderr.strip()}")
#     pass

def convert_video(ffmpeg_args: list[str]):
    process = subprocess.run(ffmpeg_args)
    if process.returncode != 0:
        raise RuntimeError(f"Процесс завершился неверно")
    pass

# FILE/PATH BLOCK
def scan_dir(dir_path: str|Path, cfg: Config) -> list:
    files_to_convert = []
    # for file_path in Path(dir_path).glob("**/*"):
    for file_path in Path(dir_path).rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in cfg.video_suffixes:
            continue
        needs_convert = False
        try:
            tracks = get_video_info(file_path, cfg)
            if len(tracks) > 1:
                raise ValueError("Более одного потока видео в файле")
            bit_depth = tracks[0].get("BitDepth")
            width = tracks[0].get("Width")
            height = tracks[0].get("Height")
        except Exception as e:
            print(f"Ошибка при чтении файла, пропускаем: {file_path}")
            print(e)
            continue
        
        if cfg.find_10bit:
            if bit_depth == 10:
                needs_convert = True
            elif bit_depth != 8:
                print(f"{file_path}: {bit_depth=}")

        if (cfg.width and width > cfg.width) or (cfg.height and height > cfg.height):
            needs_convert = True
        
        if needs_convert:
            files_to_convert.append(file_path)

    return files_to_convert

# RUN BLOCK
def run_convert(input_path, ff_cmd: FFmpegCmdBuilder, fallback_ff_cmd: FFmpegCmdBuilder):
    output_path = Path(input_path.parent, r"converted", input_path.name)
    # output_path = output_path.with_suffix('.mp4')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f'{input_path} -> {output_path}')
    try:
        convert_video(
            ff_cmd.build(input_path, output_path)
                      )
    except Exception as nvidia_ex:
        print(nvidia_ex)
        try:
            convert_video(
                fallback_ff_cmd.build(input_path, output_path)
                    )
        except Exception as fallback_ex:
            print(fallback_ex)
            if output_path.exists():
                # os.remove(output_path)
                output_path.unlink()
            return
        
def run_only_scan(dir_path, cfg: Config):
    data = scan_dir(dir_path, cfg=cfg)
    lines = []
    if not data:
        lines.append("По заданным параметрам ничего не найдено")
    else:
        lines.append("По заданным параметрам найдено:")
        lines.extend(data)
    return lines

def run_scan_and_convert(dir_path, cfg: Config):
    data = scan_dir(dir_path, cfg=cfg)

    if not data:
        return

    # kwargs = get_ffmpeg_kwargs(cfg=cfg)
    ff_cmd = FFmpegCmdBuilder(cfg)

    # fallback_cfg = cfg.get_replaced_copy(
    #     check_nvidia = False,
    #     exclude_subtitles = True, 
    #     )
    # fallback_kwargs = get_ffmpeg_kwargs(cfg=fallback_cfg)
    fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)
    
    for path in data:
        run_convert(path, ff_cmd, fallback_ff_cmd)

def run_from_cli():
        # width: int|None = None, 
        # height: int|None = None, 
        # find_10bit: bool = True,
        # check_nvidia: bool = True,
        # exclude_subtitles: bool = False,
    
    cfg = Config()
    cfg.load_cfg()
    cfg.exclude_subtitles = True
    dir = r"D:\Видео\_маме\Кафедра (нужна конвертация)"
    # dir = r"G:\\"
    # lines = run_only_scan(dir, cfg)
    # for line in lines:
    #     print(line)
    # print()
    run_scan_and_convert(dir, cfg)

# OTHER BLOCK

def main():
    run_from_cli()
    pass

if __name__ == "__main__":
    main()