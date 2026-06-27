#THEOFANIS BOURAIMIS 4745


import math
import sys

LEAF_SIZE = 20
NON_LEAF_SIZE = 36
CAPACITY = 1024

class Node:
    def __init__(self,id):
        self.id = id
        self.entries = []

    def get_mbr_from_node(self):
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        for entry in self.entries:
            min_x = min(min_x, entry[1][0])
            min_y = min(min_y, entry[1][1])
            max_x = max(max_x, entry[1][2])
            max_y = max(max_y, entry[1][3])
        
        return (min_x, min_y, max_x, max_y)
    
    def add_entry(self, entry):
        self.entries.append(entry)
    
    def area(self):
        area = 0
        for entry in self.entries:
            area += (entry[1][2] - entry[1][0]) * (entry[1][3] - entry[1][1])
        return area/len(self.entries)

    def print_node_stats(self):
        kids = ''
        for entry in self.entries:
            entry = f", ({entry[0]}, [{entry[1][0]},{entry[1][1]},{entry[1][2]},{entry[1][3]}])"
            kids += entry
        return f"{self.id}, {len(self.entries)}, 1{kids}"

class LeafNode:
    def __init__(self, id,entries):
        self.id = id
        self.entries = entries

    def get_mbr_from_node(self):
        min_x = min(entry[1][0] for entry in self.entries)
        max_x = max(entry[1][0] for entry in self.entries)
        min_y = min(entry[1][1] for entry in self.entries)
        max_y = max(entry[1][1] for entry in self.entries)
        return (min_x, min_y, max_x, max_y)
    
    def area(self):
        return 0

    def print_node_stats(self):
        kids = ''
        for entry in self.entries:
            entry = f", ({entry[0]}, ({entry[1][0]},{entry[1][1]}))"
            kids += entry
        return f"{self.id}, {len(self.entries)}, 0{kids}"

class RTree:
    def __init__(self, cap_per_node):
        self.root = None
        self.cap_per_node = cap_per_node
        self.id = 0
        self.children = []
        self.all_nodes = []
        self.leafs = []
        self.nodes_per_level = []
        self.height = 1

    def insert_leaf(self, entries):
        self.children.append(self.getId())
        leaf = LeafNode(self.id,entries=entries)
        self.all_nodes.append(leaf)
        self.leafs.append(leaf)

        self.increment()

    def insert_nodes(self):
        buffer = []
        child_indexes = [self.children[i: i + self.cap_per_node] for i in range(0, len(self.children), self.cap_per_node)]
        current_level_nodes = []
        for chunk in child_indexes:
            buffer.append(self.getId())
            new_node = Node(self.getId())
            
            for id in chunk:
                child = self.all_nodes[id]  
                new_node.add_entry((child.id, child.get_mbr_from_node()))  

            self.all_nodes.append(new_node)
            self.increment()
            current_level_nodes.append(new_node)
        
        
        self.children = buffer
        return current_level_nodes

    def create_upper_levels(self):
        x = math.ceil(len(self.children) / self.cap_per_node)
        if x == 1:
            
            self.root = Node(self.getId())
            for idx in self.children:
                child = self.all_nodes[idx]
                self.root.add_entry((child.id, child.get_mbr_from_node()))

            self.nodes_per_level.append([self.root])

            self.all_nodes.append(self.root)
            self.height += 1
            
        else:
            self.nodes_per_level.append(self.insert_nodes())
            self.height += 1
            self.create_upper_levels()

    def calculate_avg_area_per_level(self,level):
        areas = 0
        for node in level:
            areas += node.area()
        
        return areas / len(level)

    def write_file(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self.root.id) + '\n')
            for node in self.all_nodes:
                f.write(node.print_node_stats() + '\n')

    def print_rtree_stats(self):
        for i,level in enumerate(self.nodes_per_level):
            area = self.calculate_avg_area_per_level(level)
            print(f"Level: {i} | Number of Nodes: {len(level)} | Average Area: {area}")
            
    def getId(self):
        return self.id
    
    def increment(self):
        self.id += 1

def read_data(filename):
    with open(filename, "r") as f:
        r = int(f.readline())
        points = []
        for line_number,line in enumerate(f,start=1):
            x, y = map(float, line.split())
            points.append([line_number,(x, y)])
    return r, points

def calculate_entries_per_node():
    return math.floor(CAPACITY/NON_LEAF_SIZE)

def sort_by_x(points):
    return sorted(points, key=lambda point: point[1][0])

def calculate_layers(r):
    n = math.floor(CAPACITY/LEAF_SIZE)
    P = math.ceil(r/n)

    S = math.ceil(math.sqrt(P))
    print(f"n = {n}")
    print(f"P = {P}")
    print(f"S = {S}")
    return S

def create_layers(r, S):
    n = math.floor(CAPACITY/LEAF_SIZE)
    layer_size = S*n

    return [points[i:i + layer_size] for i in range(0, r, layer_size)]

def sort_slices_by_y(slices):
  for slice in slices:
    slice.sort(key=lambda point: point[1][1])  # sort by y-coordinate
  return slices

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_rtree_str.py rtree_file.txt")
        sys.exit(1)

    rtree_file = sys.argv[1]
    

    r, points = read_data('Beijing_restaurants.txt')
    points = sort_by_x(points)

    S = calculate_layers(r)
    slices = create_layers(r,S)
    slices = sort_slices_by_y(slices)
    n = math.floor(CAPACITY/LEAF_SIZE)
    cap_per_node = calculate_entries_per_node()
    tree = RTree(cap_per_node)
    for slice in slices:
        for i in range(0, len(slice), n):
            tree.insert_leaf(slice[i: i + n])
    tree.nodes_per_level.append(tree.leafs)
    tree.create_upper_levels()
    tree.print_rtree_stats()
    tree.write_file(rtree_file)