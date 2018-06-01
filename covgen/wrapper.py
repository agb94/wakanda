from .type import _type
import sys

K = 1

def write_cov_report(bid:int, depth:int, result: bool, op: str, branch_distance_true: int, branch_distance_false: int):
    assert isinstance(bid, int)
    assert isinstance(depth, int)
    assert isinstance(result, bool)
    with open('.cov', 'a') as cov_report:
        cov_report.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(bid, depth, int(result), op, branch_distance_true, branch_distance_false))

def comparison(bid, depth, op, a, b):
    if op == "Eq":
        result = a == b
        write_cov_report(bid, depth, result, 'Eq', abs(dist(a, b)), int(result))
    elif op == "NotEq":
        result = a != b
        write_cov_report(bid, depth, result, 'NotEq', int(not result), abs(dist(a, b)))
    elif op == "Lt":
        result = a < b
        write_cov_report(bid, depth, result, 'Lt', dist(a, b) + K, dist(b, a))
    elif op == "LtE":
        result = a <= b
        write_cov_report(bid, depth, result, 'LtE', dist(a, b), dist(b, a) + K)
    elif op == "Gt":
        result = a > b
        write_cov_report(bid, depth, result, 'Gt', dist(b, a) + K, dist(a, b))
    elif op == "GtE":
        result = a >= b
        write_cov_report(bid, depth, result, 'GtE', dist(b, a), dist(a, b) + K)
    else:
        assert False
    return result

def boolop(bid, depth, op, values):
    result = values[0]
    for i in range(1, len(values)):
        if op == 'And':
            result = result and values[i]
        elif op == 'Or':
            result = result or values[i]
    write_cov_report(bid, depth, result, op, 0, 0)
    return result

def unaryop(bid, depth, op, operand):
    result = not operand
    write_cov_report(bid, depth, result, op, 0, 0)
    return result

def value(bid, depth, v):
    result = bool(v)
    write_cov_report(bid, depth, result, 'V', -abs(dist(v)), abs(dist(v)))
    return result

def iter(bid, depth, expr):
    result = expr
    write_cov_report(bid, depth, len(result) > 0, 'NotEq', -abs(len(result)), abs(len(result)))
    return result

## Suppose a, b are given with 'valid' type -> one of int, float, str, list, tuple
def dist(a, b = None):
    b = _type(type(a)).get()

    # numerical values
    if (type(a) is int or type(a) is float or type(a) is bool) and (type(b) is int or type(b) is float or type(b) is bool) :
        return a - b

    # single characters
    elif type(a) is str and len(a) == 1 and type(b) is str and len(b) == 1:
        return ord(a) - ord(b)

    # seqeunce type values
    elif (type(a) is str and type(b) is str) or (type(a) is list and type(b) is list) or (type(a) is tuple and type(b) is tuple):
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                return dist(a[i], b[i])

        if len(a) == len(b):
            return 0;
        else:
            return (len(a) - len(b)) * 100

    else:
        raise MyError(type(a), type(b))
    # # boolean type values
    # elif (type(a) is bool and type(b) is bool):
    #     return a - b



def dist2(a, b = None):
    b = _type(type(a)).get()

    # numerical values
    if (type(a) is int or type(a) is float or type(a) is bool) and (type(b) is int or type(b) is float or type(b) is bool) :
        return a - b

    # single characters
    elif type(a) is str and len(a) == 1 and type(b) is str and len(b) == 1:
        return ord(a) - ord(b)

    # seqeunce type values
    elif (type(a) is str and type(b) is str) or (type(a) is list and type(b) is list) or (type(a) is tuple and type(b) is tuple):
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                return dist2(a[i], b[i])

        if len(a) == len(b):
            return 0;
        else:
            return (len(a) - len(b)) * 100

    else:
        raise MyError(type(a), type(b))


def dist2(a, b = None):
    
    def value(x):
        if type(x) is int or type(x) is float or type(x) if bool:
            return x

        elif type(x) is str and len(x) == 1:
            return ord(x)

        elif type(x) is str:
            v = 0
            for i in range(len(x)):
                v += value(x[i]) * (128 ** i)

            return v


    return value(a) - value(b)

