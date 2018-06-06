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

def next_target(branches, cannot_cover):
    not_covered = list(
        filter(lambda b: not b[1] and not b[0] in cannot_cover,
               branches.items()))
    if not_covered:
        return not_covered[0][0]
    else:
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Coverage Measurement Tool')
    parser.add_argument(
        'sourcefile', type=str, help='a file path to instrument')
    parser.add_argument('function', type=str, help='target function name')
    args = parser.parse_args()

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
    runner = Runner(target_function, total_branches)

    # Search Input Type
    num_args = len(function_node.args.args)
    types = _type.search(runner, num_args, profiler.line_and_vars)
    print("type: ", [str(t) for t in types])
    print("init value: ", [t.get() for t in types])


    # Search Input Value with determined input type
    print("\nValue Search")
    print(total_branches)
    
    vals = [t.get() for t in types]
    #vals = [0, 0, 0]

    cannot_cover = set()
    target_branch = next_target(total_branches, cannot_cover)
    while target_branch:
        covered = False

        min_fitness = 999999999999
        min_fitness_vals = vals
        count = 0

        while not covered:
            neighbours = get_neighbours(deepcopy(min_fitness_vals), 1)
            count += 1
            print(count)
            if count > 10000:
                cannot_cover.add(target_branch)
                break

            for v in neighbours:
                success, result = runner.run(v)
                if not success:
                    continue
                fitness = get_fitness(cfg, target_branch, result)
                if fitness[0] + fitness[1] < min_fitness:
                    min_fitness = fitness[0] + fitness[1]
                    min_fitness_vals = v
                
                if total_branches[target_branch]:
                    covered = True
                    break

        target_branch = next_target(total_branches, cannot_cover)

    print("\nEnd of Value Search")

    # Print Result
    print()
    print(total_branches)
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
