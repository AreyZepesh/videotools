from rich import print as rprint

from common import (
    Literal, # from typing import
    Path, # from pathlib import
        )
from proc import (
    execute_convert_video, 
        )

from config import Config
from mediainfo import MediaFileInfo
from ffmpeg import FFmpegCmdBuilder

from progress import (
    MyProgress,
    PlainProgress,
    RichProgress,
    )

# Path scan
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

def run_only_scan(dir_path, cfg: Config):
    cfg.scan_result = scan_dir(dir_path, cfg=cfg)

# Single conversion
def run_single_conversion_with_callbacks(
        input_video_file: MediaFileInfo,
        ff_cmd: FFmpegCmdBuilder,
        fallback_ff_cmd: FFmpegCmdBuilder,
        progress: MyProgress,
        ) -> None:
    input_video_file.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    on_log = progress.on_log
    on_progress = progress.on_conversion_progress

    on_log(f"\rStart: {input_video_file}")

    try:
        execute_convert_video(
            ff_cmd.build(input_video_file),
            on_progress=on_progress,
            on_stderr=on_log, 
                )
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as nvidia_ex:
        if on_log:
            on_log(str(nvidia_ex))
            on_log(f"Пробуем конвертацию с другими параметрами")
        try:
            execute_convert_video( 
                fallback_ff_cmd.build(input_video_file),
                on_progress=on_progress,
                on_stderr=on_log, 
                    )
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as fallback_ex:
            if on_log:
                on_log(str(fallback_ex))
                on_log(f"Пропуск файла: {input_video_file.path}")
            raise fallback_ex

def run_mass_conversion(dir_path, 
                        cfg: Config,
                        progress_mode: Literal["plain", "rich"] = "plain",
                        ) -> None:
    progress_type = {"plain": PlainProgress(),
                     "rich": RichProgress(),}
    progress: MyProgress = progress_type.get(progress_mode, PlainProgress)

    with progress.live_progress:
        if cfg.need_rescan or not cfg.scan_result:
            progress.print("Список пуст, запуск поиска")
            run_only_scan(dir_path, cfg=cfg)

        if not cfg.scan_result:
            return
        
        progress.print(f"По заданным параметрам найдено: {len(cfg.scan_result)}")

        ff_cmd = FFmpegCmdBuilder(cfg)
        fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)
        
        cfg.scan_result.reverse()

        progress.add_files_progress(len(cfg.scan_result))
        for video_file in cfg.scan_result:
            video_file: MediaFileInfo
            try:
                progress.add_conversion_progress(video_file.duration_us)
                run_single_conversion_with_callbacks(video_file, ff_cmd, fallback_ff_cmd, progress)
            except KeyboardInterrupt:
                print("\nПрервано пользователем")
                break
            except:
                if video_file.output_path.exists():
                    video_file.output_path.unlink()
            finally:
                progress.done_conversion_progress()
                progress.update_files_progress()

# OTHER BLOCK
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
    # for line in cfg.scan_result:
    #     print()
    #     print(ff_cmd.printable(ff_cmd.build(line)))


    run_mass_conversion(dir, cfg, 
                        "rich",
                        )

def main():
    run_test()
    pass

if __name__ == "__main__":
    main()