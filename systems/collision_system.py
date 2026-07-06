"""
ماژول سیستم برخورد (Collision System)
این ماژول ابزارهای استاتیک بررسی تصادف و محاسبات همپوشانی مستطیلی و دایره‌ای اشیاء را ارائه می‌کند.
"""
import pygame
from typing import List, Tuple, Callable

class CollisionSystem:
    """
    سیستم مدیریت و تشخیص برخوردهای فیزیکی بین اشیاء مختلف بازی.
    
    این کلاس به صورت استاتیک متدهایی برای بررسی تصادم مستطیلی (Bounding Box)
    و دایره‌ای (فاصله اقلیدسی) و برخوردهای گروهی اسپرایت‌ها را ارائه می‌دهد.
    """
    
    @staticmethod
    def check_rect_collision(rect1: pygame.Rect, rect2: pygame.Rect) -> bool:
        """
        بررسی برخورد دو کادر مستطیلی فرضی به کمک متدهای پای‌گیم.
        
        آرگومان‌ها:
            rect1 (pygame.Rect): مستطیل فیزیکی شیء اول
            rect2 (pygame.Rect): مستطیل فیزیکی شیء دوم
            
        خروجی:
            bool: مقدار True در صورت همپوشانی مستطیل‌ها
        """
        return rect1.colliderect(rect2)
    
    @staticmethod
    def check_circle_collision(pos1: Tuple[float, float], radius1: float,
                              pos2: Tuple[float, float], radius2: float) -> bool:
        """
        بررسی برخورد دو دایره فرضی با استفاده از محاسبه فاصله اقلیدسی مرکز آن‌ها.
        
        آرگومان‌ها:
            pos1 (Tuple[float, float]): مختصات مرکز دایره اول (X, Y)
            radius1 (float): شعاع دایره اول
            pos2 (Tuple[float, float]): مختصات مرکز دایره دوم (X, Y)
            radius2 (float): شعاع دایره دوم
            
        خروجی:
            bool: مقدار True در صورتی که فاصله کمتر از مجموع شعاع‌ها باشد
        """
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        distance = (dx**2 + dy**2)**0.5
        return distance < radius1 + radius2
    
    @staticmethod
    def check_group_collision(sprite: pygame.sprite.Sprite,
                            group: pygame.sprite.Group) -> List[pygame.sprite.Sprite]:
        """
        بررسی برخورد یک اسپرایت منفرد با کل اعضای یک گروه اسپرایت.
        
        آرگومان‌ها:
            sprite (pygame.sprite.Sprite): شیء منفرد مورد بررسی
            group (pygame.sprite.Group): گروه اسپرایت‌های هدف
            
        خروجی:
            List[pygame.sprite.Sprite]: لیستی از تمام اسپرایت‌های گروه که با شیء منفرد تصادف کرده‌اند
        """
        return pygame.sprite.spritecollide(sprite, group, False)
    
    @staticmethod
    def resolve_collision(obj1, obj2, callback: Callable = None):
        """
        رفع تداخل و اعمال صدمه یا رویداد برخورد بین دو شیء به کمک توابع فراخوانی (Callback).
        
        آرگومان‌ها:
            obj1: شیء اول
            obj2: شیء دوم
            callback (Callable): تابعی که باید در زمان تایید تصادم اجرا شود
        """
        if callback:
            callback(obj1, obj2)
