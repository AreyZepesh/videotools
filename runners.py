from common import (
    # subprocess, json, 
    Path,
    # run_subprocess, 
    Config,
    # TextIO, Iterable,
    rprint,
    CONSOLE
    )

from mediainfo import MediaFileInfo
from ffmpeg import FFmpegCmdBuilder

from proc import _execute_convert_video

def scan_dir(dir_path: str|Path, cfg: Config) -> list[MediaFileInfo]:
    files_to_convert = []
    for file_path in Path(dir_path).rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in cfg.video_suffixes:
            continue
        try:
            v_file = MediaFileInfo(file_path, cfg)
            if v_file.need_convert:
                files_to_convert.append(v_file)
        except Exception as scan_ex:
            rprint(scan_ex)
            continue

    return files_to_convert

def run_single_conversion(input_video_file: MediaFileInfo, ff_cmd: FFmpegCmdBuilder, fallback_ff_cmd: FFmpegCmdBuilder):
    input_video_file.output_path.parent.mkdir(parents=True, exist_ok=True)
    print(input_video_file)
    try:
        _execute_convert_video(
            ff_cmd.build(input_video_file)
                      )
    except Exception as nvidia_ex:
        print(nvidia_ex)
        try:
            _execute_convert_video(
                fallback_ff_cmd.build(input_video_file)
                    )
        except Exception as fallback_ex:
            print(fallback_ex)
            if input_video_file.output_path.exists():
                input_video_file.output_path.unlink()
            return
        
def run_only_scan(dir_path, cfg: Config):
    cfg.found_video_files = scan_dir(dir_path, cfg=cfg)

def run_mass_conversion(dir_path, cfg: Config):
    if cfg.need_rescan or not cfg.found_video_files:
        rprint("Список пуст, запуск поиска")
        cfg.found_video_files = scan_dir(dir_path, cfg=cfg)

    if not cfg.found_video_files:
        return
    
    rprint(f"По заданным параметрам найдено: {len(cfg.found_video_files)}")

    ff_cmd = FFmpegCmdBuilder(cfg)
    fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)
    
    for video_file in cfg.found_video_files:
        run_single_conversion(video_file, ff_cmd, fallback_ff_cmd)

def run_test():
    
    cfg = Config()
    cfg.load_cfg()
    cfg.use_only_basic_subtitles = True
    # cfg.exclude_subtitles = True
    # cfg.extract_subtitles = True
    # cfg.width = 1280
    # dir = r"D:\Видео\_маме\Кафедра (нужна конвертация)"
    dir = r"D:\Видео\_test"
    cfg.input_dir = Path(dir)
    cfg.output_dir = Path(r"D:\Видео\_converted")
    cfg.output_file_suffix = 'mp4'
    # cfg.output_mode = "subfolder"
    # dir = r"G:\\"

    # ff_cmd = FFmpegCmdBuilder(cfg)
    # run_only_scan(dir, cfg)
    # for line in cfg.found_video_files:
    #     print(ff_cmd.printable(ff_cmd.build(line)))


    run_mass_conversion(dir, cfg)

# OTHER BLOCK

def main():
    run_test()
    pass

if __name__ == "__main__":
    main()