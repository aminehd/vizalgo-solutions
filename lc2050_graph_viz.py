#!/usr/bin/env python3
"""
LC 2050 — Parallel Courses III  
Rich Graph Visualization with Pillow

Renders: DAG layout + BFS animation + Gantt timeline + code panel
Outputs: MP4 video
"""
import os
import sys
import subprocess
import tempfile
from collections import defaultdict, deque
from math import sin, cos, pi, sqrt
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════
#  DESIGN SYSTEM
# ═══════════════════════════════════════════════════

BG         = (15, 17, 23)
BG_PANEL   = (22, 24, 33)
BG_CODE    = (18, 20, 28)
GRID       = (30, 33, 45)

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
TEAL       = (60, 200, 180)

# Node states
STATE_WAITING    = "waiting"
STATE_READY      = "ready"      # in queue, prereqs met
STATE_PROCESSING = "processing" # currently being popped
STATE_DONE       = "done"

STATE_COLORS = {
    STATE_WAITING:    (50, 55, 70),
    STATE_READY:      YELLOW,
    STATE_PROCESSING: CYAN,
    STATE_DONE:       GREEN,
}

STATE_BORDER = {
    STATE_WAITING:    (70, 75, 90),
    STATE_READY:      ORANGE,
    STATE_PROCESSING: (100, 240, 255),
    STATE_DONE:       (60, 180, 100),
}


# ═══════════════════════════════════════════════════
#  FONT
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
    paths = [
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=1)
            except:
                pass
    return load_font(size)


# ═══════════════════════════════════════════════════
#  GRAPH LAYOUT (Sugiyama-style layered DAG)
# ═══════════════════════════════════════════════════

def compute_layers(n, adj, in_degree_orig):
    """Assign each node to a layer (topological depth)."""
    in_deg = list(in_degree_orig)
    layers = [0] * (n + 1)
    queue = deque()
    for i in range(1, n + 1):
        if in_deg[i] == 0:
            queue.append(i)
            layers[i] = 0
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            layers[v] = max(layers[v], layers[u] + 1)
            in_deg[v] -= 1
            if in_deg[v] == 0:
                queue.append(v)
    return layers


def compute_positions(n, adj, in_degree, area_x, area_y, area_w, area_h):
    """Compute (x, y) for each node in the graph area."""
    layers = compute_layers(n, adj, in_degree)
    max_layer = max(layers[1:n+1]) if n > 0 else 0

    # Group nodes by layer
    layer_groups = defaultdict(list)
    for i in range(1, n + 1):
        layer_groups[layers[i]].append(i)

    positions = {}
    for layer_idx in range(max_layer + 1):
        nodes = layer_groups[layer_idx]
        count = len(nodes)
        for j, node in enumerate(nodes):
            # Distribute horizontally within layer
            if max_layer == 0:
                y = area_y + area_h // 2
            else:
                y = area_y + 50 + int((area_h - 100) * layer_idx / max_layer)

            if count == 1:
                x = area_x + area_w // 2
            else:
                x = area_x + 60 + int((area_w - 120) * j / (count - 1))

            positions[node] = (x, y)

    return positions


# ═══════════════════════════════════════════════════
#  DRAWING PRIMITIVES
# ═══════════════════════════════════════════════════

def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)


def draw_arrow(draw, x0, y0, x1, y1, color, width=2, head_size=8):
    """Draw an arrow from (x0,y0) to (x1,y1) with arrowhead."""
    draw.line([(x0, y0), (x1, y1)], fill=color, width=width)
    # Arrowhead
    dx = x1 - x0
    dy = y1 - y0
    length = sqrt(dx*dx + dy*dy)
    if length < 1:
        return
    ux, uy = dx/length, dy/length
    # Perpendicular
    px, py = -uy, ux
    # Arrowhead points
    ax = x1 - ux * head_size
    ay = y1 - uy * head_size
    p1 = (int(ax + px * head_size/2), int(ay + py * head_size/2))
    p2 = (int(ax - px * head_size/2), int(ay - py * head_size/2))
    draw.polygon([(x1, y1), p1, p2], fill=color)


