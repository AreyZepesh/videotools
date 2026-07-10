import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.messagebox import showerror, showwarning, showinfo

from common import Config
from old.options_file import load_cfg

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple Video Converter")
        self.geometry("800x600")
        self.resizable(False, False)

        self.cfg = Config()
        self._check_cfg()

        self._build_main_menu()
        self._build_top()

    def _build_top(self):
        pass

    def _build_main_menu(self):
        self.main_menu = tk.Menu()
        self.main_menu.add_command(label='Настройки', command=self._open_options)
        self.config(menu=self.main_menu)

    def _check_cfg(self):
        self.cfg.load_cfg()
        if not self.cfg.ffmpeg_path or not self.cfg.mediainfo_path:
            showwarning(title="Предупреждение",
                        message="Не сохранены или не найдены пути к необходимым компонентам! " \
                        "Укажите пути до ffmpeg.exe и mediainfo.exe")
            self._open_options()

    def _open_options(self):
        OptionsWindow(self, self.cfg)

class OptionsWindow(tk.Toplevel):
    def __init__(self, parent, cfg: Config):
        super().__init__(parent)
        self.cfg: Config = cfg

        self.title("Настройки")
        self.geometry("500x250")

        self.options_tab = ttk.Frame(self)
        self.options_tab.pack(fill="x", padx=10, pady=10)

        self.ffmpeg_path = tk.StringVar(value=cfg.ffmpeg_path or "")
        self._build_ffmpeg()
        self.mediainfo_path = tk.StringVar(value=cfg.mediainfo_path or "")
        self._build_mediainfo()
        self._build_ok_cancel()
        

    def _build_ffmpeg(self):
        frame = ttk.LabelFrame(self.options_tab, text="1. Укажите путь к ffmpeg.exe")
        frame.pack(fill="x", padx=10, pady=10)

        # self.ffmpeg_path = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ffmpeg_path).pack(side="left", fill="x", expand=True, padx=8, pady=8)
        ttk.Button(frame, text="Обзор...", 
                   command=lambda: self.ffmpeg_path.set(choose_exe_file("ffmpeg.exe"))
                   ).pack(side="left", padx=(0, 8), pady=8)

    def _build_mediainfo(self):
        frame = ttk.LabelFrame(self.options_tab, text="2. Укажите путь к mediainfo.exe (cli)")
        frame.pack(fill="x", padx=10, pady=10)

        # self.mediainfo_path = tk.StringVar()
        ttk.Entry(frame, textvariable=self.mediainfo_path).pack(side="left", fill="x", expand=True, padx=8, pady=8)
        ttk.Button(frame, text="Обзор...", 
                   command=lambda: self.mediainfo_path.set(choose_exe_file("mediainfo.exe"))
                   ).pack(side="left", padx=(0, 8), pady=8)
        
    def _build_ok_cancel(self):
        frame = ttk.Frame(self.options_tab)
        frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(frame, text='OK',
                   command=self._ok_save # Сохранить настройки
                   ).pack(side="left")
        ttk.Button(frame, text='Отмена',
                   command=lambda: self.destroy()
                   ).pack(side="right", padx=(0, 8), pady=8)
        
    def _ok_save(self):
        self.cfg.ffmpeg_path = self.ffmpeg_path.get()
        self.cfg.mediainfo_path = self.mediainfo_path.get()
        # save_config(self.cfg)
        self.destroy()
        # TODO дописать действие для ok, сохранение параметров, а еще проверку пути при выборе
        

   


def choose_exe_file(self, filename: str = ""):
    path = filedialog.askopenfilename(title=f"Выберите файл {filename}", defaultextension = "exe", initialfile = filename)
    if path:
        if filename.lower() == Path(path).name.lower():
            return path
    return ''

def choose_dir(self):
    path = filedialog.askdirectory(title="Выберите директорию")
    if path:
        return path
    return ''

if __name__ == "__main__":
    App().mainloop()
