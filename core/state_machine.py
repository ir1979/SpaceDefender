"""
ماژول ماشین وضعیت (State Machine) بازی
این ماژول کلاس‌های مدیریتی وضعیت‌های بازی مانند منو، در حال بازی و توقف را ارائه می‌دهد.
"""
from enum import Enum
from typing import Dict, Callable, Optional

class StateMachine:
    """
    کلاس اصلی مدیریت ماشین وضعیت متناهی (FSM) بازی.
    
    این کلاس مسئول اضافه کردن وضعیت‌های بازی و مدیریت انتقال بین حالت‌ها
    (فراخوانی توابع ورود، خروج و آپدیت هر حالت در زمان مناسب) می‌باشد.
    """
    
    def __init__(self):
        """مقداردهی اولیه متغیرهای ماشین وضعیت"""
        self.current_state: Optional[Enum] = None
        self.state_handlers: Dict[Enum, Dict[str, Callable]] = {}
    
    def add_state(self, state: Enum, enter: Callable = None, 
                  update: Callable = None, exit: Callable = None):
        """
        ثبت یک وضعیت جدید به همراه هندلرهای ورودی، خروجی و فریم آپدیت آن.
        
        آرگومان‌ها:
            state (Enum): وضعیت جدید از جنس امضاها
            enter (Callable): تابعی که هنگام ورود به این وضعیت اجرا می‌شود
            update (Callable): تابعی که در هر فریم آپدیت این وضعیت فراخوانی می‌شود
            exit (Callable): تابعی که هنگام خروج از این وضعیت اجرا می‌شود
        """
        self.state_handlers[state] = {
            'enter': enter,
            'update': update,
            'exit': exit
        }
    
    def change_state(self, new_state: Enum):
        """
        انتقال وضعیت فعلی بازی به وضعیت جدید.
        
        این متد ابتدا هندلر خروج (exit) وضعیت فعلی را اجرا کرده، سپس وضعیت
        جدید را ثبت کرده و هندلر ورود (enter) آن را فراخوانی می‌کند.
        
        آرگومان‌ها:
            new_state (Enum): وضعیت هدف برای انتقال
        """
        if self.current_state in self.state_handlers:
            exit_handler = self.state_handlers[self.current_state].get('exit')
            if exit_handler:
                exit_handler()
        
        self.current_state = new_state
        if new_state in self.state_handlers:
            enter_handler = self.state_handlers[new_state].get('enter')
            if enter_handler:
                enter_handler()
    
    def update(self):
        """
        به‌روزرسانی منطق وضعیت فعلی در هر فریم از بازی.
        
        این متد تابع update متناظر با حالت جاری بازی را فراخوانی می‌کند.
        """
        if self.current_state in self.state_handlers:
            update_handler = self.state_handlers[self.current_state].get('update')
            if update_handler:
                update_handler()
