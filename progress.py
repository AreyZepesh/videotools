from rich.console import Console, Group
from rich.markup import escape
# from rich.text import Text
from rich.live import Live
from rich.progress import (
    Progress, 
    TextColumn, 
    BarColumn, TaskProgressColumn,
    TimeElapsedColumn, 
    MofNCompleteColumn, 
    # ProgressColumn,
        )

from contextlib import contextmanager
from typing import Protocol
import time

from common import ProgressData

class ConversionProgress(Protocol):
    def add_files_progress(self, total: int = 0) -> None:
        ...

    def update_files_progress(self) -> None:
        ...

    def add_conversion_progress(self, total_duration_us: float|int = 0):
        ...

    def on_conversion_progress(self, progress_data: ProgressData) -> None:
        ...

    def done_conversion_progress(self):
        ...

    def on_log(self, line: str) -> None:
        ...
    
    def print(self, line: str) -> None:
        ...

class PlainProgress:
    def __init__(self):
        self.live_progress = self._live_progress_cm()
        
        self.total_duration_us = 0
        self.total_files = 0
        self.iter_files = 0

        self.start_time = None
        self.end_time = None

    @contextmanager
    def _live_progress_cm(self):
        try:
            # Передаем управление в with
            yield
        finally:
            pass

    def add_files_progress(self, total: int = 0) -> None:
        self.total_files = total

    def update_files_progress(self) -> None:
        self.iter_files += 1
        print(f"Выполнено {self.iter_files}/{self.total_files}\n")

    def add_conversion_progress(self, total_duration_us: float|int = 0):
        self.total_duration_us = total_duration_us
        self.start_time = time.time()

    def on_conversion_progress(self, progress_data: ProgressData) -> None:
        to_print = [f"Speed: {progress_data.get('speed', '')}"]
        out_time = progress_data.get("out_time_us", 0)
        if self.total_duration_us and out_time and out_time <= self.total_duration_us:
            percent = (progress_data.get("out_time_us")*100)/self.total_duration_us
            to_print.append(f"Progress: {percent:.2f}%")
        elif out_time:
            to_print.append(f"Out time: {out_time}")

        print("\r   ", " ".join(to_print), end='', flush=True)

    def done_conversion_progress(self):
        if self.start_time is None:
            return
        self.end_time = time.time()
        execution_time = self.end_time - self.start_time
        print(f"\nЗавершено за {execution_time:.2f} секунды")

    def on_log(self, line: str) -> None:
        print("\r   ", f"Error/warning: {line}", flush=True)
        
    def print(self, line: str) -> None:
        print(line)
        
class RichProgress:
    def __init__(self):
        self.console = Console(log_path=False)

        self.files_task = None
        self.conversion_task = None
        
        self.files_progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                                    )
        self.conversion_progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                                    )
        
        self.live_progress = Live(
                                Group(
                                    self.files_progress, 
                                    self.conversion_progress,
                                    ),
                                console=self.console
                                )
    
    def add_files_progress(self, total: int = 0) -> None:
        self.files_task = self.files_progress.add_task("Converted files: ", total=total)

    def update_files_progress(self) -> None:
        if self.files_task is not None:
            self.files_progress.update(self.files_task, advance=1)

    def add_conversion_progress(self, total_duration_us: float|int = 0):
        self.conversion_task = self.conversion_progress.add_task("Convert ( speed ): ", total=total_duration_us)

    def on_conversion_progress(self, progress_data: ProgressData) -> None:
        if self.conversion_task is not None:
            self.conversion_progress.update(self.conversion_task,
                                            completed=progress_data.get("out_time_us"),
                                            description=f"Convert ({progress_data.get('speed')}): ",
                                            )
    def done_conversion_progress(self):
        try:
            task_time = self.conversion_progress.tasks[self.conversion_task].elapsed
            self.on_log(f"Завершено за {task_time:.2f} секунды\n")
        except Exception as e:
            self.console.log(e, 
                            # log_locals=True,
                            )
            self.on_log("Завершено\n")
        finally:
            self.conversion_progress.update(self.conversion_task, visible=False)
            self.conversion_task = None

    def on_log(self, line: str) -> None:
        self.console.log(escape(line))
        
    def print(self, line: str) -> None:
        self.console.print(escape(line))
        

# class AdaptiveColumn(ProgressColumn):
#     def render(self, task) -> Text:
#         if task.fields.get("style") == "count":
#             return Text(f"{int(task.completed)}/{int(task.total)}")
#         percent = (task.completed / task.total * 100) if task.total else 0
#         return Text(f"{percent:>3.0f}%")
    