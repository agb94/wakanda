def allzero(l):
    size = 7
    total = 0
    for i in range(size):
        if (l[i] == 0):
            total += 1

    if total == size:
        print('all zeros')
