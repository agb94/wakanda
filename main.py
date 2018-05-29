from covgen.type import get_base, _type, POSSIBLE_TYPES
from covgen.profiler import Profiler
from covgen.control_dependency_analyzer import get_cfg
from covgen.fitness_calculator import get_fitness
from covgen.wrapper import MyError

import argparse
import importlib
import os
import sys
import traceback
import re
import inspect
import random

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
            types = list(filter(lambda s: "{}".format(s) in str(exc_value), POSSIBLE_TYPES))
            return (False, (TypeError, (lineno, types)))
        elif type(e) is IndexError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            for elem in traceback.format_exception(exc_type, exc_value, exc_traceback):
                if function.__name__ in elem:
                    lineno = int(elem.split(',')[1].strip().split()[-1])
                    p = re.compile("\[(\d+)\]")
                    indexes = list(map(lambda i: int(i), p.findall(elem)))
                    break
            return (False, (IndexError, (lineno, indexes)))
        elif type(e) is MyError: #Need to distinguish other errors : AttributeError ...
            exc_type, exc_value, exc_traceback = sys.exc_info()
            for elem in traceback.format_exception(exc_type, exc_value, exc_traceback):
                if function.__name__ in elem:
                    lineno = int(elem.split(',')[1].strip().split()[-1])
                    break
            type_a = globals()[str(e.type_a).split("'")[1]]
            type_b = globals()[str(e.type_b).split("'")[1]]
            return (False, (Warning, (lineno, [type_a, type_b])))
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


    
    """
    Type Searching
    """
    args_cnt = len(function_node.args.args)
    curr_type = [_type(random.choice(POSSIBLE_TYPES)) for i in range(args_cnt)]
    curr_input = [t.get() for t in curr_type]
    success = False
    while not success:
        # print("curr_type: ", [str(t) for t in curr_type])
        # print("curr_input: ", curr_input)
        success, result = run(target_module.__dict__[args.function], curr_input,
                          total_branches)
        if success:
            # No Error
            break
        else:
            error_type, error_info = result
            if error_type == TypeError or error_type == Warning:
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
                        def recursively_change_type(t, target_type, candidate_types):
                            if t.this == target_type:
                                t = _type(random.choice(candidate_types))
                                return t
                            if not t.elem:
                                return t
                            for i, e in enumerate(t.elem):
                                t.elem[i] = recursively_change_type(e, target_type, candidate_types)
                            return t
                        curr_type[i] = recursively_change_type(curr_type[i], types[0], [str, list, tuple])
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
                lineno, indexes = error_info
                suspicous_inputs = set()
                _args = inspect.getargspec(target_module.__dict__[args.function]).args
                for v in profiler.line_and_vars[lineno]:
                    if v in _args:
                        suspicous_inputs.add(_args.index(v))
                for i in suspicous_inputs:
                    if curr_type[i].this == str:
                        if len(indexes) > 1 or random.random() > 0.5:
                            curr_type[i] = _type(random.choice([list, tuple]))
                        else:
                            curr_type[i].expand()
                        curr_input[i] = curr_type[i].get()
                    elif curr_type[i].this in [list, tuple]:
                        t = curr_type[i]
                        for index in indexes:
                            if t.elem:
                                if index < len(t.elem):
                                    t = t.elem[index]
                        t.expand()
                        curr_input[i] = curr_type[i].get()
            else:
                curr_type = [_type(random.choice(POSSIBLE_TYPES)) for i in range(args_cnt)]
                curr_input = [type.get() for type in curr_type]
    print("type: ", [str(t) for t in curr_type])
    print("input: ", curr_input)

