#!/usr/bin/env python3
"""
LC 994 — Rotting Oranges
Rich Grid BFS Visualization with Pillow

Renders: Grid with oranges + BFS wave animation + code panel + queue + timer
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

# Cell states
EMPTY       = 0
FRESH       = 1
ROTTEN      = 2
JUST_ROTTEN = 3   # just turned rotten this minute (for animation)

# Cell colors
CELL_COLORS = {
    EMPTY:       (30, 33, 45),
    FRESH:       (255, 180, 40),     # bright orange
    ROTTEN:      (100, 55, 20),      # dark brown/rotten
    JUST_ROTTEN: (200, 80, 30),      # transitioning — red-orange
}

CELL_BORDER = {
    EMPTY:       (45, 48, 60),
    FRESH:       (255, 200, 80),
    ROTTEN:      (130, 75, 30),
    JUST_ROTTEN: (255, 100, 50),
}

# Orange emoji-style faces
FRESH_FACE  = ":)"
ROTTEN_FACE = "X("
EMPTY_FACE  = ""


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
#  DRAWING PRIMITIVES
# ═══════════════════════════════════════════════════

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


def draw_cell(draw, x, y, size, state, font, font_sm,
              wave_ring=False, anim_t=0.0, prev_state=None):
    """Draw a grid cell with optional animated transition."""
    # Interpolate fill/border during transition
    if anim_t > 0 and prev_state is not None and prev_state != state:
        fill   = lerp_color(CELL_COLORS.get(prev_state, CELL_COLORS[EMPTY]),
                            CELL_COLORS.get(state,      CELL_COLORS[EMPTY]), anim_t)
        border = lerp_color(CELL_BORDER.get(prev_state, CELL_BORDER[EMPTY]),
                            CELL_BORDER.get(state,      CELL_BORDER[EMPTY]), anim_t)
    else:
        fill   = CELL_COLORS.get(state, CELL_COLORS[EMPTY])
        border = CELL_BORDER.get(state, CELL_BORDER[EMPTY])

    # ── Neon glow layers ──
    glow_intensity = 0.0
    if wave_ring:
        glow_intensity = 1.0
    elif anim_t > 0 and prev_state is not None and prev_state != state:
        glow_intensity = bell(anim_t)   # peaks at t=0.5

    if glow_intensity > 0.01:
        n_layers = 7
        for g in range(n_layers, 0, -1):
            strength = glow_intensity * (g / n_layers)
            gc = lerp_color(BG, (255, 210, 60), strength)
            pad = g * 3
            draw.rounded_rectangle(
                [x - pad, y - pad, x + size + pad, y + size + pad],
                radius=5 + pad, outline=gc, width=2
            )

    draw.rounded_rectangle([x, y, x + size, y + size],
                           radius=5, fill=fill, outline=border, width=2)

    # ── Face — cross-fade at anim midpoint ──
    face_state = state
    if anim_t > 0 and prev_state is not None and anim_t < 0.5:
        face_state = prev_state

    cx, cy = x + size // 2, y + size // 2
    r = size // 3

    if face_state == FRESH:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=(255, 200, 60), outline=(220, 160, 30), width=2)
        eye_r = max(2, r // 5)
        draw.ellipse([cx - r//3 - eye_r, cy - r//4 - eye_r,
                      cx - r//3 + eye_r, cy - r//4 + eye_r], fill=(60, 40, 10))
        draw.ellipse([cx + r//3 - eye_r, cy - r//4 - eye_r,
                      cx + r//3 + eye_r, cy - r//4 + eye_r], fill=(60, 40, 10))
        draw.arc([cx - r//3, cy - r//6, cx + r//3, cy + r//3],
                 start=10, end=170, fill=(60, 40, 10), width=max(1, r//6))

    elif face_state in (ROTTEN, JUST_ROTTEN):
        rot_color = (80, 45, 15) if face_state == ROTTEN else (160, 60, 20)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=rot_color, outline=(50, 30, 10), width=2)
        eye_r = max(2, r // 4)
        for ex in [cx - r//3, cx + r//3]:
            draw.line([ex - eye_r, cy - r//4 - eye_r, ex + eye_r, cy - r//4 + eye_r],
                      fill=(200, 200, 180), width=max(1, r//6))
            draw.line([ex + eye_r, cy - r//4 - eye_r, ex - eye_r, cy - r//4 + eye_r],
                      fill=(200, 200, 180), width=max(1, r//6))
        draw.arc([cx - r//3, cy + r//8, cx + r//3, cy + r//2],
                 start=190, end=350, fill=(200, 200, 180), width=max(1, r//6))
        if face_state == ROTTEN:
            for sx in [-r//2, 0, r//2]:
                draw.line([cx + sx, cy - r - 4, cx + sx + 2, cy - r - 10],
                          fill=(120, 160, 100), width=1)


def draw_particles(draw, cx, cy, cell_size, t):
    """Burst of 8 particles radiating from an infected cell. t in [0, 1]."""
    if t <= 0 or t >= 1:
        return
    max_dist = cell_size * 1.5
    for i in range(8):
        angle = (i / 8) * 2 * pi
        dist = ease_out_cubic(t) * max_dist
        px = int(cx + cos(angle) * dist)
        py = int(cy + sin(angle) * dist)
        fade = max(0.0, 1.0 - t * 1.4)
        pr = max(1, int(5 * fade))
        color = lerp_color(BG, (255, 170, 40), fade)
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=color)


def apply_scanlines(img):
    """Subtle CRT scanline overlay for the pixi aesthetic."""
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

SYN_KEYWORD  = (190, 120, 255)   # purple  — def, for, while, if, return
SYN_BUILTIN  = (80,  190, 255)   # sky blue — range, len, deque
SYN_NUMBER   = (255, 200, 70)    # warm yellow
SYN_COMMENT  = (90,  150, 90)    # muted green
SYN_STRING   = (255, 160, 90)    # soft orange
SYN_OPERATOR = (80,  230, 220)   # cyan
SYN_DEFAULT  = (170, 215, 170)   # soft green-white
SYN_BRIGHT   = (235, 245, 235)   # near-white for current line

PY_KEYWORDS = {'def','for','in','if','elif','else','while','return',
               'and','or','not','True','False','None','import','from'}
PY_BUILTINS = {'range','len','append','popleft','deque','int','str','list'}

_TOKEN_RE = re.compile(
    r'(#[^\n]*)'                                    # comment
    r'|("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'   # string
    r'|(\b\d+\b)'                                   # number
    r'|(\b[a-zA-Z_]\w*\b)'                          # identifier
    r'|([=<>!+\-*/:%\[\]{}(),.])'                   # operator/punct
    r'|(\s+)'                                       # whitespace
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
    """Draw full source code. Highlight bar slides smoothly between lines during tween."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_CODE, GRID_LINE, 1)
    draw.text((x + 10, y + 8), "SOURCE", fill=CYAN, font=font_sm)

    code_y = y + 32
    line_h = 20

    # ── Sliding highlight bar ──
    curr_bar_y = code_y + (current_line - 1) * line_h
    if prev_line and prev_line != current_line and tween_t > 0:
        prev_bar_y = code_y + (prev_line - 1) * line_h
        t_eased    = ease_in_out(tween_t)
        bar_y      = int(prev_bar_y + (curr_bar_y - prev_bar_y) * t_eased)
    else:
        bar_y = curr_bar_y

    # Background fill + left accent
    draw.rectangle([x + 2, bar_y - 1, x + w - 2, bar_y + line_h], fill=(35, 55, 65))
    draw.rectangle([x + 2, bar_y - 1, x + 5,     bar_y + line_h], fill=GREEN)

    # Faint trail when sliding (shows where we came from)
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

        is_at_bar    = (bar_y - 2 <= ly <= bar_y + 2)
        is_dest      = (i == current_line - 1)
        is_source    = (prev_line and i == prev_line - 1)

        # Animate ► marker: fade out from prev, fade in at dest
        if is_at_bar:
            draw.text((x + 8, ly), "►", fill=GREEN, font=font_code)
        elif is_dest and tween_t > 0:
            fade = lerp_color(BG_CODE, GREEN, ease_in_out(tween_t))
            draw.text((x + 8, ly), "►", fill=fade, font=font_code)
        elif is_source and tween_t > 0:
            fade = lerp_color(GREEN, BG_CODE, ease_in_out(tween_t))
            draw.text((x + 8, ly), "►", fill=fade, font=font_code)

        # Line number color
        if is_dest:
            ln_col = lerp_color(DIM, GREEN, ease_in_out(tween_t)) if tween_t > 0 else GREEN
        elif is_source and tween_t > 0:
            ln_col = lerp_color(GREEN, DIM, ease_in_out(tween_t))
        else:
            ln_col = DIM
        draw.text((x + 26, ly), f"{i+1:3}", fill=ln_col, font=font_code)

        # Code text — highlight destination line, dim others
        is_current_for_color = is_dest
        cx = x + 68
        tokens = tokenize_line(raw_text, is_current_for_color)
        for tok, color in tokens:
            draw.text((cx, ly), tok, fill=color, font=font_code)
            bb = draw.textbbox((cx, ly), tok, font=font_code)
            cx = bb[2]
            if cx > x + w - 8:
                break


