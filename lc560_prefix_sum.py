"""
LC 560 — Subarray Sum Equals K

Given an array of integers nums and an integer k, return the total number
of subarrays whose sum equals k.

Key insight: for each index i, we want to count how many previous prefix
sums equal (prefix_sum - k). We store prefix sum frequencies in a hashmap.

Demo of engine.step() — the clean single-call viz API:
  - nums    → array panel with cursor at i
  - acc     → hashmap panel with the lookup key highlighted
  - scalars → counter cards (prefix_sum, res, k)
"""

from collections import defaultdict
from vizalgo import VizEngine

engine = VizEngine("lc560", "Subarray Sum Equals K")


@engine.solution
@engine.show
def subarray_sum(nums: list, k: int) -> int:
    acc = defaultdict(int)
    acc[0] = 1
    res = 0
    prefix_sum = 0

    for i, num in enumerate(nums):
        prefix_sum += num
        res += acc[prefix_sum - k]
        acc[prefix_sum] += 1

        engine.step(
            locals(),
            mark={
                "nums": {"cursor": i},
                "acc":  {"highlight": prefix_sum - k},
            },
            label=f"i={i}  prefix={prefix_sum}  lookup acc[{prefix_sum - k}] → +{acc[prefix_sum - k - 1]}",
        )

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
