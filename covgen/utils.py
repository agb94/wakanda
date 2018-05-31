def is_true_with_prob(p: float):
    assert type(p) in [int, float]
    assert 0 <= p <= 1
    from random import random
    return random() <= p