# ═══════════════════════════════════════════════════
#  QUEUE PANEL
# ═══════════════════════════════════════════════════

def draw_queue_panel(draw, x, y, w, h, queue_contents, font, font_sm, label="QUEUE  (BFS FRONTIER)"):
    """Draw the BFS queue — large boxes with arrows and FRONT label."""
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
        fill_col   = (220, 90, 30) if is_front else (130, 55, 18)
        border_col = (255, 180, 60) if is_front else ORANGE

        # Neon outline for front item
        if is_front:
            for g in range(3, 0, -1):
                gc = lerp_color(BG, (255, 200, 60), g / 5)
                draw.rounded_rectangle(
                    [bx - g, by - g, bx + box_w + g, by + box_h + g],
                    radius=6 + g, outline=gc, width=1
                )

        draw.rounded_rectangle([bx, by, bx + box_w, by + box_h],
                               radius=6, fill=fill_col, outline=border_col, width=2)

        # FRONT badge
        if is_front:
            draw.text((bx + 4, by + 2), "FRONT", fill=(255, 220, 80), font=font_sm)

        text = f"({r}, {c})"
        bb   = draw.textbbox((0, 0), text, font=font)
        tw   = bb[2] - bb[0]
        th   = bb[3] - bb[1]
        ty   = by + (box_h - th) // 2 + (6 if is_front else 0)
        draw.text((bx + box_w // 2 - tw // 2, ty), text, fill=WHITE, font=font)

        # Arrow → between items (not after last)
        if i < len(visible) - 1 and (i + 1) % items_per_row != 0:
            ax = bx + box_w + 4
            ay = by + box_h // 2
            draw.text((ax, ay - 8), "→", fill=ORANGE, font=font)

    if not queue_contents:
        draw.text((qx, qy + 10), "(empty)", fill=DIM, font=font)


# ═══════════════════════════════════════════════════
#  STATS PANEL
# ═══════════════════════════════════════════════════

def draw_stats_panel(draw, x, y, w, h, stats, font, font_sm):
    """Draw statistics: minute, fresh count, etc."""
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
    "You are given an m×n grid of cells. Each cell holds one of three values: "
    "0 (empty slot), 1 (a fresh orange), or 2 (a rotten orange). "
    "Every minute, any fresh orange that is 4-directionally adjacent "
    "to a rotten orange becomes rotten itself — the rot spreads like a wave. "
    "Your goal: find the minimum number of minutes until no fresh orange remains. "
    "If some fresh oranges can never be reached, return -1."
)

def draw_question_panel(draw, x, y, w, h, font, font_sm):
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 12, y + 8), "PROBLEM", fill=CYAN, font=font_sm)

    # Word-wrap the paragraph to fit panel width
    max_px   = w - 24
    words    = QUESTION_TEXT.split()
    lines    = []
    current  = ""
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
#  WAVE PROGRESS BAR
# ═══════════════════════════════════════════════════

