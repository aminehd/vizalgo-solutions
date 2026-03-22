#!/usr/bin/env python3
"""
LC 200 — Number of Islands
Clean solution using the vizalgo framework with RenderConfig architecture.
Produces: videos/lc200_ex1.mp4
"""
import sys
import os

# Ensure the repo root is on the path so `vizalgo` is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vizalgo import VizEngine, RenderConfig, GridPanel, QueuePanel, Counter
from vizalgo.core.state import VizGrid, VizQueue
from vizalgo.renderers.pillow import IslandsPillowRenderer
from vizalgo.renderers.interactive import InteractiveRenderer

engine = VizEngine("LC 200", "Number of Islands")
engine.line_speed = 0.6
engine.snap_speed = 1.5
engine.config = RenderConfig(panels=[
    GridPanel("grid"),
    QueuePanel("queue"),
    Counter("count"),
])


@engine.solution
@engine.show
def numIslands(raw_grid):
    grid = VizGrid(raw_grid)
    rows, cols = grid.rows, grid.cols
    count = 0
    queue = VizQueue()

    def bfs(r, c):
        nonlocal count
        queue.push((r, c))
        grid[r][c] = 2
        engine.snap(f"BFS island {count} from ({r},{c})")
        while queue:
            cr, cc = queue.pop()
            grid[cr][cc] = 10 + count
            engine.snap(f"Marking ({cr},{cc}) as island {count}")
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = cr + dr, cc + dc
                if grid.valid(nr, nc) and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    queue.push((nr, nc))
                    engine.snap(f"Enqueue ({nr},{nc})")

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                count += 1
                engine.snap(f"Found land at ({r},{c}) -> island {count}")
                bfs(r, c)

    engine.snap(f"Done. {count} island(s)")
    return count


if __name__ == "__main__":
    grid1 = [
        ["1","1","0","0","0"],
        ["1","1","0","0","0"],
        ["0","0","1","0","0"],
        ["0","0","0","1","1"],
    ]
    result = engine.run(numIslands, grid1)
    print(f"Islands: {result}")
    import os
    output_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "videos", "lc200_ex1.mp4"))
    engine.render(IslandsPillowRenderer(), output=output_path)
    engine.render(InteractiveRenderer(scale=0.7))
    print(f"Done: {output_path}")
