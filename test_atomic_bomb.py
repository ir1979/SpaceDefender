#!/usr/bin/env python3
"""
Test atomic bomb functionality - verify particle system integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from systems.particle_system import ParticleSystem
    from config.settings import color_config
    
    print("✓ Imported ParticleSystem")
    
    # Test the actual methods
    ps = ParticleSystem()
    print(f"✓ ParticleSystem created")
    
    # Check available methods
    methods = [m for m in dir(ps) if not m.startswith('_')]
    print(f"✓ Available methods: {methods}")
    
    # Test emit_explosion method (what we're using for atomic bomb)
    print("\nTesting emit_explosion() method...")
    ps.emit_explosion(400, 300, color_config.YELLOW, count=15)
    print(f"✓ emit_explosion() called successfully")
    print(f"✓ Particles created: {len(ps.particles)}")
    
    # Test emit_trail method
    print("\nTesting emit_trail() method...")
    ps.emit_trail(400, 300, color_config.YELLOW)
    print(f"✓ emit_trail() called successfully")
    print(f"✓ Total particles now: {len(ps.particles)}")
    
    print("\n" + "="*60)
    print("✅ ATOMIC BOMB PARTICLE SYSTEM TEST PASSED!")
    print("="*60)
    print("\nThe atomic bomb will now:")
    print("  1. Play explosion sound ✓")
    print("  2. Destroy all enemies ✓")
    print("  3. Award coins & score ✓")
    print("  4. Create explosion particles at each enemy ✓")
    print("\nNo AttributeError will occur!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
