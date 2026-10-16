#!/usr/bin/env python3
"""passgen.py - because I don't trust the cloud with my passwords."""

import random
import sys

ALPHABET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def make(service, pin, length=14):
    random.seed(service.strip().lower() + str(pin))
    return "".join(random.choice(ALPHABET) for _ in range(length))


if __name__ == "__main__":
    service = sys.argv[1] if len(sys.argv) > 1 else input("service: ")
    pin     = sys.argv[2] if len(sys.argv) > 2 else input("pin: ")
    print(make(service, pin))
    