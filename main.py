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
            types = list(map(lambda x: x.strip("'"),
                        filter(lambda x: x.startswith("'") and x.endswith("'"),
                            str(exc_value).split(':')[-1].strip().split())))
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

def expand_sequence(value):
    if isinstance(value, str):
        value += " "
    elif isinstance(value, list):
        value.append(0)
    elif isinstance(value, tuple):
        value += (0)
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
    function_node, total_branches = profiler.instrument(
        args.sourcefile, inst_sourcefile, args.function)
    cfg = get_cfg(function_node, profiler.branches)
    target_module = importlib.import_module(
        inst_sourcefile.rstrip('.py').replace('/', '.'))

    # Set target branch
    target_branch = (1, True)
    # Set input
    # function_input = ["a", 2, 3]
    # Run the instrumented function

    args_cnt = len(function_node.args.args)
    #types = ["bool", "int", "float", "str", "list", "tuple"]
    curr_type = ["int" for i in range(args_cnt)]
    curr_input = [get_base(type) for type in curr_type]
    success = False
    cnt = 0
    while not success:
        success, result = run(target_module.__dict__[args.function], curr_input,
                          total_branches)
        print(curr_type, curr_input)
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
                        if curr_type[i] == types[0]:
                            curr_type[i] = "str"
                            curr_input[i] = get_base("str")
                elif len(types) == 3:
                    for i in suspicous_inputs:
                        if curr_type[i] == types[1]:
                            curr_type[i] = types[2]
                            curr_input[i] = get_base(types[2])
                        elif curr_type[i] == types[2]:
                            curr_type[i] = types[1]
                            curr_input[i] = get_base(types[1])
                # print(lineno, types, suspicous_inputs)
            elif error_type == IndexError:
                lineno = error_info
                suspicous_inputs = set()
                _args = inspect.getargspec(target_module.__dict__[args.function]).args
                for v in profiler.line_and_vars[lineno]:
                    if v in _args:
                        suspicous_inputs.add(_args.index(v))
                for i in suspicous_inputs:
                    curr_input[i] = expand_sequence(curr_input[i])
            else:
                print(result)
    print(curr_type)
