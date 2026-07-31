from common import (
    subprocess, json, Path,
    run_subprocess, Config,
    rprint,
    )

from mediainfo import MediaFileInfo, SubtitleInfo
from ffmpeg import FFmpegCmdBuilder


def scan_dir(dir_path: str|Path, cfg: Config) -> list[MediaFileInfo]:
    files_to_convert = []
    for file_path in Path(dir_path).rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in cfg.video_suffixes:
            continue
        try:
            v_file = MediaFileInfo(file_path, cfg)
            if v_file.need_convert:
                files_to_convert.append(v_file)
        except Exception as scan_ex:
            print(scan_ex)
            continue

    return files_to_convert


# RUN BLOCK
def _execut_convert_video(ffmpeg_args: list[str]):
    process = subprocess.run(ffmpeg_args)
    if process.returncode != 0:
        raise RuntimeError(f"Процесс завершился неверно")

def run_convert(input_video_file: MediaFileInfo, ff_cmd: FFmpegCmdBuilder, fallback_ff_cmd: FFmpegCmdBuilder):
    # output_path = Path(input_file.parent, r"converted", input_file.name)
    # output_path = output_path.with_suffix('.mp4')
    input_video_file.output_path.parent.mkdir(parents=True, exist_ok=True)
    print(input_video_file)
    try:
        _execut_convert_video(
            # ff_cmd.build(input_video_file.path, input_video_file.output_path)
            ff_cmd.build(input_video_file)
                      )
    except Exception as nvidia_ex:
        print(nvidia_ex)
        try:
            _execut_convert_video(
                # fallback_ff_cmd.build(input_video_file.path, input_video_file.output_path)
                fallback_ff_cmd.build(input_video_file)
                    )
        except Exception as fallback_ex:
            print(fallback_ex)
            if input_video_file.output_path.exists():
                # os.remove(input_file.output_path)
                input_video_file.output_path.unlink()
            return
        
def run_only_scan(dir_path, cfg: Config):
    data = scan_dir(dir_path, cfg=cfg)
    response = f"По заданным параметрам найдено: {len(data)}"
    return (response, data)

def run_scan_and_convert(dir_path, cfg: Config):
    data = scan_dir(dir_path, cfg=cfg)

    if not data:
        return

    ff_cmd = FFmpegCmdBuilder(cfg)
    fallback_ff_cmd = FFmpegCmdBuilder(cfg, only_CPU=True)
    
    for video_file in data:
        run_convert(video_file, ff_cmd, fallback_ff_cmd)
    # TODO: запуск как с уже отсканированными данными, так и заново сканируя

def run_test():
    
    cfg = Config()
    cfg.load_cfg()
    cfg.use_only_basic_subtitles = True
    # cfg.exclude_subtitles = True
    # cfg.extract_subtitles = True
    # cfg.width = 1280
    # dir = r"D:\Видео\_маме\Кафедра (нужна конвертация)"
    dir = r"D:\Видео\_test"
    cfg.input_dir = Path(dir)
    cfg.output_dir = Path(r"D:\Видео\_converted")
    cfg.output_file_suffix = 'mp4'
    # cfg.output_mode = "subfolder"
    # dir = r"G:\\"

    # ff_cmd = FFmpegCmdBuilder(cfg)
    # response, lines = run_only_scan(dir, cfg)
    # rprint(response)
    # for line in lines:
    # #     # print(type(line))
    #     print(
    # ff_cmd.printable
    #         (
    #         ff_cmd.build(
    #             line
    #             )
    #             )
    #            )
    #     print(line.need_convert)
    #     print(line.video_need_convert)
    #     print(line.text_need_convert)
        # rprint(cfg.build_output_path(line))
    # print()

    run_scan_and_convert(dir, cfg)

# OTHER BLOCK

def main():
    run_test()
    pass

if __name__ == "__main__":
    main()