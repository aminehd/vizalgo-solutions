"""
LC 30 – Substring with Concatenation of All Words
https://leetcode.com/problems/substring-with-concatenation-of-all-words/
Difficulty: Hard  |  Sliding Window, w offsets × two pointers
"""

# Given s and words (all same length w), return start indices where a window
# of length n*w contains every word exactly the right number of times.
#
# s="barfoothefoobarman",  words=["foo","bar"]  →  [0, 9]
# s="barfoofoobarthefoobarman", words=["bar","foo","the"]  →  [6, 9, 12]


def find_substring(s: str, words: list) -> list:
    if not s or not words:
        return []

    w     = len(words[0])
    n     = len(words)
    total = w * n
    chars = list(s)     # lets the viz show left/right as pointer arrows

    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1

    result = []

    for offset in range(w):
        left  = offset
        right = offset
        seen  = {}
        count = 0

        while right + w <= len(s):
            word   = s[right : right + w]
            right += w

            if word in word_freq:
                seen[word] = seen.get(word, 0) + 1
                count += 1

                while seen[word] > word_freq[word]:
                    drop        = s[left : left + w]
                    seen[drop] -= 1
                    count      -= 1
                    left       += w

                if count == n:
                    result.append(left)
            else:
                seen  = {}
                count = 0
                left  = right

    return result


if __name__ == "__main__":
    assert sorted(find_substring("barfoothefoobarman", ["foo","bar"])) == [0, 9]
    assert find_substring("wordgoodgoodgoodbestword", ["word","good","best","word"]) == []
    print("OK")
