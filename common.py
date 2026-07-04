import subprocess
import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict

@dataclass
class Config():
    cfg_file_path: str = field(default=Path('./config.json'))

    ffmpeg: Path|str|None = field(default=None)
    mediainfo: Path|str|None = field(default=None)

    video_suffixes: list[str] = field(default_factory=lambda: [".mp4", ".mkv", ".avi", ".mov", ".ts", '.m4v'])

    width: int|None = field(default=None)
    height: int|None = field(default=None)
    check_nvidia: bool = field(default=True)
    exclude_subtitles: bool = field(default=False)
    
    def save_cfg(self):
        config = dict(
            ffmpeg = self.ffmpeg,
            mediainfo = self.mediainfo,
            )
        with open(self.cfg_file_path, 'w', encoding='utf-8-sig') as file:
            # json.dump(config, file, indent=0)
            json.dump(asdict(self), file, indent=0)
            
    def load_cfg(self):
        if not Path(self.cfg_file_path).exists():
            pass
            # self.find_exes()
            # self.save_cfg()
        with open(self.cfg_file_path, 'r', encoding='utf-8-sig') as file:
            config = json.load(file)
            self.ffmpeg = config.get("ffmpeg")
            self.mediainfo = config.get("mediainfo")

    def find_exes(self):
        for path in Path('.').rglob('*.exe'):
            if self.ffmpeg and self.mediainfo:
                break
            if not self.ffmpeg and path.name.lower() == 'ffmpeg.exe':
                if self._is_ffmeg(path):
                    self.ffmpeg = str(path.absolute())
            if not self.mediainfo and path.name.lower() == 'mediainfo.exe':
                if self._is_mediainfo(path):
                    self.mediainfo = str(path.absolute())

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