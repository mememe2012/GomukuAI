# --coding: utf-8 --
import pygame as pg
import os
import json
import time
import numpy as np
import shutil
import sys
import pygame_gui as pgui
from tkinter import messagebox
from PIL import ImageFilter, Image, ImageOps, ImageChops, ImageDraw
from rich.console import Console
from rich.panel import Panel
import webbrowser as wb
import numpy as np
import threading
import winreg
import ctypes
import ctypes.wintypes as wintypes
import pystray
from notifypy import Notify

CONSOLE = Console()
SIZE = (1024, 768)
ERROR_ALREADY_EXISTS = 183
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040
SWP_NOACTIVATE = 0x0010
SW_RESTORE = 9

def WinMessage(title, message, icon_path=None, app_name="GomokuAI"):
    return
    notification = Notify()
    notification.title = title
    notification.message = message
    notification.application_name = app_name
    
    if icon_path:
        notification.icon = icon_path
        
    notification.send()

def TopWindow(hwnd: int) -> bool:
    CONSOLE.print(f"TopWindow HWND={hwnd}", style="bold green")

    if not hwnd:
        CONSOLE.print("No HWND provided", style="bold red")
        return False

    user32 = ctypes.windll.user32
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.restype = wintypes.BOOL

    win_handle = wintypes.HWND(hwnd)
    if not user32.IsWindow(win_handle):
        CONSOLE.print("Not a valid window", style="bold red")
        return False

    user32.ShowWindow(win_handle, SW_RESTORE)
    user32.SetWindowPos(
        win_handle,
        HWND_TOPMOST,
        0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOACTIVATE,
    )
    user32.SetForegroundWindow(win_handle)
    return True

def CheckSingleInstance(mutex_name="Global\\MyUniqueAppNameMutex"):
    mutex = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == ERROR_ALREADY_EXISTS:
        ctypes.windll.kernel32.CloseHandle(mutex)
        return False
    return True

def LoadFont(path:str, size:int):
    try:
        font = pg.font.Font(path, size)
        return font
    except Exception as e:
        return None

def GetHWND():
    return pg.display.get_wm_info()['window']

def GaussianBlur(
    surface: pg.Surface,
    radius: int,
    outline: None | tuple = None,
    border_radius: int = 0,
    mask_color: None | tuple[int, int, int, int] | list[int, int, int, int] = None,
    ) -> pg.Surface:
    
    if surface.get_bytesize() != 4:
        surface = surface.convert_alpha()

    raw_str = pg.image.tobytes(surface, "RGBA")
    img = Image.frombytes("RGBA", surface.get_size(), raw_str)
    
    if border_radius > 0:
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            [(0, 0), img.size],
            radius=border_radius,
            fill=255
        )
        alpha = img.getchannel("A")
        alpha = ImageChops.multiply(alpha, mask)
        img.putalpha(alpha)

    rgb = img.convert("RGB")
    alpha = img.getchannel("A")
    
    blurred_rgb = rgb.filter(ImageFilter.GaussianBlur(radius))
    blurred_img = Image.merge("RGBA", (*blurred_rgb.split(), alpha))

    if outline is not None:
        color, width = outline
        current_img = blurred_img
        
        expanded_size = (current_img.size + width * 2, current_img.size + width * 2)
        background = Image.new("RGBA", expanded_size, (0, 0, 0, 0))
        
        alpha_channel = current_img.getchannel("A")
        
        outline_alpha = ImageOps.expand(alpha_channel, border=width, fill=255)
        
        if border_radius > 0:
            outline_mask = Image.new("L", outline_alpha.size, 0)
            draw = ImageDraw.Draw(outline_mask)
            draw.rounded_rectangle(
                [(0, 0), outline_alpha.size],
                radius=border_radius + width,
                fill=255
            )
            outline_alpha = ImageChops.multiply(outline_alpha, outline_mask)
        
        color_layer = Image.new("RGBA", expanded_size, color)
        background.paste(color_layer, (0, 0), outline_alpha)
        
        paste_pos = (width, width)
        background.paste(current_img, paste_pos, current_img)
        
        blurred_img = background

    if mask_color is not None:
        mask_r, mask_g, mask_b, mask_a = mask_color
        color_overlay = Image.new("RGBA", blurred_img.size, (mask_r, mask_g, mask_b, mask_a))
        blurred_img = Image.alpha_composite(blurred_img, color_overlay)

    if border_radius > 0:
        final_mask = Image.new("L", blurred_img.size, 0)
        draw = ImageDraw.Draw(final_mask)
        
        current_radius = border_radius
        if outline is not None:
            _, width = outline
            current_radius += width
            
        draw.rounded_rectangle(
            [(0, 0), blurred_img.size],
            radius=current_radius,
            fill=255
        )
        
        final_alpha = blurred_img.getchannel("A")
        final_alpha = ImageChops.multiply(final_alpha, final_mask)
        blurred_img.putalpha(final_alpha)

    try:
        blurred_str = blurred_img.tobytes()
        blurred_surface = pg.image.frombytes(blurred_str, blurred_img.size, "RGBA")
    except Exception as e:
        CONSOLE.log("Failed to convert image to pygame surface: " + str(e))
        blurred_surface = pg.Surface((1, 1), pg.SRCALPHA)

    return blurred_surface

