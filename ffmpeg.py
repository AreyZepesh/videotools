from common import (
    subprocess, json, Path,
    run_subprocess, Config
    )

class FFmpegCmdBuilder:
    def __init__(self, cfg: Config, only_CPU: bool = False):
        self.cfg = cfg

        self.ffmpeg_path = Path(cfg.ffmpeg_path).absolute()
        self._global_options = []
        self._input_options = []
        # self.input_path
        self._output_options = []
        # self.output_path

        self.extra_global_options = []
        self.extra_input_options = []
        self.extra_output_options = []

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


    def _build_global_options(self): # NOTE: сделать  -> list[str] ?
        self._global_options += ['-y', '-hide_banner', 
                #  '-loglevel', 'level+datetime',
                #  '-loglevel', 'warning',
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
        _output_options = []
        if self.cfg.exclude_subtitles:
            _output_options += ["-map", "0", "-sn", "-c", "copy"]
            # _output_options += ["-map", "0:v", "-map", "0:a", "-c", "copy"]
        else:
            _output_options += ["-map", "0", "-c", "copy"]
        # NVIDIA 
        if self.use_nvidia:
            _output_options += [
                            "-c:v", "h264_nvenc",     
                            '-preset', 'p5',
                            '-rc', 'vbr',
                            '-cq', '23', 
                            "-b:v", "0",
                                ]
            if self.scale:
                _output_options += ["-vf", f'scale_cuda={self.scale}:format=nv12']
        # CPU
        else:
            _output_options += [
                        "-c:v", "libx264",
                        '-preset', 'medium',
                        '-crf', '22',
                                ]
            if self.scale:
                _output_options += ["-vf", f'scale={self.scale}']
        
        # не для scale на nvidia, так как там параметр формата уже указан и будет конфликт
        if not (self.use_nvidia and self.scale):
            _output_options += ["-pix_fmt", "yuv420p"]

        self._output_options += _output_options

    def build(self, input_path: Path|str, output_path: Path|str) -> list[str]:
        # NOTE: нужно ли еще одно преобразование в Path и проверку существования? ffmpeg и сам может отбросить
        input_path = Path(input_path).absolute()
        if not input_path.exists():
            raise FileNotFoundError(f"Файл не существует {input_path}")
        output_path = Path(output_path).absolute()

        args = [self.ffmpeg_path]
        args += self._global_options
        args += self.extra_global_options
        args += self._input_options
        args += self.extra_input_options
        args += ["-i", str(input_path)]
        args += self._output_options
        args += self.extra_output_options
        args += [str(output_path)]
        return args

    @staticmethod
    def printable(args: list[str]) -> str:
        return subprocess.list2cmdline(args)

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
    

def get_ffmpeg_kwargs(cfg: Config) -> dict[str, list[str]]:
    # # build_ffmpeg_options
    # nvidia = False
    # if cfg.check_nvidia:
    #     nvidia = is_nvidia_supported(cfg)
    
    # scale = None
    # if cfg.width or cfg.height:
    #     scale = f'{cfg.width if cfg.width else "-2"}:{cfg.height if cfg.height else "-2"}'

    # kwargs = {
    #     'ffmpeg_path': [cfg.ffmpeg_path],
    #     'global_options': [],
    #     'input_options': [],
    #     # -i input,
    #     'output_options': [],
    #     # output
    #     }
    # kwargs['global_options'] += ['-y', '-hide_banner', 
    #                             #  '-loglevel', 'level+datetime',
    #                             #  '-loglevel', 'warning',
    #                              ]
    # kwargs['input_options'] += []
    # if cfg.exclude_subtitles:
    #     kwargs['output_options'] += ["-map", "0:v", "-map", "0:a", "-c", "copy"]
    # else:
    #     kwargs['output_options'] += ["-map", "0", "-c", "copy"]

    # if nvidia:
    #     kwargs['input_options'] += ['-hwaccel', 'cuda']
    #     kwargs['output_options'] += ["-c:v", "h264_nvenc",     
    #                                 '-preset', 'p5',
    #                                 '-rc', 'vbr',
    #                                 '-cq', '23', 
    #                                 "-b:v", "0"]
    #     if scale:
    #         kwargs['input_options'] += ['-hwaccel_output_format', 'cuda']
    #         kwargs['output_options'] += ["-vf", f'scale_cuda={scale}:format=nv12']

    # else:
    #     # kwargs['input_options'] += ['-hwaccel', 'auto']
    #     kwargs['output_options'] += ["-c:v", "libx264",
    #                                 '-preset', 'medium',
    #                                 '-crf', '22',
    #                                 ]
    #     if scale:
    #         kwargs['output_options'] += ["-vf", f'scale={scale}']

    # if not (nvidia and scale):
    #     kwargs['output_options'] += ["-pix_fmt", "yuv420p"]
    # # kwargs['input_options'] += ['-fflags', '+genpts'] # создание новых timestamp’ов вместо старых
    # # kwargs['output_options'] += ['-progress','pipe:1', '-nostats'] # выводить прогресс строками, а не динамикой.

    # # old parameters
    # # c  = [f'-hwaccel cuda -hwaccel_output_format cuda -i "{Path('input_path')}" -c:v h264_nvenc -b:v 4500K -vf "scale_cuda=1280:720" "{Path('output_path')}"']
    # # rc = [f'-hwaccel auto  -i "{Path('input_path')}" -b:v 4500K -s 1280x720 "{Path('output_path')}"']

    # return kwargs
    pass

def main():
    pass

if __name__ == "__main__":
    main()