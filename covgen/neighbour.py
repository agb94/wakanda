import itertools

# returns 'neighbour' of given input value with ragne 'n' (+/- n)
# ex) get_Neighbours([3, 'e'], 1) = [[2, 'd'], [2, 'e'], [2, 'f'], [3, 'd'], [3, 'e'], [3, 'f'], [4, 'd'], [4, 'e'], [4, 'f']]
def get_Neighbours(vals, n):
	assert type(n) is int
	assert n > 0

	if len(vals) == 1:
		v = vals[0]
		
		if type(v) is int:
			res = []
			for i in range(-n, n+1):
				res.append(v + i)
			return res

#		elif type(v) is float:


#		elif type(v) is str and





	else:
		lst = []
		for v in vals:
			lst.append(get_Neighbours([v], n))
		pd = itertools.product(*lst)
		res = []
		for e in pd:
			res.append(e)
		return res