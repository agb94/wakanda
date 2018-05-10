import time
from enum import Enum

class TriangleType(Enum):
    INVALID, VALID = 0, 1

def classify_triangle(a, b, c):
    # Sort the sides so that a <= b <= c
    if a > b:
        tmp = a
        a = b
        b = tmp

    if a > c:
        tmp = a
        a = c
        c = tmp

    if b > c:
        tmp = b
        b = c
        c = tmp
    
    if a < 0:
        return TriangleType.INVALID

    if a + b <= c:
        return TriangleType.INVALID
    else:
        return TriangleType.VALID
