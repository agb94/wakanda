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

import math
import time
import numpy as np


def initializer(input_types, constants):
    values = [t.get() for t in input_types]
    for i, value in enumerate(values):
        values[i] = random.choice([value])
    return values


def get_keys(types):
    res = ''
    for item in types:
        res += str(item)
    return res


def main(args):
    print("INPUT GENERATOR for " + args.sourcefile)
    # Instrument & Get CFG
    profiler = Profiler()
    inst_sourcefile = os.path.join(
        os.path.dirname(args.sourcefile),
        'inst_' + os.path.basename(args.sourcefile))
    function_node, total_branches = profiler.instrument(
        args.sourcefile, inst_sourcefile, args.function)

    print('total branches: ', total_branches)

    # 找到每个条件判断之间的依赖关系
    cfg = get_cfg(function_node, profiler.branches)
    print(cfg)

    # Linux
    target_module = importlib.import_module(os.path.splitext(inst_sourcefile)[0].replace('/', '.'))
    target_function = target_module.__dict__[args.function]

    # Initialize Function Runner
    runner = Runner(target_function, total_branches, timeout=20)

    # Search Input Type
    print("Start type search.......")
    num_args = len(function_node.args.args)
    type_candidates = list()
    print('type search limit: ', args.type_search_limit)
    t1 = time.time()

    for i in range(args.type_search_limit):
        types = _type.search(runner, num_args, profiler.line_and_vars, type_candidates)
        if types and types not in type_candidates:
            type_candidates.append(types)
    type_candidates.sort()
    type_candidates = type_candidates[:args.num_type_candidates]
    print("{} type candidates found.".format(len(type_candidates)))
    print()

    print('run time: %fs' % (time.time() - t1))

    # Search Input Value with determined input type
    print("Start value search......")

    total_branches = deepcopy(runner.total_branch())
    print("{}/{} branches have been covered while searching types.".format(
        len(list(filter(lambda v: v, total_branches.values()))),
        len(total_branches)))

    ans_values = value_search(deepcopy(type_candidates), total_branches, runner, cfg, profiler, islog=False)

    # For testing & comparing
    
    for i in range(100):
        ans_values = value_search(deepcopy(type_candidates), deepcopy(total_branches), runner, cfg, profiler)


