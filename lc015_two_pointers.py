"""
LC 15 – 3Sum
https://leetcode.com/problems/3sum/
Difficulty: Medium  |  Sort + Two Pointers
"""

# Return all unique triplets [a,b,c] where a+b+c == 0.
#
# [-1,0,1,2,-1,-4] → [[-1,-1,2],[-1,0,1]]
# [0,0,0]          → [[0,0,0]]


def three_sum(nums: list) -> list:
    nums.sort()
    result = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        l = i + 1
        r = len(nums) - 1
        while l < r:
            total = nums[i] + nums[l] + nums[r]
            if total == 0:
                result.append([nums[i], nums[l], nums[r]])
                while l < r and nums[l] == nums[l + 1]:
                    l += 1
                while l < r and nums[r] == nums[r - 1]:
                    r -= 1
                l += 1
                r -= 1
            elif total < 0:
                l += 1
            else:
                r -= 1
    return result


if __name__ == "__main__":
    assert three_sum([-1, 0, 1, 2, -1, -4]) == [[-1, -1, 2], [-1, 0, 1]]
    assert three_sum([0, 0, 0]) == [[0, 0, 0]]
    print("OK")
