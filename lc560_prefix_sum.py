"""
LC 560 — Subarray Sum Equals K

Given an array of integers nums and an integer k, return the total number
of subarrays whose sum equals k.

Key insight: prefix_sum[i] - prefix_sum[j] = k  →  subarray nums[j+1..i] sums to k.
Store prefix sum frequencies in a hashmap; each lookup is a valid subarray count.
"""

from collections import defaultdict
from vizalgo import VizEngine

engine = VizEngine("lc560", "Subarray Sum Equals K")


@engine.solution
@engine.show(mark=lambda locs: {
    "nums": {"cursor": locs.get("i")},
    "acc":  {"highlight": locs.get("prefix_sum", 0) - locs.get("k", 0)},
})
def subarray_sum(nums: list, k: int) -> int:
    acc = defaultdict(int)
    acc[0] = 1
    res = 0
    prefix_sum = 0

    for i, num in enumerate(nums):
        prefix_sum += num
        res += acc[prefix_sum - k]
        acc[prefix_sum] += 1

    return res


EXAMPLES = [
    {"nums": [1, 1, 1],          "k": 2},
    {"nums": [1, 2, 3],          "k": 3},
    {"nums": [1, -1, 1, -1, 1],  "k": 0},
]

if __name__ == "__main__":
    for ex in EXAMPLES:
        engine.snapshots = []
        result = subarray_sum(ex["nums"], ex["k"])
        print(f"nums={ex['nums']}, k={ex['k']} → {result}  ({len(engine.snapshots)} snapshots)")
