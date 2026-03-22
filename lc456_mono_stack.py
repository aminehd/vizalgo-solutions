"""
LC 456 – 132 Pattern
https://leetcode.com/problems/132-pattern/
Difficulty: Medium  |  Monotonic Stack
"""

# Find i<j<k with nums[i] < nums[k] < nums[j]  (the "132" shape).
# Scan right-to-left: stack holds candidates for nums[j],
# candid tracks best nums[k] (the "2" — largest value popped so far).
# If any num < candid we found nums[i] → done.
#
# [3,1,4,2]  → True  (1 < 2 < 4)
# [1,2,3,4]  → False


def find132pattern(nums: list) -> bool:
    mono_stack = []
    candid = float('-inf')
    for num in reversed(nums):
        if num < candid:
            return True
        while mono_stack and num > mono_stack[-1]:
            candid = mono_stack.pop()
        mono_stack.append(num)
    return False


if __name__ == "__main__":
    assert find132pattern([3, 1, 4, 2]) is True
    assert find132pattern([1, 2, 3, 4]) is False
    assert find132pattern([-1, 3, 2, 0]) is True
    print("OK")
