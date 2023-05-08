#!/usr/bin/env python3

import atheris
import sys
import os

with atheris.instrument_imports():
    # import required libraries here
    ...

def TestOneInput(input):
    fdp = atheris.FuzzedDataProvider(input)
    # fuzzed code goes here

def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

if __name__ == "__main__":
    main()

