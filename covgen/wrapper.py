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
        write_cov_report(bid, depth, result, 'Eq', abs(a - b), -abs(a - b))
    elif op == "NotEq":
        result = a != b
        write_cov_report(bid, depth, result, 'NotEq', -abs(a - b), abs(a - b))
    elif op == "Lt":
        result = a < b
        write_cov_report(bid, depth, result, 'Lt', a - b + K, b - a)
    elif op == "LtE":
        result = a <= b
        write_cov_report(bid, depth, result, 'LtE', a - b, b - a + K)
    elif op == "Gt":
        result = a > b
        write_cov_report(bid, depth, result, 'Gt', b - a + K, a - b)
    elif op == "GtE":
        result = a >= b
        write_cov_report(bid, depth, result, 'GtE', b - a, a - b + K)
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
    print (values)
    write_cov_report(bid, depth, result, op, 0, 0)
    return result

def value(bid, depth, v):
    result = bool(v)
    write_cov_report(bid, depth, result, 'V', -abs(v), abs(v))
    return result

def iter(bid, depth, expr):
    result = expr
    write_cov_report(bid, depth, len(result) > 0, 'NotEq', -abs(len(result)), abs(len(result)))
    return result
