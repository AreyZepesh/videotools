from common import (
    # subprocess, json, 
    Literal,
    Path,
    # run_subprocess, 
    Config,
    # TextIO, Iterable,
    rprint,
    CONSOLE,
    ProgressData, ProgressCallback, StderrCallback,
    )

from rich.progress import (
    Progress, 
    TextColumn, 
    BarColumn, TaskProgressColumn,
    TimeElapsedColumn, 
    # Task, 
    # SpinnerColumn,
                           )
# from rich.pretty import pretty_repr
from rich.markup import escape

from mediainfo import MediaFileInfo
from ffmpeg import FFmpegCmdBuilder
from proc import _execute_convert_video



#TODO: Разобраться с компановкой функций по модулям

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
    cfg.found_video_files = scan_dir(dir_path, cfg=cfg)


# Progress callback
def make_rich_progress_callbacks(live_progress: Progress, task_id):
    def on_progress(progress_data: dict[str, str]) -> None:
        # live_progress.log(f"{progress_data.get("out_time_us")}")
        live_progress.update(task_id, 
                            completed=progress_data.get("out_time_us"),
                            description=f"Convert ({progress_data.get("speed")}): ",
                                )

    def on_stderr(line: str) -> None:
        live_progress.log(escape(line))

    return on_progress, on_stderr

def make_plain_progress_callbacks(total_duration_us: float|int = 0):
    def on_progress(progress_data: dict[str, str]) -> None:
        to_print = [f"Speed: {progress_data.get("speed", "")}"]
        out_time = progress_data.get("out_time_us", 0)
        if total_duration_us and out_time and out_time < total_duration_us:
            percent = (progress_data.get("out_time_us")*100)/total_duration_us
            to_print.append(f"Progress: {percent:.2f}%")
        elif out_time:
            to_print.append(f"Out time: {out_time}")

        print("\r", " ".join(to_print), end='', flush=True)

    def on_stderr(line: str) -> None:
        print("\r", f"Error/warning: {line}\n", end='', flush=True)    

    return on_progress, on_stderr



# Single conversion
def _base_run_single_conversion(
        input_video_file: MediaFileInfo,
        ff_cmd: FFmpegCmdBuilder,
        fallback_ff_cmd: FFmpegCmdBuilder,
        on_progress: ProgressCallback | None = None,
        on_stderr: StderrCallback | None = None,
        ) -> None:
    input_video_file.output_path.parent.mkdir(parents=True, exist_ok=True)
    if on_stderr:
        on_stderr(f"\rStart: {input_video_file}")
    try:
        _execute_convert_video(
            ff_cmd.build(input_video_file),
            on_progress=on_progress,
            on_stderr=on_stderr, 
                )
    except Exception as nvidia_ex:
        if on_stderr:
            on_stderr(nvidia_ex)
            on_stderr(f"Пробуем конвертацию с другими параметрами")
        try:
            _execute_convert_video( 
                fallback_ff_cmd.build(input_video_file),
                on_progress=on_progress,
                on_stderr=on_stderr, 
                    )
        except Exception as fallback_ex:
            if on_stderr:
                on_stderr(fallback_ex)
                on_stderr(f"Пропуск файла: {input_video_file.path}")
            raise fallback_ex

def run_single_conversion_plain(
        input_video_file: MediaFileInfo,
        ff_cmd: FFmpegCmdBuilder,
        fallback_ff_cmd: FFmpegCmdBuilder,
        ) -> None:
    # print(input_video_file)
    on_progress, on_stderr = make_plain_progress_callbacks(input_video_file.duration_us)

    _base_run_single_conversion(input_video_file, ff_cmd, fallback_ff_cmd, on_progress, on_stderr)
            
def run_single_conversion_rich(
        input_video_file: MediaFileInfo,
        ff_cmd: FFmpegCmdBuilder,
        fallback_ff_cmd: FFmpegCmdBuilder,
        ) -> None:
    with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=CONSOLE,
            ) as live_progress:
        # live_progress.log(f"Start: {input_video_file}")
        task_id = live_progress.add_task("Convert ( speed ): ", total=input_video_file.duration_us)
        on_progress, on_stderr = make_rich_progress_callbacks(live_progress, task_id)

        _base_run_single_conversion(input_video_file, ff_cmd, fallback_ff_cmd, on_progress, on_stderr)

# Mass conversion
def run_mass_conversion(dir_path, 
                        cfg: Config,
                        progress_mode: Literal["plain", "rich"] = "plain",
                        ) -> None:
    if cfg.need_rescan or not cfg.found_video_files:
        rprint("Список пуст, запуск поиска")
        run_only_scan(dir_path, cfg=cfg)

    if not cfg.found_video_files:
        return
    
    rprint(f"По заданным параметрам найдено: {len(cfg.found_video_files)}")

    ff_cmd = FFmpegCmdBuilder(cfg)
    fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)
    runners = {
        "plain": run_single_conversion_plain,
        "rich": run_single_conversion_rich,
        # "tkinter": run_single_conversion_tkinter,
        }
    runner = runners.get(progress_mode, run_single_conversion_plain)
    
    for video_file in cfg.found_video_files:
        video_file: MediaFileInfo
        try:
            runner(video_file, ff_cmd, fallback_ff_cmd)
        except KeyboardInterrupt:
            print("Прервано пользователем")
            break
        except:
            if video_file.output_path.exists():
                video_file.output_path.unlink()

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
    # for line in cfg.found_video_files:
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