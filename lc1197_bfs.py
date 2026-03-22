from collections import deque

def minKnightMoves(x: int, y: int) -> int:
    """
    Finds the minimum knight moves from (0,0) to (x,y) on an infinite board.
    
    Perspective:
    - Shortest path in an unweighted graph = BFS.
    - Infinite board = Use symmetry (abs(x), abs(y)).
    - Pruning = Allow a small buffer (nx >= -2, ny >= -2) for efficient paths.
    """
    x, y = abs(x), abs(y)
    queue = deque([(0, 0, 0)])
    visited = {(0, 0)}
    
    moves = [
        (2, 1), (1, 2), (-1, 2), (-2, 1),
        (-2, -1), (-1, -2), (1, -2), (2, -1)
    ]
    
    while queue:
        curr_x, curr_y, steps = queue.popleft()
        
        if curr_x == x and curr_y == y:
            return steps
            
        for dx, dy in moves:
            nx, ny = curr_x + dx, curr_y + dy
            
            # Pruning to keep the search space manageable while 
            # allowing for slight backward moves that might be optimal.
            if (nx, ny) not in visited and nx >= -2 and ny >= -2:
                visited.add((nx, ny))
                queue.append((nx, ny, steps + 1))
                
    return -1
