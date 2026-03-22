from collections import Counter


def find_substring(s: str, words):
    counter = Counter(words)
    len_word = len(words[0])
    n = len(words)
    res = []
    for k in range(len_word):
        left = k
        count = 0
        seen = {}
        for right in range(k, len(s) - len_word + 1, len_word):
            word = s[right : right + len_word]
            if word in counter:
                seen[word] = seen.get(word, 0) + 1
                count += 1

                while seen.get(word, 0) > counter[word]:
                    drop = s[left : left + len_word]
                    seen[drop] -= 1
                    count -= 1
                    left += len_word
                if count == n:
                    res.append(left)
                    drop = s[left : left + len_word]
                    seen[drop] -= 1
                    count -= 1
                    left += len_word
            else:
                seen = {}
                count = 0
                left = right + len_word
    return res



