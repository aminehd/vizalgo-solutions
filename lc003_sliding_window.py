"""
LC 3 – Longest Substring Without Repeating Characters
https://leetcode.com/problems/longest-substring-without-repeating-characters/
Difficulty: Medium  |  Sliding Window + Hash Map
"""

# Given s, return the length of the longest substring with no repeating chars.
#
# "abcabcbb" → 3   ("abc")
# "bbbbb"    → 1   ("b")
# "pwwkew"   → 3   ("wke")


def longest_substring(s: str) -> int:
    seen = {}
    l = 0
    best = 0
    for r, ch in enumerate(s):
        if ch in seen and seen[ch] >= l:
            l = seen[ch] + 1
        seen[ch] = r
        best = max(best, r - l + 1)
    return best


if __name__ == "__main__":
    assert longest_substring("abcabcbb") == 3
    assert longest_substring("bbbbb") == 1
    assert longest_substring("") == 0
    print("OK")
