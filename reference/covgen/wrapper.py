K = 1

def write_cov_report(bid:int, result: bool, op: str, branch_distance_true: int, branch_distance_false: int):
    assert isinstance(bid, int)
    assert isinstance(result, bool)
    with open('.cov', 'a') as cov_report:
        cov_report.write("{}\t{}\t{}\t{}\t{}\n".format(bid, int(result), op, branch_distance_true, branch_distance_false))

def comparison(bid, op, a, b):
    if op == "Eq":
        result = a == b
        write_cov_report(bid, result, 'Eq', abs(a - b), -abs(a - b))
    elif op == "NotEq":
        result = a != b
        write_cov_report(bid, result, 'NotEq', -abs(a - b), abs(a - b))
    elif op == "Lt":
        result = a < b
        write_cov_report(bid, result, 'Lt', a - b + K, b - a)
    elif op == "LtE":
        result = a <= b
        write_cov_report(bid, result, 'LtE', a - b, b - a + K)
    elif op == "Gt":
        result = a > b
        write_cov_report(bid, result, 'Gt', b - a + K, a - b)
    elif op == "GtE":
        result = a >= b
        write_cov_report(bid, result, 'GtE', b - a, a - b + K)
    else:
        assert False
    return result

def value(bid, v):
    result = bool(v)
    write_cov_report(bid, result, 'V', -abs(v), abs(v))
    return result

def iter(bid, expr):
    result = expr
    write_cov_report(bid, len(result) > 0, 'NotEq', -abs(len(result)), abs(len(result)))
    return result
