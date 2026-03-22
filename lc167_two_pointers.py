"""
LC 167 – Two Sum II – Input Array Is Sorted
https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/
Difficulty: Medium  |  Two Pointers
"""

# numbers is sorted. Return 1-indexed [i,j] where
# numbers[i]+numbers[j]==target.
#
# [2,7,11,15], target=9  → [1,2]
# [2,3,4],    target=6   → [1,3]


def two_sum(numbers: list, target: int) -> list:
    l = 0
    r = len(numbers) - 1
    while l < r:
        total = numbers[l] + numbers[r]
        if total == target:
            return [l + 1, r + 1]
        elif total < target:
            l += 1
        else:
            r -= 1
    return []


if __name__ == "__main__":
    assert two_sum([2, 7, 11, 15], 9) == [1, 2]
    assert two_sum([2, 3, 4], 6) == [1, 3]
    print("OK")
