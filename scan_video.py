from common import (
    subprocess, json, os, Path,
    run_subprocess,
    )
from options_file import load_cfg

CFG = load_cfg()
VIDEO_SUFFIXES = {".mp4", ".mkv", ".avi", ".mov", ".ts", '.m4v'}
# FFMPEG = r'D:\_python\.video_cli\ffmpeg\bin\ffmpeg.exe'
# MEDIAINFO = r'D:\_python\.video_cli\MediaInfo\MediaInfo.exe'
FFMPEG =CFG.get("ffmpeg")
MEDIAINFO = CFG.get("mediainfo")


# MEDIAINFO BLOCK
def get_video_info(path: str|Path, mediainfo_path: str|Path = MEDIAINFO) -> list[dict]:
    path = Path(path)
    if not Path(mediainfo_path).exists():
        raise ValueError("MediaInfo.exe не найден")
    if not path.exists():
        raise ValueError("Файл не найден")
    if not path.is_file():
        raise ValueError("Переданный путь ведет не к одиночному файлу")

    param = (
        'Video;{""VideoID"":%StreamKindID%,""BitDepth"":%BitDepth%,""Width"":%Width%,""Height"":%Height%}\\n'
            )
    process = run_subprocess( [mediainfo_path, f"--Inform={param}", path] )
    
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip())

    # NOTE: если будет падать, от того что одно из значение пустое - добавить кавычки в шаблоне, чтобы это были строки, а потом конвертировать в int|None
    video_tracks = [ 
        json.loads(r) for r in process.stdout.strip().splitlines() 
        if r.strip() #защита от пустых строк
                    ] 
    return video_tracks

# FFMPEG BLOCK
def _parse_codecs(data: str, codec_filter: str) ->list[str]:
    # NOTE: не будет работать без фильтра, так как в выводе есть строки не подходящие по шаблону
    if not codec_filter:
        raise ValueError("Необходимо указать фильтр для кодеков")
    lines = [ line for line in data.splitlines() if codec_filter in line.lower()]
    return [ line.split()[1] for line in lines ]

def get_ffmpeg_nv_support(ffmpeg_path = FFMPEG) -> dict:
    # NOTE: специально захардкодил функцию, для получения информации именно для nvidia
    if not Path(ffmpeg_path).exists():
        raise ValueError("ffmpeg.exe не найден")
    
    process_encoders = run_subprocess( [ffmpeg_path, '-hide_banner', '-encoders'] )
    process_decoders = run_subprocess( [ffmpeg_path, '-hide_banner', '-decoders'] )

    for process in [process_encoders, process_decoders]:
        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip())
    
    encoders = _parse_codecs(process_encoders.stdout.strip(), "nvenc")
    decoders = _parse_codecs(process_decoders.stdout.strip(), "cuvid")
    return {"encoders": encoders, "decoders": decoders}

def get_ffmpeg_kwargs(width: int = None, height: int = None, check_nvidia:bool = True, exclude_subtitles = False, ffmpeg_path: str|Path = FFMPEG) -> dict[str, list[str]]:
    # build_ffmpeg_options
    nvidia = False
    if check_nvidia:
        nv_codec = get_ffmpeg_nv_support(ffmpeg_path)
        encoders = nv_codec.get('encoders')
        nvidia = bool(encoders and 'h264_nvenc' in encoders and nv_codec.get('decoders'))
    
    scale = None
    if width or height:
        scale = f'{width if width else "-2"}:{height if height else "-2"}'

    kwargs = {
        'ffmpeg_path': [ffmpeg_path],
        'global_options': [],
        'input_options': [],
        # -i input,
        'output_options': [],
        # output
        }
    kwargs['global_options'] += ['-y', '-hide_banner', 
                                #  '-loglevel', 'level+datetime',
                                #  '-loglevel', 'warning',
                                 ]
    kwargs['input_options'] += []
    if exclude_subtitles:
        kwargs['output_options'] += ["-map", "0:v", "-map", "0:a", "-c", "copy"]
    else:
        kwargs['output_options'] += ["-map", "0", "-c", "copy"]

    if nvidia:
        kwargs['input_options'] += ['-hwaccel', 'cuda']
        kwargs['output_options'] += ["-c:v", "h264_nvenc",     
                                    '-preset', 'p5',
                                    '-rc', 'vbr',
                                    '-cq', '23', 
                                    "-b:v", "0"]
        if scale:
            kwargs['input_options'] += ['-hwaccel_output_format', 'cuda']
            kwargs['output_options'] += ["-vf", f'scale_cuda={scale}:format=nv12']

    else:
        # kwargs['input_options'] += ['-hwaccel', 'auto']
        kwargs['output_options'] += ["-c:v", "libx264",
                                    '-preset', 'medium',
                                    '-crf', '22',
                                    ]
        if scale:
            kwargs['output_options'] += ["-vf", f'scale={scale}']

    if not (nvidia and scale):
        kwargs['output_options'] += ["-pix_fmt", "yuv420p"]
    # kwargs['input_options'] += ['-fflags', '+genpts'] # создание новых timestamp’ов вместо старых
    # kwargs['output_options'] += ['-progress','pipe:1', '-nostats'] # выводить прогресс строками, а не динамикой.

    # old parameters
    # c  = [f'-hwaccel cuda -hwaccel_output_format cuda -i "{Path('input_path')}" -c:v h264_nvenc -b:v 4500K -vf "scale_cuda=1280:720" "{Path('output_path')}"']
    # rc = [f'-hwaccel auto  -i "{Path('input_path')}" -b:v 4500K -s 1280x720 "{Path('output_path')}"']

    return kwargs

