'''
用并查集减少搜索
node_list = [
    {neme: type_name}
    ......
]
'''

class dsu:
    def __init__(self):
        self.father_list = []
        self.node_list = []
        self.rank_list = []
        self.ele_num = 0
    
    def index_of_ele(self, name, type_name):
        ele = { name: type_name }
        idx = -1
        if ele in self.node_list:
            idx = self.node_list.index(ele)
        else:
            idx = self.ele_num
            self.father_list.append(idx)
            self.node_list.append(ele)
            self.rank_list.append(1)
            self.ele_num += 1
        return idx
    
    def dsu_find(self, idx):
        if self.father_list[idx] == idx:
            return idx
        self.father_list[idx] = self.dsu_find(self.father_list[idx])
        return self.father_list[idx]
    
    def dsu_union(self, idx1, idx2):
        f1 = self.dsu_find(idx1)
        f2 = self.dsu_find(idx2)
        if self.rank_list[f1] <= self.rank_list[f2]:
            self.father_list[f1] = f2
        else:
            self.father_list[f2] = f1
        if self.rank_list[f1] == self.rank_list[f2] and f1 != f2:
            self.rank_list[f2] += 1

    def wrapped_dsu_find(self, name, type_name):
        idx = self.index_of_ele(name, type_name)
        return self.dsu_find(idx)

    def wrapped_dsu_union(self, name_1, type_1, name_2, type_2):
        idx_1 = self.index_of_ele(name_1, type_1)
        idx_2 = self.index_of_ele(name_2, type_2)
        self.dsu_union(idx_1, idx_2)

    def clear(self):
        self.father_list = []
        self.node_list = []
        self.rank_list = []
        self.ele_num = 0
