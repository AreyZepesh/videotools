import subprocess
from pathlib import Path
# from pathlib import PurePath
# from pathlib import PureWindowsPath

MEDIAINFO = r'D:\_python\.video_cli\MediaInfo\MediaInfo.exe'
VIDIE_SUFFIXES = [".mp4", ".mkv", ".avi", ".mov", ".ts", '.m4v']

def get_bit_depth(path: str, mediainfo_path: str = MEDIAINFO) -> str|None:
    if not Path(mediainfo_path).exists():
        raise ValueError("MediaInfo.exe не найдено")
    if not Path(path).exists():
        raise ValueError("Файл не найден")

    param = '--Inform=Video;%BitDepth%'
    result = subprocess.run(
        [mediainfo_path, param, path],
        capture_output=True,
        text=True,
        encoding="utf-8-sig",
        )
    
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    
    # NOTE: Результат может быть None или списком/длинной строкой (если вдруг попадется чудофайл с более чем одним видеопотоком)
    return result.stdout.strip()

def scan_dir(dir_path, video_suffixes = VIDIE_SUFFIXES):
    tenbit_paths = []
    suffixes = set()
    for filepath in Path(dir_path).glob("**/*"):
        if filepath.is_dir():
            continue
        if filepath.suffix.lower() not in video_suffixes:
            suffixes.add(filepath.suffix)
            continue

        try:
            bit_depth = get_bit_depth(filepath)
        except Exception as e:
            print(f"Ошибка при чтении файла, пропускаем: {filepath}")
            print(e)
            continue

        if bit_depth == "10":
            tenbit_paths.append(filepath)
        elif bit_depth != "8":
            print(f"{filepath}: {bit_depth=}")

    print(suffixes)
    return tenbit_paths

def main():
    # "D:\_python\.video_cli\MediaInfo\MediaInfo.exe" --Inform="Video;%BitDepth%" "D:\Видео\_маме\Кафедра (нужна конвертация)\01. Кафедра.mkv"
    # vfile_path = r'D:\Видео\_маме\Кафедра (нужна конвертация)\01. Кафедра.mkv'
    # # vfile_path = r'D:\Видео\_маме\Анора.mkv'
    # result = get_bit_depth(vfile_path)
    # print(result)

    # data = scan_dir(r"G:")
    data = scan_dir(r"D:\Видео\_маме")
    for x in data:
        print(x)


if __name__ == "__main__":
    main()