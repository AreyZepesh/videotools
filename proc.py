import subprocess
import threading
from typing import TextIO
from collections.abc import Iterable

from common import (
    str_to_int, str_to_float,
    ProgressData, ProgressCallback, StderrCallback,
    )


def list2cmdline(*args, **kwargs):
    return subprocess.list2cmdline(*args, **kwargs)

def run_subprocess(args: list, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8-sig",
        **kwargs
        )

def read_ffmpeg_progress(stdout: Iterable[str]|TextIO):
    progress: ProgressData = {}
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
        
def execute_convert_video(ffmpeg_args: list[str],
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
            
