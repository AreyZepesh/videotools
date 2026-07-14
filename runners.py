from common import (
    subprocess, json, Path,
    run_subprocess, Config
    )

from ffmpeg import FFmpegCmdBuilder
from mediainfo import get_video_info, is_need_convert
from pathutils import scan_dir

# RUN BLOCK
def _execut_convert_video(ffmpeg_args: list[str]):
    process = subprocess.run(ffmpeg_args)
    if process.returncode != 0:
        raise RuntimeError(f"Процесс завершился неверно")
    pass

def run_convert(input_path, ff_cmd: FFmpegCmdBuilder, fallback_ff_cmd: FFmpegCmdBuilder):
    output_path = Path(input_path.parent, r"converted", input_path.name)
    # output_path = output_path.with_suffix('.mp4')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f'{input_path} -> {output_path}')
    try:
        _execut_convert_video(
            ff_cmd.build(input_path, output_path)
                      )
    except Exception as nvidia_ex:
        print(nvidia_ex)
        try:
            _execut_convert_video(
                fallback_ff_cmd.build(input_path, output_path)
                    )
        except Exception as fallback_ex:
            print(fallback_ex)
            if output_path.exists():
                # os.remove(output_path)
                output_path.unlink()
            return
        
def run_only_scan(dir_path, cfg: Config):
    data = scan_dir(dir_path, cfg=cfg, check_func=is_need_convert)
    lines = []
    if not data:
        lines.append("По заданным параметрам ничего не найдено")
    else:
        lines.append("По заданным параметрам найдено:")
        lines.extend(data)
    return lines

def run_scan_and_convert(dir_path, cfg: Config):
    data = scan_dir(dir_path, cfg=cfg, check_func=is_need_convert)

    if not data:
        return

    ff_cmd = FFmpegCmdBuilder(cfg)
    fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)
    
    for path in data:
        run_convert(path, ff_cmd, fallback_ff_cmd)
    # TODO: запуск как с уже отсканированными данными, так и заново сканируя

def run_from_cli():
    
    cfg = Config()
    cfg.load_cfg()
    cfg.exclude_subtitles = True
    dir = r"D:\Видео\_маме\Кафедра (нужна конвертация)"
    # dir = r"G:\\"
    # lines = run_only_scan(dir, cfg)
    # for line in lines:
    #     print(line)
    # print()
    run_scan_and_convert(dir, cfg)

# OTHER BLOCK

def test_cli():
    done = False
    while done:
        
        done = True
 
def main():
    run_from_cli()
    pass

if __name__ == "__main__":
    main()