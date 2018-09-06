#!/usr/bin/env python3

import io
import svgwrite

MARGIN = 32
SYMBOL_SIZE = 100
SYMBOL_SIZE_2 = SYMBOL_SIZE // 2 if SYMBOL_SIZE % 2 == 0 else SYMBOL_SIZE / 2
GRID_STROKE = 4
GRID_STROKE_2 = GRID_STROKE // 2 if GRID_STROKE % 2 == 0 else GRID_STROKE / 2
SYMBOL_STROKE = 6
TOTAL_SIZE = MARGIN + SYMBOL_SIZE + MARGIN + GRID_STROKE + MARGIN + SYMBOL_SIZE + MARGIN + GRID_STROKE + MARGIN + SYMBOL_SIZE + MARGIN

COLOR_X = '#C60000'
COLOR_O = '#12C600'
COLOR_GRID = '#000'
COLOR_LINK = '#00E'

PATH_O = [
        'm', SYMBOL_SIZE_2, 0,
        # a rX,rY rotation, arc, sweep, eX,eY
        'a', SYMBOL_SIZE_2, SYMBOL_SIZE_2, 0, 0, 0, 0, SYMBOL_SIZE,
        'a', SYMBOL_SIZE_2, SYMBOL_SIZE_2, 0, 0, 0, 0, - SYMBOL_SIZE,
    ]
PATH_X = [
        'm', 0, 0,
        'l', SYMBOL_SIZE, SYMBOL_SIZE,
        'm', 0, -SYMBOL_SIZE,
        'l', -SYMBOL_SIZE, SYMBOL_SIZE,
    ]
PATH_GRID = [
        'M', MARGIN + SYMBOL_SIZE + MARGIN + GRID_STROKE_2, 0,
        'v', TOTAL_SIZE,
        'm', MARGIN + SYMBOL_SIZE + MARGIN + GRID_STROKE, 0,
        'v', -TOTAL_SIZE,
        'M', 0, MARGIN + SYMBOL_SIZE + MARGIN + GRID_STROKE_2,
        'h', TOTAL_SIZE,
        'm', 0, MARGIN + SYMBOL_SIZE + MARGIN + GRID_STROKE,
        'h', -TOTAL_SIZE,
    ]


def make_path(base, name, color, stroke):
    p = svgwrite.path.Path(base)
    p.stroke(color=color, width=stroke)
    p.fill(color='none')
    p.attribs['stroke-linecap'] = 'round'
    p.attribs['id'] = name
    return p


def render_svg(state, links=(['#'] * 9)):
    dwg = svgwrite.Drawing(None, size=(TOTAL_SIZE, TOTAL_SIZE))
    # Prepare symbols
    if any('X' == cell for cell in state):
        dwg.defs.add(make_path(PATH_X, 'X', COLOR_X, SYMBOL_STROKE))
    if any('O' == cell for cell in state):
        dwg.defs.add(make_path(PATH_O, 'O', COLOR_O, SYMBOL_STROKE))
    dwg.defs.add(dwg.rect(id='P', size=(SYMBOL_SIZE, SYMBOL_SIZE), fill=COLOR_LINK))
    # Background
    r = dwg.add(dwg.rect(size=(TOTAL_SIZE, TOTAL_SIZE), fill='white'))
    # Put a grid on it
    dwg.add(make_path(PATH_GRID, None, COLOR_GRID, GRID_STROKE))
    # Put symbols on it
    for y in range(3):
        for x in range(3):
            cell = state[y * 3 + x]
            pos = ((MARGIN + SYMBOL_SIZE + MARGIN + GRID_STROKE) * x + MARGIN,
                   (MARGIN + SYMBOL_SIZE + MARGIN + GRID_STROKE) * y + MARGIN)
            if cell is None:
                a = dwg.a(links[y * 3 + x])
                a.add(dwg.use('#P', insert=pos))
                dwg.add(a)
            else:
                dwg.add(dwg.use('#' + cell, insert=pos))
    # Done!  Return result.
    f = io.StringIO()
    dwg.write(f, pretty=True)
    return f.getvalue()
