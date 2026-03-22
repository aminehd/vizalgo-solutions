"""
LC 53 – Maximum Subarray
https://leetcode.com/problems/maximum-subarray/
Difficulty: Medium  |  Kadane's DP
"""

# Given nums, return the largest sum of any contiguous subarray.
#
# [-2,1,-3,4,-1,2,1,-5,4] → 6   ([4,-1,2,1])
# [5,4,-1,7,8]            → 23  (whole array)


def max_subarray(nums: list) -> int:
    dp = [0] * len(nums)
    dp[0] = nums[0]
    for i in range(1, len(nums)):
        dp[i] = max(nums[i], dp[i - 1] + nums[i])
    return max(dp)


if __name__ == "__main__":
    assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert max_subarray([-1, -2, -3]) == -1
    print("OK")
