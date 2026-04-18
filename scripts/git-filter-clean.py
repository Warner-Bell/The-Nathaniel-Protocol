#!/usr/bin/env python3
"""Git clean filter - sanitizes content going TO the repo."""
import re
import sys

REPLACEMENTS = [
    (r"(?i)Example-Customer-A", "[CUSTOMER-A]"),
    (r"(?i)Example-Customer-B", "[CUSTOMER-B]"),
    (r"(?i)Example-Customer-C", "[CUSTOMER-C]"),
    (r"(?i)Example-Prospect-A", "[PROSPECT-A]"),
    (r"(?i)Example-Prospect-B", "[PROSPECT-B]"),
    (r"123456789012", "[ACCOUNT-A]"),
    (r"234567890123", "[ACCOUNT-B]"),
]

content = sys.stdin.read()
for pattern, replacement in REPLACEMENTS:
    content = re.sub(pattern, replacement, content)
sys.stdout.write(content)
