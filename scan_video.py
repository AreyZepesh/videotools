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

# MEDIAINFO BLOCK
def get_media_info(path: str|Path, mediainfo_path: str|Path = MEDIAINFO) -> list[dict]:
    if not Path(mediainfo_path).exists():
        raise ValueError("MediaInfo.exe не найден")
    if not Path(path).exists():
        raise ValueError("Файл не найден")
    if not Path(path).is_file():
        raise ValueError("Переданный путь ведет не к одиночному файлу")

    param = (
        'Video;{""VideoID"":%StreamKindID%,""BitDepth"":%BitDepth%,""Width"":%Width%,""Height"":%Height%}\\n'
            )
    process = run_subprocess( [mediainfo_path, f"--Inform={param}", path] )
    
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip())

    # NOTE: если будет падать, от того что одно из значение пустое - добавить ковычки в шаблоне, чтобы это были строки, а потом конвертировать в int|None
    video_tracks = [ 
        json.loads(r) for r in process.stdout.strip().splitlines() 
        if r.strip() #зашита от пустых строк
                    ] 
    return video_tracks

# FFMPEG BLOCK
def get_list_codecs(data: str, codec_filter: str) ->list[str]:
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
    
    encoders = get_list_codecs(process_encoders.stdout.strip(), "nvenc")
    decoders = get_list_codecs(process_decoders.stdout.strip(), "cuvid")
    return {"encoders": encoders, "decoders": decoders}

def get_ffmpeg_kwargs(width: int = None, height: int = None, ffmpeg_path: str|Path = FFMPEG, check_nvidia:bool = True) -> dict[list]:
    kwargs = {
        # ffmpeg,
        'global_options': [],
        'input_options': [],
        # -i input,
        'output_options': [],
        # output
        }
    kwargs['global_options'] += ['-y', '-hide_banner']
    kwargs['input_options'] += []
    kwargs['output_options'] += ["-map", "0", "-c", "copy", "-c:v"]
    
    nvidia = False
    if check_nvidia:
        nv_codec = get_ffmpeg_nv_support(ffmpeg_path)
        encoders = nv_codec.get('encoders')
        nvidia = encoders and 'h264_nvenc' in encoders and nv_codec.get('decoders')

    if nvidia:
        kwargs['input_options'] += ['-hwaccel', 'cuda']
        kwargs['output_options'] += ["h264_nvenc",     
                                    '-preset', 'p5',
                                    '-rc', 'vbr',
                                    '-cq', '23', 
                                    "-b:v", "0"]
        if width or height:
            kwargs['input_options'] += ['-hwaccel_output_format', 'cuda']
            kwargs['output_options'] += ["-vf", f"scale_cuda={width if width else "-2"}:{height if height else "-2"}:format=nv12"]
            # kwargs['output_options'] += ["-vf", f"scale_cuda={width}:{height}:format=nv12"]

    else:
        # kwargs['input_options'] += ['-hwaccel', 'auto']
        kwargs['output_options'] += ["libx264",
                                    '-preset', 'medium',
                                    '-crf', '22',
                                    ]
        if width or height:
            kwargs['output_options'] += ["-vf", f"scale={width if width else "-2"}:{height if height else "-2"}"]
            # kwargs['output_options'] += ["-vf", f"scale={width}:{height}"]
    kwargs['output_options'] += ["-pix_fmt", "yuv420p"]
    # old parameters
    # c  = [f'-hwaccel cuda -hwaccel_output_format cuda -i "{Path('input_path')}" -c:v h264_nvenc -b:v 4500K -vf "scale_cuda=1280:720" "{Path('output_path')}"']
    # rc = [f'-hwaccel auto  -i "{Path('input_path')}" -b:v 4500K -s 1280x720 "{Path('output_path')}"']
    return kwargs

def convert_video(input_path: str|Path, output_path: str|Path, ffmpeg_kwargs: list):
    pass

def scan_dir(dir_path: str|Path, find_10bit: bool = True, max_width: int = 1920, max_height: int = 1080, video_suffixes: set|list|tuple = VIDEO_SUFFIXES) -> list:
    files_to_convert = []
    for file_path in Path(dir_path).glob("**/*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in video_suffixes:
            continue
        needs_convert = False
        try:
            tracks = get_media_info(file_path)
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

        if width > max_width or height > max_height:
            needs_convert = True
        
        if needs_convert:
            files_to_convert.append(file_path)

    return files_to_convert

def test():
    # print(subprocess.list2cmdline( ['1', 'Video;{""VideoID"":%StreamKindID%,""BitDepth"":%BitDepth%,""Width"":%Width%,""Height"":%Height%}\\n', '1'] ))

    # Блок тестирования получения mediainfo
    vfile_path = r'D:\Видео\_маме\Кафедра (нужна конвертация)\01. Кафедра.mkv'
    # vfile_path = r'D:\_python\videotools\codex\two_video_streams_sample.mkv'
    # vfile_path = r'D:\Видео\_маме\Анора.mkv'
    results = get_media_info(vfile_path)
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

def main():
    kwargs1 = get_ffmpeg_kwargs(width=1280)
    kwargs2 = get_ffmpeg_kwargs(height=720, 
                      check_nvidia = False
                      )
    print(kwargs1)
    #Вывод: {'global_options': ['-y', '-hide_banner'], 'input_options': ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'], 'output_options': ['-map', '0', '-c', 'copy', '-c:v', 'h264_nvenc', '-preset', 'p5', '-rc', 'vbr', '-cq', '23', '-b:v', '0', '-vf', 'scale_cuda=1280:-2:format=nv12', '-pix_fmt', 'yuv420p']}
    print(kwargs2)
    #Вывод: {'global_options': ['-y', '-hide_banner'], 'input_options': [], 'output_options': ['-map', '0', '-c', 'copy', '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-vf', 'scale=-2:720', '-pix_fmt', 'yuv420p']}
    pass


if __name__ == "__main__":
    main()