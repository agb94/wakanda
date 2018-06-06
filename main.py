from covgen.runner import Runner
from covgen.profiler import Profiler
from covgen.control_dependency_analyzer import get_cfg
from covgen.fitness_calculator import get_fitness
from covgen.type import _type
from covgen.neighbour import get_neighbours
from copy import deepcopy
import argparse
import importlib
import os
import random
import sys

TYPE_SEARCH_LIMIT = 100
NUM_TYPE_CANDIDATES = 20
NUM_INPUT_CANDIDATES = 20
VALUE_SEARCH_LIMIT = 100

def next_target(branches, cannot_cover):
    not_covered = list(
        filter(lambda b: not b[1] and not b[0] in cannot_cover,
               branches.items()))
    if not_covered:
        return not_covered[0][0]
    else:
        return None

def initilizer(input_types, constants):
    values = [t.get() for t in input_types]
    for i, value in enumerate(values):
        constant_list = constants[type(value)]
        constant_list.append(value)
        values[i] = random.choice(constant_list)
    return values

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Coverage Measurement Tool')
    parser.add_argument(
        'sourcefile', type=str, help='a file path to instrument')
    parser.add_argument('function', type=str, help='target function name')
    args = parser.parse_args()

    print("INPUT GENERATOR for " + args.sourcefile)
    # Instrument & Get CFG
    profiler = Profiler()
    inst_sourcefile = os.path.join(
        os.path.dirname(args.sourcefile),
        'inst_' + os.path.basename(args.sourcefile))
    function_node, total_branches = profiler.instrument(
        args.sourcefile, inst_sourcefile, args.function)
    cfg = get_cfg(function_node, profiler.branches)
    target_module = importlib.import_module(os.path.splitext(inst_sourcefile)[0].replace('/', '.'))
    target_function = target_module.__dict__[args.function]
    
    # Initialize Function Runner
    runner = Runner(target_function, total_branches, timeout=20)

    # Search Input Type
    print("Start type search.......")
    num_args = len(function_node.args.args)
    type_candidates = list()
    for i in range(TYPE_SEARCH_LIMIT):
        types = _type.search(runner, num_args, profiler.line_and_vars)
        if types not in type_candidates:
            type_candidates.append(types)
    type_candidates.sort()
    type_candidates = type_candidates[:NUM_TYPE_CANDIDATES]
    print("{} type candidates found.".format(len(type_candidates)))
    print()

    # Search Input Value with determined input type
    print("Start value search......")

    cannot_cover = set()
    target_branch = next_target(total_branches, cannot_cover)
    while target_branch:
        covered = False
        for types in type_candidates:
            # print("TYPE: {}".format(str([str(t) for t in types])))
            # Initialize
            min_fitness = sys.maxsize
            min_fitness_vals = None

            # Select best initial input among the input candidates
            for i in range(NUM_INPUT_CANDIDATES):
                vals = initilizer(types, profiler.constants)
                success, result = runner.run(vals)
                if not success:
                    continue
                fit = get_fitness(cfg, target_branch, result)
                if fit < min_fitness:
                    min_fitness, min_fitness_vals = fit, vals

            if not min_fitness_vals:
                continue
            
            # print("Initial vals: {}".format(str(vals)))
            # Start searching
            count = 0
            while not covered and count < VALUE_SEARCH_LIMIT:
                better_neighbour_found = False
                neighbours = get_neighbours(deepcopy(min_fitness_vals), 1)
                for v in neighbours:
                    success, result = runner.run(v)
                    if not success:
                        continue
                    fit = get_fitness(cfg, target_branch, result)
                    if fit < min_fitness:
                        better_neighbour_found = True
                        min_fitness = fit
                        min_fitness_vals = v

                    if total_branches[target_branch]:
                        print("{}/{} branches have been covered.".format(
                            len(list(filter(lambda v: v, total_branches.values()))),
                            len(total_branches)))
                        covered = True
                        break
                
                if not better_neighbour_found:
                    # Stuck in local optima
                    break

                count += 1

            # Check whether the search succeeded
            # If covered, stop searching a value for the branch
            if covered:
                break

        # If the branch hasn't been covered for all candidate types, stop searching
        if not covered:
            cannot_cover.add(target_branch)

        # Change the target branch
        target_branch = next_target(total_branches, cannot_cover)

    # Print Result
    print()
    print("RESULT")
    num_branch = len(total_branches)
    if (num_branch % 2) != 0:
        raise Exception("Something wrong in total_branches")
    num_branch = int(num_branch / 2)

    for n in range(1, num_branch+1):
        branch_T = (n, True)
        if total_branches[branch_T]:
            test_input_str = ', '.join(map(lambda i: str(i), total_branches[branch_T]))
        else:
            test_input_str = '-'
        print("{}: {}".format(str(n)+'T', test_input_str))

        branch_F = (n, False)
        if total_branches[branch_F]:
            test_input_str = ', '.join(map(lambda i: str(i), total_branches[branch_F]))
        else:
            test_input_str = '-'
        print("{}: {}".format(str(n)+'F', test_input_str))

    print("Done.")
    print("============================================")
