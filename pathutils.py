# from pathlib import Path
from common import (
    Path,
    Config,
    )

# class PathMapping(Path):
#     # NOTE: мигрировал минимальный функционал из другого своего проекта
#     def __init__(self, *args):
#         super().__init__(*args)
#         self.src_path = Path(self)
#         self.dst_path = Path(self)

#     def remap_dst_path(self, input_dir, output_dir):
#         """replace in dst_path"""
#         relative = self.relative_to(input_dir)
        # self.dst_path = Path(output_dir, relative) 

# FILE/PATH BLOCK
def scan_dir(dir_path: str|Path, cfg: Config, check_func) -> list:
    files_to_convert = []
    for file_path in Path(dir_path).rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in cfg.video_suffixes:
            continue
        
        # if check_func is None:
        #     files_to_convert.append(file_path)
        # elif
        if check_func(file_path, cfg):
            files_to_convert.append(file_path)

    return files_to_convert


# def scan_dir(dir_path: str|Path, cfg: Config) -> list:
    # files_to_convert = []
    # # for file_path in Path(dir_path).glob("**/*"):
    # for file_path in Path(dir_path).rglob("*"):
    #     if file_path.is_dir():
    #         continue
    #     if file_path.suffix.lower() not in cfg.video_suffixes:
    #         continue
    #     needs_convert = False
    #     try:
    #         tracks = get_video_info(file_path, cfg)
    #         if len(tracks) > 1:
    #             raise ValueError("Более одного потока видео в файле")
    #         bit_depth = tracks[0].get("BitDepth")
    #         width = tracks[0].get("Width")
    #         height = tracks[0].get("Height")
    #     except Exception as e:
    #         print(f"Ошибка при чтении файла, пропускаем: {file_path}")
    #         print(e)
    #         continue
        
    #     if cfg.find_10bit:
    #         if bit_depth == 10:
    #             needs_convert = True
    #         elif bit_depth != 8:
    #             print(f"{file_path}: {bit_depth=}")

    #     if (cfg.width and width > cfg.width) or (cfg.height and height > cfg.height):
    #         needs_convert = True
        
    #     if needs_convert:
    #         files_to_convert.append(file_path)

    # return files_to_convert