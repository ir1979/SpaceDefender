"""
ماژول موجودیت پایه (Base Entity) بازی
این ماژول کلاس‌های انتزاعی پایه‌ای برای تمامی موجودیت‌های گرافیکی و متحرک بازی را فراهم می‌کند.
"""
import pygame
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any

class BaseEntity(pygame.sprite.Sprite, ABC):
    """
    کلاس انتزاعی پایه برای تمامی اشیاء و موجودیت‌های بازی.
    
    این کلاس از pygame.sprite.Sprite ارث‌بری می‌کند تا به متدهای
    برخورد و مدیریت گروهی اسپرایت‌ها متصل شود. تمامی اشیاء بازی نظیر
    بازیکن، تیرها و دشمنان باید از این کلاس مشتق شوند.
    """
    
    def __init__(self, x: int, y: int):
        """
        مقداردهی اولیه موجودیت در موقعیت افقی و عمودی مشخص.
        
        آرگومان‌ها:
            x (int): مختصات شروع افقی در صفحه
            y (int): مختصات شروع عمودی در صفحه
        """
        super().__init__()
        self.x = x
        self.y = y
        self._create_image()
        self.rect = self.image.get_rect(center=(x, y))
    
    @abstractmethod
    def _create_image(self):
        """
        ایجاد و مقداردهی اولیه به نمایه گرافیکی موجودیت.
        (باید در کلاس‌های فرزند بازنویسی شود)
        """
        pass
    
    @abstractmethod
    def update(self):
        """
        به‌روزرسانی منطق فیزیکی یا انیمیشن موجودیت در هر فریم.
        (باید در کلاس‌های فرزند بازنویسی شود)
        """
        pass
    
    def get_data(self) -> Dict[str, Any]:
        """
        تبدیل مشخصات فعلی موجودیت به دیکشنری جهت ذخیره‌سازی یا انتقال شبکه.
        
        خروجی:
            Dict[str, Any]: موقعیت و نام کلاس موجودیت
        """
        return {
            'type': self.__class__.__name__,
            'x': self.rect.centerx,
            'y': self.rect.centery
        }

