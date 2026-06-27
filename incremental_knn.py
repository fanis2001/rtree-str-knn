#THEOFANIS BOURAIMIS 4745

import math
import heapq
import re
import sys

nearest_neighbors = []

class Node:
    def __init__(self, id, is_leaf, entries):
        self.id = id
        self.is_leaf = is_leaf
        self.entries = entries

class RTree:
    def __init__(self, root, all_nodes):
        self.root = root
        self.all_nodes = all_nodes

def create_nodes(prefix,entries):
    if int(prefix[2]) == 1:
        leaf = Node(prefix[0],1,entries)
        return leaf
    elif int(prefix[2]) == 0:
        node = Node(prefix[0],0,entries)
        return node

def extract_entries(entry):
    indexes = []
    start_index = 0
    while True:
        index = entry.find('),', start_index)
        
        if index == -1:
            break
        indexes.append(index)
        start_index = index + len('),')
    new_entry = entry
    
    for index in indexes:
        new_entry = new_entry[:index+1] + '|' + new_entry[index+2:]
        
    new_entry = new_entry.replace(" ","").rstrip('\n')
    listed_entry = new_entry.split("|")
    tuple_list = [eval(item) for item in listed_entry]
    #print(new_entry)
    return tuple_list

def min_dist_of_points(q,point):
    x1,y1 = q
    x2,y2 = point
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def mindist(point, mbr):
    point_x, point_y = point
    min_x = float(mbr[0])
    min_y =float(mbr[1])
    max_x =float(mbr[2])
    max_y = float(mbr[3])

    if point_x < min_x:
        # Το σημείο είναι αριστερά του MBR
        distance_x = min_x - point_x
    elif point_x > max_x:
        # Το σημείο είναι δεξιά του MBR
        distance_x = point_x - max_x
    else:
        # Το σημείο βρίσκεται εντός του MBR στον άξονα x
        distance_x = 0

    if point_y < min_y:
        # Το σημείο είναι κάτω από το MBR
        distance_y = min_y - point_y
    elif point_y > max_y:
        # Το σημείο είναι πάνω από το MBR
        distance_y = point_y - max_y
    else:
        # Το σημείο βρίσκεται εντός του MBR στον άξονα y
        distance_y = 0

    # Επιστροφή της Ευκλείδειας απόστασης
    return math.sqrt(distance_x ** 2 + distance_y ** 2)

def read_specific_line(filename, line_number):
    
    with open(filename, 'r') as file:
        lines = file.readlines()
        if 0 < line_number <= len(lines):
            return lines[line_number - 1].strip()
        else:
            return "Η γραμμή δεν υπάρχει στο αρχείο."


def bfs(Q):
    global nearest_neighbors
    while True:
        dist,node_id,is_leaf = heapq.heappop(Q)
            
        
        if is_leaf==0:
            print(Q)
            nearest_neighbors.append((node_id,dist))
            coordinates = read_specific_line('Beijing_restaurants.txt',node_id)
            print(f"({node_id}, {coordinates})")
            return Q
        else:
            node = rtree.all_nodes[node_id]
            for entry in node.entries:
                if node.is_leaf==0:
                    heapq.heappush(Q, (min_dist_of_points(q, entry[1]), entry[0], node.is_leaf))
                else:
                    heapq.heappush(Q, (mindist(q, entry[1]), entry[0], node.is_leaf))        

def incremental_nearest_neighbors(q, k, rtree):
    Q = []
    for entries in rtree.root.entries: 
        heapq.heappush(Q, (mindist(q, entries[1]), entries[0], rtree.root.is_leaf))
        
    while len(nearest_neighbors) != k:
        Q = bfs(Q)
    Q = bfs(Q)
    Q = bfs(Q)
    
    return nearest_neighbors
    
def read_rtree(filename):
    all_nodes = []
    with open(filename, "r") as f:
        root_id = f.readline().rstrip('\n')
        lines = f.readlines()

    for line in lines:
        prefix = line.split(',', 3)[:3]
        entry = line.split(',', 3)[3]
        #print(entry)
        listed_entries = extract_entries(entry)
        node = create_nodes(prefix, listed_entries)
        all_nodes.append(node)

    for node in all_nodes:
        if int(node.id) == int(root_id):
            root = RTree(node, all_nodes)
            break

    return root

if __name__ == "__main__":

    if len(sys.argv) != 5:
        print("Usage: python incremental_knn.py rtree_file.txt q_x q_y k")
        sys.exit(1)

    rtree_file = sys.argv[1]
    q_x = float(sys.argv[2])
    q_y = float(sys.argv[3])
    k = int(sys.argv[4])

    q = (q_x, q_y)

    rtree = read_rtree(rtree_file)
    
    neighbors = incremental_nearest_neighbors(q, k, rtree)
    
    for i,neighbor in enumerate(neighbors,start=1):
        print(f"Neighbor {i}: {neighbor}")
    