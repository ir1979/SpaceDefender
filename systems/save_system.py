"""
Save System Module
"""
import json
import os
import time
from typing import List, Optional, Dict, Any
from .logger import get_logger

logger = get_logger('space_defender.save_system')

class PlayerProfile:
    """Player profile with persistent data

    Note: older save files used `current_score` / `current_coins`.
    New unified fields are `score` and `coins`. This class remains
    backwards-compatible (loads old keys) while exposing `score`/
    `coins` properties for the rest of the codebase.
    """
    
    def __init__(self, name: str, password: str = ""):
        self.name = name
        self.password = password
        self.total_score = 0
        self.total_coins = 0
        self.highest_level = 1
        self.games_played = 0
        self.total_time_played = 0
        self.last_played = time.time()
        
        # Weapon inventory: dict mapping weapon names to counts
        # Example: {'atomic_bomb': 2, 'enemy_freeze': 3}
        self.weapon_inventory = {}
        
        # transient / session state
        self.current_score = 0
        self.current_coins = 0
        self.current_level = 1
        self.session_start_coins = 0 # Track coins at the start of a game session
    
    # expose unified property names for easier usage (backward-compatible)
    @property
    def score(self) -> int:
        return self.current_score

    @score.setter
    def score(self, value: int):
        self.current_score = int(value)

    @property
    def coins(self) -> int:
        return self.current_coins

    @coins.setter
    def coins(self, value: int):
        self.current_coins = int(value)

    def to_dict(self) -> dict:
        # write both legacy (`current_...`) and new (`score`/`coins`) keys
        return {
            'name': self.name,
            'password': self.password,
            'total_score': self.total_score,
            'total_coins': self.total_coins,
            'highest_level': self.highest_level,
            'games_played': self.games_played,
            'total_time_played': self.total_time_played,
            'last_played': self.last_played,
            'score': self.current_score,
            'coins': self.current_coins,
            'current_score': self.current_score,
            'current_coins': self.current_coins,
            'current_level': self.current_level,
            'weapon_inventory': self.weapon_inventory
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'PlayerProfile':
        profile = PlayerProfile(data['name'], data.get('password', ''))
        profile.total_score = data.get('total_score', 0)
        profile.total_coins = data.get('total_coins', 0)
        profile.highest_level = data.get('highest_level', 1)
        profile.games_played = data.get('games_played', 0)
        profile.total_time_played = data.get('total_time_played', 0)
        profile.last_played = data.get('last_played', time.time())
        # Load weapon inventory
        profile.weapon_inventory = data.get('weapon_inventory', {})
        # Load transient/session state (prefer new keys, fallback to legacy)
        # When loading a profile from scratch, the session coins should reflect the total
        # available coins. The 'coins' field in the save file represents a saved
        # mid-game state, which we can ignore when starting a fresh session from the menu.
        profile.current_score = 0 # Always start a new session with 0 score
        profile.current_coins = data.get('coins', data.get('current_coins', 0))
        profile.current_coins = profile.total_coins
        profile.current_level = data.get('current_level', 1)
        return profile
    
    def add_weapon(self, weapon_name: str):
        """Add a weapon to the inventory (for purchased weapons)"""
        if weapon_name not in self.weapon_inventory:
            self.weapon_inventory[weapon_name] = 0
        self.weapon_inventory[weapon_name] += 1
        logger.info(f"Profile '{self.name}': Added weapon '{weapon_name}'. Total: {self.weapon_inventory[weapon_name]}")
    
    def use_weapon(self, weapon_name: str) -> bool:
        """Use a weapon from inventory. Returns True if successful, False if not available."""
        if weapon_name in self.weapon_inventory and self.weapon_inventory[weapon_name] > 0:
            self.weapon_inventory[weapon_name] -= 1
            logger.info(f"Profile '{self.name}': Used weapon '{weapon_name}'. Remaining: {self.weapon_inventory[weapon_name]}")
            return True
        logger.warning(f"Profile '{self.name}': No '{weapon_name}' available to use!")
        return False
    
    def get_weapon_count(self, weapon_name: str) -> int:
        """Get the count of a specific weapon in inventory"""
        return self.weapon_inventory.get(weapon_name, 0)
    
    def start_new_game(self):
        self.current_score = 0
        self.current_coins = self.total_coins  # Start with the total coins from the profile
        self.current_level = 1
        self.session_start_coins = self.total_coins  # Remember what we started with
        self.games_played += 1
        logger.info(f"Profile '{self.name}': Starting new game. "
                    f"Session coins set to {self.current_coins}, session score to 0.")
    
    def end_game(self, score: int, coins: int, level: int, time_played: float):
        logger.info(f"Profile '{self.name}': Ending game. Adding score: {score}, coins: {coins}.")
        logger.info(f"  - Before: total_score={self.total_score}, total_coins={self.total_coins}")
        self.total_score += score
        self.total_coins += coins
        self.highest_level = max(self.highest_level, level)
        self.total_time_played += time_played
        self.last_played = time.time()
        logger.info(f"  - After: total_score={self.total_score}, total_coins={self.total_coins}")

    def sync_after_shop(self, session_coins: int):
        """
        Syncs the profile's state after a shopping session.
        The session_coins (from player.coins) becomes the new total.
        """
        logger.info(f"Profile '{self.name}': Syncing after shop. New total_coins: {session_coins}")
        self.current_coins = session_coins
        self.total_coins = session_coins
        self.last_played = time.time()

    def apply_purchase(self, cost: int):
        """
        Applies the cost of a purchase to the player's totals.
        This is a transactional method that should be followed by a save.
        """
        logger.debug(f"Profile '{self.name}': Applying purchase cost: {cost}. Current coins: {self.current_coins}")
        if self.current_coins >= cost:
            self.current_coins -= cost
            # Also deduct from total_coins to persist the change immediately
            self.total_coins -= cost
            return True
        return False


class SaveSystem:
    """Handle save data"""
    
    SAVE_FILE = "data/profiles.json"
    
    @staticmethod
    def _ensure_data_dir():
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
    
    @staticmethod
    def save_profile(profile: PlayerProfile):
        SaveSystem._ensure_data_dir()
        try:
            data = SaveSystem.load_all_profiles()
            data['profiles'][profile.name] = profile.to_dict()
            
            with open(SaveSystem.SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Profile '{profile.name}' saved successfully.")
        except Exception as e:
            print(f"Error saving profile: {e}")
    
    @staticmethod
    def load_all_profiles() -> dict:
        try:
            if os.path.exists(SaveSystem.SAVE_FILE):
                with open(SaveSystem.SAVE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'profiles': {}, 'high_scores': []}

    @staticmethod
    def get_profile_names() -> List[str]:
        """Return profile names, filtering out invalid placeholder entries."""
        data = SaveSystem.load_all_profiles()
        raw_names = list(data.get('profiles', {}).keys())
        filtered = [n for n in raw_names if 'create new profile' not in n.strip().lower()]
        return filtered
    
    @staticmethod
    def get_profiles() -> List[PlayerProfile]:
        """Return PlayerProfile objects, skipping invalid placeholder entries."""
        data = SaveSystem.load_all_profiles()
        profiles = []
        for name, profile_data in data.get('profiles', {}).items():
            if 'create new profile' in name.strip().lower():
                # Skip invalid placeholder-like entries that may have been saved by mistake
                continue
            profiles.append(PlayerProfile.from_dict(profile_data))
        return profiles
    
    @staticmethod
    def load_profile(name: str) -> Optional[PlayerProfile]:
        data = SaveSystem.load_all_profiles()
        profile_data = data.get('profiles', {}).get(name)
        if profile_data:
            return PlayerProfile.from_dict(profile_data)
        logger.warning(f"Attempted to load profile '{name}', but it was not found.")
        return None

    @staticmethod
    def verify_password(name: str, password: str) -> bool:
        """Verify if the password matches the profile's stored password."""
        data = SaveSystem.load_all_profiles()
        profile_data = data.get('profiles', {}).get(name)
        if profile_data:
            stored_password = profile_data.get('password', '')
            return password == stored_password
        return False

    @staticmethod
    def profile_exists(name: str) -> bool:
        """Check if a profile with the given name already exists."""
        data = SaveSystem.load_all_profiles()
        return name in data.get('profiles', {})

    @staticmethod
    def delete_profile(name: str) -> bool:
        """Remove a profile by name from the save file. Returns True on success."""
        SaveSystem._ensure_data_dir()
        try:
            data = SaveSystem.load_all_profiles()
            profiles = data.get('profiles', {})
            if name in profiles:
                profiles.pop(name, None)
                data['profiles'] = profiles
                with open(SaveSystem.SAVE_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
        return False
    
    @staticmethod
    def save_high_score(profile: PlayerProfile, score: int, level: int):
        SaveSystem._ensure_data_dir()
        try:
            data = SaveSystem.load_all_profiles()
            data['high_scores'].append({
                'name': profile.name,
                'score': score,
                'level': level,
                'timestamp': time.time()
            })
            data['high_scores'].sort(key=lambda x: x['score'], reverse=True)
            data['high_scores'] = data['high_scores'][:10]
            
            with open(SaveSystem.SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving high score: {e}")
    
    @staticmethod
    def get_high_scores() -> List[dict]:
        data = SaveSystem.load_all_profiles()
        return data.get('high_scores', [])
