#!/usr/bin/env python3
"""
LC 200 — Number of Islands
Rich Grid BFS Visualization with Pillow

Renders: Grid with land/water cells + BFS island exploration animation + code panel + queue + stats
Outputs: MP4 video
"""
import os
import re
import sys
import subprocess
import tempfile
from collections import deque
from math import sin, cos, pi, sqrt
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════
#  DESIGN SYSTEM
# ═══════════════════════════════════════════════════

BG         = (15, 17, 23)
BG_PANEL   = (22, 24, 33)
BG_CODE    = (18, 20, 28)
GRID_LINE  = (35, 38, 50)

WHITE      = (230, 230, 240)
GRAY       = (100, 105, 120)
DIM        = (60, 62, 75)

CYAN       = (80, 220, 240)
GREEN      = (80, 220, 120)
YELLOW     = (255, 220, 80)
ORANGE     = (255, 160, 60)
RED        = (255, 85, 85)
PINK       = (255, 100, 200)
BLUE       = (80, 140, 255)
PURPLE     = (160, 100, 255)

# Cell states (integers)
WATER    = 0
LAND     = 1
VISITING = 2
# Island N visited: state = 10 + N

CELL_COLORS = {
    WATER:    (18, 28, 52),
    LAND:     (55, 150, 65),
    VISITING: (255, 215, 50),
    # Island palettes at 10+N
    10: (70, 150, 255),   # blue
    11: (230, 100, 50),   # orange
    12: (160, 70, 230),   # purple
    13: (50, 210, 180),   # teal
}

CELL_BORDER = {
    WATER:    (28, 42, 75),
    LAND:     (75, 180, 85),
    VISITING: (255, 240, 100),
    10: (100, 175, 255),
    11: (255, 130, 80),
    12: (190, 100, 255),
    13: (80, 240, 210),
}

ISLAND_PALETTE = [
    (70, 150, 255),   # island 0 blue
    (230, 100, 50),   # island 1 orange
    (160, 70, 230),   # island 2 purple
    (50, 210, 180),   # island 3 teal
]
ISLAND_BORDER_PALETTE = [
    (100, 175, 255),
    (255, 130, 80),
    (190, 100, 255),
    (80, 240, 210),
]


def cell_color(state):
    if state in CELL_COLORS:
        return CELL_COLORS[state]
    # island N = 10 + N
    if state >= 10:
        idx = (state - 10) % len(ISLAND_PALETTE)
        return ISLAND_PALETTE[idx]
    return CELL_COLORS[WATER]


def cell_border(state):
    if state in CELL_BORDER:
        return CELL_BORDER[state]
    if state >= 10:
        idx = (state - 10) % len(ISLAND_BORDER_PALETTE)
        return ISLAND_BORDER_PALETTE[idx]
    return CELL_BORDER[WATER]


# ═══════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════

def load_font(size):
    paths = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFMono-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=0)
            except:
                pass
    return ImageFont.load_default()

def load_font_bold(size):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size, index=1)
    except:
        return load_font(size)


# ═══════════════════════════════════════════════════
#  ANIMATION UTILITIES
# ═══════════════════════════════════════════════════

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def bell(t):
    """Peaks at t=0.5, zero at 0 and 1."""
    return sin(max(0.0, min(1.0, t)) * pi)


def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)


# ═══════════════════════════════════════════════════
#  CELL DRAWING
# ═══════════════════════════════════════════════════

