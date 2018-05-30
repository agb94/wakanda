import random

POSSIBLE_TYPES = [bool, int, float, str, list, tuple, type(None)]

def get_base(t):
    assert t in POSSIBLE_TYPES
    if t == int:
        return 0
    elif t == float:
        return 0.12345
    elif t == str:
        return ""
    elif t == list:
        return []
    elif t == tuple:
        return ()
    elif t == bool:
        return False
    elif t == type(None):
        return None

def str_to_type_class(s):
    if s == 'NoneType':
        return type(None)
    else:
        return globals()[s]

class MyError(Exception):
    def __init__(self, type_a, type_b):
        self.type_a = type_a
        self.type_b = type_b

class _type:
    def __init__(self, t):
        assert t in POSSIBLE_TYPES
        self.this = t
        if t in [list, tuple]:
            self.elem = []
        else:
            self.elem = None
        self.elem_cnt = 0
        self.val = None

    def __str__(self):
        s = self.this.__name__
        if self.elem:
            str_elem = list(map(lambda e: str(e), self.elem))
            s += "([{}])".format(",".join(str_elem))
        return s

    def get(self):
        # if self.val not None:
        #     return self.val
        if self.this in [int, float, bool]:
            return get_base(self.this)
        elif self.this == str:
            return " " * self.elem_cnt
        elif self.this == list:
            tmp = []
            for i in self.elem:
                tmp.append(i.get())
            return tmp
        elif self.this == tuple:
            tmp = ()
            for i in self.elem:
                tmp += (i.get(),)
            return tmp

    def add(self, t):
        assert(self.this in [list, tuple])
        self.elem.append(_type(t))
        self.elem_cnt += 1

    def expand(self):
        if self.this in [list, tuple]:
            self.elem.append(_type(random.choice(POSSIBLE_TYPES)))
            self.elem_cnt += 1
        elif self.this == str:
            self.elem_cnt += 1
        else:
            return

    def set_elem(self, idx, obj):
        self.elem[idx] = obj

    def __getitem__(self, num):
        return self.elem[num]
    
