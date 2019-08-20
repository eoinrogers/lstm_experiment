import new_cluster as nc

def decorate_links(links): 
    return [(item, i) for i, item in enumerate(links)]

def levinshtein(one, two): 
    # m indexes over one, n over two
    # so indexes are of the form [n][m]
    m = len(one)
    n = len(two)
    matrix = [[0 for i in range(m)] for j in range(n)]
    for i in range(1, n): matrix[i][0] = i
    for i in range(1, m): matrix[0][i] = i
    for j in range(1, m): 
        for i in range(1, n): 
            subst_cost = 0 if one[j] == two[i] else 1
            choices = [matrix[i-1][j] + 1, matrix[i][j-1] + 1, matrix[i-1][j-1] + subst_cost]
            print(i, j, choices, matrix)
            matrix[i][j] = min(choices)
    print(matrix)
    return matrix[-1][-1]

def similarity(one, two): 
    ed = levinshtein(one[0], two[0])
    return ed #/ max(len(one[0]), len(two[0]))

def cluster_using_centroids(centroids, links): 
    output = [[] for i in centroids]
    for item in links: 
        distances = [similarity(item, i) for i in centroids]
        index = distances.index(min(distances))
        output[index].append(item)
    return output

def get_centroids(clusters): 
    output = []
    for cluster in clusters: 
        similarities = [sum([similarity(i, j) for i in cluster]) for j in cluster]
        index = similarities.index(min(similarities))
        output.append(cluster[index])
    return output

g = nc.load_ground_labels('k3_ground_non_interleaved.txt')
train = open('test_data/ptb.train.txt', 'r')
valid = open('test_data/ptb.valid.txt', 'r')    
test = open('test_data/ptb.test.txt', 'r')
d = [item for item in train.read().strip().split()] + [item for item in valid.read().strip().split()] + [item for item in test.read().strip().split()]
d = nc.combine_discrete(d)
train.close(); valid.close(); test.close()
#f = compute_freq(d)

l = nc.load_linkset('/media/eoin/BigDisk/lstm/outputs/lstm_linkset.txt')
l2 = [[d[i] for i in range(min(link), max(link)+1)] for idx, link in enumerate(l)]

l2 = decorate_links(l2)
print(l2)


print(similarity(l2[8], l2[7]), l2[8], l2[7])

centroids = l2[:7]

clusters = cluster_using_centroids(centroids, l2)
print(clusters, [len(c) for c in clusters]);exit()
print(get_centroids(clusters))
