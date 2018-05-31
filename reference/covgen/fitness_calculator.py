def get_fitness(cfg, target_branch, cov_result):
    dependency_chain = cfg[target_branch[0]] + [target_branch]
    cov_result_tuples = list(map(lambda b: b.to_tuple(), cov_result))
    div_point = None
    approach_level = len(dependency_chain)
    for b in dependency_chain:
        not_b = (b[0], not b[1])
        if b not in cov_result_tuples and not_b in cov_result_tuples:
            div_point = b
            break
        approach_level -= 1
    if div_point:
        for i, t in enumerate(cov_result_tuples):
            if t == (div_point[0], not div_point[1]):
                branch_distance = cov_result[i].branch_distance[div_point[1]]
                break
    else:
        branch_distance = 0
    return -approach_level, -1+(1.001)**(-branch_distance)
