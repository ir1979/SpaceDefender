"""
بازی محافظ فضا (Space Defender) - نقطه ورود اصلی برنامه
توسعه‌دهنده: علی مرتضوی

این ماژول وظیفه دریافت آرگومان‌های ورودی خط فرمان، راه‌اندازی ماژول‌های لاگ و فیزیک
و استارت زدن حلقه بازی در حالت‌های بازی محلی، سرور یا کلاینت شبکه‌ای را بر عهده دارد.
"""

import os
import sys
import argparse
import pygame
from core.game import Game
from systems.save_system import SaveSystem, PlayerProfile
from systems.logger import setup_logging

def main():
    """
    تابع اصلی راه‌اندازی و مدیریت اولیه منطق شروع بازی.
    
    این تابع آرگومان‌های خط فرمان را پردازش کرده و بر اساس تنظیمات ورودی (به عنوان مثال
    پورت سرور، آی‌پی اتصال یا حالت تمام‌صفحه) شیء اصلی موتور بازی را راه‌اندازی می‌کند.
    """
    # پردازش آرگومان‌های ورودی خط فرمان
    parser = argparse.ArgumentParser(description='Space Defender - Game Entry Point')
    parser.add_argument('mode', nargs='?', default=None, 
                        choices=['game', 'server', 'client'],
                        help='Game mode: game (local), server (listen for clients), client (connect to server)')
    parser.add_argument('--host', default='127.0.0.1', help='Server host (for client mode)')
    parser.add_argument('--port', type=int, default=35555, help='Server port')
    parser.add_argument('--windowed', action='store_true',
                        help='Run in a window (non-fullscreen). Useful for side-by-side online play.')
        
    args = parser.parse_args()
    
    # تشخیص خودکار حالت کلاینت در صورت مشخص شدن هاست یا پورت
    if args.mode is None:
        host_specified = '--host' in sys.argv
        port_specified = '--port' in sys.argv
        
        if host_specified or port_specified:
            args.mode = 'client'
        else:
            args.mode = 'game'
            
    # راه‌اندازی لاگ‌سیستم بازی
    logger = setup_logging()
    logger.info(f"Starting Space Defender in {args.mode} mode...")
    
    if args.mode == 'server':
        # اجرای بازی در حالت سرور اختصاصی شبکه
        from server import main as server_main
        server_main([None, str(args.port)])
    
    elif args.mode == 'client':
        # اجرای بازی در حالت کلاینت شبکه (اتصال به سرور)
        game = Game(None, is_server=False, fullscreen=not args.windowed)
        # ذخیره مشخصات سرور برای استفاده در منوی بازی
        game.server_host = args.host
        game.server_port = args.port
        game.run()

    else:
        # اجرای بازی به صورت تک‌نفره و محلی
        game = Game(None, is_server=False, fullscreen=not args.windowed)
        game.run()

if __name__ == "__main__":
    main()
