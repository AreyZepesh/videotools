import subprocess
import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict, replace

@dataclass
class Config():
    ffmpeg_path: Path|str|None = field(default=None)
    mediainfo_path: Path|str|None = field(default=None)

    video_suffixes: list[str] = field(default_factory=lambda: [".mp4", ".mkv", ".avi", ".mov", ".ts", '.m4v'])

    width: int|None = field(default=None)
    height: int|None = field(default=None)
    find_10bit: bool = field(default=True)
    check_nvidia: bool = field(default=True)
    exclude_subtitles: bool = field(default=False)

    cfg_file_path: str = field(default=Path('./config.json'))

    def __post_init__(self):
        if self.ffmpeg_path:
            self.ffmpeg_path = Path(self.ffmpeg_path).absolute()
        if self.mediainfo_path:
            self.mediainfo_path = Path(self.mediainfo_path).absolute()
    
    def save_cfg(self):
        config = dict(
            ffmpeg = self.ffmpeg_path,
            mediainfo = self.mediainfo_path,
            )
        with open(self.cfg_file_path, 'w', encoding='utf-8-sig') as file:
            # json.dump(config, file, indent=0)
            json.dump(asdict(self), file, indent=0)
            
    def load_cfg(self):
        if Path(self.cfg_file_path).exists():
            with open(self.cfg_file_path, 'r', encoding='utf-8-sig') as file:
                config = json.load(file)
                self.ffmpeg_path = config.get("ffmpeg")
                self.mediainfo_path = config.get("mediainfo")
        else:
            self.find_exes()
            # self.save_cfg()
            pass
        self.__post_init__()

    def find_exes(self):
        for path in Path('.').rglob('*.exe'):
            if self.ffmpeg_path and self.mediainfo_path:
                break
            if not self.ffmpeg_path and path.name.lower() == 'ffmpeg.exe':
                if self._is_ffmeg(path):
                    self.ffmpeg_path = str(path.absolute())
            if not self.mediainfo_path and path.name.lower() == 'mediainfo.exe':
                if self._is_mediainfo(path):
                    self.mediainfo_path = str(path.absolute())

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

    def get_dict(self):
        return asdict(self)
    
    def get_replaced_copy(self, **changes):
        return replace(self, **changes)



# SUBPROCESS BLOCK
def run_subprocess(args: list, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8-sig",
        **kwargs
        )

if __name__ == "__main__":
    x = Config()
    # x.cfg_file_path = "./config.2"
    # x.save_cfg()
    pass