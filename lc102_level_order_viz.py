#!/usr/bin/env python3
"""
LC 102 — Binary Tree Level Order Traversal
Rich Tree BFS Visualization with Pillow

Renders: Binary tree + BFS level animation + code panel + queue + result panel
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

# Node states
UNSEEN  = 0
QUEUED  = 1
CURRENT = 2
DONE    = 3

NODE_COLORS = {
    UNSEEN:  (40, 45, 68),
    QUEUED:  (55, 170, 220),
    CURRENT: (255, 210, 50),
    DONE:    (50, 160, 80),
}

NODE_BORDER = {
    UNSEEN:  (55, 60, 88),
    QUEUED:  (80, 200, 245),
    CURRENT: (255, 235, 100),
    DONE:    (70, 190, 100),
}

NODE_RADIUS = 32


# ═══════════════════════════════════════════════════
#  TREE NODE
# ═══════════════════════════════════════════════════

class TNode:
    def __init__(self, nid, val, left=None, right=None):
        self.nid   = nid
        self.val   = val
        self.left  = None
        self.right = None


def build_tree(vals):
    """Build tree from LeetCode-style list. Returns root TNode or None."""
    if not vals or vals[0] is None:
        return None
    root = TNode(0, vals[0])
    queue = deque([root])
    nid = 1
    i = 1
    while queue and i < len(vals):
        node = queue.popleft()
        if i < len(vals) and vals[i] is not None:
            node.left = TNode(nid, vals[i])
            nid += 1
            queue.append(node.left)
        i += 1
        if i < len(vals) and vals[i] is not None:
            node.right = TNode(nid, vals[i])
            nid += 1
            queue.append(node.right)
        i += 1
    return root


def collect_nodes(root):
    """Return list of all TNodes (BFS order)."""
    if root is None:
        return []
    result = []
    q = deque([root])
    while q:
        node = q.popleft()
        result.append(node)
        if node.left:
            q.append(node.left)
        if node.right:
            q.append(node.right)
    return result


# ═══════════════════════════════════════════════════
#  TREE LAYOUT
# ═══════════════════════════════════════════════════

def compute_layout(root, panel_x, panel_y, panel_w, panel_h):
    """
    Compute pixel positions for each node.
    Returns dict: nid -> (px, py)
    Uses level-based layout: level determines y, x is spread evenly within each level.
    """
    if root is None:
        return {}

    # BFS to get levels
    levels = []
    q = deque([(root, 0)])
    node_level = {}
    while q:
        node, lvl = q.popleft()
        node_level[node.nid] = lvl
        while len(levels) <= lvl:
            levels.append([])
        levels[lvl].append(node)
        if node.left:
            q.append((node.left, lvl + 1))
        if node.right:
            q.append((node.right, lvl + 1))

    n_levels = len(levels)
    margin_y = 60
    margin_x = 40
    usable_h = panel_h - margin_y * 2
    usable_w = panel_w - margin_x * 2

    level_h = usable_h / max(1, n_levels)

    positions = {}
    for lvl, nodes in enumerate(levels):
        n = len(nodes)
        y = panel_y + margin_y + lvl * level_h + level_h / 2
        for idx, node in enumerate(nodes):
            x = panel_x + margin_x + (idx + 0.5) * (usable_w / max(1, n))
            positions[node.nid] = (int(x), int(y))

    return positions


def get_parent_map(root):
    """Return dict: nid -> parent TNode (or None for root)."""
    parents = {}
    if root is None:
        return parents
    q = deque([root])
    parents[root.nid] = None
    while q:
        node = q.popleft()
        if node.left:
            parents[node.left.nid] = node
            q.append(node.left)
        if node.right:
            parents[node.right.nid] = node
            q.append(node.right)
    return parents


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
    return sin(max(0.0, min(1.0, t)) * pi)


def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)


def apply_scanlines(img):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, img.size[1], 3):
        d.line([(0, y), (img.size[0], y)], fill=(0, 0, 0, 28))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


# ═══════════════════════════════════════════════════
#  TREE DRAWING
# ═══════════════════════════════════════════════════

def draw_tree(draw, root, positions, node_states, font,
              prev_node_states=None, tween_t=0.0, parent_map=None):
    """
    Draw tree: edges first, then nodes with state-based colors.
    """
    if root is None:
        return

    all_nodes = collect_nodes(root)

    # Draw edges
    edge_color = (55, 60, 85)
    for node in all_nodes:
        if node.nid not in positions:
            continue
        px, py = positions[node.nid]
        for child in [node.left, node.right]:
            if child and child.nid in positions:
                cx, cy = positions[child.nid]
                draw.line([px, py, cx, cy], fill=edge_color, width=3)

    # Draw nodes
    r = NODE_RADIUS
    for node in all_nodes:
        if node.nid not in positions:
            continue
        nx, ny = positions[node.nid]
        state = node_states.get(node.nid, UNSEEN)
        prev_state = prev_node_states.get(node.nid, UNSEEN) if prev_node_states else None

        # Interpolate colors
        if tween_t > 0 and prev_state is not None and prev_state != state:
            fill   = lerp_color(NODE_COLORS.get(prev_state, NODE_COLORS[UNSEEN]),
                                NODE_COLORS.get(state, NODE_COLORS[UNSEEN]), tween_t)
            border = lerp_color(NODE_BORDER.get(prev_state, NODE_BORDER[UNSEEN]),
                                NODE_BORDER.get(state, NODE_BORDER[UNSEEN]), tween_t)
        else:
            fill   = NODE_COLORS.get(state, NODE_COLORS[UNSEEN])
            border = NODE_BORDER.get(state, NODE_BORDER[UNSEEN])

        # Glow
        glow = 0.0
        if state == CURRENT:
            glow = 1.0
        elif state == QUEUED:
            glow = 0.5
        elif tween_t > 0 and prev_state is not None and prev_state != state:
            glow = bell(tween_t)

        if glow > 0.01:
            n_layers = 7
            for g in range(n_layers, 0, -1):
                strength = glow * (g / n_layers)
                glow_c = lerp_color(BG, (255, 235, 100) if state == CURRENT else (80, 200, 245), strength)
                pad = g * 3
                draw.ellipse([nx - r - pad, ny - r - pad, nx + r + pad, ny + r + pad],
                             outline=glow_c, width=2)

        draw.ellipse([nx - r, ny - r, nx + r, ny + r],
                     fill=fill, outline=border, width=3)

        # Node value text
        val_str = str(node.val)
        bb = draw.textbbox((0, 0), val_str, font=font)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        draw.text((nx - tw // 2, ny - th // 2), val_str, fill=WHITE, font=font)


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
#  QUEUE PANEL (shows node vals)
# ═══════════════════════════════════════════════════

def draw_queue_panel(draw, x, y, w, h, queue_vals, font, font_sm, label="QUEUE  (BFS FRONTIER)"):
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 10, y + 6), label, fill=CYAN, font=font_sm)

    box_w   = 62
    box_h   = 46
    arrow_w = 18
    gap     = arrow_w + 4
    qx      = x + 14
    qy      = y + 30

    items_per_row = max(1, (w - 20) // (box_w + gap))
    visible = queue_vals[: items_per_row * 2]

    for i, val in enumerate(visible):
        row_idx = i // items_per_row
        col_idx = i % items_per_row
        bx = qx + col_idx * (box_w + gap)
        by = qy + row_idx * (box_h + 10)
        if by + box_h > y + h - 6:
            break

        is_front = (i == 0)
        fill_col   = (30, 100, 160) if is_front else (20, 65, 110)
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

        text = str(val)
        bb   = draw.textbbox((0, 0), text, font=font)
        tw   = bb[2] - bb[0]
        th   = bb[3] - bb[1]
        ty   = by + (box_h - th) // 2 + (6 if is_front else 0)
        draw.text((bx + box_w // 2 - tw // 2, ty), text, fill=WHITE, font=font)

        if i < len(visible) - 1 and (i + 1) % items_per_row != 0:
            ax = bx + box_w + 4
            ay = by + box_h // 2
            draw.text((ax, ay - 8), "→", fill=BLUE, font=font)

    if not queue_vals:
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
#  RESULT PANEL
# ═══════════════════════════════════════════════════

def draw_result_panel(draw, x, y, w, h, result, font, font_sm):
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 10, y + 6), "RESULT", fill=GREEN, font=font_sm)

    if not result:
        draw.text((x + 12, y + 30), "[]", fill=DIM, font=font)
        return

    # Format result as nested list
    parts = ["["]
    for i, level in enumerate(result):
        parts.append(f"[{', '.join(str(v) for v in level)}]")
        if i < len(result) - 1:
            parts.append(", ")
    parts.append("]")
    text = "".join(parts)

    # Word-wrap if needed
    max_px = w - 24
    bb = draw.textbbox((0, 0), text, font=font)
    if bb[2] - bb[0] <= max_px:
        draw.text((x + 12, y + 30), text, fill=(80, 220, 120), font=font)
    else:
        # Multiline: one level per line
        ty = y + 28
        lh = 22
        draw.text((x + 12, ty), "[", fill=(80, 220, 120), font=font)
        ty += lh
        for i, level in enumerate(result):
            suffix = "," if i < len(result) - 1 else ""
            line = f"  [{', '.join(str(v) for v in level)}]{suffix}"
            draw.text((x + 12, ty), line, fill=(80, 220, 120), font=font)
            ty += lh
            if ty > y + h - lh:
                break
        draw.text((x + 12, ty), "]", fill=(80, 220, 120), font=font)


# ═══════════════════════════════════════════════════
#  QUESTION PANEL
# ═══════════════════════════════════════════════════

QUESTION_TEXT = (
    "Given the root of a binary tree, return the level order traversal of its node values "
    "— left to right, level by level. BFS uses a queue: enqueue the root, then repeatedly "
    "process all nodes at the current level while enqueuing their children. "
    "The key insight: snapshot len(queue) before processing — that's exactly one level."
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
    "def levelOrder(root):",
    "    if not root:",
    "        return []",
    "    result = []",
    "    queue = deque([root])",
    "",
    "    while queue:",
    "        level = []",
    "        for _ in range(len(queue)):",
    "            node = queue.popleft()",
    "            level.append(node.val)",
    "            if node.left:",
    "                queue.append(node.left)",
    "            if node.right:",
    "                queue.append(node.right)",
    "        result.append(level)",
    "",
    "    return result",
]


def simulate(root):
    """
    Run BFS level order traversal step by step, yielding snapshots.
    """
    all_nodes = collect_nodes(root)

    # Initial states: all UNSEEN
    node_states = {node.nid: UNSEEN for node in all_nodes}
    result = []

    def snap(line, desc, queue_vals=None, extra_vars=None):
        return {
            "line": line,
            "desc": desc,
            "node_states": dict(node_states),
            "queue_vals": queue_vals if queue_vals is not None else [],
            "result": [lvl[:] for lvl in result],
            "source_lines": SOURCE_LINES,
            "variables": extra_vars or {},
        }

    if root is None:
        yield snap(2, "root is None — return []")
        return

    yield snap(1, "Starting levelOrder BFS traversal")

    q = deque([root])
    node_states[root.nid] = QUEUED
    yield snap(5, "Enqueued root node",
               queue_vals=[root.val],
               extra_vars={"queue_size": 1})

    level_num = 0
    while q:
        level_num += 1
        level_size = len(q)
        level = []

        yield snap(7, f"Level {level_num}: processing {level_size} node(s)",
                   queue_vals=[n.val for n in q],
                   extra_vars={"level": level_num, "level_size": level_size})

        for _ in range(level_size):
            node = q.popleft()
            node_states[node.nid] = CURRENT

            yield snap(10, f"Popped node {node.val} from queue",
                       queue_vals=[n.val for n in q],
                       extra_vars={"node_val": node.val, "level": level_num})

            level.append(node.val)

            yield snap(11, f"Appended {node.val} to current level",
                       queue_vals=[n.val for n in q],
                       extra_vars={"node_val": node.val, "level_vals": level[:]})

            if node.left:
                node_states[node.left.nid] = QUEUED
                q.append(node.left)
                yield snap(13, f"Enqueued left child {node.left.val}",
                           queue_vals=[n.val for n in q],
                           extra_vars={"child_val": node.left.val, "level": level_num})

            if node.right:
                node_states[node.right.nid] = QUEUED
                q.append(node.right)
                yield snap(15, f"Enqueued right child {node.right.val}",
                           queue_vals=[n.val for n in q],
                           extra_vars={"child_val": node.right.val, "level": level_num})

            node_states[node.nid] = DONE

        result.append(level)
        yield snap(16, f"Level {level_num} complete: {level}",
                   queue_vals=[n.val for n in q],
                   extra_vars={"level": level_num, "level_vals": level,
                               "result_len": len(result)})

    yield snap(18, f"Done! Result: {result}",
               extra_vars={"result": result, "levels": len(result)})


# ═══════════════════════════════════════════════════
#  RENDER FRAME
# ═══════════════════════════════════════════════════

def desc_style(desc):
    d = desc.lower()
    if "done" in d or "result:" in d:
        return (12, 38, 18), GREEN, (0, 200, 90)
    elif "level" in d and "complete" in d:
        return (16, 38, 28), GREEN, GREEN
    elif "level" in d and "processing" in d:
        return (14, 26, 50), CYAN, BLUE
    elif "popped" in d:
        return (44, 40, 10), YELLOW, (200, 180, 0)
    elif "enqueued" in d:
        return (20, 22, 38), GRAY, BLUE
    elif "appended" in d:
        return (25, 32, 25), GREEN, GREEN
    else:
        return (25, 28, 40), WHITE, GRAY


def render_frame_image(frame_data, frame_idx, total_frames,
                       root,
                       problem_desc="",
                       img_w=1920, img_h=1080,
                       prev_node_states=None, tween_t=0.0,
                       prev_line=None):
    img = Image.new("RGB", (img_w, img_h), BG)
    draw = ImageDraw.Draw(img)

    font_lg   = load_font_bold(26)
    font_md   = load_font(20)
    font_sm   = load_font(16)
    font_xs   = load_font(13)
    font_code = load_font(19)
    font_node = load_font_bold(18)

    # Header
    draw.rectangle([0, 0, img_w, 52], fill=(20, 22, 32))
    draw.text((16, 12), "LC 102 — Binary Tree Level Order Traversal", fill=CYAN, font=font_lg)
    draw.text((img_w - 240, 16), f"Frame {frame_idx+1}/{total_frames}",
              fill=GRAY, font=font_sm)

    draw.rectangle([0, 52, img_w, 84], fill=(18, 20, 30))
    draw.text((16, 60), problem_desc, fill=GRAY, font=font_sm)

    step_bg, step_fg, step_accent = desc_style(frame_data["desc"])
    draw.rectangle([0, 84, img_w, 120], fill=step_bg)
    draw.rectangle([0, 84, 6, 120], fill=step_accent)
    draw.text((16, 92), frame_data["desc"], fill=step_fg, font=font_md)

    # Layout
    # Left 45%: Question (top 130px) → Queue+Stats row (110px) → Tree panel (fills rest)
    # Right 55%: Code panel (top ~750px) → Result panel (bottom ~110px)
    # Bottom full: Legend

    left_w  = int(img_w * 0.45)
    right_x = left_w + 16
    right_w = img_w - right_x - 16

    question_x = 16
    question_y = 130
    question_w = left_w - 16
    question_h = 130

    queue_x = 16
    queue_y = question_y + question_h + 10
    queue_w = (left_w - 16) * 3 // 5 - 5
    queue_h = 110

    stats_x = queue_x + queue_w + 10
    stats_y = queue_y
    stats_w = (left_w - 16) - queue_w - 10
    stats_h = queue_h

    tree_panel_x = 16
    tree_panel_y = queue_y + queue_h + 10
    tree_panel_w = left_w - 16
    tree_panel_h = img_h - tree_panel_y - 78

    legend_y = img_h - 70
    legend_h = 62

    # Right side
    result_h = 110
    code_x = right_x
    code_y = 130
    code_w = right_w
    code_h = img_h - 130 - result_h - 10 - 78

    result_x = right_x
    result_y = code_y + code_h + 10
    result_w = right_w

    # Question panel
    draw_question_panel(draw, question_x, question_y, question_w, question_h,
                        font_sm, font_xs)

    # Queue panel
    draw_queue_panel(draw, queue_x, queue_y, queue_w, queue_h,
                     frame_data["queue_vals"], font_sm, font_xs)

    # Stats panel
    level_num = frame_data["variables"].get("level", 0)
    stats = [
        ("Level",  level_num,                    CYAN),
        ("Queue",  len(frame_data["queue_vals"]), BLUE),
        ("Levels", len(frame_data["result"]),     GREEN),
    ]
    draw_stats_panel(draw, stats_x, stats_y, stats_w, stats_h,
                     stats, font_md, font_sm)

    # Tree panel
    draw_rounded_rect(draw, (tree_panel_x, tree_panel_y,
                             tree_panel_x + tree_panel_w,
                             tree_panel_y + tree_panel_h),
                      8, BG_PANEL, GRID_LINE, 1)
    draw.text((tree_panel_x + 10, tree_panel_y + 6), "BINARY TREE", fill=CYAN, font=font_sm)

    if root is not None:
        positions = compute_layout(
            root,
            tree_panel_x + 10,
            tree_panel_y + 28,
            tree_panel_w - 20,
            tree_panel_h - 36
        )
        draw_tree(draw, root, positions, frame_data["node_states"], font_node,
                  prev_node_states=prev_node_states, tween_t=tween_t)

    # Code panel
    draw_code_panel(draw, code_x, code_y, code_w, code_h,
                    frame_data["source_lines"], frame_data["line"], font_code, font_xs,
                    prev_line=prev_line, tween_t=tween_t)

    # Result panel
    draw_result_panel(draw, result_x, result_y, result_w, result_h,
                      frame_data["result"], font_sm, font_xs)

    # Legend
    draw_rounded_rect(draw, (16, legend_y, img_w - 16, legend_y + legend_h),
                      8, BG_PANEL, GRID_LINE, 1)
    lx = 32
    ly = legend_y + 8
    items = [
        (NODE_COLORS[UNSEEN],  "Unseen"),
        (NODE_COLORS[QUEUED],  "Queued"),
        (NODE_COLORS[CURRENT], "Current (processing)"),
        (NODE_COLORS[DONE],    "Done"),
    ]
    for color, label in items:
        draw.ellipse([lx, ly, lx + 18, ly + 18], fill=color)
        draw.text((lx + 24, ly + 1), label, fill=GRAY, font=font_xs)
        lx += 200

    return apply_scanlines(img)


# ═══════════════════════════════════════════════════
#  TIMING
# ═══════════════════════════════════════════════════

N_TWEEN = 10

def frame_duration(frame_data):
    desc = frame_data["desc"].lower()
    if "done" in desc or "result:" in desc:
        return 3.5
    elif "level" in desc and "complete" in desc:
        return 2.0
    elif "level" in desc and "processing" in desc:
        return 2.0
    elif "popped" in desc:
        return 1.0
    elif "enqueued" in desc:
        return 1.0
    elif "starting" in desc or "enqueued root" in desc:
        return 1.2
    else:
        return 0.8


# ═══════════════════════════════════════════════════
#  GENERATE VIDEO
# ═══════════════════════════════════════════════════

def generate_video(tree_vals, output="lc102_viz.mp4",
                   problem_desc="LC 102 · Binary Tree Level Order Traversal · Medium  |  BFS level by level",
                   img_w=1920, img_h=1080):
    root = build_tree(tree_vals)
    snapshots = list(simulate(root))
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
                pns = prev["node_states"]
                cns = curr["node_states"]
                has_change = any(pns.get(nid) != cns.get(nid) for nid in cns)
                if has_change:
                    for f in range(N_TWEEN):
                        t = ease_in_out(f / N_TWEEN)
                        img = render_frame_image(
                            curr, i, len(snapshots), root,
                            problem_desc, img_w, img_h,
                            prev_node_states=pns, tween_t=t,
                            prev_line=prev["line"],
                        )
                        save(img, 1 / 30)

            img = render_frame_image(
                curr, i, len(snapshots), root,
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
    # Example 1: [3, 9, 20, None, None, 15, 7]
    #       3
    #      / \
    #     9  20
    #        / \
    #       15   7
    # → [[3], [9, 20], [15, 7]]
    print("═" * 50)
    print("Example 1: [3, 9, 20, None, None, 15, 7]")
    print("═" * 50)
    generate_video(
        tree_vals=[3, 9, 20, None, None, 15, 7],
        output="videos/lc102_ex1.mp4",
    )

    # Example 2: [1, 2, 3, 4, 5]
    #       1
    #      / \
    #     2   3
    #    / \
    #   4   5
    # → [[1], [2, 3], [4, 5]]
    print("\n" + "═" * 50)
    print("Example 2: [1, 2, 3, 4, 5]")
    print("═" * 50)
    generate_video(
        tree_vals=[1, 2, 3, 4, 5],
        output="videos/lc102_ex2.mp4",
    )
