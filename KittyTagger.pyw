import os
import sys
import webbrowser
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import piexif
import ctypes
import sys

def resource_path(relative_path):
    """Получает абсолютный путь к ресурсу, работает для dev и для PyInstaller"""
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def hide_console():
    """Скрывает терминал"""
    if sys.platform.startswith('win'):
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def main():
    hide_console()
    root = tk.Tk()
    app = GeoTagApp(root)
    root.mainloop()
# ---------- Helpers for GPS EXIF ----------
def _to_deg_rational(value):
    abs_val = abs(float(value))
    deg = int(abs_val)
    min_float = (abs_val - deg) * 60
    minutes = int(min_float)
    sec_float = (min_float - minutes) * 60
    sec = int(round(sec_float * 100))
    return ((deg, 1), (minutes, 1), (sec, 100))

def dec_to_exif_gps(lat, lon):
    lat_ref = b'N' if lat >= 0 else b'S'
    lon_ref = b'E' if lon >= 0 else b'W'
    lat_deg = _to_deg_rational(lat)
    lon_deg = _to_deg_rational(lon)
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: lat_ref,
        piexif.GPSIFD.GPSLatitude: lat_deg,
        piexif.GPSIFD.GPSLongitudeRef: lon_ref,
        piexif.GPSIFD.GPSLongitude: lon_deg,
    }
    return gps_ifd

def exif_gps_to_dec(gps_ifd):
    try:
        lat_ref_raw = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
        lon_ref_raw = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)
        lat_ref = lat_ref_raw.decode() if isinstance(lat_ref_raw, (bytes, bytearray)) else (lat_ref_raw or 'N')
        lon_ref = lon_ref_raw.decode() if isinstance(lon_ref_raw, (bytes, bytearray)) else (lon_ref_raw or 'E')

        lat = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        lon = gps_ifd.get(piexif.GPSIFD.GPSLongitude)
        if not lat or not lon:
            return None

        def rational_to_float(r):
            d = r[0][0] / r[0][1]
            m = r[1][0] / r[1][1]
            s = r[2][0] / r[2][1]
            return d + m / 60.0 + s / 3600.0

        lat_f = rational_to_float(lat)
        lon_f = rational_to_float(lon)
        if str(lat_ref).upper().startswith('S'):
            lat_f = -lat_f
        if str(lon_ref).upper().startswith('W'):
            lon_f = -lon_f
        return (lat_f, lon_f)
    except Exception:
        return None

