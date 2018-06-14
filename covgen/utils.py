def is_true_with_prob(p: float):
    assert type(p) in [int, float]
    assert 0 <= p <= 1
    from random import random
    return random() <= p

def get_index_or_used_args(function, used_vars):
    import inspect
    indexes = []
    _args = inspect.getargspec(function).args
    used_args = filter(lambda var: var in _args, used_vars)
    for arg in used_args:
        indexes.append(_args.index(arg))
    return indexes
