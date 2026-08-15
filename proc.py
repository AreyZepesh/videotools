from common import (
    subprocess, 
    # json, Path,
    # run_subprocess, Config,
    TextIO, Iterable,
    rprint, 
    str_to_int, str_to_float,
    # CONSOLE,
    ProgressData, ProgressCallback, StderrCallback,
    )

import threading

def read_ffmpeg_progress(stdout: Iterable[str]|TextIO):
    progress = {}
    for line in stdout:
        line = line.strip()
        if not line or "=" not in line:
            continue

        key, _, value = line.partition("=")
        if key in ['frame', 'total_size', 'out_time_us', 'out_time_ms', 'dup_frames', 'drop_frames']:
            value = str_to_int(value)
        if key in ['fps']:
            value = str_to_float(value)
        progress[key] = value

        if key == "progress":
            yield progress
            progress = {}

def read_stderr(stderr, stderr_pipe: list[str], on_stderr: StderrCallback | None = None):
    for line in stderr:
        line: str = line.rstrip()
        if line:
            stderr_pipe.append(line)
            if on_stderr:
                on_stderr(line)
        
def _execute_convert_video(ffmpeg_args: list[str],
        on_progress: ProgressCallback | None = None,
        on_stderr: StderrCallback | None = None,
        ) -> None:
    with subprocess.Popen(ffmpeg_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8-sig",
                    ) as process:
        
        # Читаем ошибки в другом потоке
        stderr_pipe = []
        stderr_thread = threading.Thread(
            target=read_stderr,
            args=(process.stderr, stderr_pipe, on_stderr),
            daemon=True, 
                )
        stderr_thread.start()

        for progress_data in read_ffmpeg_progress(process.stdout):
            if on_progress:
                on_progress(progress_data)

        returncode = process.wait()
        stderr_thread.join(timeout=1)
        stderr = '\n'.join(stderr_pipe)

        if returncode != 0:
            raise RuntimeError(f"ffmpeg завершился с ошибкой: {returncode}\n{stderr}")
            

def __execute_convert_video_old(ffmpeg_args: list[str]):
    # with subprocess.Popen(ffmpeg_args,
    #                     stdout=subprocess.PIPE,
    #                     stderr=subprocess.PIPE,
    #                     # stderr=None,
    #                     text=True,
    #                     encoding="utf-8-sig",) as process:
        
    #     with Progress(
    #         SpinnerColumn(),
    #         *Progress.get_default_columns(),
    #         # TextColumn("{task.description}"), 
    #         TimeElapsedColumn(),
    #         # console=CONSOLE,
    #         ) as live_progress:
    #         # task_id_err = live_progress.add_task("Warning/Error:", total=None)
    #         task_id_out = live_progress.add_task("Convert:", total=duration)
            
    #         # Читаем ошибки в другом потоке
    #         stderr_pipe = []
    #         stderr_thread = threading.Thread(
    #             target=read_stderr,
    #             args=(process.stderr, stderr_pipe, live_progress),
    #             daemon=True, 
    #                 )
    #         stderr_thread.start()

    #         for progress_data in read_ffmpeg_progress(process.stdout):
    #             # live_progress.update(task_id_err, description=pretty_repr(stderr_pipe))
    #             live_progress.update(task_id_out, 
    #                                 completed=progress_data.get("out_time_us"),
    #                                 # description=pretty_repr(progress_data),
    #                                  )

    #         returncode = process.wait()
    #         stderr_thread.join()
    #         # print()
    #         stderr = '\n'.join(stderr_pipe) #process.stderr.read()
    #         # print(stderr)

    #         if returncode != 0:
    #             raise RuntimeError(f"ffmpeg завершился с ошибкой: {returncode}\n{stderr}")
    process = subprocess.run(ffmpeg_args)
    if process.returncode != 0:
        raise RuntimeError(f"Процесс завершился неверно")