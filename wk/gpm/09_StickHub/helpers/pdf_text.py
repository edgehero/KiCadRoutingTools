#!/usr/bin/env python3
"""Crude PDF text dump: inflate every FlateDecode stream and print the text
operands of Tj/TJ operators, one page-ish block per stream.

Why this exists (TOOL_GAPS.md): the skill's datasheet step reads a PDF with
the Read tool's `pages` or poppler's pdftotext, and this machine has neither
poppler nor pypdf/fitz, so the Read tool refuses every PDF page. This is a
stand-in good enough to grep a datasheet's electrical table and section
headings; it does not decode CID fonts or render figures.

    python3 -I helpers/pdf_text.py datasheet.pdf [--grep REGEX]
"""
import re
import sys
import zlib


def streams(data):
    for m in re.finditer(rb'stream\r?\n', data):
        start = m.end()
        end = data.find(b'endstream', start)
        if end < 0:
            continue
        raw = data[start:end]
        try:
            yield zlib.decompress(raw)
        except Exception:
            try:
                yield zlib.decompressobj().decompress(raw)
            except Exception:
                continue


def text_of(s):
    out = []
    for m in re.finditer(rb'\[(.*?)\]\s*TJ|\((.*?)(?<!\\)\)\s*Tj|(T\*|Td|TD|ET)', s, re.S):
        if m.group(3):
            out.append('\n' if m.group(3) in (b'T*', b'ET', b'Td', b'TD') else '')
            continue
        chunk = m.group(1) if m.group(1) is not None else b'(' + m.group(2) + b')'
        parts = re.findall(rb'\((.*?)(?<!\\)\)|(-?\d+\.?\d*)', chunk, re.S)
        for txt, num in parts:
            if txt:
                out.append(txt.replace(b'\\(', b'(').replace(b'\\)', b')')
                           .decode('latin-1', 'replace'))
            elif num and float(num) < -200:
                out.append(' ')
    return ''.join(out)


def main():
    path = sys.argv[1]
    pat = None
    if '--grep' in sys.argv:
        pat = re.compile(sys.argv[sys.argv.index('--grep') + 1], re.I)
    data = open(path, 'rb').read()
    for i, s in enumerate(streams(data)):
        t = text_of(s)
        if not t.strip():
            continue
        for line in t.split('\n'):
            line = line.strip()
            if line and (pat is None or pat.search(line)):
                print(f'[{i}] {line}')


if __name__ == '__main__':
    main()
