from deap import base
from deap import creator
from deap import tools
from deap.tools import cxOnePoint
from covgen.profiler import Profiler
from covgen.control_dependency_analyzer import get_cfg
from covgen.fitness_calculator import get_fitness
import argparse
import ast
import astor
import importlib
import itertools
import random
import inspect
import sys

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

def around_constants(constants, sigma):
    return int(random.gauss(random.choice(list(constants)), sigma))

def mut_gaussian_int(parent, mu, sigma, indpb):
    from deap.tools import mutGaussian
    mutant = mutGaussian(parent, mu, sigma, indpb)
    for i in range(len(mutant[0])):
        mutant[0][i] = int(mutant[0][i])
    return mutant


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Coverage Measurement Tool')
    parser.add_argument('sourcefile', type=str, help='a file path to instrument')
    parser.add_argument('function', type=str, help='target function name')
    parser.add_argument('-p', type=int, help='Population Size', default=100)
    parser.add_argument('-g', type=int, help='Generation Limit', default=100)
    parser.add_argument('-t', type=int, help='Time Limit (s)', default=5)
    parser.add_argument('-c', type=float, help='Crossover Probability', default=0.3)
    parser.add_argument('-m', type=float, help='Mutation Probability', default=0.6)

    args = parser.parse_args()
    
    # Constraints on the arguments
    assert args.p > 1
    assert args.g > 0
    assert args.t > 0
    assert args.c >= 0 and args.c <= 1
    assert args.m >= 0 and args.m <= 1

    profiler = Profiler()
    function_node, total_branches = profiler.instrument(args.sourcefile, 'inst_' + args.sourcefile, args.function)
    cfg = get_cfg(function_node, profiler.branches)
    target_module = importlib.import_module('inst_' + args.sourcefile.rstrip('.py'))

    # Parameter Setting
    DIM = len(inspect.getargspec(target_module.__dict__[args.function]).args)
    POPULATION_SIZE, GENERATION_LIMIT, TIMEOUT = args.p, args.g, args.t
    NUM_ELITES = int(POPULATION_SIZE * 0.05)
    NUM_NEW_POPULATION = int(POPULATION_SIZE * 0.05)
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,1.0))
    creator.create("Individual", list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    
    # Base Population
    toolbox.register("around_constants", around_constants, constants=profiler.int_constants, sigma=10)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.around_constants, DIM)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Random Population (Exploration)
    toolbox.register("attr_rand_int", random.randint, -sys.maxsize-1, sys.maxsize)
    toolbox.register("rand_individual", tools.initRepeat, creator.Individual, toolbox.attr_rand_int, DIM)
    toolbox.register("rand_population", tools.initRepeat, list, toolbox.rand_individual)
    
    # Selection
    toolbox.register("selectBest", tools.selBest)
    toolbox.register("selectTour", tools.selTournament, tournsize=NUM_ELITES)
    
    # CrossOver
    toolbox.register("mate", tools.cxOnePoint)
    
    # Mutation
    toolbox.register("mutate", mut_gaussian_int, mu=0, sigma=100, indpb=1/float(DIM))
    
    cannot_cover=set()
    target_branch = next_target(total_branches, cannot_cover)
    while target_branch:
        generation = 0
        population = toolbox.population(n=POPULATION_SIZE)
        covered = False
        while not covered and generation < GENERATION_LIMIT:
            for ind in population:
                cov_report = run(target_module.__dict__[args.function], ind, total_branches, timeout=TIMEOUT)
                if not cov_report:
                    continue
                fitness = get_fitness(cfg, target_branch, cov_report)
                ind.fitness.values = fitness
                if total_branches[target_branch]:
                    covered = True
                    break
            if not covered:
                # Select the next generation individuals
                real_elites = toolbox.selectBest(population, NUM_ELITES)
                offspring = toolbox.selectTour(population, POPULATION_SIZE - NUM_ELITES - NUM_NEW_POPULATION)
                offspring += toolbox.rand_population(n=NUM_NEW_POPULATION)
                
                # Apply crossover and mutation on the offspring
                if DIM > 1:
                    for child1, child2 in zip(offspring[::2], offspring[1::2]):
                        if random.random() < args.c:
                            toolbox.mate(child1, child2)
                            del child1.fitness.values
                            del child2.fitness.values

                for mutant in offspring:
                    if random.random() < args.m:
                        toolbox.mutate(mutant)
                        del mutant.fitness.values

                population[:] = real_elites + offspring
                generation += 1
        if not covered:
            cannot_cover.add(target_branch)
        target_branch = next_target(total_branches, cannot_cover)
    
    # Print Result
    for branch in total_branches:
        branch_str = str(branch[0]) + ('T' if branch[1] else 'F')
        test_input = total_branches[branch] if total_branches[branch] else '-'
        print("{}: {}".format(branch_str, ', '.join(map(lambda i: str(i), test_input))))
