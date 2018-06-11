from .utils import get_index_or_used_args
from copy import deepcopy
import random

# POSSIBLE_TYPES = [bool, int, float, str, list, tuple, type(None)]
POSSIBLE_TYPES = [bool, int, float, str, list, tuple]
TYPE_PRIORITY = {bool: 1, int: 2, str: 3, tuple: 4, list: 4, float: 5}

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
        # self.val = None

    def __str__(self):
        s = self.this.__name__
        if self.elem:
            str_elem = list(map(lambda e: str(e), self.elem))
            s += "([{}])".format(",".join(str_elem))
        return s

    def __eq__(self, other):
        return self.this == other.this and self.elem == other.elem
    
    def __ne__(self, other):
        return not self.__eq__(self, other)

    def __lt__(self, other):
        if (TYPE_PRIORITY[self.this] == TYPE_PRIORITY[other.this]) and (self.elem and other.elem):
            num_lt = 0
            num_not_lt = 0
            for e1, e2 in zip(self.elem, other.elem):
                if e1 < e2:
                    num_lt += 1
                else:
                    num_not_lt += 1
            return num_lt < num_not_lt
        else:
            return TYPE_PRIORITY[self.this] < TYPE_PRIORITY[other.this]
    
    def __le__(self, other):
        return self.__lt__(self, other) or self.__eq__(self, other)

    def __gt__(self, other):
        return not self.__le__(self, other)
    
    def __ge__(self, other):
        return not self.__lt__(self, other)

    def get(self):
        # if self.val not None:
        #     return self.val
        assert self.this in POSSIBLE_TYPES
        if self.this == int:
            return random.choice([-100, -10, 0, 10, 100])
        elif self.this == float:
            return random.choice([0.01, 0.00, -0.001, 0.123])
        elif self.this == bool:
            return random.choice([False, True])
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
        elif self.this == type(None):
            return None

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
    
    def recursively_change_type(self, target_type, candidate_types):
        if self.this == target_type:
            self = self.__class__.get_random(candidate_types)
            return self
        if not self.elem:
            return self
        for i, e in enumerate(self.elem):
            self.set_elem(i, e.recursively_change_type(target_type, candidate_types))
        return self

    @classmethod
    def get_neighbour(cls, runner, num_args, line_and_vars, types, error_result):
        error_type, error_info = error_result
        
        curr_types = deepcopy(types)

        # Case1: TypeError or MyError
        if error_type == TypeError or error_type == MyError:
            lineno, types = error_info
            suspicous_inputs = get_index_or_used_args(runner.function, line_and_vars[lineno])

            if suspicous_inputs and random.random() < 0.8:
                i = random.choice(suspicous_inputs)
            else:
                i = random.randrange(num_args)

            if len(types) == 1:
                # It might be a subscription error. So, we change the type into sequence types.
                curr_types[i] = curr_types[i].recursively_change_type(types[0], [str, list, tuple])
            elif curr_types[i].this in types:
                curr_types[i] = cls.get_random(types)
        # Case2: IndexError
        elif error_type == IndexError:
            lineno, indexes = error_info
            suspicous_inputs = get_index_or_used_args(runner.function, line_and_vars[lineno])

            if suspicous_inputs and random.random() < 0.8:
                i = random.choice(suspicous_inputs)
            else:
                i = random.randrange(num_args)

            if curr_types[i].this == str:
                if len(indexes) > 1:
                    curr_types[i] = cls.get_random([list, tuple])
                else:
                    curr_types[i].expand()
            elif curr_types[i].this in [list, tuple]:
                t = curr_types[i]
                for index in indexes:
                    if t.elem and index < len(t.elem):
                        t = t.elem[index]
                    else:
                        break
                t.expand()
        else:
            curr_types = [cls.get_random() for i in range(num_args)]
        
        return curr_types

    @classmethod
    def get_random(cls, candidates=POSSIBLE_TYPES):
        return cls(random.choice(candidates))

    @classmethod
    def search(cls, runner, num_args: int, line_and_vars: dict):
        curr_types = [cls.get_random() for i in range(num_args)]
        while True:
            success, result = runner.run(deepcopy([t.get() for t in curr_types]))
            if success:
                break
            curr_types = cls.get_neighbour(runner, num_args, line_and_vars, curr_types, result)
        return curr_types

    @staticmethod
    def str_to_type_class(s):
        if s == 'NoneType':
            return type(None)
        else:
            return eval(s)

    @staticmethod
    def check(types, values):
        if type(types) != type(values):
            return False
        if len(types) == len(values):
            return False
        for i in range(types):
            if types[i].this != type(values[i]):
                return False
            if types[i].elem and not type_check(types[i].elem, values[i]):
                return False
        return True
