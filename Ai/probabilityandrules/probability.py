import math


def calculate_entropy(byte_sequence):
    if not byte_sequence:
        return 0.0
    length = len(byte_sequence)
    freq = {}
    for b in byte_sequence:
        freq[b] = freq.get(b, 0) + 1

    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 4)


def bayes_risk_probability(base_rate, indicators, weights=None):
    if weights is None:
        weights = [0.8] * len(indicators)

    odds = base_rate / (1.0 - base_rate)
    for ind, w in zip(indicators, weights):
        if ind:
            odds *= (w / (1.0 - w))

    prob = odds / (1.0 + odds)
    return min(max(prob, 0.0), 1.0)
