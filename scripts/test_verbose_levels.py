#!/usr/bin/env python
"""Test script to verify verbose level functionality."""
import subprocess
import time
import os
import signal
import sys

def test_verbose_level(level):
    """Test server with a specific verbosity level."""
    print(f"\n{'='*60}")
    print(f"Testing Verbosity Level: {level}")
    print(f"{'='*60}\n")
    
    # Start the server with the specified verbosity level
    process = subprocess.Popen(
        [sys.executable, 'server.py', '35555', '-v', str(level)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Let it run for 1 second
    time.sleep(1)
    
    # Terminate the process
    process.terminate()
    
    try:
        output, _ = process.communicate(timeout=2)
        print(output)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
        print(output)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    for level in [0, 1, 2, 3]:
        test_verbose_level(level)
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("Test Complete!")
    print(f"{'='*60}\n")