def draw_cell(draw, x, y, size, state, font, font_sm,
              is_active=False, anim_t=0.0, prev_state=None):
    """Draw a grid cell with optional animated transition."""
    if anim_t > 0 and prev_state is not None and prev_state != state:
        fill   = lerp_color(cell_color(prev_state), cell_color(state), anim_t)
        border = lerp_color(cell_border(prev_state), cell_border(state), anim_t)
    else:
        fill   = cell_color(state)
        border = cell_border(state)

    # Neon glow
    glow_intensity = 0.0
    is_glowing = (state == VISITING) or (is_active)
    if is_glowing:
        glow_intensity = 1.0
    elif anim_t > 0 and prev_state is not None and prev_state != state:
        glow_intensity = bell(anim_t)

    if glow_intensity > 0.01:
        n_layers = 7
        for g in range(n_layers, 0, -1):
            strength = glow_intensity * (g / n_layers)
            gc = lerp_color(BG, (255, 240, 100), strength)
            pad = g * 3
            draw.rounded_rectangle(
                [x - pad, y - pad, x + size + pad, y + size + pad],
                radius=5 + pad, outline=gc, width=2
            )

    draw.rounded_rectangle([x, y, x + size, y + size],
                           radius=5, fill=fill, outline=border, width=2)

    cx, cy = x + size // 2, y + size // 2

    # Icon: mountain triangle on LAND, dot on VISITING, circle on visited island
    display_state = state
    if anim_t > 0 and prev_state is not None and anim_t < 0.5:
        display_state = prev_state

    if display_state == LAND:
        # Small mountain triangle
        mh = max(6, size // 5)
        mw = max(8, size // 4)
        pts = [(cx, cy - mh), (cx - mw, cy + mh // 2), (cx + mw, cy + mh // 2)]
        draw.polygon(pts, fill=(75, 180, 85), outline=(100, 210, 110))
    elif display_state == VISITING:
        # Bright dot
        r = max(3, size // 8)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 240, 100))
    elif display_state >= 10:
        # Small circle for visited island
        r = max(4, size // 7)
        idx = (display_state - 10) % len(ISLAND_PALETTE)
        c_inner = tuple(min(255, v + 60) for v in ISLAND_PALETTE[idx])
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c_inner)


def apply_scanlines(img):
    """Subtle CRT scanline overlay."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, img.size[1], 3):
        d.line([(0, y), (img.size[0], y)], fill=(0, 0, 0, 28))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


# ═══════════════════════════════════════════════════
#  SYNTAX HIGHLIGHTING
# ═══════════════════════════════════════════════════

SYN_KEYWORD  = (190, 120, 255)
SYN_BUILTIN  = (80,  190, 255)
SYN_NUMBER   = (255, 200, 70)
SYN_COMMENT  = (90,  150, 90)
SYN_STRING   = (255, 160, 90)
SYN_OPERATOR = (80,  230, 220)
SYN_DEFAULT  = (170, 215, 170)
SYN_BRIGHT   = (235, 245, 235)

PY_KEYWORDS = {'def','for','in','if','elif','else','while','return',
               'and','or','not','True','False','None','import','from'}
PY_BUILTINS = {'range','len','append','popleft','deque','int','str','list'}

_TOKEN_RE = re.compile(
    r'(#[^\n]*)'
    r'|("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
    r'|(\b\d+\b)'
    r'|(\b[a-zA-Z_]\w*\b)'
    r'|([=<>!+\-*/:%\[\]{}(),.])'
    r'|(\s+)'
)

def tokenize_line(text, is_current=False):
    if text.lstrip().startswith('#'):
        return [(text, SYN_COMMENT)]
    tokens = []
    for m in _TOKEN_RE.finditer(text):
        t = m.group(0)
        if   m.group(1): tokens.append((t, SYN_COMMENT))
        elif m.group(2): tokens.append((t, SYN_STRING))
        elif m.group(3): tokens.append((t, SYN_NUMBER))
        elif m.group(4):
            if   t in PY_KEYWORDS: tokens.append((t, SYN_KEYWORD))
            elif t in PY_BUILTINS: tokens.append((t, SYN_BUILTIN))
            else:                  tokens.append((t, SYN_BRIGHT if is_current else SYN_DEFAULT))
        elif m.group(5): tokens.append((t, SYN_OPERATOR))
        else:            tokens.append((t, SYN_DEFAULT))
    return tokens or [(text, SYN_DEFAULT)]


# ═══════════════════════════════════════════════════
#  CODE PANEL
# ═══════════════════════════════════════════════════

def draw_code_panel(draw, x, y, w, h, source_lines, current_line, font_code, font_sm,
                    prev_line=None, tween_t=0.0):
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_CODE, GRID_LINE, 1)
    draw.text((x + 10, y + 8), "SOURCE", fill=CYAN, font=font_sm)

    code_y = y + 32
    line_h = 20

    curr_bar_y = code_y + (current_line - 1) * line_h
    if prev_line and prev_line != current_line and tween_t > 0:
        prev_bar_y = code_y + (prev_line - 1) * line_h
        t_eased    = ease_in_out(tween_t)
        bar_y      = int(prev_bar_y + (curr_bar_y - prev_bar_y) * t_eased)
    else:
        bar_y = curr_bar_y

    draw.rectangle([x + 2, bar_y - 1, x + w - 2, bar_y + line_h], fill=(35, 55, 65))
    draw.rectangle([x + 2, bar_y - 1, x + 5,     bar_y + line_h], fill=GREEN)

    if prev_line and prev_line != current_line and 0 < tween_t < 1:
        trail_alpha = 1.0 - ease_in_out(tween_t)
        trail_col   = lerp_color(BG_CODE, (35, 55, 65), trail_alpha * 0.6)
        prev_bar_y  = code_y + (prev_line - 1) * line_h
        draw.rectangle([x + 2, prev_bar_y - 1, x + w - 2, prev_bar_y + line_h],
                       fill=trail_col)

    for i, raw_text in enumerate(source_lines):
        ly = code_y + i * line_h
        if ly + line_h > y + h - 4:
            break

        is_at_bar = (bar_y - 2 <= ly <= bar_y + 2)
        is_dest   = (i == current_line - 1)
        is_source = (prev_line and i == prev_line - 1)

        if is_at_bar:
            draw.text((x + 8, ly), "►", fill=GREEN, font=font_code)
        elif is_dest and tween_t > 0:
            fade = lerp_color(BG_CODE, GREEN, ease_in_out(tween_t))
            draw.text((x + 8, ly), "►", fill=fade, font=font_code)
        elif is_source and tween_t > 0:
            fade = lerp_color(GREEN, BG_CODE, ease_in_out(tween_t))
            draw.text((x + 8, ly), "►", fill=fade, font=font_code)

        if is_dest:
            ln_col = lerp_color(DIM, GREEN, ease_in_out(tween_t)) if tween_t > 0 else GREEN
        elif is_source and tween_t > 0:
            ln_col = lerp_color(GREEN, DIM, ease_in_out(tween_t))
        else:
            ln_col = DIM
        draw.text((x + 26, ly), f"{i+1:3}", fill=ln_col, font=font_code)

        is_current_for_color = is_dest
        cx_text = x + 68
        tokens = tokenize_line(raw_text, is_current_for_color)
        for tok, color in tokens:
            draw.text((cx_text, ly), tok, fill=color, font=font_code)
            bb = draw.textbbox((cx_text, ly), tok, font=font_code)
            cx_text = bb[2]
            if cx_text > x + w - 8:
                break


# ═══════════════════════════════════════════════════
#  QUEUE PANEL
# ═══════════════════════════════════════════════════

def draw_queue_panel(draw, x, y, w, h, queue_contents, font, font_sm, label="QUEUE  (BFS FRONTIER)"):
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 10, y + 6), label, fill=CYAN, font=font_sm)

    box_w   = 82
    box_h   = 46
    arrow_w = 18
    gap     = arrow_w + 4
    qx      = x + 14
    qy      = y + 30

    items_per_row = max(1, (w - 20) // (box_w + gap))
    visible = queue_contents[: items_per_row * 2]

    for i, (r, c) in enumerate(visible):
        row_idx = i // items_per_row
        col_idx = i % items_per_row
        bx = qx + col_idx * (box_w + gap)
        by = qy + row_idx * (box_h + 10)
        if by + box_h > y + h - 6:
            break

        is_front = (i == 0)
        fill_col   = (30, 100, 200) if is_front else (20, 65, 130)
        border_col = (80, 180, 255) if is_front else BLUE

        if is_front:
            for g in range(3, 0, -1):
                gc = lerp_color(BG, (80, 180, 255), g / 5)
                draw.rounded_rectangle(
                    [bx - g, by - g, bx + box_w + g, by + box_h + g],
                    radius=6 + g, outline=gc, width=1
                )

        draw.rounded_rectangle([bx, by, bx + box_w, by + box_h],
                               radius=6, fill=fill_col, outline=border_col, width=2)

        if is_front:
            draw.text((bx + 4, by + 2), "FRONT", fill=(80, 200, 255), font=font_sm)

        text = f"({r}, {c})"
        bb   = draw.textbbox((0, 0), text, font=font)
        tw   = bb[2] - bb[0]
        th   = bb[3] - bb[1]
        ty   = by + (box_h - th) // 2 + (6 if is_front else 0)
        draw.text((bx + box_w // 2 - tw // 2, ty), text, fill=WHITE, font=font)

        if i < len(visible) - 1 and (i + 1) % items_per_row != 0:
            ax = bx + box_w + 4
            ay = by + box_h // 2
            draw.text((ax, ay - 8), "→", fill=BLUE, font=font)

    if not queue_contents:
        draw.text((qx, qy + 10), "(empty)", fill=DIM, font=font)


# ═══════════════════════════════════════════════════
#  STATS PANEL
# ═══════════════════════════════════════════════════

def draw_stats_panel(draw, x, y, w, h, stats, font, font_sm):
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 10, y + 6), "STATUS", fill=CYAN, font=font_sm)

    sy = y + 30
    for key, val, color in stats:
        draw.text((x + 12, sy), f"{key}:", fill=GRAY, font=font_sm)
        draw.text((x + 12 + len(key) * 9 + 10, sy), str(val), fill=color, font=font)
        sy += 26


# ═══════════════════════════════════════════════════
#  QUESTION PANEL
# ═══════════════════════════════════════════════════

QUESTION_TEXT = (
    "Given an m×n binary grid of '1's (land) and '0's (water), count the number of islands. "
    "An island is formed by connecting adjacent land cells horizontally or vertically. "
    "Use BFS to explore each island fully before moving on — mark visited cells so you "
    "never count the same island twice."
)

def draw_question_panel(draw, x, y, w, h, font, font_sm):
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 12, y + 8), "PROBLEM", fill=CYAN, font=font_sm)

    max_px  = w - 24
    words   = QUESTION_TEXT.split()
    lines   = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bb   = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_px:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    ty     = y + 30
    line_h = 22
    for line in lines:
        if ty + line_h > y + h - 4:
            break
        draw.text((x + 12, ty), line, fill=(185, 210, 185), font=font)
        ty += line_h


# ═══════════════════════════════════════════════════
#  SIMULATION ENGINE
# ═══════════════════════════════════════════════════

SOURCE_LINES = [
    "def numIslands(grid):",
    "    rows = len(grid)",
    "    cols = len(grid[0])",
    "    count = 0",
    "",
    "    for r in range(rows):",
    "        for c in range(cols):",
    "            if grid[r][c] == '1':",
    "                count += 1",
    "                q = deque([(r, c)])",
    "                grid[r][c] = '0'",
    "",
    "                while q:",
    "                    cr, cc = q.popleft()",
    "                    for dr, dc in [(-1,0),",
    "                                    (1,0),",
    "                                   (0,-1),",
    "                                    (0,1)]:",
    "                        nr = cr + dr",
    "                        nc = cc + dc",
    "                        if (0<=nr<rows and",
    "                            0<=nc<cols and",
    "                            grid[nr][nc]=='1'):",
    "                            grid[nr][nc]='0'",
    "                            q.append((nr,nc))",
    "",
    "    return count",
]


def simulate(grid):
    """
    Run BFS island counting step by step, yielding frame data for visualization.
    Grid is a list of lists of '1'/'0' strings (original input).
    Internally works with integers: 0=water, 1=land, 2=visiting, 10+N=visited island N.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Convert original string grid to internal integer grid
    g = []
    for row in grid:
        g.append([1 if cell == '1' else 0 for cell in row])

    island_num = -1   # current island being explored (-1 = none yet)
    count = 0

    def snap(line, desc, queue_list=None, extra_vars=None):
        return {
            "line": line,
            "desc": desc,
            "grid": [row[:] for row in g],
            "queue": queue_list or [],
            "count": count,
            "island_num": island_num,
            "source_lines": SOURCE_LINES,
            "variables": extra_vars or {},
        }

    yield snap(1, f"Starting numIslands on {rows}×{cols} grid")

    for r in range(rows):
        for c in range(cols):
            if g[r][c] == LAND:
                count += 1
                island_num = count - 1  # 0-indexed island number

                yield snap(8, f"Found land at ({r},{c}) — new island #{count}!",
                           extra_vars={"r": r, "c": c, "count": count, "island": island_num})

                q = deque([(r, c)])
                g[r][c] = VISITING

                yield snap(9, f"Island #{count}: BFS started at ({r},{c}), marking visiting",
                           queue_list=list(q),
                           extra_vars={"r": r, "c": c, "count": count})

                while q:
                    cr, cc = q.popleft()

                    yield snap(13, f"Island #{count}: processing ({cr},{cc})",
                               queue_list=list(q),
                               extra_vars={"cr": cr, "cc": cc, "count": count,
                                          "queue_size": len(q)})

                    # Mark current cell as visited island
                    g[cr][cc] = 10 + island_num

                    yield snap(14, f"Island #{count}: marking ({cr},{cc}) as visited",
                               queue_list=list(q),
                               extra_vars={"cr": cr, "cc": cc, "count": count})

                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr = cr + dr
                        nc = cc + dc
                        if 0 <= nr < rows and 0 <= nc < cols and g[nr][nc] == LAND:
                            g[nr][nc] = VISITING
                            q.append((nr, nc))

                            yield snap(24, f"Island #{count}: enqueuing neighbor ({nr},{nc})",
                                       queue_list=list(q),
                                       extra_vars={"nr": nr, "nc": nc, "count": count,
                                                  "queue_size": len(q)})

                yield snap(12, f"Island #{count} fully explored",
                           extra_vars={"count": count, "island_num": island_num})

    yield snap(27, f"Done! Total islands = {count}",
               extra_vars={"result": count})


# ═══════════════════════════════════════════════════
#  RENDER FRAME
# ═══════════════════════════════════════════════════

def desc_style(desc):
    d = desc.lower()
    if "done" in d or "total islands" in d or "result" in d:
        return (12, 38, 18), GREEN, (0, 200, 90)
    elif "found land" in d or "new island" in d:
        return (14, 26, 50), CYAN, BLUE
    elif "enqueuing" in d:
        return (30, 28, 12), YELLOW, (200, 180, 0)
    elif "fully explored" in d:
        return (16, 38, 28), GREEN, GREEN
    elif "processing" in d or "marking" in d:
        return (20, 22, 38), GRAY, BLUE
    else:
        return (25, 28, 40), WHITE, GRAY


def render_frame_image(frame_data, frame_idx, total_frames,
                       orig_grid,
                       problem_desc="",
                       img_w=1920, img_h=1080,
                       prev_grid=None, tween_t=0.0,
                       prev_line=None):
    img = Image.new("RGB", (img_w, img_h), BG)
    draw = ImageDraw.Draw(img)

    font_lg   = load_font_bold(26)
    font_md   = load_font(20)
    font_sm   = load_font(16)
    font_xs   = load_font(13)
    font_code = load_font(19)

    grid = frame_data["grid"]
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Header
    draw.rectangle([0, 0, img_w, 52], fill=(20, 22, 32))
    draw.text((16, 12), "LC 200 — Number of Islands", fill=GREEN, font=font_lg)
    draw.text((img_w - 240, 16), f"Frame {frame_idx+1}/{total_frames}",
              fill=GRAY, font=font_sm)

    draw.rectangle([0, 52, img_w, 84], fill=(18, 20, 30))
    draw.text((16, 60), problem_desc, fill=GRAY, font=font_sm)

    step_bg, step_fg, step_accent = desc_style(frame_data["desc"])
    draw.rectangle([0, 84, img_w, 120], fill=step_bg)
    draw.rectangle([0, 84, 6, 120], fill=step_accent)
    draw.text((16, 92), frame_data["desc"], fill=step_fg, font=font_md)

    # Layout
    question_x = 16
    question_y = 130
    question_w = int(img_w * 0.45)
    question_h = 145

    left_x = 16
    left_w  = question_w

    queue_x = left_x
    queue_y = question_y + question_h + 10
    queue_w = left_w * 3 // 5 - 5
    queue_h = 105

    stats_x = queue_x + queue_w + 10
    stats_y = queue_y
    stats_w = left_w - queue_w - 10
    stats_h = queue_h

    grid_panel_x = left_x
    grid_panel_y = queue_y + queue_h + 10
    grid_panel_w = left_w
    grid_panel_h = img_h - grid_panel_y - 78

    code_x = left_x + left_w + 16
    code_y = 130
    code_w = img_w - code_x - 16
    code_h = img_h - 130 - 78

    legend_x = 16
    legend_y = img_h - 70
    legend_w = img_w - 32
    legend_h = 62

    # Question panel
    draw_question_panel(draw, question_x, question_y, question_w, question_h,
                        font_sm, font_xs)

    # Queue panel
    draw_queue_panel(draw, queue_x, queue_y, queue_w, queue_h,
                     frame_data["queue"], font_sm, font_xs)

    # Stats panel
    count = frame_data["count"]
    island_num = frame_data["island_num"]
    result = frame_data["variables"].get("result", "—")
    stats = [
        ("Islands", count,        GREEN if count > 0 else GRAY),
        ("Queue",   len(frame_data["queue"]), CYAN),
        ("Island#", island_num if island_num >= 0 else "—",
                                 YELLOW if island_num >= 0 else GRAY),
        ("Result",  result,       GREEN if result != "—" else GRAY),
    ]
    draw_stats_panel(draw, stats_x, stats_y, stats_w, stats_h,
                     stats, font_md, font_sm)

    # Grid panel
    draw_rounded_rect(draw, (grid_panel_x, grid_panel_y,
                             grid_panel_x + grid_panel_w,
                             grid_panel_y + grid_panel_h),
                      8, BG_PANEL, GRID_LINE, 1)
    draw.text((grid_panel_x + 10, grid_panel_y + 6), "ISLAND GRID", fill=GREEN, font=font_sm)

    if rows > 0 and cols > 0:
        avail_w = grid_panel_w - 40
        avail_h = grid_panel_h - 50
        cell_size = min(avail_w // cols, avail_h // rows, 80)
        cell_gap  = 4

        total_grid_w = cols * (cell_size + cell_gap) - cell_gap
        total_grid_h = rows * (cell_size + cell_gap) - cell_gap
        gx0 = grid_panel_x + (grid_panel_w - total_grid_w) // 2
        gy0 = grid_panel_y + 30 + (grid_panel_h - 30 - total_grid_h) // 2

        for r in range(rows):
            for c in range(cols):
                cx = gx0 + c * (cell_size + cell_gap)
                cy = gy0 + r * (cell_size + cell_gap)
                state = grid[r][c]

                p_state = prev_grid[r][c] if prev_grid else None
                cell_t  = tween_t if (p_state is not None and p_state != state) else 0.0

                draw_cell(draw, cx, cy, cell_size, state,
                          font_sm, font_xs,
                          is_active=False,
                          anim_t=cell_t, prev_state=p_state)

        # Row/col labels
        for r in range(rows):
            cy = gy0 + r * (cell_size + cell_gap) + cell_size // 2
            draw.text((gx0 - 18, cy - 6), str(r), fill=DIM, font=font_xs)
        for c in range(cols):
            cx = gx0 + c * (cell_size + cell_gap) + cell_size // 2
            draw.text((cx - 3, gy0 - 16), str(c), fill=DIM, font=font_xs)

    # Code panel
    draw_code_panel(draw, code_x, code_y, code_w, code_h,
                    frame_data["source_lines"], frame_data["line"], font_code, font_xs,
                    prev_line=prev_line, tween_t=tween_t)

    # Legend
    if legend_h > 20:
        draw_rounded_rect(draw, (legend_x, legend_y, legend_x + legend_w, legend_y + legend_h),
                          8, BG_PANEL, GRID_LINE, 1)
        lx = legend_x + 16
        ly = legend_y + 8
        items = [
            (CELL_COLORS[WATER],    "Water"),
            (CELL_COLORS[LAND],     "Unvisited Land"),
            (CELL_COLORS[VISITING], "Visiting (BFS)"),
            (ISLAND_PALETTE[0],     "Island 1"),
            (ISLAND_PALETTE[1],     "Island 2"),
            (ISLAND_PALETTE[2],     "Island 3"),
            (ISLAND_PALETTE[3],     "Island 4"),
        ]
        for color, label in items:
            draw.rounded_rectangle([lx, ly, lx + 18, ly + 18], radius=3, fill=color)
            draw.text((lx + 24, ly + 1), label, fill=GRAY, font=font_xs)
            lx += 150

    return apply_scanlines(img)


# ═══════════════════════════════════════════════════
#  TIMING
# ═══════════════════════════════════════════════════

N_TWEEN = 10

def frame_duration(frame_data):
    desc = frame_data["desc"].lower()
    if "done" in desc or "total islands" in desc:
        return 3.5
    elif "found land" in desc or "new island" in desc:
        return 1.8
    elif "fully explored" in desc:
        return 1.2
    elif "enqueuing" in desc:
        return 0.6
    elif "processing" in desc:
        return 0.5
    elif "marking" in desc:
        return 0.4
    elif "starting" in desc:
        return 1.0
    else:
        return 0.5


# ═══════════════════════════════════════════════════
#  GENERATE VIDEO
# ═══════════════════════════════════════════════════

def generate_video(grid, output="lc200_viz.mp4",
                   problem_desc="LC 200 · Number of Islands · Medium  |  BFS connected components on a grid",
                   img_w=1920, img_h=1080):
    snapshots = list(simulate(grid))
    print(f"Simulated {len(snapshots)} key frames")

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        png_idx  = 0
        manifest = os.path.join(tmp, "frames.txt")

        def save(img, duration):
            nonlocal png_idx
            path = os.path.join(tmp, f"f_{png_idx:06d}.png")
            img.save(path)
            with open(manifest, "a") as mf:
                mf.write(f"file 'f_{png_idx:06d}.png'\nduration {duration:.4f}\n")
            png_idx += 1

        for i, curr in enumerate(snapshots):
            prev = snapshots[i - 1] if i > 0 else None

            if prev is not None:
                pg = prev["grid"]
                cg = curr["grid"]
                has_change = any(
                    pg[r][c] != cg[r][c]
                    for r in range(len(cg)) for c in range(len(cg[r]))
                )
                if has_change:
                    for f in range(N_TWEEN):
                        t = ease_in_out(f / N_TWEEN)
                        img = render_frame_image(
                            curr, i, len(snapshots), grid,
                            problem_desc, img_w, img_h,
                            prev_grid=pg, tween_t=t,
                            prev_line=prev["line"],
                        )
                        save(img, 1 / 30)

            img = render_frame_image(
                curr, i, len(snapshots), grid,
                problem_desc, img_w, img_h,
            )
            hold = frame_duration(curr)
            save(img, hold)

            print(f"  snapshot {i+1}/{len(snapshots)}  ({png_idx} PNGs)", end="\r", flush=True)

        last = os.path.join(tmp, f"f_{png_idx-1:06d}.png")
        with open(manifest, "a") as mf:
            mf.write(f"file '{last}'\n")

        print(f"\nStitching {png_idx} PNGs → {output}")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", manifest,
            "-vf", "fps=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    print(f"✓ Saved → {output}")
    return output


if __name__ == "__main__":
    print("═" * 50)
    print("Example 1: 3 islands")
    print("═" * 50)
    generate_video(
        grid=[
            ["1","1","0","0","0"],
            ["1","1","0","0","0"],
            ["0","0","1","0","0"],
            ["0","0","0","1","1"]
        ],
        output="videos/lc200_ex1.mp4",
    )

    print("\n" + "═" * 50)
    print("Example 2: 1 island")
    print("═" * 50)
    generate_video(
        grid=[
            ["1","1","1","1","0"],
            ["1","1","0","1","0"],
            ["1","1","0","0","0"],
            ["0","0","0","0","0"]
        ],
        output="videos/lc200_ex2.mp4",
    )
