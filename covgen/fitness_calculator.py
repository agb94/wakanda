def get_fitness(cfg, target_branch, cov_result):
    dependency_chain = cfg[target_branch[0]] + [target_branch]
    covered_branches = list(map(lambda b: b.to_branch(), cov_result))
    div_point = None
    approach_level = len(dependency_chain)

    for branch in dependency_chain:
        opposite = (branch[0], not branch[1])
        if branch not in covered_branches and opposite in covered_branches:
            # Divergence Point
            div_point = branch
            break
        approach_level -= 1
    
    if div_point:
        cursor = -1
        report = None
        for i in reversed(range(len(cov_result))):
            if cov_result[i].id == div_point[0] and cov_result[i].predicate_result != div_point[1]:
                cursor = i
                report = cov_result[i]
                break
        if report.op == 'Or' or report.op == 'And' or report.op == 'Not':
            branch_distance = report.branch_distance[div_point[1]]
            accumulated = list()
            max_depth = 0
            while cursor >= 0 and abs(cov_result[cursor].id) == report.id:
                accumulated.append(cov_result[cursor])
                max_depth = max(cov_result[cursor].depth, max_depth)
                cursor -= 1
            while max_depth > 0:
                distances = list()
                for row in reversed(accumulated):
                    if row.depth == max_depth:
                        distances.append(row.branch_distance)
                    elif row.depth == max_depth - 1:
                        if row.op == 'Or':
                            neg = list(filter(lambda d: d[True] <= 0, distances))
                            if neg:
                                # Evaluated to True
                                row.branch_distance[True] = 0
                                # every subexpression must be False
                                row.branch_distance[False] = float(sum(map(lambda d: abs(d[False]), neg)))/len(neg)
                            else:
                                # Evaluated to False
                                row.branch_distance[False] = 0
                                # At least one subexpression must be True
                                # Use both min and average
                                row.branch_distance[True] = min(map(lambda d: d[True], distances)) / 2
                                row.branch_distance[True] += float(sum(map(lambda d: d[True], distances)))/len(distances) / 2
                        elif row.op == 'And':
                            pos = list(filter(lambda d: d[True] > 0, distances))
                            if pos:
                                # Evaluated to False
                                row.branch_distance[False] = 0
                                # every subexpression must be True
                                row.branch_distance[True] = float(sum(map(lambda d: d[True], pos)))/len(pos)
                            else:
                                # Evaluated to True
                                row.branch_distance[True] = 0
                                # At least one subexpression must be False
                                # Use both min and average
                                row.branch_distance[False] = min(map(lambda d: abs(d[False]), distances)) / 2
                                row.branch_distance[False] += float(sum(map(lambda d: abs(d[False]), distances)))/len(distances) / 2
                        elif row.op == 'Not':
                            assert len(distances) == 1
                            row.branch_distance[True] = distances[0][False]
                            row.branch_distance[False] = distances[0][True]
                        distances = list()
                max_depth -= 1
        branch_distance = report.branch_distance[div_point[1]]
    else:
        branch_distance = 0
    return approach_level + (1-(1.001)**(-branch_distance))
