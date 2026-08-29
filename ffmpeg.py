# from common import Path # from pathlib import
from pathlib import Path
from config import Config

from proc import list2cmdline, run_subprocess

from mediainfo import MediaFileInfo

class FFmpegCmdBuilder:
    def __init__(self, cfg: Config, only_CPU: bool = False):
        self.cfg = cfg
        self._check_exe()

        self.ffmpeg_path = Path(cfg.ffmpeg_path).absolute()
        self._global_options = []
        self._input_options = []
        # self.input_path
        self._output_map_options = []
        self._output_copy_options = []
        self._output_codec_options = []
        # self.output_path

        # self.extra_global_options = []
        # self.extra_input_options = []
        # self.extra_output_options = []

        self.use_nvidia = False
        if not only_CPU and cfg.check_nvidia:
            self.use_nvidia = is_nvidia_supported(cfg)
            # TODO: использование функции извне класса, норм ли?

        self.scale = None
        if cfg.width or cfg.height:
            self.scale = f'{cfg.width if cfg.width else "-2"}:{cfg.height if cfg.height else "-2"}'

        self._build_global_options()
        self._build_input_options()
        self._build_output_options()

    def _check_exe(self):
        if not self.cfg.ffmpeg_path or not Path(self.cfg.ffmpeg_path).exists():
            raise ValueError("ffmpeg.exe не найден")  

    def _build_global_options(self): # NOTE: сделать  -> list[str] ?
        self._global_options += ['-y', '-hide_banner', 
                #  '-loglevel', 'level+datetime',
                 '-loglevel', 'warning',
                #  '-loglevel', 'error',
                '-nostats',
                '-progress', 'pipe:1', 
                ]

    def _build_input_options(self):
        _input_args = []
        if self.use_nvidia:
            _input_args += ['-hwaccel', 'cuda']
            if self.scale:
                _input_args += ['-hwaccel_output_format', 'cuda']
        else:
            _input_args += [
                # '-hwaccel', 'auto'
                            ]    
        
        self._input_options += _input_args

    def _build_output_options(self):
        # if self.cfg.exclude_subtitles:
        #     # _output_options += ["-map", "0", "-sn"]
        #     _output_options += ["-map", "0:v", "-map", "0:a"]
        # else:
        #     _output_options += ["-map", "0"]
        self._output_map_options += ["-map", "0:v:0", "-map", "0:a"]
        # NOTE в выходной файл попадет только первый видеопоток!

        self._output_copy_options = ["-c", "copy"]
        # NVIDIA 
        _output_codec_options = []
        if self.use_nvidia:
            _output_codec_options += [
                            "-c:v", "h264_nvenc",     
                            '-preset', 'p5',
                            '-rc', 'vbr',
                            '-cq', '23', 
                            "-b:v", "0",
                                ]
            if self.scale:
                _output_codec_options += ["-vf", f'scale_cuda={self.scale}:format=nv12']
        # CPU
        else:
            _output_codec_options += [
                        "-c:v", "libx264",
                        '-preset', 'medium',
                        '-crf', '22',
                                ]
            if self.scale:
                _output_codec_options += ["-vf", f'scale={self.scale}']
        
        # не для scale на nvidia, так как там параметр формата уже указан и будет конфликт
        if not (self.use_nvidia and self.scale):
            _output_codec_options += ["-pix_fmt", "yuv420p"]

        self._output_codec_options += _output_codec_options

    def build(self, 
              input_video_file: MediaFileInfo,
              ) -> list[str]:
        """Создание команды ffmpeg. \n
        """
        if not input_video_file.path.exists():
            raise FileNotFoundError(f"Файл не существует {input_video_file.path}")

        args = [str(self.ffmpeg_path)]
        args += self._global_options
        args += self._input_options
        args += ["-i", str(input_video_file.path)]

        args += self._output_map_options

        # NOTE: is_mkv автоматизирует исключение субтитров из файла и извелечение их рядом
        is_mkv = input_video_file.output_path.suffix == ".mkv"
        if not self.cfg.exclude_subtitles and is_mkv and input_video_file.subtitles:
            if self.cfg.use_only_basic_subtitles:
                for sub in input_video_file.subtitles:
                    if sub.is_basic():
                        args += ["-map", f"0:s:{sub.index}"]
            else:
                args += ["-map", "0:s"]

        # NOTE если видеопоток НЕ нужно конвертировать, будет просто скопирован как есть: 
        args += self._output_copy_options 
        if input_video_file.video_need_convert:
            args += self._output_codec_options

        args += [str(input_video_file.output_path)]

        if (self.cfg.extract_subtitles or not is_mkv) and input_video_file.subtitles:
            for sub in input_video_file.subtitles:
                if self.cfg.use_only_basic_subtitles and not sub.is_basic():
                    # Если опция говорит 'только базовые субтитры', то пропускаем не базовые
                    continue
                args += ["-map", f"0:s:{sub.index}", "-c:s", sub.codec, str(sub.out_path)]

        return args

    @staticmethod
    def printable(args: list[str]) -> str:
        return list2cmdline(args)

# FFMPEG BLOCK
def _parse_codecs(data: str, codec_filter: str) ->list[str]:
    # NOTE: не будет работать без фильтра, так как в выводе есть строки не подходящие по шаблону
    if not codec_filter:
        raise ValueError("Необходимо указать фильтр для кодеков")
    lines = [ line for line in data.splitlines() if codec_filter in line.lower()]
    return [ line.split()[1] for line in lines ]

def get_ffmpeg_nv_support(cfg: Config) -> dict:
    # NOTE: специально захардкодил функцию, для получения информации именно для nvidia
    if not Path(cfg.ffmpeg_path).exists():
        raise ValueError("ffmpeg.exe не найден")
    
    process_encoders = run_subprocess( [cfg.ffmpeg_path, '-hide_banner', '-encoders'] )
    process_decoders = run_subprocess( [cfg.ffmpeg_path, '-hide_banner', '-decoders'] )

    for process in [process_encoders, process_decoders]:
        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip())
    
    encoders = _parse_codecs(process_encoders.stdout.strip(), "nvenc")
    decoders = _parse_codecs(process_decoders.stdout.strip(), "cuvid")
    return {"encoders": encoders, "decoders": decoders}

def is_nvidia_supported(cfg: Config):
        nv_codec = get_ffmpeg_nv_support(cfg)
        encoders = nv_codec.get('encoders')
        return bool(encoders and 'h264_nvenc' in encoders and nv_codec.get('decoders'))
    
def main():
    pass

if __name__ == "__main__":
    main()