def draw_wave_bar(draw, x, y, w, h, minute, max_minutes, total_fresh, remaining_fresh, font_sm):
    """Draw a progress bar showing the BFS wave propagation."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 10, y + 6), "INFECTION PROGRESS", fill=CYAN, font=font_sm)

    bar_x = x + 12
    bar_y = y + 28
    bar_w = w - 24
    bar_h = 20

    # Background
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                          radius=4, fill=(40, 42, 55))

    # Progress
    if total_fresh > 0:
        progress = (total_fresh - remaining_fresh) / total_fresh
        pw = int(bar_w * progress)
        if pw > 0:
            # Gradient from orange to dark brown
            draw.rounded_rectangle([bar_x, bar_y, bar_x + pw, bar_y + bar_h],
                                  radius=4, fill=(200, 80, 30))

        # Percentage
        pct_text = f"{int(progress * 100)}% infected"
        bb = draw.textbbox((0, 0), pct_text, font=font_sm)
        tw = bb[2] - bb[0]
        draw.text((bar_x + bar_w // 2 - tw // 2, bar_y + 3),
                 pct_text, fill=WHITE, font=font_sm)

    # Minute markers
    if max_minutes > 0:
        for m in range(max_minutes + 1):
            mx = bar_x + int(bar_w * m / max_minutes) if max_minutes > 0 else bar_x
            draw.text((mx - 3, bar_y + bar_h + 4), str(m), fill=DIM, font=font_sm)


# ═══════════════════════════════════════════════════
#  SIMULATION ENGINE
# ═══════════════════════════════════════════════════

def simulate(grid):
    """
    Run BFS step by step, yielding frame data for visualization.
    """
    source_lines = [
        "def orangesRotting(grid):",
        "    rows, cols = len(grid), len(grid[0])",
        "    queue = deque()",
        "    fresh = 0",
        "",
        "    # Find all rotten & count fresh",
        "    for r in range(rows):",
        "        for c in range(cols):",
        "            if grid[r][c] == 2:",
        "                queue.append((r, c))",
        "            elif grid[r][c] == 1:",
        "                fresh += 1",
        "",
        "    if fresh == 0: return 0",
        "    minutes = 0",
        "",
        "    while queue and fresh > 0:",
        "        minutes += 1",
        "        # Process entire wave",
        "        for _ in range(len(queue)):",
        "            r, c = queue.popleft()",
        "            for dr, dc in [(-1,0),(1,0),",
        "                           (0,-1),(0,1)]:",
        "                nr, nc = r+dr, c+dc",
        "                if (0<=nr<rows and",
        "                    0<=nc<cols and",
        "                    grid[nr][nc]==1):",
        "                    grid[nr][nc] = 2",
        "                    fresh -= 1",
        "                    queue.append((nr,nc))",
        "",
        "    return minutes if fresh==0 else -1",
    ]

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Deep copy grid for simulation
    g = [row[:] for row in grid]

    queue = deque()
    fresh = 0
    total_fresh = 0

    def snap(line, desc, extra_vars=None, highlight_cells=None):
        return {
            "line": line,
            "desc": desc,
            "grid": [row[:] for row in g],
            "queue": list(queue),
            "fresh": fresh,
            "total_fresh": total_fresh,
            "source": source_lines,
            "variables": extra_vars or {},
            "highlight_cells": highlight_cells or set(),
        }

    # ── Init: find rotten, count fresh ──
    yield snap(2, f"Scanning {rows}×{cols} grid for oranges...")

    for r in range(rows):
        for c in range(cols):
            if g[r][c] == 2:
                queue.append((r, c))
            elif g[r][c] == 1:
                fresh += 1
                total_fresh += 1

    yield snap(12, f"Found {len(queue)} rotten orange(s), {fresh} fresh orange(s)",
               {"rotten_count": len(queue), "fresh": fresh})

    if fresh == 0:
        yield snap(14, "No fresh oranges! Answer = 0", {"result": 0})
        return

    minutes = 0

    # ── BFS waves ──
    while queue and fresh > 0:
        minutes += 1
        wave_size = len(queue)

        yield snap(18, f"⏱ Minute {minutes} begins — processing wave of {wave_size} rotten orange(s)",
                   {"minutes": minutes, "wave_size": wave_size, "fresh": fresh})

        newly_rotten = []

        for i in range(wave_size):
            r, c = queue.popleft()

            yield snap(21, f"Processing rotten orange at ({r},{c})",
                       {"r": r, "c": c, "minutes": minutes, "fresh": fresh},
                       highlight_cells={(r, c)})

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and g[nr][nc] == 1:
                    g[nr][nc] = JUST_ROTTEN
                    fresh -= 1
                    queue.append((nr, nc))
                    newly_rotten.append((nr, nc))

                    yield snap(29, f"🍊→🤢 Orange at ({nr},{nc}) infected! Fresh remaining: {fresh}",
                               {"nr": nr, "nc": nc, "fresh": fresh, "minutes": minutes},
                               highlight_cells={(r, c), (nr, nc)})

        # Convert JUST_ROTTEN → ROTTEN for next wave
        for rr, cc in newly_rotten:
            if g[rr][cc] == JUST_ROTTEN:
                g[rr][cc] = ROTTEN

        yield snap(17, f"Minute {minutes} complete — {fresh} fresh remaining",
                   {"minutes": minutes, "fresh": fresh})

    if fresh == 0:
        yield snap(32, f"✅ All oranges rotten in {minutes} minute(s)!",
                   {"result": minutes})
    else:
        yield snap(32, f"❌ Impossible! {fresh} orange(s) unreachable. Answer = -1",
                   {"result": -1, "unreachable": fresh})


# ═══════════════════════════════════════════════════
#  RENDER FRAME → IMAGE
# ═══════════════════════════════════════════════════

def desc_style(desc):
    """Return (bg, text_color, accent) based on event type."""
    d = desc.lower()
    if any(x in d for x in ["all oranges rotten", "impossible", "answer"]):
        return (12, 38, 18), GREEN,  (0, 200, 90)
    elif "infected" in d:
        return (44, 16, 16), (255, 130, 80), RED
    elif "begins" in d:
        return (14, 26, 50), CYAN,   BLUE
    elif "complete" in d:
        return (16, 38, 28), GREEN,  GREEN
    elif "scanning" in d or "found" in d:
        return (20, 22, 38), GRAY,   BLUE
    else:
        return (25, 28, 40), WHITE,  GRAY


def render_frame_image(frame_data, frame_idx, total_frames,
                       orig_grid, total_fresh_start,
                       problem_desc="",
                       img_w=1920, img_h=1080,
                       prev_grid=None, tween_t=0.0,
                       prev_line=None):
    """Render one simulation frame to a PIL Image."""
    img = Image.new("RGB", (img_w, img_h), BG)
    draw = ImageDraw.Draw(img)

    font_lg = load_font_bold(26)
    font_md = load_font(20)
    font_sm = load_font(16)
    font_xs = load_font(13)
    font_code = load_font(19)

    grid = frame_data["grid"]
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    highlight = frame_data.get("highlight_cells", set())

    # ── Header ──
    draw.rectangle([0, 0, img_w, 52], fill=(20, 22, 32))
    draw.text((16, 12), "LC 994 — Rotting Oranges 🍊", fill=ORANGE, font=font_lg)
    draw.text((img_w - 240, 16), f"Frame {frame_idx+1}/{total_frames}",
              fill=GRAY, font=font_sm)

    # Static problem description bar
    draw.rectangle([0, 52, img_w, 84], fill=(18, 20, 30))
    draw.text((16, 60), problem_desc, fill=GRAY, font=font_sm)

    # Current step bar — color-coded by event type
    step_bg, step_fg, step_accent = desc_style(frame_data["desc"])
    draw.rectangle([0, 84, img_w, 120], fill=step_bg)
    draw.rectangle([0, 84, 6, 120], fill=step_accent)
    draw.text((16, 92), frame_data["desc"], fill=step_fg, font=font_md)

    # ── Layout ──
    # Left:  Question desc (top) + Grid (below)
    # Right: Full code (top) + Queue + Stats (below)
    # Full width bottom: Legend

    question_x = 16
    question_y = 130
    question_w = int(img_w * 0.45)
    question_h = 145

    left_x = 16
    left_w = question_w

    # Queue + Stats sit side-by-side below the question, above the grid
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
    grid_panel_h = img_h - grid_panel_y - 78  # leave room for legend

    code_x = left_x + left_w + 16
    code_y = 130
    code_w = img_w - code_x - 16
    code_h = img_h - 130 - 78               # full height minus legend

    legend_x = 16
    legend_y = img_h - 70
    legend_w = img_w - 32
    legend_h = 62

    # ── Draw Question Panel ──
    draw_question_panel(draw, question_x, question_y, question_w, question_h,
                        font_sm, font_xs)

    # ── Draw Queue Panel ──
    draw_queue_panel(draw, queue_x, queue_y, queue_w, queue_h,
                     frame_data["queue"], font_sm, font_xs)

    # ── Draw Stats Panel ──
    minutes = frame_data["variables"].get("minutes", 0)
    fresh = frame_data["fresh"]
    result = frame_data["variables"].get("result", "—")
    stats = [
        ("Minute", minutes, CYAN),
        ("Fresh",  fresh,   YELLOW if fresh > 0 else GREEN),
        ("Queue",  len(frame_data["queue"]), ORANGE),
        ("Answer", result,  GREEN if result != "—" else GRAY),
    ]
    draw_stats_panel(draw, stats_x, stats_y, stats_w, stats_h,
                     stats, font_md, font_sm)

    # ── Draw Grid Panel ──
    draw_rounded_rect(draw, (grid_panel_x, grid_panel_y,
                             grid_panel_x + grid_panel_w,
                             grid_panel_y + grid_panel_h),
                      8, BG_PANEL, GRID_LINE, 1)
    draw.text((grid_panel_x + 10, grid_panel_y + 6), "ORANGE GRID", fill=ORANGE, font=font_sm)

    if rows > 0 and cols > 0:
        # Compute cell size to fit
        avail_w = grid_panel_w - 40
        avail_h = grid_panel_h - 50
        cell_size = min(avail_w // cols, avail_h // rows, 80)
        cell_gap = 4

        total_grid_w = cols * (cell_size + cell_gap) - cell_gap
        total_grid_h = rows * (cell_size + cell_gap) - cell_gap
        gx0 = grid_panel_x + (grid_panel_w - total_grid_w) // 2
        gy0 = grid_panel_y + 30 + (grid_panel_h - 30 - total_grid_h) // 2

        for r in range(rows):
            for c in range(cols):
                cx = gx0 + c * (cell_size + cell_gap)
                cy = gy0 + r * (cell_size + cell_gap)
                state = grid[r][c]
                is_highlight = (r, c) in highlight

                p_state = prev_grid[r][c] if prev_grid else None
                cell_t  = tween_t if (p_state is not None and p_state != state) else 0.0

                draw_cell(draw, cx, cy, cell_size, state,
                          font_sm, font_xs,
                          wave_ring=is_highlight and tween_t == 0,
                          anim_t=cell_t, prev_state=p_state)

                # Particle burst on infection
                if cell_t > 0 and p_state == FRESH and state in (JUST_ROTTEN, ROTTEN):
                    ccx = cx + cell_size // 2
                    ccy = cy + cell_size // 2
                    draw_particles(draw, ccx, ccy, cell_size, tween_t)

        # Row/col labels
        for r in range(rows):
            cy = gy0 + r * (cell_size + cell_gap) + cell_size // 2
            draw.text((gx0 - 18, cy - 6), str(r), fill=DIM, font=font_xs)
        for c in range(cols):
            cx = gx0 + c * (cell_size + cell_gap) + cell_size // 2
            draw.text((cx - 3, gy0 - 16), str(c), fill=DIM, font=font_xs)

    # ── Draw Code Panel ──
    draw_code_panel(draw, code_x, code_y, code_w, code_h,
                    frame_data["source"], frame_data["line"], font_code, font_xs,
                    prev_line=prev_line, tween_t=tween_t)

    # ── Legend ──
    if legend_h > 20:
        draw_rounded_rect(draw, (legend_x, legend_y, legend_x + legend_w, legend_y + legend_h),
                          8, BG_PANEL, GRID_LINE, 1)
        lx = legend_x + 16
        ly = legend_y + 8
        items = [
            ((255, 200, 60), "Fresh 🍊"),
            ((200, 80, 30), "Just Infected 🤢"),
            ((80, 45, 15), "Rotten 💀"),
            ((30, 33, 45), "Empty"),
        ]
        for color, label in items:
            draw.rounded_rectangle([lx, ly, lx + 18, ly + 18], radius=3, fill=color)
            draw.text((lx + 24, ly + 1), label, fill=GRAY, font=font_xs)
            lx += 170

    return apply_scanlines(img)


# ═══════════════════════════════════════════════════
#  TIMING — Per-frame duration
# ═══════════════════════════════════════════════════

def frame_duration(frame_data):
    """Return how many seconds this frame should stay on screen."""
    desc = frame_data["desc"].lower()
    if any(x in desc for x in ["all oranges rotten", "impossible", "answer"]):
        return 3.5   # final result — let it land
    elif "begins" in desc:
        return 2.0   # wave start — key moment
    elif "complete" in desc:
        return 1.5   # end of a wave
    elif "infected" in desc:
        return 1.0   # each infection event
    elif "scanning" in desc or "found" in desc:
        return 1.2   # init
    else:
        return 0.8   # default


# ═══════════════════════════════════════════════════
#  MAIN — Generate MP4
# ═══════════════════════════════════════════════════

N_TWEEN = 10   # animation frames per state transition


def generate_video(grid, output="lc994_viz.mp4",
                   problem_desc="LC 994 · Rotting Oranges · Medium  |  BFS wave propagation on a grid",
                   img_w=1920, img_h=1080):
    """Generate video with smooth tween animation between state changes."""
    total_fresh_start = sum(1 for row in grid for c in row if c == 1)
    snapshots = list(simulate(grid))
    print(f"Simulated {len(snapshots)} key frames")

    with tempfile.TemporaryDirectory() as tmp:
        png_idx   = 0
        manifest  = os.path.join(tmp, "frames.txt")

        def save(img, duration):
            nonlocal png_idx
            path = os.path.join(tmp, f"f_{png_idx:06d}.png")
            img.save(path)
            with open(manifest, "a") as mf:
                mf.write(f"file 'f_{png_idx:06d}.png'\nduration {duration:.4f}\n")
            png_idx += 1

        for i, curr in enumerate(snapshots):
            prev = snapshots[i - 1] if i > 0 else None

            # ── Tween: animate cells that changed since last snapshot ──
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
                            curr, i, len(snapshots), grid, total_fresh_start,
                            problem_desc, img_w, img_h,
                            prev_grid=pg, tween_t=t,
                            prev_line=prev["line"],
                        )
                        save(img, 1 / 30)

            # ── Hold frame ──
            img = render_frame_image(
                curr, i, len(snapshots), grid, total_fresh_start,
                problem_desc, img_w, img_h,
            )
            hold = frame_duration(curr)
            save(img, hold)

            print(f"  snapshot {i+1}/{len(snapshots)}  ({png_idx} PNGs)", end="\r", flush=True)

        # ffmpeg concat needs last file listed twice
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
    # Example 1: Standard case
    print("═" * 50)
    print("Example 1: [[2,1,1],[1,1,0],[0,1,1]]")
    print("═" * 50)
    generate_video(
        grid=[[2, 1, 1],
              [1, 1, 0],
              [0, 1, 1]],
        output="videos/lc994_ex1.mp4",
    )

    # Example 2: Impossible case
    print("\n" + "═" * 50)
    print("Example 2: [[2,1,1],[0,1,1],[1,0,1]]")
    print("═" * 50)
    generate_video(
        grid=[[2, 1, 1],
              [0, 1, 1],
              [1, 0, 1]],
        output="videos/lc994_ex2.mp4",
    )

    # Example 3: Bigger grid, multiple rotten sources
    print("\n" + "═" * 50)
    print("Example 3: 4x5 grid with 2 rotten sources")
    print("═" * 50)
    generate_video(
        grid=[[2, 1, 1, 1, 1],
              [1, 1, 0, 0, 1],
              [1, 0, 1, 1, 1],
              [1, 1, 1, 1, 2]],
        output="videos/lc994_ex3.mp4",
    )
