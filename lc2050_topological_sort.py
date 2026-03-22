from collections import deque, defaultdict

def minimumTime(n: int, relations: list[list[int]], time: list[int]) -> int:
    """
    LC 2050. Parallel Courses III
    
    This is a "Longest Path in a DAG" problem. 
    The minimum time to complete all courses is the length of the longest 
    dependency chain, where each node has a weight (its duration).
    
    Logic:
    1. Build the graph and calculate in-degrees.
    2. Use Kahn's algorithm (Topological Sort).
    3. Maintain 'max_completion_time[i]', which stores the earliest time course i can be finished.
    4. For any edge (u -> v):
       max_completion_time[v] = max(max_completion_time[v], max_completion_time[u] + time[v-1])
    """
    adj = defaultdict(list)
    in_degree = [0] * (n + 1)
    for u, v in relations:
        adj[u].append(v)
        in_degree[v] += 1
        
    # max_time[i] is the earliest time course i is FINISHED
    max_time = [0] * (n + 1)
    queue = deque()
    
    # Initialize with courses that have no dependencies
    for i in range(1, n + 1):
        if in_degree[i] == 0:
            queue.append(i)
            max_time[i] = time[i-1]
            
    while queue:
        u = queue.popleft()
        
        for v in adj[u]:
            # The earliest v can be finished is:
            # (earliest u was finished) + (duration of v)
            # We take the MAX because v must wait for ALL its dependencies.
            max_time[v] = max(max_time[v], max_time[u] + time[v-1])
            
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    return max(max_time)
