# Tests Organization

This directory contains all unit and integration tests for Space Defender, organized by functionality:

## Directory Structure

### `/network` - Network Protocol Tests
Tests for the networking layer and communication protocol.
- `test_network_framing.py` - Tests for message framing and packet structure
- `test_network_integration.py` - Tests for network communication between client and server

### `/server` - Server-side Tests  
Tests for server logic and game simulation.
- `test_server.py` - Server initialization and basic functionality tests
- `test_server_startup.py` - Server startup and initialization tests

### `/client` - Client-side Tests
Tests for client logic and state management.
- `test_client_apply_state.py` - Tests for applying server state on client
- `test_client_args.py` - Tests for command-line argument parsing

### `/gameplay` - Gameplay Feature Tests
Tests for game mechanics and features.
- `test_shop.py` - Shop system tests
- `test_profile_and_shop.py` - Profile and shop integration tests

### `/integration` - Integration Tests
End-to-end tests for online multiplayer gameplay.
- `test_play_online_crash.py` - Tests for crash scenarios during online play
- `test_play_online_loop.py` - Tests for online gameplay loop stability

## Running Tests

### Quick Start: Run All Tests

**Option 1: Using pytest directly**
```bash
pytest
```

**Option 2: Using the test runner script**
```bash
python run_tests.py
```

### Run Tests by Category

Using the test runner script:
```bash
python run_tests.py --network      # Network tests only
python run_tests.py --server       # Server tests only
python run_tests.py --client       # Client tests only
python run_tests.py --gameplay     # Gameplay tests only
python run_tests.py --integration  # Integration tests only
```

Using pytest directly:
```bash
pytest tests/network/
pytest tests/server/
pytest tests/client/
pytest tests/gameplay/
pytest tests/integration/
```

### Run Specific Test Files

```bash
pytest tests/network/test_network_framing.py
pytest tests/gameplay/test_shooting.py
```

### Test Runner Script Options

```bash
python run_tests.py --help              # Show help
python run_tests.py --verbose           # Verbose output
python run_tests.py --quiet             # Minimal output
python run_tests.py --failfast          # Stop on first failure
python run_tests.py --markers MARKER    # Run tests by pytest marker
```

### Environment Requirements

Make sure you have pytest installed:
```bash
pip install pytest
```
