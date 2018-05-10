def test(a, b, c):
    if a > b:
        t = a
        a = b
        b = t
    if a > c:
        t = a
        a = c
        c = t
    if b > c:
        t = b
        b = c
        c = t

    if a + b <= c:
        ty = 0
    else:
        ty = 1
        if a == b:
            if b == c:
                ty = 3
        else:
            if a == b:
                ty = 4
            elif b == c:
                ty = 4
    
    return ty