def draw_node(draw, x, y, radius, node_id, state, time_val, completion_time,
              font, font_sm, is_current=False):
    """Draw a graph node with ID, time, and state coloring."""
    fill = STATE_COLORS[state]
    border = STATE_BORDER[state]
    bw = 3 if is_current else 2

    # Glow for current
    if is_current:
        for r in range(radius + 8, radius, -1):
            alpha_col = tuple(max(0, min(255, c - (r - radius) * 15)) for c in CYAN)
            draw.ellipse([x-r, y-r, x+r, y+r], outline=alpha_col, width=1)

    draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                 fill=fill, outline=border, width=bw)

    # Node label (course number)
    text = str(node_id)
    bb = draw.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    text_color = WHITE if state != STATE_READY else (30, 30, 40)
    draw.text((x - tw//2, y - th//2 - 2), text, fill=text_color, font=font)

    # Duration below
    dur_text = f"t={time_val}"
    bb2 = draw.textbbox((0, 0), dur_text, font=font_sm)
    tw2 = bb2[2] - bb2[0]
    draw.text((x - tw2//2, y + radius + 4), dur_text, fill=GRAY, font=font_sm)

    # Completion time (if done)
    if state == STATE_DONE and completion_time > 0:
        ct_text = f"done@{completion_time}"
        bb3 = draw.textbbox((0, 0), ct_text, font=font_sm)
        tw3 = bb3[2] - bb3[0]
        draw.text((x - tw3//2, y - radius - 16), ct_text, fill=GREEN, font=font_sm)


# ═══════════════════════════════════════════════════
#  GANTT CHART
# ═══════════════════════════════════════════════════

def draw_gantt(draw, x, y, w, h, n, time_arr, completion_times, current_time,
               node_states, font_sm):
    """Draw a Gantt-style timeline showing course start/end times."""
    # Background
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID, 1)

    # Title
    draw.text((x + 10, y + 6), "TIMELINE", fill=CYAN, font=font_sm)

    max_t = max(max(completion_times[1:n+1]) if any(completion_times[1:n+1]) else 1, 1)
    max_t = max(max_t, current_time + 1)

    chart_x = x + 50
    chart_y = y + 28
    chart_w = w - 70
    chart_h = h - 45
    bar_h = max(6, min(20, (chart_h - 10) // n))
    gap = max(2, (chart_h - n * bar_h) // (n + 1))

    # Time axis
    draw.line([(chart_x, chart_y + chart_h), (chart_x + chart_w, chart_y + chart_h)],
              fill=GRAY, width=1)

    # Time labels
    for t in range(0, max_t + 1, max(1, max_t // 6)):
        tx = chart_x + int(chart_w * t / max_t)
        draw.line([(tx, chart_y + chart_h), (tx, chart_y + chart_h + 5)], fill=GRAY, width=1)
        draw.text((tx - 4, chart_y + chart_h + 6), str(t), fill=DIM, font=font_sm)

    # Current time marker
    if current_time > 0:
        ctx = chart_x + int(chart_w * current_time / max_t)
        draw.line([(ctx, chart_y), (ctx, chart_y + chart_h)], fill=RED, width=1)
        draw.text((ctx - 8, chart_y - 14), f"t={current_time}", fill=RED, font=font_sm)

    # Bars
    for i in range(1, n + 1):
        by = chart_y + gap + (i - 1) * (bar_h + gap)
        # Course label
        draw.text((x + 8, by), f"C{i}", fill=GRAY, font=font_sm)

        ct = completion_times[i]
        dur = time_arr[i - 1]
        state = node_states.get(i, STATE_WAITING)

        if ct > 0:
            # Course is done or processing
            start_t = ct - dur
            sx = chart_x + int(chart_w * start_t / max_t)
            ex = chart_x + int(chart_w * ct / max_t)
            color = STATE_COLORS[state]
            draw.rectangle([sx, by, max(sx+2, ex), by + bar_h], fill=color)
            # Duration label
            if ex - sx > 20:
                draw.text((sx + 3, by + 1), str(dur), fill=WHITE, font=font_sm)
        elif state == STATE_READY:
            # Show as pending
            draw.rectangle([chart_x, by, chart_x + 4, by + bar_h], fill=YELLOW)


# ═══════════════════════════════════════════════════
#  CODE PANEL
# ═══════════════════════════════════════════════════

def draw_code_panel(draw, x, y, w, h, source_lines, current_line, font, font_sm,
                    font_code=None):
    """Draw source code with line highlight."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_CODE, GRID, 1)
    draw.text((x + 10, y + 8), "SOURCE", fill=CYAN, font=font_sm)

    cf = font_code or font  # code font (bigger)
    code_y = y + 32
    line_h = 22              # taller lines for bigger font
    # Show lines around current
    context = 7
    start = max(0, current_line - context - 1)
    end = min(len(source_lines), current_line + context)

    for i in range(start, end):
        ly = code_y + (i - start) * line_h
        if ly + line_h > y + h - 4:
            break

        is_current = (i == current_line - 1)

        if is_current:
            draw.rectangle([x + 2, ly - 2, x + w - 2, ly + line_h - 1],
                          fill=(35, 55, 65))
            draw.text((x + 8, ly), "►", fill=GREEN, font=cf)

        line_num_color = GREEN if is_current else DIM
        draw.text((x + 26, ly), f"{i+1:3}", fill=line_num_color, font=cf)

        code_color = WHITE if is_current else (140, 200, 140)
        text = source_lines[i] if i < len(source_lines) else ""
        # Truncate based on actual available width
        max_chars = (w - 80) // 9   # ~9px per char at font 15
        if len(text) > max_chars:
            text = text[:max_chars - 1] + "…"
        draw.text((x + 68, ly), text, fill=code_color, font=cf)


# ═══════════════════════════════════════════════════
#  VARIABLES PANEL
# ═══════════════════════════════════════════════════

def draw_vars_panel(draw, x, y, w, h, variables, font_sm, changed=None):
    """Draw current variable values."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID, 1)
    draw.text((x + 10, y + 6), "VARIABLES", fill=CYAN, font=font_sm)

    changed = changed or set()
    vy = y + 26
    for name, val in variables.items():
        color = PINK if name in changed else YELLOW
        val_color = WHITE if name in changed else GRAY
        val_str = str(val)
        if len(val_str) > 30:
            val_str = val_str[:27] + "..."
        draw.text((x + 12, vy), f"{name}", fill=color, font=font_sm)
        draw.text((x + 12 + len(name) * 8 + 8, vy), f"= {val_str}", fill=val_color, font=font_sm)
        vy += 18
        if vy > y + h - 10:
            break


# ═══════════════════════════════════════════════════
#  QUEUE PANEL
# ═══════════════════════════════════════════════════

def draw_queue_panel(draw, x, y, w, h, queue_contents, font, font_sm):
    """Draw the BFS queue."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID, 1)
    draw.text((x + 10, y + 6), "QUEUE (BFS)", fill=CYAN, font=font_sm)

    qx = x + 15
    qy = y + 28
    box_size = 32
    for i, item in enumerate(queue_contents):
        bx = qx + i * (box_size + 6)
        if bx + box_size > x + w - 10:
            break
        draw.rounded_rectangle([bx, qy, bx + box_size, qy + box_size],
                              radius=4, fill=YELLOW, outline=ORANGE, width=2)
        text = str(item)
        bb = draw.textbbox((0, 0), text, font=font)
        tw = bb[2] - bb[0]
        draw.text((bx + box_size//2 - tw//2, qy + 6), text,
                 fill=(30, 30, 40), font=font)

    if not queue_contents:
        draw.text((qx, qy + 8), "(empty)", fill=DIM, font=font_sm)


# ═══════════════════════════════════════════════════
#  SIMULATION ENGINE
# ═══════════════════════════════════════════════════

def simulate(n, relations, time_arr):
    """
    Run the algorithm step by step, yielding frame data for each visualization state.
    """
    source_lines = [
        "def minimumTime(n, relations, time):",
        "    adj = defaultdict(list)",
        "    in_degree = [0] * (n + 1)",
        "    for u, v in relations:",
        "        adj[u].append(v)",
        "        in_degree[v] += 1",
        "",
        "    max_time = [0] * (n + 1)",
        "    queue = deque()",
        "",
        "    # Init: courses with no prerequisites",
        "    for i in range(1, n + 1):",
        "        if in_degree[i] == 0:",
        "            queue.append(i)",
        "            max_time[i] = time[i-1]",
        "",
        "    while queue:",
        "        u = queue.popleft()",
        "",
        "        for v in adj[u]:",
        "            max_time[v] = max(max_time[v],",
        "                max_time[u] + time[v-1])",
        "            in_degree[v] -= 1",
        "            if in_degree[v] == 0:",
        "                queue.append(v)",
        "",
        "    return max(max_time)",
    ]

    # Build graph
    adj = defaultdict(list)
    in_degree = [0] * (n + 1)
    for u, v in relations:
        adj[u].append(v)
        in_degree[v] += 1

    max_time = [0] * (n + 1)
    node_states = {i: STATE_WAITING for i in range(1, n + 1)}
    queue = deque()

    def frame(line, desc, variables=None, highlight_edge=None, current_node=None):
        return {
            "line": line,
            "desc": desc,
            "node_states": dict(node_states),
            "max_time": list(max_time),
            "queue": list(queue),
            "in_degree": list(in_degree),
            "variables": variables or {},
            "highlight_edge": highlight_edge,
            "current_node": current_node,
            "source": source_lines,
        }

    # ── Frame: building graph ──
    yield frame(2, f"Building adjacency list from {len(relations)} relations",
                {"n": n, "relations": relations})

    # ── Frame: init ──
    for i in range(1, n + 1):
        if in_degree[i] == 0:
            queue.append(i)
            max_time[i] = time_arr[i - 1]
            node_states[i] = STATE_READY
            yield frame(14, f"Course {i} has no prereqs → queue it (duration={time_arr[i-1]})",
                        {"i": i, "in_degree[i]": 0, "max_time[i]": max_time[i]},
                        current_node=i)

    yield frame(17, f"BFS starts! Queue = {list(queue)}",
                {"queue": list(queue)})

    # ── BFS loop ──
    while queue:
        u = queue.popleft()
        node_states[u] = STATE_PROCESSING

        yield frame(18, f"Pop course {u} from queue (completed at t={max_time[u]})",
                    {"u": u, "max_time[u]": max_time[u], "queue": list(queue)},
                    current_node=u)

        for v in adj[u]:
            old_time = max_time[v]
            new_time = max_time[u] + time_arr[v - 1]
            max_time[v] = max(max_time[v], new_time)

            yield frame(21, f"Edge {u}→{v}: max_time[{v}] = max({old_time}, {max_time[u]}+{time_arr[v-1]}) = {max_time[v]}",
                        {"u": u, "v": v, "max_time[u]": max_time[u],
                         "time[v-1]": time_arr[v-1], "max_time[v]": max_time[v]},
                        highlight_edge=(u, v), current_node=u)

            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                node_states[v] = STATE_READY
                yield frame(25, f"All prereqs for course {v} done → queue it!",
                            {"v": v, "in_degree[v]": 0, "queue": list(queue)},
                            highlight_edge=(u, v), current_node=u)

        node_states[u] = STATE_DONE
        yield frame(18, f"Course {u} fully processed (done at t={max_time[u]})",
                    {"u": u, "max_time[u]": max_time[u]},
                    current_node=u)

    result = max(max_time)
    yield frame(27, f"✓ All courses done! Answer = {result} months",
                {"result": result, "max_time": max_time[1:]})


# ═══════════════════════════════════════════════════
#  RENDER FRAME → IMAGE
# ═══════════════════════════════════════════════════

def render_frame_image(frame_data, frame_idx, total_frames,
                       n, relations, time_arr, adj, in_degree_orig,
                       img_w=1920, img_h=1080):
    """Render one simulation frame to a PIL Image."""
    img = Image.new("RGB", (img_w, img_h), BG)
    draw = ImageDraw.Draw(img)

    font_lg = load_font_bold(24)
    font_md = load_font(18)
    font_sm = load_font(16)
    font_xs = load_font(13)
    font_code = load_font(15)       # dedicated code font

    # ── Header ──
    draw.rectangle([0, 0, img_w, 50], fill=(20, 22, 32))
    draw.text((16, 12), "LC 2050 — Parallel Courses III", fill=CYAN, font=font_lg)
    draw.text((img_w - 220, 16), f"Frame {frame_idx+1}/{total_frames}",
              fill=GRAY, font=font_sm)

    # Description bar
    draw.rectangle([0, 50, img_w, 84], fill=(25, 28, 40))
    draw.text((16, 56), frame_data["desc"], fill=WHITE, font=font_md)

    # ── Layout zones ──
    # Left: Graph (48%)  Right: Code + Vars (52%) — wider code panel
    graph_x, graph_y = 16, 94
    graph_w = int(img_w * 0.46)
    graph_h = int(img_h * 0.50)

    code_x = graph_x + graph_w + 16
    code_y = 94
    code_w = img_w - code_x - 16
    code_h = int(img_h * 0.38)     # taller code panel

    vars_x = code_x
    vars_y = code_y + code_h + 10
    vars_w = code_w // 2 - 5
    vars_h = int(img_h * 0.13)

    queue_x = vars_x + vars_w + 10
    queue_y = vars_y
    queue_w = code_w - vars_w - 10
    queue_h = vars_h

    gantt_x = 16
    gantt_y = max(graph_y + graph_h, vars_y + vars_h) + 16
    gantt_w = img_w - 32
    gantt_h = img_h - gantt_y - 16

    # ── Draw Graph Panel ──
    draw_rounded_rect(draw, (graph_x, graph_y, graph_x + graph_w, graph_y + graph_h),
                      8, BG_PANEL, GRID, 1)
    draw.text((graph_x + 10, graph_y + 6), "DEPENDENCY GRAPH (DAG)", fill=CYAN, font=font_sm)

    positions = compute_positions(n, adj, in_degree_orig,
                                 graph_x, graph_y + 25, graph_w, graph_h - 30)
    node_radius = min(28, max(18, 200 // max(n, 1)))

    # Draw edges
    for u, v in relations:
        if u in positions and v in positions:
            x0, y0 = positions[u]
            x1, y1 = positions[v]
            # Shorten to not overlap with node circles
            dx, dy = x1 - x0, y1 - y0
            length = sqrt(dx*dx + dy*dy)
            if length > 0:
                ux, uy = dx/length, dy/length
                x0i = int(x0 + ux * (node_radius + 2))
                y0i = int(y0 + uy * (node_radius + 2))
                x1i = int(x1 - ux * (node_radius + 6))
                y1i = int(y1 - uy * (node_radius + 6))

                edge_color = GRAY
                edge_w = 2
                if frame_data.get("highlight_edge") == (u, v):
                    edge_color = CYAN
                    edge_w = 3
                draw_arrow(draw, x0i, y0i, x1i, y1i, edge_color, edge_w)

    # Draw nodes
    ns = frame_data["node_states"]
    mt = frame_data["max_time"]
    cn = frame_data.get("current_node")

    for i in range(1, n + 1):
        if i in positions:
            px, py = positions[i]
            state = ns.get(i, STATE_WAITING)
            draw_node(draw, px, py, node_radius, i, state,
                     time_arr[i-1], mt[i], font_md, font_xs,
                     is_current=(i == cn))

    # ── Draw Code Panel ──
    draw_code_panel(draw, code_x, code_y, code_w, code_h,
                    frame_data["source"], frame_data["line"], font_sm, font_xs,
                    font_code=font_code)

    # ── Draw Variables Panel ──
    draw_vars_panel(draw, vars_x, vars_y, vars_w, vars_h,
                    frame_data["variables"], font_sm)

    # ── Draw Queue Panel ──
    draw_queue_panel(draw, queue_x, queue_y, queue_w, queue_h,
                     frame_data["queue"], font_md, font_xs)

    # ── Draw Gantt Timeline ──
    draw_gantt(draw, gantt_x, gantt_y, gantt_w, gantt_h,
               n, time_arr, mt,
               max(mt) if any(mt) else 0,
               ns, font_xs)

    return img


# ═══════════════════════════════════════════════════
#  MAIN — Generate MP4
# ═══════════════════════════════════════════════════

def generate_video(n, relations, time_arr, output="lc2050_viz.mp4", fps=1.5,
                   img_w=1920, img_h=1080):
    """Generate the full visualization video."""
    # Pre-compute graph structure
    adj = defaultdict(list)
    in_degree = [0] * (n + 1)
    for u, v in relations:
        adj[u].append(v)
        in_degree[v] += 1

    # Collect all frames
    frames = list(simulate(n, relations, time_arr))
    total = len(frames)
    print(f"Simulated {total} frames")

    with tempfile.TemporaryDirectory() as tmp:
        for i, fdata in enumerate(frames):
            img = render_frame_image(fdata, i, total, n, relations, time_arr,
                                     adj, in_degree, img_w, img_h)
            img.save(os.path.join(tmp, f"frame_{i:05d}.png"))
            print(f"  rendered {i+1}/{total}", end="\r", flush=True)

        print(f"\nStitching {total} frames → {output}")
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", os.path.join(tmp, "frame_%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    print(f"✓ Saved → {output}")
    return output


if __name__ == "__main__":
    # Example 1: Simple
    print("═" * 50)
    print("Example 1: n=3, [[1,3],[2,3]], time=[3,2,5]")
    print("═" * 50)
    generate_video(
        n=3,
        relations=[[1, 3], [2, 3]],
        time_arr=[3, 2, 5],
        output="videos/lc2050_ex1.mp4",
        fps=1.2,
    )

    # Example 2: More complex
    print("\n" + "═" * 50)
    print("Example 2: n=5, [[1,5],[2,5],[3,5],[3,4],[4,5]], time=[1,2,3,4,5]")
    print("═" * 50)
    generate_video(
        n=5,
        relations=[[1, 5], [2, 5], [3, 5], [3, 4], [4, 5]],
        time_arr=[1, 2, 3, 4, 5],
        output="videos/lc2050_ex2.mp4",
        fps=1.2,
    )
