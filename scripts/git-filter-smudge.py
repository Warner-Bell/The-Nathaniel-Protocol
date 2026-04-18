#!/usr/bin/env python3
"""Git smudge filter - passes content through unchanged FROM the repo."""
import sys
sys.stdout.write(sys.stdin.read())
