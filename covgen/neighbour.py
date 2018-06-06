import itertools

# returns 'neighbour' of given input value with ragne 'n' (+/- n)
# ex) get_neighbours([3, 'e'], 1) = [[2, 'd'], [2, 'e'], [2, 'f'], [3, 'd'], [3, 'e'], [3, 'f'], [4, 'd'], [4, 'e'], [4, 'f']]
def get_neighbours(vals, n):
    assert type(n) is int
    assert n > 0

    if len(vals) == 1:
        v = vals[0]
		
        if type(v) is int:
            res = []
            for i in range(-n, n+1):
                res.append([v + i])
            return res

        # needs to be changed
        elif type(v) is float:
            res = []
            for i in range(-n, n+1):
                res.append([v + i*0.00000000000001])
            return res

        elif type(v) is str and len(v) == 1:
            res = []
            for i in range(-n, n+1):
                res.append([chr(ord(v) + i)])
            return res

        elif type(v) is bool:
            return [[True], [False]]

        elif type(v) is str or type(v) is list or type(v) is tuple:
            nei = get_neighbours(v, n)
            lst = []
            for e in nei:
                if type(v) is str:
                    lst.append([''.join(e)])
                else:
                    lst.append([e])

            return lst



    else:
        lst = []
        for v in vals:
            neighbour = get_neighbours([v], n)
            l = []
            for e in neighbour:
                if (len(e) != 1):
                    raise Exception("Something wrong in get_neighbours")
                l.append(e[0])
            lst.append(l)
        pd = itertools.product(*lst)
        res = []
        for e in pd:
            res.append(list(e))
        return res