class ShapeRenderer:
    """
    رندرکننده اشکال گرافیکی هندسی و بارگذاری اسپرایت‌های بازی.
    
    این کلاس تلاش می‌کند اسپرایت‌های تصویری را لود کند و در صورت عدم وجود،
    اشکال هندسی پیش‌فرض (دایره، مستطیل، ستاره) را به صورت الگوریتمی نقاشی کند.
    """
    
    # ارجاع به مدیر منابع برای بارگذاری اسپرایت‌ها
    asset_manager = None
    
    @staticmethod
    def set_asset_manager(asset_mgr):
        """
        ثبت کردن مدیر منابع بازی جهت بارگذاری تصاویر.
        
        آرگومان‌ها:
            asset_mgr: شیء مدیریت دارایی‌ها (AssetManager)
        """
        ShapeRenderer.asset_manager = asset_mgr
    
    @staticmethod
    def create_shape(shape_type: str, size: Tuple[int, int], 
                     color: Tuple[int, int, int]) -> pygame.Surface:
        """
        تولید یک بوم تصویری (Surface) بر اساس نوع شکل و ابعاد.
        
        ابتدا سعی می‌شود اسپرایت متناظر لود شود و در غیر این صورت اشکال
        هندسی پایه با کدهای رنگی و ضخامت مشخص ترسیم می‌شوند.
        
        آرگومان‌ها:
            shape_type (str): نام فایل اسپرایت یا نوع شکل هندسی (مثل spaceship یا star)
            size (Tuple[int, int]): ابعاد عرض و ارتفاع بوم به پیکسل
            color (Tuple[int, int, int]): کد رنگی RGB
            
        خروجی:
            pygame.Surface: بوم گرافیکی ساخته شده آماده رندر
        """
        # تلاش برای بارگذاری اسپرایت تصویری
        if ShapeRenderer.asset_manager:
            sprite = ShapeRenderer.asset_manager.get_sprite(shape_type)
            if sprite:
                # تغییر سایز متناسب به ابعاد مورد نیاز همراه با حفظ کانال آلفا (شفافیت)
                scaled_sprite = pygame.transform.smoothscale(sprite.convert_alpha(), size)
                return scaled_sprite
        
        # در صورت نبود فایل تصویر، رندر اشکال هندسی پایه
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        if shape_type == "rectangle":
            surface.fill(color)
            pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 2)
        
        elif shape_type == "circle":
            radius = min(size) // 2
            center = (size[0] // 2, size[1] // 2)
            pygame.draw.circle(surface, color, center, radius)
            pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)
        
        elif shape_type == "triangle":
            points = [
                (size[0] // 2, 0),
                (size[0], size[1]),
                (0, size[1])
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "diamond":
            points = [
                (size[0] // 2, 0),
                (size[0], size[1] // 2),
                (size[0] // 2, size[1]),
                (0, size[1] // 2)
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "star":
            center = (size[0] // 2, size[1] // 2)
            outer_radius = min(size) // 2
            inner_radius = outer_radius // 2
            points = []
            
            for i in range(10):
                angle = (i * 36 - 90) * 3.14159 / 180
                radius = outer_radius if i % 2 == 0 else inner_radius
                x = center[0] + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).x
                y = center[1] + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).y
                points.append((x, y))
            
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "spaceship":
            # رسم هندسی سفینه کلاسیک نوک‌تیز
            points = [
                (size[0] // 2, 0),
                (int(size[0] * 0.8), int(size[1] * 0.4)),
                (int(size[0] * 0.6), int(size[1] * 0.5)),
                (size[0], size[1]),
                (size[0] // 2, int(size[1] * 0.7)),
                (0, size[1]),
                (int(size[0] * 0.4), int(size[1] * 0.5)),
                (int(size[0] * 0.2), int(size[1] * 0.4))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "fighter":
            # رسم جنگنده باریک آیرودینامیک
            points = [
                (size[0] // 2, 0),
                (int(size[0] * 0.75), int(size[1] * 0.3)),
                (size[0], int(size[1] * 0.4)),
                (int(size[0] * 0.85), int(size[1] * 0.7)),
                (size[0] // 2, int(size[1] * 0.8)),
                (int(size[0] * 0.15), int(size[1] * 0.7)),
                (0, int(size[1] * 0.4)),
                (int(size[0] * 0.25), int(size[1] * 0.3))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "bullet_basic":
            # رسم تیر معمولی کلاسیک
            points = [
                (size[0] // 2, 0),
                (size[0], int(size[1] * 0.3)),
                (int(size[0] * 0.8), size[1]),
                (size[0] // 2, int(size[1] * 0.9)),
                (int(size[0] * 0.2), size[1]),
                (0, int(size[1] * 0.3))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 1)
        
        elif shape_type == "bullet_laser":
            # رسم تیر باریک لیزری فیروزه‌ای
            pygame.draw.line(surface, color, (size[0] // 2, 0), (size[0] // 2, size[1]), 3)
            pygame.draw.circle(surface, (255, 255, 255), (size[0] // 2, 0), 2)
            pygame.draw.circle(surface, (255, 255, 255), (size[0] // 2, size[1]), 2)
        
        elif shape_type == "bullet_plasma":
            # رسم گلوله پلاسمای دایره‌ای با هاله
            center = (size[0] // 2, size[1] // 2)
            radius = min(size) // 2
            pygame.draw.circle(surface, color, center, radius)
            pygame.draw.circle(surface, (255, 255, 255), center, radius, 1)
            pygame.draw.circle(surface, color, center, max(1, radius - 3), 0)
        
        elif shape_type == "bullet_missile":
            # رسم فیزیکی راکت یا موشک جنگی
            points = [
                (int(size[0] * 0.4), 0),
                (int(size[0] * 0.6), 0),
                (int(size[0] * 0.7), int(size[1] * 0.6)),
                (size[0] // 2, size[1]),
                (int(size[0] * 0.3), int(size[1] * 0.6))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "gun_mount":
            # رسم لوله توپ سنگین
            points = [
                (int(size[0] * 0.3), 0),
                (int(size[0] * 0.7), 0),
                (int(size[0] * 0.8), int(size[1] * 0.4)),
                (int(size[0] * 0.6), int(size[1] * 0.8)),
                (int(size[0] * 0.4), int(size[1] * 0.8)),
                (int(size[0] * 0.2), int(size[1] * 0.4))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "cannon":
            # رسم پایه تانک شلیک گلوله پلاسمایی
            rect = pygame.Rect(int(size[0] * 0.25), int(size[1] * 0.2), int(size[0] * 0.5), int(size[1] * 0.6))
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        
        elif shape_type == "enemy_basic":
            # رسم مربع دشمن ساده با چشمان متحرک
            pygame.draw.rect(surface, color, (int(size[0] * 0.2), int(size[1] * 0.2), int(size[0] * 0.6), int(size[1] * 0.6)))
            pygame.draw.rect(surface, (255, 255, 255), (int(size[0] * 0.2), int(size[1] * 0.2), int(size[0] * 0.6), int(size[1] * 0.6)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(size[0] * 0.35), int(size[1] * 0.35)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(size[0] * 0.65), int(size[1] * 0.35)), 2)
        
        elif shape_type == "enemy_fast":
            # رسم دشمن سرعتی فلش‌مانند
            points = [
                (size[0] // 2, 0),
                (size[0], int(size[1] * 0.3)),
                (int(size[0] * 0.8), int(size[1] * 0.7)),
                (size[0], size[1]),
                (size[0] // 2, int(size[1] * 0.8)),
                (0, size[1]),
                (int(size[0] * 0.2), int(size[1] * 0.7)),
                (0, int(size[1] * 0.3))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "enemy_tank":
            # رسم سپر فیزیکی تانک سنگین
            points = [
                (int(size[0] * 0.1), int(size[1] * 0.3)),
                (int(size[0] * 0.9), int(size[1] * 0.3)),
                (int(size[0] * 0.95), int(size[1] * 0.5)),
                (int(size[0] * 0.95), int(size[1] * 0.8)),
                (size[0] // 2, size[1]),
                (int(size[0] * 0.05), int(size[1] * 0.8)),
                (int(size[0] * 0.05), int(size[1] * 0.5))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "enemy_weaver":
            # رسم نوسان‌ساز دشمن سینوسی
            points = [
                (int(size[0] * 0.3), int(size[1] * 0.2)),
                (int(size[0] * 0.7), int(size[1] * 0.2)),
                (int(size[0] * 0.9), int(size[1] * 0.4)),
                (int(size[0] * 0.8), int(size[1] * 0.6)),
                (size[0], int(size[1] * 0.8)),
                (size[0] // 2, size[1]),
                (0, int(size[1] * 0.8)),
                (int(size[0] * 0.2), int(size[1] * 0.6)),
                (int(size[0] * 0.1), int(size[1] * 0.4))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "enemy_boss":
            # رسم دایره‌ای با جزئیات غول مرحله آخر
            center = (size[0] // 2, size[1] // 2)
            pygame.draw.circle(surface, color, center, min(size) // 2)
            pygame.draw.circle(surface, (255, 255, 255), center, min(size) // 2, 3)
            pygame.draw.circle(surface, (255, 255, 255), center, min(size) // 3, 1)
        
        elif shape_type == "hexagon":
            # رسم شش‌ضلعی منتظم
            center = (size[0] // 2, size[1] // 2)
            radius = min(size) // 2
            points = []
            for i in range(6):
                angle = i * 60 * 3.14159 / 180
                x = center[0] + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).x
                y = center[1] + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).y
                points.append((x, y))
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "cross":
            # رسم به علاوه یا ضربدر کمک‌کمک
            pygame.draw.rect(surface, color, (int(size[0] * 0.4), 0, int(size[0] * 0.2), size[1]))
            pygame.draw.rect(surface, color, (0, int(size[1] * 0.4), size[0], int(size[1] * 0.2)))
            pygame.draw.rect(surface, (255, 255, 255), (int(size[0] * 0.4), 0, int(size[0] * 0.2), size[1]), 1)
            pygame.draw.rect(surface, (255, 255, 255), (0, int(size[1] * 0.4), size[0], int(size[1] * 0.2)), 1)
        
        elif shape_type == "crescent":
            # رسم هلال ماه
            center = (size[0] // 2, size[1] // 2)
            radius = min(size) // 2
            pygame.draw.circle(surface, color, center, radius)
            pygame.draw.circle(surface, (0, 0, 0, 0), (center[0] + radius // 2, center[1]), radius - 3)
            pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)
        
        else:  # مستطیل پیش‌فرض در صورت نشناختن نوع شکل
            surface.fill(color)
        
        return surface

class EntityFactory:
    """
    کارخانه تولید و ثبت کلاس‌های مختلف موجودیت در پروژه (الگوی طراحی Factory).
    """
    
    _entity_types = {}
    
    @classmethod
    def register(cls, entity_type: str, entity_class):
        """
        ثبت یک نوع جدید موجودیت به همراه نام کلاس والد آن.
        
        آرگومان‌ها:
            entity_type (str): نام نوع موجودیت (مثلاً player)
            entity_class: مرجع کلاس پایتون
        """
        cls._entity_types[entity_type] = entity_class
    
    @classmethod
    def create(cls, entity_type: str, **kwargs) -> Optional[BaseEntity]:
        """
        ساخت و بازگرداندن یک نمونه جدید از موجودیت ثبت شده.
        
        آرگومان‌ها:
            entity_type (str): نوع موجودیت درخواستی
            **kwargs: متغیرهای ارسالی به سازنده کلاس
            
        خروجی:
            Optional[BaseEntity]: شیء ساخته شده یا None در صورت عدم تطابق
        """
        entity_class = cls._entity_types.get(entity_type)
        if entity_class:
            return entity_class(**kwargs)
        return None
    
    @classmethod
    def get_registered_types(cls):
        """
        دریافت لیست تمامی انواع موجودیت‌های ثبت شده.
        """
        return list(cls._entity_types.keys())
