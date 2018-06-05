from .type import MyError, POSSIBLE_TYPES, _type
import signal
import sys
import traceback
import re

class CovResult:
    def __init__(self, branch_id: int, depth: int, predicate_result: bool,
                 op: str, branch_distance: int):
        self.id = branch_id
        self.depth = depth
        self.predicate_result = predicate_result
        self.op = op
        self.branch_distance = branch_distance

    def __str__(self):
        return "{}\t{}\t{}\t{}\t{}".format(self.id, self.depth,
                                           self.predicate_result, self.op,
                                           self.branch_distance)

    def to_branch(self):
        return (self.id, self.predicate_result)

    @classmethod
    def parse_line(cls, l: str):
        cols = l.strip().split('\t')
        return cls(
            int(cols[0]),
            int(cols[1]),
            bool(int(cols[2])), cols[3],
            {True: float(cols[4]),
             False: float(cols[5])})
    
    @staticmethod
    def clear():
        open('.cov', 'w').close()

    @staticmethod
    def read():
        cov_results = list()
        with open('.cov', 'r') as cov_report:
            for l in cov_report:
                result = l.strip().split('\t')
                cov_results.append(CovResult.parse_line(l))
        return cov_results

class Runner:
    def __init__(self, function, total_branches):
        self.function = function
        self.total_branches = total_branches

    def run(self, input_value, timeout=5):
        def handler(signum, frame):
            raise Exception("end of time")

        CovResult.clear()

        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout)
        try:
            self.function(*input_value)
        except Exception as e:
            if type(e) is TypeError:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                for elem in traceback.format_exception(exc_type, exc_value, exc_traceback):
                    if self.function.__name__ in elem:
                        lineno = int(elem.split(',')[1].strip().split()[-1])
                        break
                types = list(filter(lambda s: "'{}'".format(s.__name__) in str(exc_value), POSSIBLE_TYPES))
                return (False, (TypeError, (lineno, types)))
            elif type(e) is IndexError:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                for elem in traceback.format_exception(exc_type, exc_value, exc_traceback):
                    if self.function.__name__ in elem:
                        lineno = int(elem.split(',')[1].strip().split()[-1])
                        p = re.compile("\[(\d+)\]")
                        indexes = list(map(lambda i: int(i), p.findall(elem)))
                        break
                return (False, (IndexError, (lineno, indexes)))
            elif type(e) is MyError:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                for elem in traceback.format_exception(exc_type, exc_value, exc_traceback):
                    if self.function.__name__ in elem:
                        lineno = int(elem.split(',')[1].strip().split()[-1])
                        break
                type_a = _type.str_to_type_class(str(e.type_a).split("'")[1])
                type_b = _type.str_to_type_class(str(e.type_b).split("'")[1])
                return (False, (MyError, (lineno, [type_a, type_b])))
            else:
                return (False, (type(e), e))
        cov_results = CovResult.read()
        for cov_result in cov_results:
            branch = cov_result.to_branch()
            if branch[0] > 0:
                self.total_branches[branch] = tuple(input_value)
        return (True, cov_results)
