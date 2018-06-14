def string2(s1, s2):
    if s1 == "string test???":
        return 1
    elif s1 == "string" and s2 == "also string":
        return 2
    elif s1 >= s2:
        return "s1 is greater than s2"
    else:
        return "s2 is greater than s1"
