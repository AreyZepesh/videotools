from common import (
    subprocess, json, Path,
    run_subprocess, Config,
    TextIO, Iterable,
    rprint,
    )

from mediainfo import MediaFileInfo
from ffmpeg import FFmpegCmdBuilder

from rich.progress import Progress, TextColumn, Task, TimeElapsedColumn, SpinnerColumn
from rich.pretty import pretty_repr
import threading

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
            print(scan_ex)
            continue

    return files_to_convert


# RUN BLOCK
def _execute_convert_video_(ffmpeg_args: list[str]):
    process = subprocess.run(ffmpeg_args)
    if process.returncode != 0:
        raise RuntimeError(f"Процесс завершился неверно")
    
def read_ffmpeg_progress(stdout: Iterable[str]|TextIO):
    progress = {}
    for line in stdout:
        line = line.strip()
        if not line or "=" not in line:
            continue

        key, _, value = line.partition("=")
        progress[key] = value

        if key == "progress":
            yield progress
            progress = {}

def read_stderr(stderr, stderr_pipe: list[str]):
    for line in stderr:
        line = line.rstrip()
        if line:
            stderr_pipe.append(line)
        
def _execute_convert_video(ffmpeg_args: list[str], on_progress = None):
    with subprocess.Popen(ffmpeg_args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        # stderr=None,
                        text=True,
                        encoding="utf-8-sig",) as process:
        
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"), 
            TimeElapsedColumn(),

            ) as progress:
            task_id_err = progress.add_task("Warning/Error:", total=None)
            task_id_out = progress.add_task("Convert: starting...", total=None)
            stderr_pipe = []
            stderr_thread = threading.Thread(
                target=read_stderr,
                args=(process.stderr, stderr_pipe),
                daemon=True, )
            
            stderr_thread.start()
            for progress_data in read_ffmpeg_progress(process.stdout):
                progress.update(task_id_err, description=pretty_repr(stderr_pipe))
                progress.update(task_id_out, description=pretty_repr(progress_data))

            returncode = process.wait()
            print()
            stderr = process.stderr.read()
            print(stderr)

            if returncode != 0:
                raise RuntimeError(f"ffmpeg завершился с ошибкой: {returncode}\n{stderr}")


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