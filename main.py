from covgen.profiler import Profiler
from covgen.control_dependency_analyzer import get_cfg
from covgen.fitness_calculator import get_fitness
import argparse
import importlib
import os
import sys
import traceback
import re
import inspect
import random

POSSIBLE_TYPES = ["bool", "int", "float", "str", "list", "tuple"]


def get_base(type):
    if type == "int":
        return 0
    elif type == "float":
        return 0.12345
    elif type == "str":
        return ""
    elif type == "list":
        return []
    elif type == "tuple":
        return ()
    elif type == "bool":
        return True

class _type:
    def __init__(self, t):
        self.this = t
        if t in ["list", "tuple"]:
            self.elem = []
        self.elem_cnt = 0
        self.val = None
        #length str

    def get(self):
        # if self.val not None:
        #     return self.val
        if self.this in ["int", "float", "str", "bool"]:
            return get_base(self.this)
        elif self.this == "list":
            tmp = []
            for i in self.elem:
                tmp.append(i.get())
            return tmp
        elif self.this == "tuple":
            tmp = ()
            for i in self.elem:
                tmp += (i.get(),)
            return tmp

    def add(self, t):
        assert(self.this in ["list", "tuple"])
        self.elem.append(_type(t))
        self.elem_cnt += 1

    def expand(self):
        assert(self.this in ["list", "tuple"])
        self.elem.append(_type(random.choice(POSSIBLE_TYPES)))
        self.elem_cnt += 1

    def __getitem__(self, num):
        return self.elem[num]

    # def __str__(self):

def run(function, input_value, total_branches, timeout=5):
    import signal

    class Branch:
        def __init__(self, branch_id: int, depth: int, predicate_result: bool,
                     op: str, branch_distance: int):
            self.id = branch_id
            self.depth = depth
            self.predicate_result = predicate_result
            self.op = op
            self.branch_distance = branch_distance

        def __str__(self):
            return "{}\t{}\t{}\t{}\t{}".format(self.id, self.depth,
                                               self.predicate_result, self.op,
                                               self.branch_distance)

        def to_tuple(self):
            return (self.id, self.predicate_result)

        @classmethod
        def parse_line(cls, l: str):
            cols = l.strip().split('\t')
            return cls(
                int(cols[0]),
                int(cols[1]),
                bool(int(cols[2])), cols[3],
                {True: float(cols[4]),
                 False: float(cols[5])})

    def clear_coverage_report():
        open('.cov', 'w').close()

    def read_coverage_report():
        cov_result = list()
        with open('.cov', 'r') as cov_report:
            for l in cov_report:
                result = l.strip().split('\t')
                cov_result.append(Branch.parse_line(l))
        return cov_result

    def handler(signum, frame):
        raise Exception("end of time")

    clear_coverage_report()

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        function(*input_value)
    except Exception as e:
        if type(e) is TypeError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            for elem in traceback.format_exception(exc_type, exc_value, exc_traceback):
                if function.__name__ in elem:
                    lineno = int(elem.split(',')[1].strip().split()[-1])
                    break
            types = list(filter(lambda s: "'{}'".format(s) in str(exc_value), POSSIBLE_TYPES))
            #types = list(map(lambda x: x.strip("'"),
            #            filter(lambda x: x.startswith("'") and x.endswith("'"),
            #                str(exc_value).split(':')[-1].strip().split())))
            return (False, (TypeError, (lineno, types)))
        elif type(e) is IndexError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            for elem in traceback.format_exception(exc_type, exc_value, exc_traceback):
                if function.__name__ in elem:
                    lineno = int(elem.split(',')[1].strip().split()[-1])
                    break
            return (False, (IndexError, lineno))
        else:
            return (False, (type(e), e))
    cov_result = read_coverage_report()
    for b in cov_result:
        total_branches[b.to_tuple()] = tuple(input_value)
    return (True, cov_result)


def next_target(branches, cannot_cover):
    not_covered = list(
        filter(lambda b: not b[1] and not b[0] in cannot_cover,
               branches.items()))
    if not_covered:
        return not_covered[0][0]
    else:
        return None


def expand_sequence(value):
    if isinstance(value, str):
        value += " "
    elif isinstance(value, list):
        value.append(get_base(random.choice(POSSIBLE_TYPES)))
    elif isinstance(value, tuple):
        value += (get_base(random.choice(POSSIBLE_TYPES)), )
    return value

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Coverage Measurement Tool')
    parser.add_argument(
        'sourcefile', type=str, help='a file path to instrument')
    parser.add_argument('function', type=str, help='target function name')
    args = parser.parse_args()

    profiler = Profiler()
    inst_sourcefile = os.path.join(
        os.path.dirname(args.sourcefile),
        'inst_' + os.path.basename(args.sourcefile))
    print("{} is generated.".format(inst_sourcefile))
    function_node, total_branches = profiler.instrument(
        args.sourcefile, inst_sourcefile, args.function)
    cfg = get_cfg(function_node, profiler.branches)
    target_module = importlib.import_module(os.path.splitext(inst_sourcefile)[0].replace('/', '.'))

    # Set target branch
    target_branch = (1, True)
    # Set input
    # function_input = ["a", 2, 3]
    # Run the instrumented function


    args_cnt = len(function_node.args.args)
    curr_type = [_type(random.choice(POSSIBLE_TYPES)) for i in range(args_cnt)]
    # print(curr_type)
    curr_input = [type.get() for type in curr_type]
    success = False
    cnt = 0
    while not success:
        print([t.this for t in curr_type])
        print(curr_input)
        success, result = run(target_module.__dict__[args.function], curr_input,
                          total_branches)
        if success:
            # No Error
            cov_result = result
            break
        else:
            error_type, error_info = result
            if error_type == TypeError:
                # Type Error
                lineno, types = error_info
                suspicous_inputs = set()
                _args = inspect.getargspec(target_module.__dict__[args.function]).args
                for v in profiler.line_and_vars[lineno]:
                    if v in _args:
                        #print("{} is suspicous".format(v))
                        suspicous_inputs.add(_args.index(v))
                if len(types) == 1:
                    for i in suspicous_inputs:
                        if curr_type[i].this == types[0]:
                            curr_type[i] = _type(random.choice(["str", "list", "tuple"]))
                            curr_input[i] = curr_type[i].get()
                else:
                    for i in range(args_cnt):
                        change_probability = 1 if i in suspicous_inputs else 0.1
                        if random.random() < change_probability:
                            if curr_type[i].this in types:
                                curr_type[i] = _type(random.choice(types))
                                curr_input[i] = curr_type[i].get()
                            elif random.random() < 0.1:
                                curr_type[i] = _type(random.choice(POSSIBLE_TYPES))
                                curr_input[i] = curr_type[i].get()
            elif error_type == IndexError:
                lineno = error_info
                suspicous_inputs = set()
                _args = inspect.getargspec(target_module.__dict__[args.function]).args
                for v in profiler.line_and_vars[lineno]:
                    if v in _args:
                        suspicous_inputs.add(_args.index(v))
                for i in suspicous_inputs:
                    if curr_type[i].this == "str":
                        curr_input[i] = expand_sequence(curr_input[i])
                    elif curr_type[i].this in ["list", "tuple"]:
                        curr_type[i].expand()
                        curr_input[i] = curr_type[i].get()
            else:
                curr_type = [_type(random.choice(POSSIBLE_TYPES)) for i in range(args_cnt)]
                curr_input = [type.get() for type in curr_type]

    print([t.this for t in curr_type])
