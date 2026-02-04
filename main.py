"""
Space Defender - Main Entry Point
Created by Ali Mortazavi
"""

import pygame
from core.game import Game
from systems.save_system import SaveSystem, PlayerProfile

def select_profile():
    profiles = SaveSystem.get_profile_names()
    print("Available profiles:")
    for i, name in enumerate(profiles):
        print(f"{i+1}. {name}")
    print(f"{len(profiles)+1}. Create new profile")
    choice = input("Select profile: ").strip()

    # Empty choice -> prompt for a default name
    if not choice:
        new_name = input("Enter new profile name (leave blank for 'Player'): ").strip()
        if not new_name:
            new_name = "Player"
        profile = PlayerProfile(new_name)
        SaveSystem.save_profile(profile)
        return profile

    # Normalise the first token so inputs like '1.' or '1.' are handled
    token = choice.split()[0]
    if token.endswith('.'):
        token = token[:-1]

    # If user entered a number, handle selecting existing profile or the 'create new' option
    if token.isdigit():
        idx = int(token) - 1
        if 0 <= idx < len(profiles):
            return SaveSystem.load_profile(profiles[idx])
        elif idx == len(profiles):
            # User explicitly selected the 'Create new profile' option
            new_name = input("Enter new profile name: ").strip()
            if not new_name:
                new_name = "Player"
            profile = PlayerProfile(new_name)
            SaveSystem.save_profile(profile)
            return profile

    # If the user typed the literal 'Create new profile' (or similar), treat as create
    lower_choice = choice.lower()
    if "create" in lower_choice and "profile" in lower_choice:
        new_name = input("Enter new profile name: ").strip()
        if not new_name:
            new_name = "Player"
        profile = PlayerProfile(new_name)
        SaveSystem.save_profile(profile)
        return profile

    # Otherwise use the entered string as a new profile name
    profile = PlayerProfile(choice)
    SaveSystem.save_profile(profile)
    return profile

def main():
    profile = select_profile()
    print(f"Loaded profile: {profile.name}")
    game = Game(profile)
    game.run()

if __name__ == "__main__":
    main()