def value_search(type_candidates, total_branches, runner, cfg, profiler, islog=True):

    all_target_branch = [i[0] for i in total_branches.items()]
    runner.clear_total_branch()

    # Set original score for each type combination
    type_score_dict_item, type_score_dict = {}, {}
    for types in type_candidates:
        for type_item in types:
            type_score_dict_item.update({str(type_item): len(all_target_branch)})
    score = 0
    for types in type_candidates:
        keys = ''
        for type_item in types:
            score += type_score_dict_item[str(type_item)]
            keys += str(type_item)
        type_score_dict.update({keys: score})

    ans_values, ans_covered = [], 0
    i, n, count = 0, 0, 0
    all_len = len(deepcopy(type_candidates))

    time_value_search_begin = time.time()
    # Searching
    while n < all_len:
        types = deepcopy(type_candidates[i])
        type_candidates.remove(types)
        type_score_dict.pop(get_keys(types))
        '''
        print('searching types: ')
        for type_item in types:
            print(type_item.this)
        n += 1
        '''
        invalid_flag = False
        values, min_fitness = generate_parent(types, profiler, runner)

        runner.clear_total_branch()
        success, result = runner.run(values)
        '''
        print('root selected: ', values)
        print("{}/{} branches have been covered".format(
            len(list(filter(lambda v: v, runner.total_branch().values()))),
            len(total_branches)))
        print(runner.total_branch())
        '''
        not_covered = list(filter(lambda v: v[1] is None, runner.total_branch().items()))

        type_res, type_fit = [], []
        type_res.append(values)
        type_fit.append(min_fitness)

        # print(values)

        t = 100
        delta = 0.98
        threshold = 0.15
        while not_covered and t > threshold:
            neighbours = get_neighbours(deepcopy(values), 1, args.float_amplitude)
            random.shuffle(neighbours)
            neighbours = neighbours[:args.neighbours_limit]
            temp_vals, temp_fits = [], []
            runner.clear_total_branch()
            for neighbour in neighbours:
                if neighbour == values:
                    continue
                success, result = runner.run(neighbour)
                if not success:
                    error_type, error_info = result
                    if error_type == TypeError or error_type == MyError:
                        invalid_flag = True
                        # print('invalid types!')
                        break
                    continue
                fit = 0
                for target in not_covered:
                    fit += get_fitness(cfg, target[0], result)
                temp_vals.append(neighbour)
                temp_fits.append(fit / len(not_covered))

            if invalid_flag:
                break

            # Simulated Annealing
            if temp_fits and temp_vals:
                best_neighbour_idx = random.choice(
                    list(map(lambda v: v[0], filter(lambda v: v[1] == min(temp_fits), enumerate(temp_fits))))
                )
                if min(temp_fits) <= min_fitness:
                    min_fitness = temp_fits[best_neighbour_idx]
                    values = temp_vals[best_neighbour_idx]
                else:
                    delta_f = abs(min(temp_fits) - min_fitness)
                    ran = random.uniform(0, 1)
                    if ran < math.exp(-delta_f / t):
                        min_fitness = temp_fits[best_neighbour_idx]
                        values = temp_vals[best_neighbour_idx]
                t *= delta

            runner.clear_total_branch()
            for val in type_res:
                runner.run(val)
            runner.run(values)
            ori_len = len(not_covered)
            not_covered = list(filter(lambda v: v[1] is None, runner.total_branch().items()))
            if len(not_covered) < ori_len:
                type_res.append(values)
                type_fit.append(min_fitness)

            count += 1

        if len(not_covered) == 0:
            # print('found!')
            ans_values = type_res
            ans_covered = len(all_target_branch) - len(not_covered)
            break
        elif len(all_target_branch) - len(not_covered) >= ans_covered:
            ans_covered = len(all_target_branch) - len(not_covered)
            ans_values = type_res

        if count >= args.value_search_limit or not type_candidates:
            break

        type_score = len(not_covered)
        for type_item in types:
            type_score_dict_item[str(type_item)] = (type_score + type_score_dict_item[str(type_item)]) / 2

        # print(type_score_dict_item)
        # Update scores
        temp_score = []
        for types in type_candidates:
            keys = get_keys(types)
            score = 0
            for type_item in types:
                score += type_score_dict_item[str(type_item)]
            type_score_dict[keys] = min(type_score_dict[keys], score)
            if score > type_score_dict[keys]:
                ran = random.uniform(0, 1)
                if ran <= 0.2:
                    type_score_dict[keys] = score
            temp_score.append(type_score_dict[keys])

        array_temp_score = np.array(temp_score)
        type_candidates = np.array(type_candidates)[array_temp_score.argsort()].tolist()
        
        i = random.choice(list(map(lambda v: v[0], filter(lambda v: array_temp_score[v[0]] == min(array_temp_score),
                                                          enumerate(type_candidates)))))

    time_value_search = time.time() - time_value_search_begin

    # Print Results
    print('Search Over!')
    runner.clear_total_branch()
    for val in ans_values:
        runner.run(val)
    total_branches = runner.total_branch()
    num_branch = len(total_branches)
    for n in range(1, int(num_branch / 2) + 1):
        branch_T = (n, True)
        if total_branches[branch_T]:
            # test_input_str = ', '.join(map(lambda i: str(i), total_branches[branch_T]))
            print("{}: {}".format(str(n) + 'T', total_branches[branch_T]))
        else:
            print("{}: -".format(str(n) + 'T'))

        branch_F = (n, False)
        if total_branches[branch_F]:
            # test_input_str = ', '.join(map(lambda i: str(i), total_branches[branch_F]))
            print("{}: {}".format(str(n) + 'F', total_branches[branch_F]))
        else:
            print("{}: -".format(str(n) + 'F'))

    print('found values covering %d branches' % ans_covered)
    print(ans_values)

    if islog:
        f1 = open('search_value_modified_anscovered.txt', 'a+')
        f2 = open('search_value_modified_time.txt', 'a+')
        f1.write(str(ans_covered) + ' ' + str(num_branch) + ' ' + str(len(ans_values)) + '\n')
        f2.write(str(time_value_search) + '\n')
        f1.close()
        f2.close()

    return ans_values


def generate_parent(types, profiler, runner):
    # Generate the first case to begin with
    values, fits = [], []
    for i in range(args.num_input_candidates):
        vals = initializer(types, profiler.constants)
        if vals not in values:
            runner.clear_total_branch()
            success, result = runner.run(vals)
            if not success:
                continue
            values.append(vals)
            not_covered = list(filter(lambda v: v[1] is None, runner.total_branch().items()))
            fits.append(len(not_covered))
    res = np.array(fits)
    res_index = np.argsort(res)
    res = res[res_index]
    val = np.array(values)
    return random.choice([values[res_index[0]], val[res_index[0]].tolist()]), res[0]


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
