from typing import Literal
from pathlib import Path
from proc import execute_convert_video

from config import Config
from mediainfo import MediaFileInfo
from ffmpeg import FFmpegCmdBuilder

from progress import (
    ConversionProgress,
    make_progress,
    )

# Path scan
def scan_dir(cfg: Config) -> list[MediaFileInfo]:
    files_to_convert = []
    for file_path in cfg.input_dir.rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in cfg.video_suffixes:
            continue
        try:
            v_file = MediaFileInfo(file_path, cfg)
            if v_file.need_convert:
                files_to_convert.append(v_file)
        except Exception as scan_ex:
            print(scan_ex)
            continue

    return files_to_convert

def run_only_scan(cfg: Config):
    cfg.scan_result = scan_dir(cfg=cfg)

# Single conversion
def run_single_conversion_with_callbacks(
        input_video_file: MediaFileInfo,
        ff_cmd: FFmpegCmdBuilder,
        fallback_ff_cmd: FFmpegCmdBuilder,
        progress: ConversionProgress,
        ) -> None:
    input_video_file.output_path.parent.mkdir(parents=True, exist_ok=True)
    primary_args = ff_cmd.build(input_video_file)
    fallback_args = fallback_ff_cmd.build(input_video_file)
    on_log = progress.on_log
    on_progress = progress.on_conversion_progress

    on_log(f"\rStart: {input_video_file}")
    try:
        execute_convert_video(
            primary_args,
            on_progress=on_progress,
            on_stderr=on_log, 
                )
    except KeyboardInterrupt:
        raise 
    except Exception as primary_ex:
        on_log(str(primary_ex))
        if primary_args == fallback_args:
            # on_log("Запасная команда совпадает с основной, повтор пропущен")
            raise primary_ex
        on_log(f"Пробуем конвертацию с другими параметрами")

        try:
            execute_convert_video( 
                fallback_args,
                on_progress=on_progress,
                on_stderr=on_log, 
                    )
        except KeyboardInterrupt:
            raise 
        except Exception as fallback_ex:
            on_log(str(fallback_ex))
            on_log(f"Пропуск файла: {input_video_file.path}")
            raise fallback_ex

def run_mass_conversion(
        # dir_path, 
                        cfg: Config,
                        # progress_mode: Literal["plain", "rich"] = "plain",
                        ) -> None:
    progress = make_progress(cfg.progress_mode)

    with progress.live_progress:
        if cfg.need_rescan or not cfg.scan_result:
            progress.print("Список пуст, запуск поиска")
            run_only_scan(cfg=cfg)

        if not cfg.scan_result:
            return
        
        progress.print(f"По заданным параметрам найдено: {len(cfg.scan_result)}")

        ff_cmd = FFmpegCmdBuilder(cfg)
        fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)
        
        cfg.scan_result.reverse() #TODO - для тестов, убрать после

        progress.add_files_progress(len(cfg.scan_result))
        for video_file in cfg.scan_result:
            video_file: MediaFileInfo
            try:
                progress.add_conversion_progress(video_file.duration_us)
                run_single_conversion_with_callbacks(video_file, ff_cmd, fallback_ff_cmd, progress)
            except KeyboardInterrupt:
                print("\nПрервано пользователем")
                break
            except Exception as convert_ex:
                progress.on_log(str(convert_ex))
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
    # cfg.progress_mode = "plain"
    # cfg.output_mode = "subfolder"
    # dir = r"G:\\"

    # ff_cmd = FFmpegCmdBuilder(cfg)
    # fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)

    # run_only_scan(cfg)
    # for line in cfg.scan_result:
    #     print()
    #     print(ff_cmd.printable(ff_cmd.build(line)))
    #     print(ff_cmd.printable(fallback_ff_cmd.build(line)))


    run_mass_conversion(cfg)

def main():
    run_test()
    pass

if __name__ == "__main__":
    main()