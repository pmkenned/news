#!/usr/bin/env python3

import os
import sys

if __name__ == "__main__":

    os.chdir('npr')

    lines = list()
    try:
        with open('db.txt', 'r') as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        pass

    db = dict()

    for line in lines:
        words = line.split()
        db[words[0]] = words[1]

    html_files = [f for f in os.listdir() if f.endswith('.html')]

    for html_file in html_files:
        if html_file in db:
            pass
        else:
            sys.stdout.write('file: %s\n' % html_file)
            sys.stdout.write('action: ')
            sys.stdout.flush()
            x = sys.stdin.readline()
            sys.stdout.write('doing: %s\n' % x)
