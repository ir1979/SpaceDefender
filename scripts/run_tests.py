#!/usr/bin/env python
"""
Test runner script for Space Defender
Run all tests with various options from command line
"""

import subprocess
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='Run Space Defender tests')
    parser.add_argument(
        '--all', action='store_true',
        help='Run all tests (default)'
    )
    parser.add_argument(
        '--network', action='store_true',
        help='Run network tests only'
    )
    parser.add_argument(
        '--server', action='store_true',
        help='Run server tests only'
    )
    parser.add_argument(
        '--client', action='store_true',
        help='Run client tests only'
    )
    parser.add_argument(
        '--gameplay', action='store_true',
        help='Run gameplay tests only'
    )
    parser.add_argument(
        '--integration', action='store_true',
        help='Run integration tests only'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Quiet output'
    )
    parser.add_argument(
        '--failfast', '-x', action='store_true',
        help='Stop on first failure'
    )
    parser.add_argument(
        '--markers', '-m', type=str,
        help='Run tests with specific pytest markers'
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = ['pytest']

    # Determine which tests to run
    if args.network:
        cmd.append('tests/network/')
    elif args.server:
        cmd.append('tests/server/')
    elif args.client:
        cmd.append('tests/client/')
    elif args.gameplay:
        cmd.append('tests/gameplay/')
    elif args.integration:
        cmd.append('tests/integration/')
    elif args.markers:
        cmd.extend(['-m', args.markers])
    else:
        cmd.append('tests/')

    # Add verbosity
    if args.verbose:
        cmd.append('-vv')
    elif args.quiet:
        cmd.append('-q')
    else:
        cmd.append('-v')

    # Add failfast
    if args.failfast:
        cmd.append('-x')

    # Run pytest
    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
