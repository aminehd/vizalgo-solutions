"""
LC 238 – Product of Array Except Self
https://leetcode.com/problems/product-of-array-except-self/
Difficulty: Medium  |  Prefix / Suffix Product
"""

# Return answer[] where answer[i] = product of all nums except nums[i].
# O(n) time, no division, O(1) extra space.
#
# [1,2,3,4]       → [24,12,8,6]
# [-1,1,0,-3,3]   → [0,0,9,0,0]


def product_except_self(nums: list) -> list:
    n = len(nums)
    result = [1] * n
    prefix = 1
    for i in range(n):
        result[i] = prefix
        prefix *= nums[i]
    suffix = 1
    for i in range(n - 1, -1, -1):
        result[i] *= suffix
        suffix *= nums[i]
    return result


if __name__ == "__main__":
    assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
    print("OK")
