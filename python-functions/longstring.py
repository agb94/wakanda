def longstring(s):
    l = ['this', 'is', 'a', 'demo', 'video', ':)']
    c = ' '.join(map(lambda s: s.upper(), l))
    if s == c:
        return True
