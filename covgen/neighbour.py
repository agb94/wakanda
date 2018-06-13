from copy import deepcopy
import itertools
import random

# returns 'neighbour' of given input value with ragne 'n' (+/- n)
# ex) get_neighbours([3, 'e'], 1) = [[2, 'd'], [2, 'e'], [2, 'f'], [3, 'd'], [3, 'e'], [3, 'f'], [4, 'd'], [4, 'e'], [4, 'f']]
def get_neighbours(vals, n, float_amplitude):
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
                res.append([v + i*float_amplitude])
            return res

        elif type(v) is str and len(v) == 1:
            res = []
            for i in range(-n, n+1):
                try:
                    res.append([chr(ord(v) + i)])
                except:
                    continue

            if randomTorF(1):
                for len_diff in range(1, n+1):
                    # add element of (len(v) + len_diff) long
                    res.append([v + random_seq(v, len_diff)])

                    res.append([''])
            return res


        elif type(v) is bool:
            return [[True], [False]]

        elif type(v) is str or type(v) is list or type(v) is tuple:
            nei = get_neighbours(deepcopy(v), n, float_amplitude)
            lst = []

            for e in nei:
                lst.append([e])

            if randomTorF(1):
                for len_diff in range(1, n+1):
                    # add element of (len(v) + len_diff) long
                    lst.append([v + random_seq(v, len_diff)])

                    # add element of (len(v) - len_diff) long
                    if len(v) - len_diff >= 0:
                        new = v[0:(-len_diff)]
                        lst.append([new])
            
            return lst

    else:
        lst = []
        for v in vals:
            v = deepcopy(v)
            if randomTorF(len(vals)):
                neighbour = get_neighbours([v], n, float_amplitude)
                l = []
                for e in neighbour:
                    if (len(e) != 1):
                        raise Exception("Something wrong in get_neighbours")
                    l.append(e[0])
                lst.append(l)
            else:
                lst.append([v])

        pd = itertools.product(*lst)
        res = []
        for e in pd:
            if type(vals) == list:
                res.append(list(e))
            elif type(vals) == tuple:
                res.append(tuple(e))
            elif type(vals) == str:
                res.append(''.join(e))
        return res


# returns True with probability of 1/n
def randomTorF(n):
    r = random.randrange(n)
    if r == 0:
        return True
    else:
        return False


# return random sequence of length n and type 'type(v)'
def random_seq(v, n):
    if type(v) is str:
        seq = ''
        for i in range(n):
            seq += chr(random.randrange(32, 127))
        return seq

    elif type(v) is list:
        seq = []
        for i in range(n):
            if len(v) > 0:
                sample = v[0]
                if type(sample) is int:
                    seq.append(0)
                    #seq.append(random_int())
                elif type(sample) is float:
                    seq.append(0.0)
                    #seq.append(random_float())
                elif type(sample) is str:
                    seq.append('')
                    #seq.append(random_str())
                elif type(sample) is list:
                    seq.append([])
                    #seq.append(random_list())
                elif type(sample) is tuple:
                    seq.append(())
                    #seq.append(random_tuple())
                elif type(sample) is bool:
                    seq.append(True)
                    #seq.append(random_bool())
            else:
                seq.append(0) # for now, arbitrary append 0(intger type value). Could be changed

        return seq

    elif type(v) is tuple:
        seq = ()
        for i in range(n):
            if len(v) > 0:
                sample = v[0]
                if type(sample) is int:
                    seq += (0, )
                    #seq += (random_int(), )
                elif type(sample) is float:
                    seq += (0.0, )
                    #seq += (random_float(), )
                elif type(sample) is str:
                    seq += ('', )
                    #seq += (random_str(), )
                elif type(sample) is list:
                    seq += ([], )
                    #seq += (random_list(), )
                elif type(sample) is tuple:
                    seq += ((), )
                    #seq += (random_tuple(), )
                elif type(sample) is bool:
                    seq += (True, )
                    #seq += (random_bool(), )
            else:
                seq += (0, ) # for now, arbitrary append 0(intger type value). Could be changed
 
        return seq
