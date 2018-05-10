import itertools
import ast
import astor

class Profiler(ast.NodeTransformer):
    def __init__(self):
        super()
        self.branches = dict()
        self.branch_id = 1

    def visit_predicate(self, expr_node):
        if isinstance(expr_node, ast.Compare):
            if len(expr_node.ops) > 1:
                left_node = ast.Compare(
                    left=expr_node.left,
                    ops=expr_node.ops[:-1],
                    comparators=expr_node.comparators[:-1]
                )
            else:
                left_node = expr_node.left
            expr_node = ast.Call(
                func = ast.Attribute(value = ast.Name(id='covw', ctx=ast.Load()), attr='comparison', ctx=ast.Load()),
                args=[ast.Num(n = self.branch_id), ast.Str(s = expr_node.ops[-1].__class__.__name__), left_node, expr_node.comparators[-1]],
                keywords=[])
        elif isinstance(expr_node, ast.BoolOp):
            for i, value in enumerate(expr_node.values):
                expr_node.values[i] = self.visit_predicate(value)
            expr_node = ast.Call(
                func = ast.Attribute(value = ast.Name(id='covw', ctx=ast.Load()), attr='boolop', ctx=ast.Load()),
                args=[ast.Num(n = self.branch_id), ast.Str(s = expr_node.op.__class__.__name__), ast.List(elts=expr_node.values, ctx=ast.Load())],
                keywords=[])
        elif isinstance(expr_node, ast.Name) or isinstance(expr_node, ast.Call):
            expr_node = ast.Call(
                func = ast.Attribute(value = ast.Name(id='covw', ctx=ast.Load()), attr='value', ctx=ast.Load()),
                args=[ast.Num(n = self.branch_id), expr_node],
                keywords=[])
        else:
            raise Exception("Unsupported Branch Predicate")
        return expr_node

    def visit_branch_node(self, node):
        expr_node = node.test
        expr_node = self.visit_predicate(expr_node)
        self.branches[node] = self.branch_id
        self.branch_id += 1
        node.test = expr_node
        self.generic_visit(node)
        return ast.fix_missing_locations(node)

    def visit_If(self, node):
        return self.visit_branch_node(node)
    
    def visit_While(self, node):
        return self.visit_branch_node(node)
    
    def visit_For(self, node):
        iter_node = ast.Call(
            func = ast.Attribute(value = ast.Name(id='covw', ctx=ast.Load()), attr='iter', ctx=ast.Load()),
            args=[ast.Num(n = self.branch_id), node.iter],
            keywords=[])
        self.branches[node] = self.branch_id
        self.branch_id += 1
        node.iter = iter_node
        self.generic_visit(node)
        return ast.fix_missing_locations(node)
    
    def collect_int_constants(self, node):
        self.int_constants = set()
        def visit_all_attr(node):
            if not hasattr(node, '__dict__'):
                return
            if isinstance(node, ast.Num):
                if isinstance(node.n, int):
                    self.int_constants.add(node.n)
                return
            node_vars = vars(node)
            for k in node_vars:
                if isinstance(node_vars[k], list):
                    for stmt in node_vars[k]:
                        visit_all_attr(stmt)
                else:
                    visit_all_attr(node_vars[k])
        visit_all_attr(node)
        return self.int_constants

    def instrument(self, sourcefile, inst_sourcefile, function):
        def get_source(path):
            with open(path) as source_file:
                return source_file.read()

        source = get_source(sourcefile)
        root = ast.parse(source)

        # Insert 'import covgen.wrapper as covw' in front of the file
        import_node = ast.Import(names=[ast.alias(name='covgen.wrapper', asname='covw')]) 
        root.body.insert(0, import_node)
        ast.fix_missing_locations(root)

        function_node = None
        for stmt in root.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == function:
                function_node = stmt
                break
        assert function_node
        
        self.collect_int_constants(function_node)
        self.visit(function_node)
        total_branches = { k: None for k in list(itertools.product(range(1, self.branch_id), [True, False])) }

        with open(inst_sourcefile, 'w') as instrumented:
            instrumented.write(astor.to_source(root))
        
        return function_node, total_branches
