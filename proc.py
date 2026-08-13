from common import (
    subprocess, 
    # json, Path,
    # run_subprocess, Config,
    TextIO, Iterable,
    rprint, 
    CONSOLE
    )

from rich.progress import Progress, TextColumn, Task, TimeElapsedColumn, SpinnerColumn
from rich.pretty import pretty_repr
from rich.markup import escape
import threading

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

def read_stderr(stderr, stderr_pipe: list[str], live_progress: Progress = None):
    for line in stderr:
        line: str = line.rstrip()
        if line:
            stderr_pipe.append(line)
            if live_progress:
                live_progress.log(escape(line))

def rich_progress():
    return
        
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
            # console=CONSOLE,
            ) as live_progress:
            # task_id_err = live_progress.add_task("Warning/Error:", total=None)
            task_id_out = live_progress.add_task("Convert: starting...", total=None)
            
            # Читаем ошибки в другом потоке
            stderr_pipe = []
            stderr_thread = threading.Thread(
                target=read_stderr,
                args=(process.stderr, stderr_pipe, live_progress),
                daemon=True, 
                    )
            stderr_thread.start()

            for progress_data in read_ffmpeg_progress(process.stdout):
                # live_progress.update(task_id_err, description=pretty_repr(stderr_pipe))
                live_progress.update(task_id_out, description=pretty_repr(progress_data))

            returncode = process.wait()
            # print()
            stderr = '\n'.join(stderr_pipe) #process.stderr.read()
            # print(stderr)

            if returncode != 0:
                raise RuntimeError(f"ffmpeg завершился с ошибкой: {returncode}\n{stderr}")