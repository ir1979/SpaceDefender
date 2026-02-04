"""State Machine Module"""
from enum import Enum
from typing import Dict, Callable, Optional

class StateMachine:
    """Finite state machine for game states"""
    
    def __init__(self):
        self.current_state: Optional[Enum] = None
        self.state_handlers: Dict[Enum, Dict[str, Callable]] = {}
    
    def add_state(self, state: Enum, enter: Callable = None, 
                  update: Callable = None, exit: Callable = None):
        """Add a state with handlers"""
        self.state_handlers[state] = {
            'enter': enter,
            'update': update,
            'exit': exit
        }
    
    def change_state(self, new_state: Enum):
        """Change to a new state"""
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
        """Update current state"""
        if self.current_state in self.state_handlers:
            update_handler = self.state_handlers[self.current_state].get('update')
            if update_handler:
                update_handler()
