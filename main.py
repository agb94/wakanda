from covgen.profiler import Profiler
from covgen.control_dependency_analyzer import get_cfg
from covgen.fitness_calculator import get_fitness
import argparse
import importlib
import os

def run(function, input_value, total_branches, timeout=5):
    import signal

    class Branch:
        def __init__(self, branch_id: int, predicate_result: bool, op: str, branch_distance: int):
            self.id = branch_id
            self.predicate_result = predicate_result
            self.op = op
            self.branch_distance = branch_distance
        
        def __str__(self):
            return "{}\t{}\t{}\t{}".format(self.id, self.predicate_result, self.op, self.branch_distance)

        def to_tuple(self):
            return (self.id, self.predicate_result)

        @classmethod
        def parse_line(cls, l: str):
            cols = l.strip().split('\t')
            return cls(int(cols[0]), bool(int(cols[1])), cols[2], { True: int(cols[3]), False: int(cols[4]) })
   
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
    except Exception:
        return None
    cov_result = read_coverage_report()
    for b in cov_result:
        total_branches[b.to_tuple()] = tuple(input_value)
    return cov_result

def next_target(branches, cannot_cover):
    not_covered = list(filter(lambda b: not b[1] and not b[0] in cannot_cover, branches.items()))
    if not_covered:
        return not_covered[0][0]
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Coverage Measurement Tool')
    parser.add_argument('sourcefile', type=str, help='a file path to instrument')
    parser.add_argument('function', type=str, help='target function name')
    args = parser.parse_args()
    
    profiler = Profiler()
    inst_sourcefile = os.path.join(
        os.path.dirname(args.sourcefile),
        'inst_' + os.path.basename(args.sourcefile))
    function_node, total_branches = profiler.instrument(args.sourcefile, inst_sourcefile, args.function)
    cfg = get_cfg(function_node, profiler.branches)
    target_module = importlib.import_module(inst_sourcefile.rstrip('.py').replace('/', '.'))
    
    print (total_branches)
    cov_report = run(target_module.__dict__[args.function], [1,2,3], total_branches)
    print (total_branches)
    
    cannot_cover=set()
    target_branch = next_target(total_branches, cannot_cover)
    fitness = get_fitness(cfg, target_branch, cov_report)
    print (fitness)