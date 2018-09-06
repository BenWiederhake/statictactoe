#!/usr/bin/env python3

import io
import os
import shutil
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


def place(state, x, y, symbol):
    """
    In the current `state`, player `symbol` makes a mark at place `x`, `y`.
    Returns a new, copied `state`.
    """
    state = list(state)
    assert state[y * 3 + x] is None
    state[y * 3 + x] = symbol
    return tuple(state)


def get_winner(state):
    def w(*positions):
        assert len(positions) == 3
        seen = set(state[pos] for pos in positions)
        if len(seen) == 1:
            return list(seen)[0]
        else:
            return None

    winner = w(0, 1, 2) or w(3, 4, 5) or w(6, 7, 8) or w(0, 3, 6) or \
        w(1, 4, 7) or w(2, 5, 8) or w(0, 4, 8) or w(2, 4, 6)
    if winner is not None:
        return winner
    if all(state):
        return '!'
    return None


# Note that the player responding is implicit.
# keys are tuples of states (9-tuples of None, 'X', or 'O') and turn symbol ('X' or 'O')
# value are tuples of x, y, and best outcome
# (-1 for 'lose', 0 for 'draw' or +1 for 'guaranteed win'; assuming the best possible opponent)
# Don't use directly; use `solve_for` instead.
RESPONSES = dict()


# Very stupid, brute-force enumeration of all states.
def solve_for(state, turn_symbol):
    response = RESPONSES.get((state, turn_symbol))
    if response is not None:
        #print('CACHED', state, response)
        return response
    #print('BEGIN', state)
    assert get_winner(state) == None
    other_symbol = {'X': 'O', 'O': 'X'}[turn_symbol]
    available_responses = []
    for y in range(3):
        for x in range(3):
            if state[y * 3 + x] is not None:
                continue
            substate = place(state, x, y, turn_symbol)
            winner = get_winner(substate)
            if winner is not None:
                rating = {turn_symbol: +1, '!': 0, other_symbol: -1}[winner]
            else:
                _, _, other_rating = solve_for(substate, other_symbol)
                rating = -other_rating
            available_responses.append((x, y, rating))
    #print('AVAILABLE', available_responses)
    response = max(available_responses, key=lambda x: x[2])
    RESPONSES[(state, turn_symbol)] = response
    #print('END', state, response)
    return response


EMPTY_BOARD = (None,) * 9


def html_name(state):
    def cell_name(cell):
        return {None: 'n', 'X': 'x', 'O': 'o'}[cell]
    return ''.join(map(cell_name, state)) + '.html'


GENERATED_FOR_STATETURNS = set()


# Recursively generate the HTML page for this state, and all that are reachable
# via SVG links but don't appear in `GENERATED_FOR_STATETURNS` yet.
def render_htmlpage(state, ai_first_name):
    name = html_name(state)
    if name in GENERATED_FOR_STATETURNS:
        return  # Nothing to do!
    GENERATED_FOR_STATETURNS.add(name)

    # Prepare
    kind = {None: 'play', 'X': 'won', 'O': 'lost', '!': 'draw'}[get_winner(state)]
    template_name = 'templates' + os.path.sep + kind + '.html'
    with open(template_name, 'r') as fp:
        template = fp.read()
    links = ['#'] * 9
    for y in range(3):
        for x in range(3):
            if state[y * 3 + x] is not None or kind != 'play':
                continue
            substate = place(state, x, y, 'X')
            if get_winner(substate) is not None:
                next_state = substate
            else:
                ai_x, ai_y, _ = solve_for(substate, 'O')
                next_state = place(substate, ai_x, ai_y, 'O')
            render_htmlpage(next_state, ai_first_name)
            next_name = html_name(next_state)
            links[y * 3 + x] = next_name
    html_page = template.format(ai_first=ai_first_name, game_svg=render_svg(state, links))

    # Actually write
    os.makedirs('out', exist_ok=True)
    filename = 'out' + os.path.sep + name
    with open(filename, 'w') as fp:
        fp.write(html_page)


def render_all_htmlpages():
    ai_x, ai_y, _ = solve_for(EMPTY_BOARD, 'O')
    ai_first_board = place(EMPTY_BOARD, ai_x, ai_y, 'O')
    ai_first_name = html_name(ai_first_board)
    render_htmlpage(ai_first_board, ai_first_name)
    render_htmlpage(EMPTY_BOARD, ai_first_name)
    render_htmlpage(('X') * 9, ai_first_name)  # ;-)
    render_htmlpage(('O') * 9, ai_first_name)  # ;-)
    shutil.copy('templates' + os.path.sep + 'index.html', 'out' + os.path.sep + 'index.html')


if __name__ == '__main__':
    render_all_htmlpages()
