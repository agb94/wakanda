def get_fitness(cfg, target_branch, cov_result):
    dependency_chain = cfg[target_branch[0]] + [target_branch]
    cov_result_tuples = list(map(lambda b: b.to_tuple(), cov_result))
    div_point = None
    approach_level = len(dependency_chain)

    for branch in dependency_chain:
        opposite = (branch[0], not branch[1])
        if branch not in cov_result_tuples and opposite in cov_result_tuples:
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
        if report.op == 'Or' or report.op == 'And':
            branch_distance = report.branch_distance[div_point[1]]
            accumulated = list()
            max_depth = 0
            while abs(cov_result[cursor].id) == report.id:
                accumulated.append(cov_result[cursor])
                max_depth = max(cov_result[cursor].depth, max_depth)
                cursor -= 1
            while max_depth > 0:
                distances = list()
                for row in reversed(accumulated):
                    if row.depth == max_depth:
                        distances.append(row.branch_distance[True])
                        del row
                    else:
                        if row.op == 'Or':
                            neg = [distance <= 0 for distance in distances]
                            if neg:
                                row.branch_distance[True] = 0
                                row.branch_distance[False] = float(sum(neg))/len(neg)
                            else:
                                row.branch_distance[True] = float(sum(distances))/len(distances)
                                row.branch_distance[False] = 0
                        elif row.op == 'And':
                            pos = [distance > 0 for distance in distances]
                            if pos:
                                row.branch_distance[True] = float(sum(pos))/len(pos)
                                row.branch_distance[False] = 0
                            else:
                                row.branch_distance[True] = 0
                                row.branch_distance[False] = abs(float(sum(distances))/len(distances))
                max_depth -= 1
        branch_distance = report.branch_distance[div_point[1]]
    else:
        branch_distance = 0
    return approach_level, 1-(1.001)**(-branch_distance)
