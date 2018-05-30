from covgen.runner import Runner
from covgen.profiler import Profiler
from covgen.control_dependency_analyzer import get_cfg
from covgen.fitness_calculator import get_fitness
from covgen.type import get_base, str_to_type_class, _type, POSSIBLE_TYPES
from copy import deepcopy
import argparse
import importlib
import os
import sys
import traceback
import re
import inspect
import random

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

    runner = Runner(target_module.__dict__[args.function], total_branches)

    """
    Type Searching
    """
    args_cnt = len(function_node.args.args)
    curr_type = [_type(random.choice(POSSIBLE_TYPES)) for i in range(args_cnt)]
    curr_input = [t.get() for t in curr_type]
    success = False
    
    while not success:
        print("curr_type: ", [str(t) for t in curr_type])
        print("curr_input: ", curr_input)
        success, result = runner.run(deepcopy(curr_input))
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
                                t.set_elem(i, recursively_change_type(e, target_type, candidate_types))
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

