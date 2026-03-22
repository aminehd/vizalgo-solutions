"""
LC 56 – Merge Intervals
https://leetcode.com/problems/merge-intervals/
Difficulty: Medium  |  Sort + Greedy Merge
"""

# Given intervals, merge all overlapping ones.
#
# [[1,3],[2,6],[8,10],[15,18]] → [[1,6],[8,10],[15,18]]
# [[1,4],[4,5]]               → [[1,5]]


def merge(intervals: list) -> list:
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for i in range(1, len(intervals)):
        if intervals[i][0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], intervals[i][1])
        else:
            merged.append(intervals[i])
    return merged


if __name__ == "__main__":
    assert merge([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
    assert merge([[1,4],[4,5]]) == [[1,5]]
    print("OK")
