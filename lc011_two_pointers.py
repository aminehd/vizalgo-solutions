"""
LC 11 – Container With Most Water
https://leetcode.com/problems/container-with-most-water/
Difficulty: Medium  |  Two Pointers
"""

# Choose two lines in height[] that form the largest container.
# Area = min(height[l], height[r]) * (r - l).
#
# [1,8,6,2,5,4,8,3,7] → 49   (index 1 and 8)
# [4,3,2,1,4]         → 16


def max_water(height: list) -> int:
    l = 0
    r = len(height) - 1
    best = 0
    while l < r:
        water = min(height[l], height[r]) * (r - l)
        best = max(best, water)
        if height[l] < height[r]:
            l += 1
        else:
            r -= 1
    return best


if __name__ == "__main__":
    assert max_water([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert max_water([1, 1]) == 1
    print("OK")
