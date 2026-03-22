def largestRectangleArea(heights: list[int]) -> int:
    """
    Finds the largest rectangular area in a histogram.
    
    The perspective shift:
    - Trapping Rain Water: At index i, water is limited by the MAX to left/right. (Looking UP)
    - Largest Rectangle: At index i, width is limited by the first SMALLER to left/right. (Looking DOWN/OUT)
    
    We use a monotonic increasing stack to store indices. When we see a height smaller than 
    the top of the stack, it means the bar at the top of the stack has found its right boundary.
    The left boundary is the index below it in the stack.
    """
    stack = [] # Stores indices
    max_area = 0
    # Append a 0 to the end to ensure we pop everything at the end
    heights.append(0)
    
    for i, h in enumerate(heights):
        # While the current height is smaller than the height at the top of the stack
        while stack and heights[stack[-1]] >= h:
            # The bar at stack[-1] is the height of our rectangle
            height = heights[stack.pop()]
            
            # The width is determined by the current index (right boundary)
            # and the new top of the stack (left boundary)
            # If the stack is empty, it means this bar was the smallest seen so far,
            # so it spans all the way to the beginning (width = i)
            width = i if not stack else i - stack[-1] - 1
            
            max_area = max(max_area, height * width)
            
        stack.append(i)
    
    # Clean up (though appending 0 handled this)
    heights.pop() 
    
    return max_area