def istri(lst):
    #Determine whether a triangle can be built from a given set of edges
    num = len(lst)
    lst.sort()
    if num < 3:
        return "Need more elements"
    else:
        for i in range(num-2):
            if lst[i] < 0:
                continue
            else:
                if lst[i] + lst[i+1] > lst[i+2]:
                    return True
    return False
