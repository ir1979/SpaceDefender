"""
ماژول تنظیمات و پیکربندی بازی
این ماژول مقادیر ثابت، ساختار پیکربندی و رنگ‌های رابط کاربری بازی را مدیریت می‌کند.
"""
from dataclasses import dataclass
from typing import Tuple
from enum import Enum
import logging

# تنظیمات مربوط به ثبت لاگ‌های سیستم
LOG_LEVEL = logging.DEBUG  # سطح ثبت لاگ (دیباگ، اینفو، هشدار، خطا)
LOG_FILE = "game.log"      # مسیر فایل لاگ خروجی

@dataclass
class GameConfig:
    """
    تنظیمات ابعاد، نسخه و مشخصات اصلی موتور بازی.
    """
    SCREEN_WIDTH: int = 1024  # عرض پنجره بازی به پیکسل
    SCREEN_HEIGHT: int = 768  # ارتفاع پنجره بازی به پیکسل
    FPS: int = 30             # نرخ فریم قفل بازی در ثانیه
    TITLE: str = "Space Defender"  # عنوان پنجره بازی
    VERSION: str = "2.1"      # نسخه بازی
    AUTHOR: str = "Ali Mortazavi"  # نام توسعه‌دهنده
    
    # متغیرهای منطق بازی
    LEVEL_TIME_LIMIT: int = 90  # محدودیت زمانی هر مرحله به ثانیه
    STARTING_COINS: int = 0     # سکه‌های اولیه بازیکن
    LEVEL_COIN_BONUS: int = 100 # جایزه به اتمام رساندن هر مرحله
    
    # مسیرهای فیزیکی فایل‌های داده
    SAVE_FILE: str = "data/profiles.json"     # فایل ذخیره پروفایل‌ها
    PLUGIN_DIR: str = "plugins"               # پوشه افزونه‌های داینامیک
    DATA_DIR: str = "data"                     # پوشه فایل‌های داده JSON
    BACKGROUND_DIR: str = "assets/backgrounds" # پوشه بک‌گراندهای بازی

@dataclass
class ColorConfig:
    """
    پالت رنگ‌های مورد استفاده در بازی و رابط کاربری (مبتنی بر RGB).
    """
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    RED: Tuple[int, int, int] = (255, 50, 50)
    GREEN: Tuple[int, int, int] = (50, 255, 50)
    BLUE: Tuple[int, int, int] = (50, 150, 255)
    YELLOW: Tuple[int, int, int] = (255, 255, 50)
    PURPLE: Tuple[int, int, int] = (200, 50, 255)
    ORANGE: Tuple[int, int, int] = (255, 150, 50)
    CYAN: Tuple[int, int, int] = (50, 255, 255)
    
    # رنگ‌های رابط کاربری
    UI_BG: Tuple[int, int, int] = (20, 20, 40)
    UI_BORDER: Tuple[int, int, int] = (100, 100, 150)
    UI_TEXT: Tuple[int, int, int] = (220, 220, 255)

@dataclass
class PlayerConfig:
    """
    تنظیمات فیزیکی اولیه سفینه بازیکن (سرعت، شتاب، اصطکاک و غیره).
    """
    SPEED: int = 6                  # سرعت پایه حرکت
    HEALTH: int = 65                # مقدار سلامتی اولیه
    DAMAGE: int = 20                # قدرت آسیب پایه گلوله‌ها
    FIRE_RATE: int = 14             # نرخ آتش تفنگ سفینه
    ACCELERATION: float = 0.45      # شتاب حرکت سفینه در فضا
    MAX_SPEED: float = 8.0          # حداکثر سرعت مجاز سفینه
    DRAG: float = 0.90              # ضریب اصطکاک خلاء برای اینرسی سفینه
    MOUSE_FOLLOW_FACTOR: float = 0.25  # ضریب سرعت دنبال کردن نشانه ماوس

class GameState(Enum):
    """
    حالت‌های مختلف مجاز در چرخه اجرای بازی.
    """
    SPLASH_SCREEN = 0        # صفحه نمایش لوگو اولیه
    NAME_INPUT = 1           # دریافت نام بازیکن جدید
    PROFILE_SELECT = 2       # انتخاب پروفایل‌های موجود
    PASSWORD_INPUT = 3       # دریافت رمز عبور
    MAIN_MENU = 4            # منوی اصلی بازی
    PLAYING = 5              # در حال گیم‌پلی اصلی
    PAUSED = 6               # حالت توقف بازی
    SHOP = 7                 # فروشگاه ارتقای سپر و اسلحه
    GAME_OVER = 8            # صفحه گیم‌اور (باختن بازیکن)
    LEVEL_COMPLETE = 9       # صفحه اتمام موفقیت‌آمیز مرحله
    HIGH_SCORES = 10         # صفحه رکوردهای برتر بازیکنان
    QUIT_CONFIRM = 11        # تاییدیه خروج از بازی
    WAITING_FOR_PLAYERS = 12 # فاز انتظار برای بازی تحت شبکه
    SERVER_CONNECT = 13      # تنظیمات اتصال به سرور آنلاین

# ایجاد نمونه‌های گلوبال ثابت جهت استفاده در سایر کلاس‌ها
game_config = GameConfig()
color_config = ColorConfig()
player_config = PlayerConfig()
