from common import (
    subprocess, json, Path,
    run_subprocess, Config
    )

from ffmpeg import FFmpegCmdBuilder
from mediainfo import MediaFileInfo
# from pathutils import scan_dir


def scan_dir(dir_path: str|Path, cfg: Config) -> list[MediaFileInfo]:
    files_to_convert = []
    for file_path in Path(dir_path).rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in cfg.video_suffixes:
            continue
        
        # if check_func is None:
        #     files_to_convert.append(file_path)
        # elif
        v_file = MediaFileInfo(file_path, cfg)
        if v_file.need_convert:
            files_to_convert.append(v_file)

    return files_to_convert


# RUN BLOCK
def _execut_convert_video(ffmpeg_args: list[str]):
    process = subprocess.run(ffmpeg_args)
    if process.returncode != 0:
        raise RuntimeError(f"Процесс завершился неверно")
    pass

def run_convert(input_file: MediaFileInfo, ff_cmd: FFmpegCmdBuilder, fallback_ff_cmd: FFmpegCmdBuilder):
    # output_path = Path(input_file.parent, r"converted", input_file.name)
    # output_path = output_path.with_suffix('.mp4')
    input_file.output_path.parent.mkdir(parents=True, exist_ok=True)
    print(input_file)
    try:
        _execut_convert_video(
            ff_cmd.build(input_file.path, input_file.output_path)
                      )
    except Exception as nvidia_ex:
        print(nvidia_ex)
        try:
            _execut_convert_video(
                fallback_ff_cmd.build(input_file.path, input_file.output_path)
                    )
        except Exception as fallback_ex:
            print(fallback_ex)
            if input_file.output_path.exists():
                # os.remove(input_file.output_path)
                input_file.output_path.unlink()
            return
        
def run_only_scan(dir_path, cfg: Config):
    data = scan_dir(dir_path, cfg=cfg)
    lines = []
    if not data:
        lines.append("По заданным параметрам ничего не найдено")
    else:
        lines.append("По заданным параметрам найдено:")
        lines.extend(data)
    return lines

def run_scan_and_convert(dir_path, cfg: Config):
    data = scan_dir(dir_path, cfg=cfg)

    if not data:
        return

    ff_cmd = FFmpegCmdBuilder(cfg)
    fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)
    
    for f_file in data:
        run_convert(f_file, ff_cmd, fallback_ff_cmd)
    # TODO: запуск как с уже отсканированными данными, так и заново сканируя

def run_from_cli():
    
    cfg = Config()
    cfg.load_cfg()
    cfg.exclude_subtitles = True
    # cfg.width = 1280
    dir = r"D:\Видео\_маме\Кафедра (нужна конвертация)"
    dir = r"D:\Видео\_маме"
    cfg.input_dir = Path(dir)
    # cfg.output_dir = Path(r"C:\1")
    # cfg.output_mode = "tree"
    cfg.output_mode = "subfolder"
    # dir = r"G:\\"

    # lines = run_only_scan(dir, cfg)
    # for line in lines[1:]:
    #     # print(type(line))
    #     print(line)

        # print(cfg.build_output_path(line))
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