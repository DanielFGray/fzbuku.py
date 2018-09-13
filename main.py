#!/usr/bin/env python3

"""pybm

Usage: [...OPTIONS]

Commands:
  add    add bookmark
  del    delete bookmark
  edit   edit bookmark

Options:
  -h --help      show this message
  -v --version   show version
  --json         dump output as json
"""


from __future__ import unicode_literals
import errno
import sys
import subprocess
import sqlite3
from docopt import docopt
# import json
# from prompt_toolkit import prompt

db = sqlite3.connect('/home/dan/.local/share/buku/bookmarks.db')
db.row_factory = sqlite3.Row
dbc = db.cursor()


# def import_firefox():
#     # pick profile
#     query = """
#         select moz_bookmarks.title, moz_places.url from moz_bookmarks
#         left join moz_places ON fk=moz_places.id;"""
#     result = dbc.execute(query).fetchall()

def row_to_dict(row):
    for r in row:
        yield dict(zip(r.keys(), r))


def get_bookmarks():
    query = "select * from bookmarks;"
    return row_to_dict(dbc.execute(query))


def cmd(name, args, input):
    proc = subprocess.Popen(
        [name, *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None
    )
    stdin = proc.stdin
    encoding = sys.getdefaultencoding()
    for line in input:
        try:
            stdin.write(line.encode(encoding) + b'\n')
            stdin.flush()
        except IOError as e:
            if e.errno != errno.EPIPE:
                raise
            break
    try:
        stdin.close()
    except IOError as e:
        if e.errno != errno.EPIPE:
            raise
    stdout = proc.stdout
    return [l.strip(b'\n').decode(encoding)
            for l in iter(stdout.readline, b'')]


def dmenu(args, input):
    return cmd('dmenu', args, input)


def fzf(args, input):
    output = cmd('fzf', args, input)
    query = None
    expect = None
    if '--print-query' in args:
        query = output.pop(0)
    if '--expect' in args:
        expect = output.pop(0)
    if '--multi' not in args and '-m' not in args:
        output = output[0]
    return {output, query, expect}


def dmenu_bookmarks():
    pretty = ("{URL} {metadata}".format(**l) for l in get_bookmarks())
    url = dmenu(['-l', '10', '-nb', '#131313', '-fn', 'Fira Code-7'], list(pretty).reverse())
    id, url, *title = url['output'].split(' ')
    open_url(url)


def fzf_bookmarks():
    pretty = ("{URL} {metadata}".format(**l) for l in get_bookmarks())
    choice = fzf(['--with-nth=3..'], pretty)
    id, url, *title = choice['output'].split(' ')
    open_url(url)


def open_url(url):
    if 'youtube.com' in url:
        subprocess.run(['mpv', url])
    elif 'youtu.be' in url:
        subprocess.run(['mpv', url])
    elif 'vimeo.com' in url:
        subprocess.run(['mpv', url])
    else:
        subprocess.run(['x-www-browser', url])


def main():
    dmenu_bookmarks()


if __name__ == '__main__':
    arguments = docopt(__doc__, version='0.1')
    main()