def fillrgba(width, height, r, g, b, a):
    surface = pg.Surface((width, height), pg.SRCALPHA)
    surface.fill((r, g, b, a))
    return surface

def CreateScreen(
        size:tuple=(640,480),
        title:str="Pygame Window",
        icon:str=None
        ) -> pg.Surface:
    screen = pg.display.set_mode(size)
    pg.display.set_caption(title)
    if icon:
        icon_surface = pg.image.load(icon)
        pg.display.set_icon(icon_surface)
    return screen

def SetClock(fps:int=60):
    return pg.time.Clock().tick(fps)

def PathType(path:str):
    if os.path.isfile(path):
        return "file"
    elif os.path.isdir(path):
        return "dir"
    else:
        return "unknown"

def checkStart():
    return False

def getSystemTheme():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        theme_value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
        if theme_value == 1:
            return "light"
        elif theme_value == 0:
            return "dark"
        else:
            return "Unknown"
            
    except FileNotFoundError:
        return "Registry key not found"
    except Exception as e:
        return str(e)

def CleanDir(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                raise Exception(f'Failed to delete {file_path}. Reason: {e}')
    else:
        os.makedirs(directory, exist_ok=True)

def ImportIcon(icon_path):
    img = Image.open(icon_path)
    img.resize((48,48))
    return img

def HideWindow(hwnd):
    ctypes.windll.user32.ShowWindow(hwnd, 0)

def ShowWindow(hwnd):
    ctypes.windll.user32.ShowWindow(hwnd, 5)

class Main:
    def __init__(self):
        pg.init()
        pg.display.init()
        pg.font.init()
        pg.mixer.init()
        #pg.freetype.init()

        self.loadConfig()
        self.running = True
        self.setting_page = 1
        self.setting_max_page = 2
        self.logname = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + ".log"
        self.screen = CreateScreen(SIZE,"GomokuAI","icon/icon.ico")
        self.clock = SetClock(60)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.fontpath = os.path.join(self.base_dir, "font", "HarmonyOS_Sans_SC_Bold.ttf")
        self.page = "home"
        self.font_family = "HarmonyOS_Sans_SC"
        self.version = "0.0.1"
        self.url = "https://github.com/mememe2012/GomukuAI"
        self.sound = {}
        self.hwnd = GetHWND()
        os.makedirs("tmp", exist_ok=True)
        with open("tmp/HWND.key", "w", encoding="utf-8") as f:
            f.write(str(self.hwnd))
        self.chessboard = self.ChessBoard(self, 414, 10, 600)
        self.chessboard.boardlst = [(1,1),(2,3),(8,1)]

        CONSOLE.print(f"Window HWND={self.hwnd}", style="yellow")

    def SetupStray(self, icon):
        icon.visible = True

    def OpenWindow(self):
        ShowWindow(self.hwnd)
        TopWindow(self.hwnd)
        
    def createTray(self):
        menu = pystray.Menu(
            pystray.MenuItem(self.tr('Open'), self.OpenWindow, default=True),
            pystray.MenuItem(self.tr('Hide'), lambda:HideWindow(self.hwnd)),
            pystray.MenuItem(self.tr('Exit'), self.quit)
        )
        self.tray = pystray.Icon('GomokuAI', ImportIcon("icon/icon144.png"), 'GomokuAI', menu)
        self.thTray = threading.Thread(target=lambda:self.tray.run(setup=self.SetupStray))
        self.thTray.daemon = True
        self.thTray.start()
        CONSOLE.print("Tray created", style="yellow")

    def loadConfig(self):
        self.gmktxt = open("assets/GMKAI-text.txt", "r", encoding="utf-8").read()
        self.lang_list = [f[:-5] for f in os.listdir("lang") if f.endswith(".json")]
        self.theme_list = [f[:-5] for f in os.listdir("themes") if f.endswith(".json")] + ["system"]

        with open("config/setting.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)
        
        with open("lang/" + self.config["lang"]["default"] + ".json", "r", encoding="utf-8") as f:
            self.dictionary = json.load(f)

        if self.config["theme"]["system"]:
            systheme = getSystemTheme()
            if systheme == "dark" or systheme == "light":
                self.loadTheme(systheme)
            else:
                CONSOLE.print(systheme, style="red")
                self.loadTheme("dark")
        else:
            self.loadTheme(self.config["theme"]["default"])

        self.lang_dct = {}
        for lang in self.lang_list:
            with open("lang/" + lang + ".json", "r", encoding="utf-8") as f:
                self.lang_dct[lang] = json.load(f)["__name__"]

    def loadTheme(self, style):
        self.theme_path = f"themes/{style}.json"
        with open(f"themes/{style}.json", "r") as f:
            self.style = json.load(f)["UIstyle"]
        self.bg = pg.image.load(f"icon/bg/{self.style['bg']}")

    def writeLog(self, text):
        if not os.path.exists("log"):
            os.makedirs("log")
            
        with open("log/"+self.logname, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())}]{text}" + "\n")

    def run(self):
        os.makedirs("tmp", exist_ok=True)
        with open("tmp/HWND.key", "w", encoding="utf-8") as f:
            f.write(str(self.hwnd))

        CONSOLE.print("font family: ", self.font_family, style="green")
        self.controls()

        if len(sys.argv) > 1:
            self.filepath = sys.argv[1]
            filetype = PathType(self.filepath)
            self.page = "chess"
            if filetype == "dir":
                CONSOLE.print("Start from dir", self.filepath, style="green")
            elif filetype == "file":
                CONSOLE.print("Start from file",self.filepath, style="green")
            else:
                CONSOLE.print("unknown file", self.filepath, style="red")
                self.running = False

        CONSOLE.print(Panel(f"[bold green]{self.gmktxt}\nSuccessful to init GomokuAI![/bold green]", title="Init"))
        self.writeLog(f"{self.gmktxt}\nSuccessful to init GomokuAI!")

        WinMessage("GomokuAI",self.tr("GomokuAI is already inited!\nYou can find it in System Tray!"),"icon/icon144.png")

        while self.running:
            time_delta = self.clock / 1000.0
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quitB()

                if self.page == "home":
                    self.homemanager.process_events(event)
                    if event.type == pgui.UI_BUTTON_PRESSED:
                        if event.ui_element == self.btn_quit:
                            self.quitB()
                        if event.ui_element == self.btn_github:
                            open_ = threading.Thread(target=self.github)
                            open_.daemon = True
                            open_.start()
                        if event.ui_element == self.btn_wiki:
                            open_ = threading.Thread(target=lambda:wb.open(self.url+"/wiki") if messagebox.askyesno(self.tr("GomokuAI-Wiki"), self.tr("Do you want to open the wiki in your browser?")) else None)
                            open_.daemon = True
                            open_.start()
                        if event.ui_element == self.btn_issues:
                            oig = threading.Thread(target=lambda:wb.open(self.url+"/issues") if messagebox.askyesno(self.tr("GomokuAI-Issues"), self.tr("Do you want to open the issues in your browser?")) else None)
                            oig.daemon = True
                            oig.start()
                        if event.ui_element == self.btn_setting:
                            self.page = "setting"
                        if event.ui_element == self.btn_start:
                            self.page = "play"

                elif self.page == "setting":
                    self.settingmanager.process_events(event)
                    
                    if event.type == pgui.UI_BUTTON_PRESSED:
                        if event.ui_element == self.btn_back1:
                            self.page = "home"
                        if event.ui_element == self.btn_pageup:
                            if self.setting_page > 1:
                                self.setting_page -= 1
                        if event.ui_element == self.btn_pagedown:
                            if self.setting_page < self.setting_max_page:
                                self.setting_page += 1
                        if event.ui_element == self.btn_save:
                            CONSOLE.print(f"Save settings,index={[self.tr(i) for i in self.theme_list].index(self.choice_theme.selected_option[0])}", style="green")
                            get_english_theme = self.theme_list[[self.tr(i) for i in self.theme_list].index(self.choice_theme.selected_option[0])]
                            if get_english_theme == "system":
                                self.config["theme"]["system"] = True
                            else:
                                self.config["theme"]["system"] = False
                                self.config["theme"]["default"] = get_english_theme
                            self.config["volume"]["main"] = self.slider_mainv.get_current_value() / 100
                            self.config["volume"]["bg"] = self.slider_bg.get_current_value() / 100
                            self.config["volume"]["effect"] = self.slider_effect.get_current_value() / 100
                            self.config["closed"]["default"] = [self.tr(i) for i in self.config["closed"]["choices"]].index(self.choice_wclosed.selected_option[0])
                            self.config["volume"]["chess"] = self.chk_chessv.is_checked
                            self.config["volume"]["enable"] = self.chk_enable.is_checked
                            self.config["lang"]["default"] = list(self.lang_dct.keys())[list(self.lang_dct.values()).index(self.choice_language.selected_option[0])]
                            with open("config/setting.json", "w", encoding="utf-8") as f:
                                json.dump(self.config, f, indent=4, ensure_ascii=False)

                            self.loadConfig()
                            self.controls()

                            self.writeLog(f"Settings saved.\nconfigs = {self.config}")

                        if event.ui_element == self.btn_openlog:
                            os.startfile("log")

                        if event.ui_element == self.btn_clean:
                            CleanDir("log")
                            self.writeLog("Clean log success.")
                            a = threading.Thread(target=lambda:messagebox.showinfo(self.tr("clean log"), self.tr("Clean log success")))
                            a.daemon = True
                            a.start()

                elif self.page == "play":
                    self.playmanager.process_events(event)

                    if event.type == pgui.UI_BUTTON_PRESSED:
                        if event.ui_element == self.btn_back2:
                            self.page = "home"  

            self.screen.fill("#ffffff")

            self.screen.blit(self.bg, (0,0))

            if self.page == "home":
                self.GaussianScreen(self.screen, (20, 10, 350, 740), radius=10, border_radius=10, mask_color=self.style["maskcolor"])
                self.GaussianScreen(self.screen, (400, 220, 280, 480), radius=10, border_radius=10, mask_color=self.style["maskcolor"])

                self.screen.blit(pg.font.Font(self.fontpath, 32).render("Gomoku AI",True,self.style["fontcolor"]),(25,15))
                self.screen.blit(pg.font.Font(self.fontpath, 48).render(time.ctime(),True,self.style["fontcolor"]),(400,50))
                self.screen.blit(pg.font.Font(self.fontpath, 16).render(f"GMK AI-V{self.version}\nCopyright (c) 2026 mememe2012",True,self.style["fontcolor"]),(400,170))
                self.screen.blit(pg.font.Font(self.fontpath, 10).render(self.tr("Github: {url}\nCopyright © 2026 mememe2012").format(url=self.url),True,self.style["fontcolor"]),(25,720))

                pg.draw.line(self.screen, self.style["fontcolor"], (400,150), (1000,150), 2)
                pg.draw.line(self.screen, self.style["fontcolor"], (700,180), (700,700), 1)

                self.screen.blit(pg.image.load("icon/icon144.png"), (470, 230))

                self.homemanager.update(time_delta)
                self.homemanager.draw_ui(self.screen)

            elif self.page == "setting":
                self.GaussianScreen(self.screen, (10, 80, 1004, 650), radius=10, border_radius=10, mask_color=self.style["maskcolor"])

                self.screen.blit(pg.font.Font(self.fontpath, 48).render(self.tr("Setting"),True,self.style["fontcolor"]),(450,15))
                self.screen.blit(pg.font.Font(self.fontpath, 32).render(f"{self.setting_page}/{self.setting_max_page}",True,self.style["fontcolor"]),(600,675))

                pg.draw.line(self.screen, self.style["fontcolor"], (20,660), (1004,660), 2)

                if self.setting_page == 1:
                    self.choice_language.show()
                    self.choice_theme.show()
                    self.btn_clean.show()
                    self.btn_openlog.show()
                    self.slider_mainv.show()
                    self.slider_bg.show()
                    self.slider_effect.show()
                    self.chk_chessv.show()
                    self.chk_enable.show()
                    self.choice_wclosed.hide()
                    self.screen.blit(pg.font.Font(self.fontpath, 20).render(self.tr("Theme"),True,self.style["fontcolor"]),(20,100))
                    pg.draw.line(self.screen, self.style["fontcolor"], (20,170), (1004,170), 1)
                    self.screen.blit(pg.font.Font(self.fontpath, 20).render(self.tr("Language"),True,self.style["fontcolor"]),(20,180))
                    pg.draw.line(self.screen, self.style["fontcolor"], (20,250), (1004,250), 1)
                    self.screen.blit(pg.font.Font(self.fontpath, 20).render(self.tr("Log and Temp Files"),True,self.style["fontcolor"]),(20,260))
                    pg.draw.line(self.screen, self.style["fontcolor"], (20,330), (1004,330), 1)
                    self.screen.blit(pg.font.Font(self.fontpath, 20).render(self.tr("Volume"),True,self.style["fontcolor"]),(20,340))
                    self.screen.blit(pg.font.Font(self.fontpath, 24).render(self.tr("Master Volume")+f" {int(self.slider_mainv.get_current_value())}%",True,self.style["fontcolor"]),(520,370))
                    self.screen.blit(pg.font.Font(self.fontpath, 24).render(self.tr("Background Music Volume")+f" {int(self.slider_bg.get_current_value())}%",True,self.style["fontcolor"]),(520,410))
                    self.screen.blit(pg.font.Font(self.fontpath, 24).render(self.tr("Effect Volume")+f" {int(self.slider_effect.get_current_value())}%",True,self.style["fontcolor"]),(520,450))
                    self.screen.blit(pg.font.Font(self.fontpath, 24).render(self.tr("Chess Volume")+f" {self.tr("Enable") if self.chk_chessv.is_checked else self.tr("Disable")}",True,self.style["fontcolor"]),(80,490))
                    self.screen.blit(pg.font.Font(self.fontpath, 24).render(self.tr("Master Volume")+f" {self.tr("Enable") if self.chk_enable.is_checked else self.tr("Disable")}",True,self.style["fontcolor"]),(80,530))

                if self.setting_page == 2:
                    self.choice_language.hide()
                    self.choice_theme.hide()
                    self.btn_clean.hide()
                    self.btn_openlog.hide()
                    self.slider_mainv.hide()
                    self.slider_bg.hide()
                    self.slider_effect.hide()
                    self.chk_chessv.hide()
                    self.chk_enable.hide()
                    self.choice_wclosed.show()
                    self.screen.blit(pg.font.Font(self.fontpath, 20).render(self.tr("When the window is closed"),True,self.style["fontcolor"]),(20,100))
                    pg.draw.line(self.screen, self.style["fontcolor"], (20,170), (1004,170), 1)

                self.settingmanager.update(time_delta)
                self.settingmanager.draw_ui(self.screen)

            elif self.page == "play":
                self.playmanager.update(time_delta)
                self.playmanager.draw_ui(self.screen)

                self.chessboard.draw()

            pg.display.update()

        self.quit()
        pg.quit()
        self.tray.stop()
        WinMessage("GomokuAI", self.tr("Quit the Program sucessfully."), "icon/icon144.png")
        self.writeLog("Quit the Program.")
        sys.exit()

    def GaussianScreen(self, 
                        parent:pg.Surface,
                        xywh:tuple[int, int, int, int],
                        radius:int, 
                        border_radius:int, 
                        mask_color:tuple[int, int, int, int] | None = None
                        ):
        x, y, width, height = xywh
        menu_surface = pg.Surface((width, height), pg.SRCALPHA)
        menu_surface.blit(parent, (0, 0), (x, y, width, height))
        gmenu = GaussianBlur(menu_surface, radius=radius, border_radius=border_radius, mask_color=mask_color)
        parent.blit(gmenu, (x, y))

    def quit(self):
        self.running = False

    def quitB(self):
        if self.config["closed"]["default"] == 0:
            self.quit()
        elif self.config["closed"]["default"] == 1:
            HideWindow(self.hwnd)
            self.tray.update_menu()
            WinMessage("GomokuAI", self.tr("The program is minimize to the system tray. You can open or quit this program in the system tray."), "icon/icon144.png")
            self.writeLog("Hide the Program.")

    def github(self):
        if messagebox.askyesno(self.tr("View on GitHub"), self.tr("Do you want to view on Github?")):
            wb.open(self.url)
        
    def controls(self):
        if hasattr(self, "thTray"):
            self.thTray.join(0.1)
            self.tray.stop()
        self.createTray()
        self.homemanager = pgui.UIManager(SIZE, self.theme_path)
        if os.path.exists(self.fontpath):
            self.homemanager.add_font_paths(self.font_family, regular_path=self.fontpath)
            self.homemanager.preload_fonts([
                {"name": self.font_family, "point_size": 16, "style": "regular"},
                {"name": self.font_family, "point_size": 20, "style": "regular"},
                {"name": self.font_family, "point_size": 32, "style": "regular"},
            ])
            self.homemanager.get_theme().get_font({"name": self.font_family, "size": "16"})
            self.homemanager.get_theme().get_font({"name": self.font_family, "size": "20"})
            self.homemanager.get_theme().get_font({"name": self.font_family, "size": "32"})

        self.btn_update = pgui.elements.UIButton(
            relative_rect=pg.Rect(400, 390, 280, 50),
            text=self.tr("Check Update"),
            manager=self.homemanager
        )

        self.btn_update = pgui.elements.UIButton(
            relative_rect=pg.Rect(400, 390, 280, 50),
            text=self.tr("Check Update"),
            manager=self.homemanager
        )
        
        self.btn_issues = pgui.elements.UIButton(
            relative_rect=pg.Rect(400, 450, 280, 50),
            text=self.tr("Issues"),
            manager=self.homemanager
        )

        self.btn_wiki = pgui.elements.UIButton(
            relative_rect=pg.Rect(400, 510, 280, 50),
            text=self.tr("GomokuAI-Wiki"),
            manager=self.homemanager
        )

        self.btn_github = pgui.elements.UIButton(
            relative_rect=pg.Rect(400, 570, 280, 50),
            text=self.tr("View on GitHub"),
            manager=self.homemanager
        )

        self.btn_quit = pgui.elements.UIButton(
            relative_rect=pg.Rect(400, 630, 280, 50),
            text=self.tr("Exit"),
            manager=self.homemanager
        )

        self.btn_setting = pgui.elements.UIButton(
            relative_rect=pg.Rect(20, 55, 350, 50),
            text=self.tr("Settings"),
            manager=self.homemanager
        )

        self.btn_start = pgui.elements.UIButton(
            relative_rect=pg.Rect(20, 115, 350, 50),
            text=self.tr("Play Gomoku"),
            manager=self.homemanager
        )

        self.btn_online = pgui.elements.UIButton(
            relative_rect=pg.Rect(20, 175, 350, 50),
            text=self.tr("Play Gomoku Online"),
            manager=self.homemanager
        )

        self.btn_train = pgui.elements.UIButton(
            relative_rect=pg.Rect(20, 235, 350, 50),
            text=self.tr("Train Gomoku Model"),
            manager=self.homemanager
        )

        self.btn_report = pgui.elements.UIButton(
            relative_rect=pg.Rect(20, 295, 350, 50),
            text=self.tr("Create a Report"),
            manager=self.homemanager
        )

        self.btn_chesslib = pgui.elements.UIButton(
            relative_rect=pg.Rect(20, 355, 350, 50),
            text=self.tr("Chess Library"),
            manager=self.homemanager
        )

        self.settingmanager = pgui.UIManager(SIZE, self.theme_path)
        if os.path.exists(self.fontpath):
            self.settingmanager.add_font_paths(self.font_family, regular_path=self.fontpath)
            self.settingmanager.preload_fonts([
                {"name": self.font_family, "point_size": 16, "style": "regular"},
                {"name": self.font_family, "point_size": 20, "style": "regular"},
                {"name": self.font_family, "point_size": 32, "style": "regular"},
            ])
            self.settingmanager.get_theme().get_font({"name": self.font_family, "size": "16"})
            self.settingmanager.get_theme().get_font({"name": self.font_family, "size": "20"})
            self.settingmanager.get_theme().get_font({"name": self.font_family, "size": "32"})

        self.btn_back1 = pgui.elements.UIButton(
            relative_rect=pg.Rect(10, 10, 100, 60),
            text=self.tr("← Back"),
            manager=self.settingmanager,
        )

        self.btn_pageup = pgui.elements.UIButton(
            relative_rect=pg.Rect(20, 670, 150, 40),
            text=self.tr("Page Up ↑"),
            manager=self.settingmanager,
        )

        self.btn_pagedown = pgui.elements.UIButton(
            relative_rect=pg.Rect(180, 670, 150, 40),
            text=self.tr("Page Down ↓"),
            manager=self.settingmanager,
        )

        self.btn_save = pgui.elements.UIButton(
            relative_rect=pg.Rect(340, 670, 40, 40),
            text=self.tr("√"),
            manager=self.settingmanager,
        )

        self.choice_theme = pgui.elements.UIDropDownMenu(
            options_list=[self.tr(i) for i in self.theme_list],
            starting_option=self.tr(self.config["theme"]["default"]) if not self.tr(self.config["theme"]["system"]) else self.tr("system"),
            relative_rect=pg.Rect(20, 130, 300, 30),
            manager=self.settingmanager,
        )

        self.choice_language = pgui.elements.UIDropDownMenu(
            options_list=self.lang_dct.values(),
            starting_option=self.lang_dct[self.config["lang"]["default"]],
            relative_rect=pg.Rect(20, 210, 300, 30),
            manager=self.settingmanager,
        )

        self.btn_clean = pgui.elements.UIButton(
            relative_rect=pg.Rect(20, 285, 300, 40),
            text=self.tr("Clean Temp Files and Logs"),
            manager=self.settingmanager,
        )

        self.btn_openlog = pgui.elements.UIButton(
            relative_rect=pg.Rect(350, 285, 300, 40),
            text=self.tr("Open Log Directory"),
            manager=self.settingmanager,
        )

        self.slider_mainv = pgui.elements.UIHorizontalSlider(
            relative_rect=pg.Rect(20, 370, 400, 30),
            start_value=self.config["volume"]["main"] * 100,
            value_range=(0,100),
            manager=self.settingmanager,
            click_increment=1,
        )

        self.slider_bg = pgui.elements.UIHorizontalSlider(
            relative_rect=pg.Rect(20, 410, 400, 30),
            start_value=self.config["volume"]["bg"] * 100,
            value_range=(0,100),
            manager=self.settingmanager,
            click_increment=1,
        )

        self.slider_effect = pgui.elements.UIHorizontalSlider(
            relative_rect=pg.Rect(20, 450, 400, 30),
            start_value=self.config["volume"]["effect"] * 100,
            value_range=(0,100),
            manager=self.settingmanager,
            click_increment=1,
        )

        self.chk_chessv = pgui.elements.UICheckBox(
            text = "",
            relative_rect=pg.Rect(20, 490, 30, 30),
            manager=self.settingmanager,
            initial_state=self.config["volume"]["chess"],
        )

        self.chk_enable = pgui.elements.UICheckBox(
            text = "",
            relative_rect=pg.Rect(20, 530, 30, 30),
            manager=self.settingmanager,
            initial_state=self.config["volume"]["enable"],
        )

        self.choice_wclosed = pgui.elements.UIDropDownMenu(
            options_list=[self.tr(i) for i in self.config["closed"]["choices"]],
            relative_rect=pg.Rect(20, 130, 300, 30),
            manager=self.settingmanager,
            starting_option=self.tr(self.config["closed"]["choices"][self.config["closed"]["default"]]),
        )

        self.playmanager = pgui.UIManager(SIZE, self.theme_path)
        if os.path.exists(self.fontpath):
            self.playmanager.add_font_paths(self.font_family, regular_path=self.fontpath)
            self.playmanager.preload_fonts([
                {"name": self.font_family, "point_size": 16, "style": "regular"},
                {"name": self.font_family, "point_size": 20, "style": "regular"},
                {"name": self.font_family, "point_size": 32, "style": "regular"},
            ])
            self.playmanager.get_theme().get_font({"name": self.font_family, "size": "16"})
            self.playmanager.get_theme().get_font({"name": self.font_family, "size": "20"})
            self.playmanager.get_theme().get_font({"name": self.font_family, "size": "32"})

        self.btn_back2 = pgui.elements.UIButton(
            relative_rect=pg.Rect(10, 10, 100, 60),
            text=self.tr("← Back"),
            manager=self.playmanager,
        )

    def tr(self, text):
        if self.config["lang"]["default"] == "en-US":
            return text
        if text in self.dictionary:
            return self.dictionary[text]
        return text
    
    class ChessBoard:
        """
        :boardlst: [(1,1),(2,2),(3,3)...] 记录了落子顺序和坐标的有序列表
        :parent: 父类，用于获取配置信息
        """
        def __init__(self, parent, x, y, size):
            self.parent = parent
            self.boardlst = []
            self.board = [[0 for _ in range(15)] for _ in range(15)]
            self.x = x
            self.y = y
            self.size = size
            self.config = {
                "bgcolor" : "#dd8800",
                "border_radius" : 10,
                "line" : 1,
                "linecolor" : "#000000",
                "textcolor" : "#000000",
                "linewidth" : 2,
                "blackcolor" : "#000000",
                "whitecolor" : "#FFFFFF",
                "latest" : "#ff0000"
            }
            self.ind = 0
            self.sidelen = 30
            self.chesslength = (self.size - self.sidelen*2) // 14
            self.drawmode = "latest" # latest只绘制最新一步, steps绘制所有步数, none:不绘制步数
            CONSOLE.print(f"ChessBoard init, chesslength={self.chesslength}", style="bold green")

        def listToBoard(self):
            self.board = [[0 for _ in range(15)] for _ in range(15)]
            if self.boardlst:
                for k, i in enumerate(self.boardlst):
                    self.board[i[0]][i[1]] = -1 if k % 2 else 1

        def draw(self):
            pg.draw.rect(self.parent.screen, self.config["bgcolor"], (self.x, self.y, self.size, self.size), border_radius=self.config["border_radius"])
            bias = 0
            for i in range(15):
                pg.draw.line(self.parent.screen,
                            self.config["linecolor"],
                            (self.x + self.sidelen + i * self.chesslength, self.y + self.sidelen),
                            (self.x + self.sidelen + i * self.chesslength, self.y + self.size - self.sidelen),
                            self.config["linewidth"]
                            )
                
                pg.draw.line(self.parent.screen,
                            self.config["linecolor"],
                            (self.x + self.sidelen, self.y + self.sidelen + i * self.chesslength),
                            (self.x + self.size - self.sidelen, self.y + self.sidelen + i * self.chesslength),
                            self.config["linewidth"]
                            )
                
                if not self.ind:
                    CONSOLE.print(Panel(f"""[bold white]
(x1,y1):{(self.x + self.sidelen + i * self.chesslength, self.y + self.sidelen)}
(x2,y2):{(self.x + self.sidelen + i * self.chesslength, self.y + self.size - self.sidelen)}
 
(x3,y3):{(self.x + self.sidelen, self.y + self.sidelen + i * self.chesslength)}
(x4,y4):{(self.x + self.size - self.sidelen, self.y + self.sidelen + i * self.chesslength)}
[/bold white]""", title=f"range {i+1}"))
            if not self.ind:self.ind = 1
                
            for i, step in enumerate(self.boardlst):
                xindex, yindex = step
                pg.draw.circle(
                    self.parent.screen,
                    self.config["blackcolor"] if i % 2 == 0 else self.config["whitecolor"],
                    (self.x + self.sidelen + xindex * self.chesslength, self.y + self.sidelen + yindex * self.chesslength),
                    self.chesslength // 2
                )
                if self.drawmode == "latest":
                    if i == len(self.boardlst) - 1:
                        self.parent.screen.blit(pg.font.Font(self.parent.fontpath, self.chesslength).render(
                                str(i + 1),
                                True, 
                                self.config["latest"]
                            ),
                            (
                                self.x + self.sidelen + xindex * self.chesslength - self.chesslength // 4 + bias,
                                self.y + self.sidelen + yindex * self.chesslength - self.chesslength // 2 + bias
                            )
                        )
                elif self.drawmode == "steps":
                    self.parent.screen.blit(pg.font.Font(self.parent.fontpath, self.chesslength).render(
                            str(i + 1),
                            True, 
                            self.config["blackcolor"] if i % 2 == 0 else self.config["whitecolor"] if i ==len(self.boardlst) - 1 else self.config["latest"]
                        ),
                        (
                            self.x + self.sidelen + xindex * self.chesslength - self.chesslength // 4 + bias,
                            self.y + self.sidelen + yindex * self.chesslength - self.chesslength // 2 + bias
                        )
                    )
                        

        def debugPrint(self):
            tmp_board = [["+" for _ in range(16)] for _ in range(16)]
            for i in range(15):
                tmp_board[i][0] = chr(ord("A") + i)
                tmp_board[15][i+1] = chr(ord("A") + i)
            tmp_board[15][0] = " "
            self.listToBoard()
            CONSOLE.print("ChessBoard2D",style="bold blue")
            CONSOLE.print("_"*50, style="bold yellow")
            for i, y in enumerate(self.board):
                for j, x in enumerate(y):
                    if x == -1:
                        tmp_board[i][j+1] = "●"
                    elif x == 1:
                        tmp_board[i][j+1] = "○"

            CONSOLE.print("\n".join([" ".join(x) for x in tmp_board]), style="bold white")

            CONSOLE.print("Steps", style="bold blue")
            CONSOLE.print("_"*50, style="bold yellow")
            for k, i in enumerate(self.boardlst):
                CONSOLE.print((f"{k+1} - {"white" if k % 2 else "black"} | {chr(ord('A')+i[0])}{i[1]+1}({chr(ord('A')+i[0])}{chr(ord('A')+i[1])})"), style="bold white")

if __name__ == '__main__':
    if not CheckSingleInstance():
        hwnd = None
        try:
            with open("tmp/HWND.key", "r", encoding="utf-8") as f:
                hwnd = int(f.readline().strip())
        except (FileNotFoundError, ValueError, OSError):
            hwnd = None

        if hwnd:
            TopWindow(hwnd)
        else:
            CONSOLE.print("No existing HWND found, nothing to activate.", style="yellow")
        sys.exit(0)

    main = Main()
    main.run()