def convert_video(input_path: str|Path, output_path: str|Path, ffmpeg_kwargs: dict[str, list[str]]):
    args = []
    args += ffmpeg_kwargs.get('ffmpeg_path')
    args += ffmpeg_kwargs.get('global_options')
    args += ffmpeg_kwargs.get('input_options')
    args += ['-i', input_path]
    args += ffmpeg_kwargs.get('output_options')
    args += [output_path]

    process = subprocess.run(args)
    # process = run_subprocess(args)
    if process.returncode != 0:
        raise RuntimeError(f"Процесс завершился неверно")
        # raise RuntimeError(f"Процесс завершился неверно\n{process.stderr.strip()}")
    pass

# FILE/PATH BLOCK
def scan_dir(dir_path: str|Path, find_10bit: bool = True, max_width: int|None = None, max_height: int|None = None, video_suffixes: set|list|tuple = VIDEO_SUFFIXES) -> list:
    files_to_convert = []
    # for file_path in Path(dir_path).glob("**/*"):
    for file_path in Path(dir_path).rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in video_suffixes:
            continue
        needs_convert = False
        try:
            tracks = get_video_info(file_path)
            if len(tracks) > 1:
                raise ValueError("Более одного потока видео в файле")
            bit_depth = tracks[0].get("BitDepth")
            width = tracks[0].get("Width")
            height = tracks[0].get("Height")
        except Exception as e:
            print(f"Ошибка при чтении файла, пропускаем: {file_path}")
            print(e)
            continue
        
        if find_10bit:
            if bit_depth == 10:
                needs_convert = True
            elif bit_depth != 8:
                print(f"{file_path}: {bit_depth=}")

        if (max_width and width > max_width) or (max_height and height > max_height):
            needs_convert = True
        
        if needs_convert:
            files_to_convert.append(file_path)

    return files_to_convert

# RUN BLOCK
def run_convert(input_path, kwargs, fallback_kwargs):
    output_path = Path(input_path.parent, r"converted", input_path.name)
    # output_path = output_path.with_suffix('.mp4')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f'{input_path} -> {output_path}')
    try:
        convert_video(input_path, output_path, kwargs)
    except Exception as nvidia_ex:
        print(nvidia_ex)
        try:
            convert_video(input_path, output_path, fallback_kwargs)
        except Exception as fallback_ex:
            print(fallback_ex)
            if output_path.exists():
                # os.remove(output_path)
                output_path.unlink()
            return

# OTHER BLOCK
def test():
    # print(subprocess.list2cmdline( ['1', 'Video;{""VideoID"":%StreamKindID%,""BitDepth"":%BitDepth%,""Width"":%Width%,""Height"":%Height%}\\n', '1'] ))

    # Блок тестирования получения mediainfo
    vfile_path = r'D:\Видео\_маме\Кафедра (нужна конвертация)\01. Кафедра.mkv'
    # vfile_path = r'D:\_python\videotools\codex\two_video_streams_sample.mkv'
    # vfile_path = r'D:\Видео\_маме\Анора.mkv'
    results = get_video_info(vfile_path)
    print(type(results))
    print(results)
    for result in results:
        print(type(result))
        print(result)


    # Блок тестирования сканирования директорий
    # data = scan_dir(r"G:")
    # data = scan_dir(r"D:\_python\videotools\codex")
    data = scan_dir(r"D:\Видео\_маме", 
                    # find_10bit=False, 
                    # max_width=800, max_height=600
                    )
    for x in data:
        print(x)

    # Тест получения совместимых кодеков
    print(get_ffmpeg_nv_support())

def test_convert():
    width = 1280
    height = None
    exclude_subtitles = True

    data = scan_dir(r"D:\Видео\_маме\Кафедра (нужна конвертация)", max_width = width, max_height = height)

    kwargs = get_ffmpeg_kwargs(width = width, height=height, 
                               exclude_subtitles=exclude_subtitles)
    fallback_kwargs = get_ffmpeg_kwargs(width = width, height=height, 
                                        check_nvidia=False, exclude_subtitles=exclude_subtitles)
    
    for path in data:
        run_convert(path, kwargs, fallback_kwargs)
        

    # input_path = Path(r'D:\Видео\_маме\Кафедра (нужна конвертация)\01. Кафедра.mkv')
    # output_path = Path(input_path.parent, r"converted", input_path.name)
    # output_path.parent.mkdir(parents=True, exist_ok=True)
    # print(f'{input_path} -> {output_path}')
    # try:
    #     convert_video(input_path, output_path, kwargs)
    # except Exception as nvidia_ex:
    #     print(nvidia_ex)
    #     try:
    #         convert_video(input_path, output_path, fallback_kwargs)
    #     except Exception as fallback_ex:
    #         print(fallback_ex)
    #         if output_path.exists():
    #             os.remove(output_path)
            

def main():
    # test_convert()
    print(get_ffmpeg_kwargs())
    # print(get_ffmpeg_kwargs(width = 1280, height=None))
    # print(get_ffmpeg_kwargs(width = 1280, height=None, check_nvidia=False))
    # print(get_ffmpeg_kwargs(check_nvidia=False))
    pass


if __name__ == "__main__":
    main()