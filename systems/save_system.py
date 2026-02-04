"""
Save System Module
"""
import json
import os
import time
from typing import List, Optional, Dict, Any

class PlayerProfile:
    """Player profile with persistent data"""
    
    def __init__(self, name: str):
        self.name = name
        self.total_score = 0
        self.total_coins = 0
        self.highest_level = 1
        self.games_played = 0
        self.total_time_played = 0
        self.last_played = time.time()
        
        self.current_score = 0
        self.current_coins = 0
        self.current_level = 1
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'total_score': self.total_score,
            'total_coins': self.total_coins,
            'highest_level': self.highest_level,
            'games_played': self.games_played,
            'total_time_played': self.total_time_played,
            'last_played': self.last_played
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'PlayerProfile':
        profile = PlayerProfile(data['name'])
        profile.total_score = data.get('total_score', 0)
        profile.total_coins = data.get('total_coins', 0)
        profile.highest_level = data.get('highest_level', 1)
        profile.games_played = data.get('games_played', 0)
        profile.total_time_played = data.get('total_time_played', 0)
        profile.last_played = data.get('last_played', time.time())
        return profile
    
    def start_new_game(self):
        self.current_score = 0
        self.current_coins = 0
        self.current_level = 1
        self.games_played += 1
    
    def end_game(self, score: int, coins: int, level: int, time_played: float):
        self.total_score += score
        self.total_coins += coins
        self.highest_level = max(self.highest_level, level)
        self.total_time_played += time_played
        self.last_played = time.time()

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
        return None
    
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
