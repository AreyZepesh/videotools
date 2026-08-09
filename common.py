import subprocess
import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict, replace
from typing import Literal, TextIO
from collections.abc import Iterable

from rich import print as rprint

DEFAULT_VIDEO_SUFFIXES = [
    ".mp4", ".mkv", ".avi", ".mov", ".ts", '.m4v',
    ".webm", ".flv", ".wmv", ".mpg", ".mpeg",
    ".m2ts", ".mts", ".vob", ".3gp", ".3g2",
    ".ogv", ".rm", ".rmvb", ".asf", ".divx",
    ".f4v", ".mxf", ".y4m", ".nut", ".dv",
    ]
@dataclass
class Config():
    input_dir: Path|str|None = field( default_factory=lambda: Path(__file__).parent.absolute() )
    output_dir: Path|str|None = field(default=None)
    output_mode: Literal["tree", "subfolder"] = field(default="tree")

    ffmpeg_path: Path|str|None = field(default=None)
    mediainfo_path: Path|str|None = field(default=None)

    video_suffixes: list[str] = field( default_factory=lambda: DEFAULT_VIDEO_SUFFIXES[:5] )
    output_file_suffix: str|None = field(default=None)

    width: int|None = field(default=None)
    height: int|None = field(default=None)
    find_10bit: bool = field(default=True)
    check_nvidia: bool = field(default=True)

    use_only_basic_subtitles: bool = field(default=False)
    exclude_subtitles: bool = field(default=False)
    extract_subtitles: bool = field(default=False)
    
    found_video_files: list|None = field(default=None)
    need_rescan: bool = field(default=False)

    cfg_file_path: str = field(default=Path('./config.json'))
    _exe_pathes_is_check: bool = field(default=False)
    
    def __setattr__(self, name, value):
        if name =='output_file_suffix':
            if value:
                if value[0] != ".":
                    value = "."+value
                if value not in DEFAULT_VIDEO_SUFFIXES:
                    raise ValueError(f"Неизвестный формат видео: '{value}', возможно не предусмотрен при разработке")
        if name =='output_mode':
            if value not in ["tree", "subfolder"]:
                raise ValueError('output_mode может быть только "tree" или "subfolder"')
        if name in ['input_dir', 'output_dir', 'ffmpeg_path', 'mediainfo_path', 'cfg_file_path']:
            value = Path(value).absolute() if value else None
        super().__setattr__(name, value)

    def save_cfg(self):
        config = dict(
            ffmpeg = str(self.ffmpeg_path),
            mediainfo = str(self.mediainfo_path),
            )
        with open(self.cfg_file_path, 'w', encoding='utf-8-sig') as file:
            # json.dump(config, file, indent=0)
            json.dump(self.get_dict(from_save=True), file, indent=0)
            
    def load_cfg(self):
        cfg_loaded = False
        if self.cfg_file_path.exists():
            try:
                with open(self.cfg_file_path, 'r', encoding='utf-8-sig') as file:
                    content = file.read()
                    if len(content) != 0:
                        config = json.loads(content)
                        if config:
                            for k, v in config.items():
                                if k in self.__dataclass_fields__:
                                    self.__setattr__(k, v)
                            cfg_loaded = True
                            
            except Exception as load_ex:
                print(load_ex)
                cfg_loaded = False
        if cfg_loaded:
            self.check_exes()
        # if not cfg_loaded or not self.ffmpeg_path or not self.mediainfo_path:
        if not cfg_loaded or not self._exe_pathes_is_check:
            self.find_exes()
            self.save_cfg()
            pass
        # self.__post_init__()

    def find_exes(self):
        if self.ffmpeg_path and self.mediainfo_path:
            return
        for path in Path('.').rglob('*.exe'):
            if not self.ffmpeg_path and path.name.lower() == 'ffmpeg.exe':
                if self._is_ffmeg(path):
                    self.ffmpeg_path = str(path.absolute())
            if not self.mediainfo_path and path.name.lower() == 'mediainfo.exe':
                if self._is_mediainfo(path):
                    self.mediainfo_path = str(path.absolute())
        if self.ffmpeg_path and self.mediainfo_path:
            self._exe_pathes_is_check = True

    def check_exes(self) -> bool:
        if self.ffmpeg_path and self.mediainfo_path and not self._exe_pathes_is_check:
            self._exe_pathes_is_check = self._is_ffmeg(self.ffmpeg_path) and self._is_mediainfo(self.mediainfo_path)
        return self._exe_pathes_is_check
            

    def _is_ffmeg(self, ffmpeg_path: Path|str) -> bool:
        ffmpeg_path = Path(ffmpeg_path)
        try:
            process = run_subprocess([ffmpeg_path.absolute(), '-version'])
            if 'ffmpeg' in process.stdout.strip().split():
                return True
        except:
            return False

    def _is_mediainfo(self, mediainfo_path: Path|str) -> bool:
        mediainfo_path = Path(mediainfo_path)
        try:
            # NOTE: таймаут выкидывает прогу если она долго отвечает, мини защита от открытого гуя
            process = run_subprocess([mediainfo_path.absolute(), '--Version'], 
                                    **dict(timeout = 10)
                                    )
            if 'MediaInfo' in process.stdout.strip().split():
                return True
        except:
            return False

    def get_dict(self, from_save = False):
        data = asdict(self)
        if from_save:
            data.pop('input_dir', None)
            data.pop('cfg_file_path', None)
        for k, v in data.items():
            if isinstance(v, Path):
                data[k] = str(v)
        return data
    
    def get_replaced_copy(self, **changes):
        return replace(self, **changes)

    def build_output_path(self, file_path: Path|str):
        """Заменяет корень в пути, сохраняя структуру дерева"""
        fp = Path(file_path)
        output_path = None
        relative = fp.relative_to(self.input_dir)
        if self.output_mode == "subfolder":
            output_path = Path(fp.parent,"_converted", fp.name).absolute()
        elif self.output_mode == "tree":
            if self.output_dir is not None:
                output_path = Path(self.output_dir, relative).absolute()
            else:
                output_path = Path(self.input_dir.parent, f"{self.input_dir.name}_converted", relative).absolute()
        else:
            raise ValueError("Output mode must be 'subfolder' or 'tree' only")

        if self.output_file_suffix:
            output_path = output_path.with_suffix(self.output_file_suffix)
        return output_path
        


# SUBPROCESS BLOCK
def run_subprocess(args: list, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8-sig",
        **kwargs
        )

def str_to_int(value, default=None):
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    digits = "".join(c for c in str(value or "") if c.isdecimal())
    return int(digits) if digits else default

if __name__ == "__main__":
    # print(str_to_int("s"))
    pass