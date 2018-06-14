import ast

# break in for (else)

def get_cfg(root, branch_ids):
    cfg = dict()
    contain_return = set()

    def is_return_inside(nodes):
        return any([ isinstance(node, ast.Return) for node in nodes ])

    def visit_node(parent, node):
        if isinstance(node, ast.If):
            cfg[branch_ids[node]] = sorted(parent)
            for stmt in node.body:
                visit_node(parent + [(branch_ids[node], True)], stmt)
            for stmt in node.orelse:
                visit_node(parent + [(branch_ids[node], False)], stmt)
        elif isinstance(node, ast.While):
            cfg[branch_ids[node]] = sorted(parent)
            for stmt in node.body:
                visit_node(parent + [(branch_ids[node], True)], stmt)
        elif isinstance(node, ast.For):
            cfg[branch_ids[node]] = sorted(parent)
            for stmt in node.body:
                visit_node(parent + [(branch_ids[node], True)], stmt)
            for stmt in node.orelse:
                visit_node(parent, stmt)
        elif isinstance(node, ast.Return):
            if parent:
                contain_return.add(parent[-1])
        else:
            for attr in ['body', 'orelse', 'finalbody']:
                if not hasattr(node, attr):
                    continue
                for stmt in node.__dict__[attr]:
                    visit_node(parent, stmt)
    visit_node([], root)

    for branch in contain_return:
        siblings = list(filter(lambda k: cfg[k] == cfg[branch[0]] and k > branch[0], cfg))
        for sibling in siblings:
            cfg[sibling].append((branch[0], not branch[1]))
    
    for branch in cfg:
        cfg[branch] = sorted(cfg[branch])

    return cfg