# ---------- GUI application ----------
class GeoTagApp:
    def __init__(self, root):
        self.root = root
        self.lang = 'ru'
        self.strings = {}
        self._set_strings()
        
        # ФИКСИРОВАННЫЙ РАЗМЕР ОКНА
        self.root.geometry("666x666")
        self.root.resizable(False, False)
        root.title(self.strings['title'])

        # Icon
        try:
            if os.path.exists('2.png'):
                img = Image.open('2.png')
                self.icon_img = ImageTk.PhotoImage(img)
                root.iconphoto(True, self.icon_img)
        except:
            pass

        #Canvas для фона на ВЕСЬ ЭКРАН (bg='black' только для случая без изображения)
        self.canvas = tk.Canvas(root, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)

        # Загрузка фона
        def resource_path(relative_path):
            """Получает абсолютный путь к ресурсу, работает для dev и PyInstaller"""
            try:
                # PyInstaller создаёт временную папку и сохраняет туда путь в _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)

        self.bg_pil = None
        self.bg_tk = None
        bg_path1 = resource_path('1.png')
        bg_path2 = resource_path('1.gif')

        if os.path.exists(bg_path1):
            try:
                self.bg_pil = Image.open(bg_path1).convert('RGBA')
            except:
                self.bg_pil = None
        elif os.path.exists(bg_path2):
            try:
                self.bg_pil = Image.open(bg_path2).convert('RGBA')
            except:
                self.bg_pil = None

        # Инициализация шрифтов
        self.title_font = ('Comic Sans MS', 9, 'bold')
        self.desc_font = ('Comic Sans MS', 8)
        self.btn_font = ('Arial', 11, 'bold')

        # ЧЕРНЫЙ ТЕКСТ НА СВЕТЛОМ ФОНE
        self.title_lbl = tk.Label(root, text=self.strings['title'], 
                                font=self.title_font, 
                                fg='black')
        self.title_lbl.place(relx=0.5, rely=0.25, anchor='center')
        
        self.desc_lbl = tk.Label(root, text=self.strings['desc'], 
                               justify='center', wraplength=620,
                               font=self.desc_font, 
                               fg='black')
        self.desc_lbl.place(relx=0.5, rely=0.38, anchor='center')



        # Кнопки с цветными фонами
        y_pos = 0.52
        spacing = 0.08
        
        self.btn_add = tk.Button(root, text=self.strings['add'], width=22, height=2,
                               font=self.btn_font, command=self.add_geotag,
                               bg='#4CAF50', fg='white', relief='flat', bd=0)
        self.btn_add.place(relx=0.5, rely=y_pos, anchor='center')
        y_pos += spacing

        self.btn_remove = tk.Button(root, text=self.strings['remove'], width=22, height=2,
                                  font=self.btn_font, command=self.remove_geotag,
                                  bg='#f44336', fg='white', relief='flat', bd=0)
        self.btn_remove.place(relx=0.5, rely=y_pos, anchor='center')
        y_pos += spacing

        self.btn_view = tk.Button(root, text=self.strings['view'], width=22, height=2,
                                font=self.btn_font, command=self.view_geotag,
                                bg='#2196F3', fg='white', relief='flat', bd=0)
        self.btn_view.place(relx=0.5, rely=y_pos, anchor='center')
        y_pos += spacing

        self.btn_lang = tk.Button(root, text=self.strings['lang'], width=22, height=2,
                                font=self.btn_font, command=self.change_language,
                                bg='#FF9800', fg='white', relief='flat', bd=0)
        self.btn_lang.place(relx=0.5, rely=y_pos, anchor='center')
        y_pos += spacing

        self.btn_exit = tk.Button(root, text=self.strings['exit'], width=22, height=2,
                                font=self.btn_font, command=root.quit,
                                bg='#9E9E9E', fg='white', relief='flat', bd=0)
        self.btn_exit.place(relx=0.5, rely=y_pos, anchor='center')

        # Инициализация макета
        self.root.after(100, self._init_layout)

    def paste_from_clipboard(self):
        #ВСТАВКА ИЗ БУФЕРА ОБМЕНА
        try:
            clipboard_text = self.root.clipboard_get()
            # Проверяем формат координат из буфера
            coords = self.parse_coords(clipboard_text)
            if coords:
                simpledialog.askstring("Координаты из буфера", 
                                     f"Вставлены координаты:\n{clipboard_text}\n\nПодтвердить?", 
                                     initialvalue=clipboard_text)
                return coords
            else:
                messagebox.showwarning("Предупреждение", 
                                     f"Текст из буфера не содержит корректные координаты:\n{clipboard_text}\n\nФормат: широта, долгота")
                return None
        except tk.TclError:
            messagebox.showwarning("Буфер обмена", "Буфер обмена пуст или недоступен")
            return None
    def _adjust_fonts(self):
        title_size = 24    # ← ЗАГОЛОВОК (было 20)
        desc_size = 16     # ← ОПИСАНИЕ (было 14)
        btn_size = 13      # ← КНОПКИ (было 11)
    
        self.title_font = ('Comic Sans MS', title_size, 'bold')
        self.desc_font = ('Comic Sans MS', desc_size)
        self.btn_font = ('Arial', btn_size, 'bold')
    
        #config() + update() для НУЖНОЙ геометрии
        self.title_lbl.config(font=self.title_font, fg='black')
        self.title_lbl.update()
    
        self.desc_lbl.config(font=self.desc_font, wraplength=620, fg='black')
        self.desc_lbl.update()
    
        self.btn_add.config(font=self.btn_font)
        self.btn_remove.config(font=self.btn_font)
        self.btn_view.config(font=self.btn_font)
        self.btn_lang.config(font=self.btn_font)
        self.btn_exit.config(font=self.btn_font)

    def _init_layout(self):
        """Инициализация макета"""
        self._on_resize()
        self._adjust_fonts()

    def _on_resize(self):
        """ФОН ТОЧНО РАЗМЕРОМ ВСЕГО ОКНА 666x666"""
        FIXED_WIDTH = 666
        FIXED_HEIGHT = 666
        
        if self.bg_pil:
            resized = self.bg_pil.resize((FIXED_WIDTH, FIXED_HEIGHT), Image.LANCZOS)
            self.bg_tk = ImageTk.PhotoImage(resized)
        else:
            # Если нет фона - черный прямоугольник
            self.canvas.delete('bg')
            self.canvas.create_rectangle(0, 0, FIXED_WIDTH, FIXED_HEIGHT, 
                                       fill='black', outline='', tags='bg')
            self.canvas.tag_lower('bg')
            return
            self.canvas.delete('bg')
            self.canvas.create_image(FIXED_WIDTH//2, FIXED_HEIGHT//2, 
                                   image=self.bg_tk, anchor='center', tags='bg')
            self.canvas.tag_lower('bg')
        #ФОН ТОЧНО НА ВЕСЬ КАНВАС ПОД ВСЕ ЭЛЕМЕНТЫ
        self.canvas.delete('bg')
        self.canvas.create_image(FIXED_WIDTH//2, FIXED_HEIGHT//2, 
                               image=self.bg_tk, anchor='center', tags='bg')
        self.canvas.tag_lower('bg')  # Фон ПОД текстом и кнопками

    def _set_strings(self):
        if self.lang == 'ru':
            self.strings = {
                'title': 'KᵢₜₜyTₐggₑᵣ\nᵥ₀.₀.₃-ᵣₑₗₑₐₛₑ',
                'desc': 'Используйте меню ниже для добавления, удаления или просмотра геометок GPS в метаданных изображения.',
                'add': 'Добавить геометку', 'remove': 'Убрать геометку', 
                'view': 'Посмотреть геометку', 'lang': 'Change Language', 'exit': 'Выход',
                'input_coord': 'Введите координаты (формат: широта, долгота). Пример: 55.7558, 37.6173',
                'invalid_coord': 'Некорректный формат координат.',
                'select_file': 'Выберите файл изображения', 'no_gps': 'Геометка не найдена в файле.',
                'gps_removed': 'Геометка удалена.', 'gps_added': 'Геометка добавлена.',
                'error': 'Ошибка', 'open_browser_fail': 'Не удалось открыть браузер.',
            }
        else:
            self.strings = {
                'title': 'KᵢₜₜyTₐggₑᵣ\nᵥ₀.₀.₃-ᵣₑₗₑₐₛₑ',
                'desc': 'Use the menu below to add, remove or view geotags GPS in image metadata.',
                'add': 'Add geotag', 'remove': 'Remove geotag', 
                'view': 'View geotag', 'lang': 'Сменить язык', 'exit': 'Exit',
                'input_coord': 'Enter coordinates (lat, lon). Example: 55.7558, 37.6173',
                'invalid_coord': 'Invalid coordinate format.',
                'select_file': 'Select image file', 'no_gps': 'No geotag found in file.',
                'gps_removed': 'Geotag removed.', 'gps_added': 'Geotag added.',
                'error': 'Error', 'open_browser_fail': 'Failed to open browser.',
            }

    def change_language(self):
        self.lang = 'en' if self.lang == 'ru' else 'ru'
        self._set_strings()
    
        lang_button_text = 'Change Language' if self.lang == 'ru' else 'Сменить язык'
        self.btn_lang.config(text=lang_button_text)
    
        self.title_lbl.config(text=self.strings['title'], fg='black')
        self.desc_lbl.config(text=self.strings['desc'], fg='black')
        self.btn_add.config(text=self.strings['add'])
        self.btn_remove.config(text=self.strings['remove'])
        self.btn_view.config(text=self.strings['view'])
        self.btn_exit.config(text=self.strings['exit'])
        self.root.title(self.strings['title'])
    
        self._adjust_fonts()  #Новые шрифты

    def ask_for_file(self):
        filetypes = [("Image files", ("*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.png", "*.PNG")), ("All files", "*.*")]
        path = filedialog.askopenfilename(title=self.strings['select_file'], filetypes=filetypes)
        return path

    def parse_coords(self, txt):
        try:
            parts = txt.replace(',', ' ').split()
            if len(parts) < 2:
                return None
            lat = float(parts[0])
            lon = float(parts[1])
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                return None
            return (lat, lon)
        except:
            return None

    def add_geotag(self):
        coords_from_clipboard = self.paste_from_clipboard()
        if coords_from_clipboard:
            res = str(coords_from_clipboard[0]) + ", " + str(coords_from_clipboard[1])
        else:
            prompt = self.strings['input_coord']
            res = simpledialog.askstring(self.strings['add'], prompt)
            if res is None:
                return
        coords = self.parse_coords(res)
        if not coords:
            messagebox.showerror(self.strings['error'], self.strings['invalid_coord'])
            return
        path = self.ask_for_file()
        if not path:
            return
        try:
            if path.lower().endswith('.png'):
                xmp = f'''<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description xmlns:exif="http://ns.adobe.com/exif/1.0/" exif:GPSLatitude="{coords[0]}" exif:GPSLongitude="{coords[1]}"/>
 </rdf:RDF>
</x:xmpmeta>'''
                self._write_png_xmp(path, xmp)
                messagebox.showinfo(self.strings['add'], self.strings['gps_added'])
                return
            exif_dict = piexif.load(path)
            gps_ifd = dec_to_exif_gps(coords[0], coords[1])
            exif_dict['GPS'] = gps_ifd
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, path)
            messagebox.showinfo(self.strings['add'], self.strings['gps_added'])
        except Exception as e:
            messagebox.showerror(self.strings['error'], f"{self.strings.get('error')}: {e}")

    def remove_geotag(self):
        path = self.ask_for_file()
        if not path:
            return
        try:
            if path.lower().endswith('.png'):
                self._write_png_xmp(path, "")
                messagebox.showinfo(self.strings['remove'], self.strings['gps_removed'])
                return
            exif_dict = piexif.load(path)
            if not exif_dict.get('GPS'):
                messagebox.showinfo(self.strings['remove'], self.strings['no_gps'])
                return
            exif_dict['GPS'] = {}
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, path)
            messagebox.showinfo(self.strings['remove'], self.strings['gps_removed'])
        except Exception as e:
            messagebox.showerror(self.strings['error'], f"{self.strings.get('error')}: {e}")

    def view_geotag(self):
        path = self.ask_for_file()
        if not path:
            return
        try:
            coords = None
            if path.lower().endswith('.png'):
                xmp = self._read_png_xmp(path)
                if xmp:
                    import re
                    lat_m = re.search(r'GPSLatitude=["\']?([-\d.]+)["\']?', xmp)
                    lon_m = re.search(r'GPSLongitude=["\']?([-\d.]+)["\']?', xmp)
                    if lat_m and lon_m:
                        lat = float(lat_m.group(1))
                        lon = float(lon_m.group(1))
                        coords = (lat, lon)
            if coords is None:
                exif_dict = piexif.load(path)
                gps = exif_dict.get('GPS', {})
                coords = exif_gps_to_dec(gps) if gps else None
            if not coords:
                messagebox.showinfo(self.strings['view'], self.strings['no_gps'])
                return
            lat, lon = coords
            if self.lang == 'ru':
                url = f"https://yandex.ru/maps/?whatshere%5Bpoint%5D={lon}%2C{lat}&whatshere%5Bzoom%5D=16"
            else:
                url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror(self.strings['error'], f"{self.strings.get('error')}: {e}")

    def _read_png_xmp(self, path):
        try:
            im = Image.open(path)
            info = im.info
            xmp = info.get('XML:com.adobe.xmp') or info.get('xmp') or info.get('xml')
            return xmp
        except:
            return None

    def _write_png_xmp(self, path, xmp_str):
        try:
            from PIL import PngImagePlugin
            im = Image.open(path)
            meta = PngImagePlugin.PngInfo()
            try:
                for k, v in im.info.items():
                    if k in ('XML:com.adobe.xmp', 'xmp', 'xml'):
                        continue
                    if isinstance(v, bytes):
                        try:
                            v = v.decode('utf-8')
                        except:
                            v = v.decode(errors='ignore')
                    meta.add_text(k, str(v))
            except:
                pass
            meta.add_text("XML:com.adobe.xmp", xmp_str)
            im.save(path, "PNG", pnginfo=meta)
            return True
        except:
            return False

def main():
    root = tk.Tk()
    app = GeoTagApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
