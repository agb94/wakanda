from covgen.runner import Runner
from covgen.profiler import Profiler
from covgen.control_dependency_analyzer import get_cfg
from covgen.fitness_calculator import get_fitness
from covgen.type import _type, MyError
from covgen.neighbour import get_neighbours
from copy import deepcopy
import argparse
import importlib
import os
import random
import sys

def next_target(branches, cannot_cover):
    not_covered = list(
        filter(lambda b: not b[1] and not b[0] in cannot_cover,
               branches.items()))
    if not_covered:
        return not_covered[0][0]
    else:
        return None

def initializer(input_types, constants):
    values = [t.get() for t in input_types]
    for i, value in enumerate(values):
        values[i] = random.choice(constants[type(value)] + [value])
    return values

def main(args):
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
    for i in range(args.type_search_limit):
        types = _type.search(runner, num_args, profiler.line_and_vars)
        if types not in type_candidates:
            type_candidates.append(types)
    type_candidates.sort()
    type_candidates = type_candidates[:args.num_type_candidates]
    print("{} type candidates found.".format(len(type_candidates)))
    print()

    # Search Input Value with determined input type
    print("Start value search......")
    
    print("{}/{} branches have been covered while searching types.".format(
        len(list(filter(lambda v: v, total_branches.values()))),
        len(total_branches)))
    cannot_cover = set()
    target_branch = next_target(total_branches, cannot_cover)
    invalid_types = []
    while target_branch:
        covered = False
        for types in type_candidates:
            
            if types in invalid_types:
                continue

            # Initialize
            min_fitness = sys.maxsize
            min_fitness_vals = None

            # Select best initial input among the input candidates
            for i in range(args.num_input_candidates):
                vals = initializer(types, profiler.constants)
                
                # for the first attempt
                if i == 0:
                    dependencies = cfg[target_branch[0]]
                    for branch in reversed(dependencies):
                        if total_branches[branch] and _type.check(types, total_branches[branch]):
                            vals = total_branches[branch]
                
                success, result = runner.run(vals)
                if not success:
                    continue
                fit = get_fitness(cfg, target_branch, result)
                if fit < min_fitness:
                    min_fitness, min_fitness_vals = fit, vals

            if args.verbose:
                print("{}\t{}\t{}".format(target_branch, [str(t) for t in types], str(min_fitness_vals)))
            
            if not min_fitness_vals:
                continue
            
            # Start searching
            count = 0
            
            while not covered and not types in invalid_types and count < args.value_search_limit:
                better_neighbour_found = False
                neighbours = get_neighbours(deepcopy(min_fitness_vals), 1, args.float_amplitude)
                random.shuffle(neighbours)
                neighbours = neighbours[:args.neighbours_limit]
                vals, fits = [], []
                for v in neighbours:
                    if v == min_fitness_vals:
                        continue
                    success, result = runner.run(v)
                    if not success:
                        error_type, error_info = result
                        if error_type == TypeError or error_type == MyError:
                            invalid_types.append(types)
                            break
                        continue
                    fit = get_fitness(cfg, target_branch, result)
                    vals.append(v)
                    fits.append(fit)
                    if total_branches[target_branch]:
                        print("{}/{} branches have been covered.".format(
                            len(list(filter(lambda v: v, total_branches.values()))),
                            len(total_branches)))
                        covered = True
                        break
                
                count += 1

                # Random Ascent
                if fits and vals and min(fits) <= min_fitness:
                    best_neighbour_index = random.choice(list(map(lambda t: t[0], filter(lambda t: t[1] == min(fits), enumerate(fits)))))
                    min_fitness = fits[best_neighbour_index]
                    min_fitness_vals = vals[best_neighbour_index]
                    if args.verbose:
                        print("best:", min_fitness, min_fitness_vals)
                else:
                    continue

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
            #test_input_str = ', '.join(map(lambda i: str(i), total_branches[branch_T]))
            print("{}: {}".format(str(n)+'T', total_branches[branch_T]))
        else:
            print("{}: -".format(str(n)+'T'))

        branch_F = (n, False)
        if total_branches[branch_F]:
            #test_input_str = ', '.join(map(lambda i: str(i), total_branches[branch_F]))
            print("{}: {}".format(str(n)+'F', total_branches[branch_F]))
        else:
            print("{}: -".format(str(n)+'F'))

    print("Done.")
    print("============================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Coverage Measurement Tool')
    parser.add_argument('sourcefile', type=str, help='a file path to instrument')
    parser.add_argument('function', type=str, help='target function name')
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument('--type_search_limit', type=int, default=200)
    parser.add_argument('--value_search_limit', type=int, default=1000)
    parser.add_argument('--neighbours_limit', type=int, default=1000)
    parser.add_argument('--num_type_candidates', type=int, default=30)
    parser.add_argument('--num_input_candidates', type=int, default=50)
    parser.add_argument('--float_amplitude', type=float, default=0.0000000001)
    args = parser.parse_args()

    assert args.num_type_candidates <= args.type_search_limit

    main(args)
