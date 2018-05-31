from covgen.runner import Runner
from covgen.profiler import Profiler
from covgen.control_dependency_analyzer import get_cfg
from covgen.fitness_calculator import get_fitness
from covgen.type import _type
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
    with open(args.sourcefile, 'r') as f:
        print(f.read())
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
    print("===========================================")
