import random, sys, math, integrate

def overlap(one, two, min_type_overlap): 
    count_one = sum([(1 if item in two else 0) for item in one])
    count_two = sum([(1 if item in one else 0) for item in two])
    overlap_one = count_one / len(one)
    overlap_two = count_two / len(two)
    return min(overlap_one, overlap_two) if min_type_overlap else max(overlap_one, overlap_two)

def overlap_clusters(one, two, min_type_overlap=True): 
    if type(one[0]) == list and type(two[0]) == list: # Both inputs are clusters
        sum_overlaps = 0
        for x in one: 
            for y in two: sum_overlaps += overlap(x, y, min_type_overlap)
        return sum_overlaps / (len(one) * len(two))
    elif type(one[0]) == list: # Input one is a cluster
        sum_overlaps = 0
        for x in one: sum_overlaps += overlap(x, two, min_type_overlap)
        return sum_overlaps / len(one)
    elif type(two[0]) == list: # Input two is a cluster
        sum_overlaps = 0
        for y in two: sum_overlaps += overlap(one, y, min_type_overlap)
        return sum_overlaps / len(two)
    return overlap(one, two, min_type_overlap)

def load_linkset(path): 
    output = []
    for line in open(path, 'r'):
        this_link = [int(item.strip()) for item in line.strip().split(',')]
        output.append(this_link)
    return output

def cluster_two(clusters, cluster2links, min_overlap): 
    highest_overlap, idx_one, idx_two, found = 0, 0, 0, False
    for i in range(len(clusters)):
        # Iterate through all pairs of clusters: 
        # find the two with the highest overlap, 
        # but only if the overlap meets the minimum
        # specified. 
        one = clusters[i]
        for j in range(len(clusters)): 
            if i == j: continue
            two = clusters[j]
            ovlp = overlap_clusters(one, two)
            if ovlp >= min_overlap and ovlp > highest_overlap: 
                highest_overlap, idx_one, idx_two, found = ovlp, i, j, True
    if found: 
        # If an overlap meeting the requirements is found, pop the two clusters and links and join then together. 
        print('Found clusters {} and {} with overlap of {}'.format(idx_one, idx_two, highest_overlap))
        new_cluster = clusters.pop(idx_one) + clusters.pop(idx_two if idx_two < idx_one else idx_two-1)
        clusters.append(new_cluster)
        new_cluster_link_mapping = cluster2links.pop(idx_one) + cluster2links.pop(idx_two if idx_two < idx_one else idx_two-1)
        cluster2links.append(new_cluster_link_mapping)
    return clusters, cluster2links

def cluster_two_using_centroids(clusters, cluster2links, centroids, min_overlap): 
    highest_overlap, idx_one, idx_two, found = 0, 0, 0, False
    for i in range(len(centroids)): 
        one = centroids[i]
        for j in range(len(centroids)): 
            if i == j: continue
            two = centroids[j]
            ovlp = overlap_clusters(one, two, True)
            if ovlp >= min_overlap and ovlp > highest_overlap: 
                highest_overlap, idx_one, idx_two, found = ovlp, i, j, True
    if found: 
        print('Found clusters {} and {} with overlap of {}'.format(idx_one, idx_two, highest_overlap))
        new_cluster = clusters.pop(idx_one) + clusters.pop(idx_two if idx_two < idx_one else idx_two-1)
        clusters.append(new_cluster)
        new_cluster_link_mapping = cluster2links.pop(idx_one) + cluster2links.pop(idx_two if idx_two < idx_one else idx_two-1)
        cluster2links.append(new_cluster_link_mapping)
        first_centroid = centroids.pop(idx_one)
        second_centroid = centroids.pop(idx_two if idx_two < idx_one else idx_two-1)
        new_centroid = list(set([item for item in first_centroid if item in second_centroid]))
        centroids.append(new_centroid)
    return clusters, cluster2links, centroids

def cluster_types_2(dataset, linkset, destination, min_overlap=.66, event_resume=0, centroids=False, save_clusters_to_file=None, save_centroids_to_file=None): 
    cluster_centroids = [[dataset[i] for i in link] for link in linkset] # List of centroids 
    clusters = [[centroid] for centroid in cluster_centroids] # List of clusters 
    cluster2links = [[i] for i in range(len(linkset))] # List of link indicies 
    previous = len(clusters) + 1
    while len(clusters) < previous and len(clusters) > min_overlap: 
        previous = len(clusters)
        if not centroids:
            if type(min_overlap) == int: clusters, cluster2links = cluster_two(clusters, cluster2links, 0)
            else: clusters, cluster2links = cluster_two(clusters, cluster2links, min_overlap)
        else:   
            if type(min_overlap) == int: clusters, cluster2links, cluster_centroids = cluster_two_using_centroids(clusters, cluster2links, cluster_centroids, 0)
            else: clusters, cluster2links, cluster_centroids = cluster_two_using_centroids(clusters, cluster2links, cluster_centroids, min_overlap)
    print('Saving {} clusters'.format(len(clusters)))
    f = open(destination, 'w')
    output = [None for i in linkset]
    for i in range(len(cluster2links)): 
        for item in cluster2links[i]: output[item] = i + event_resume
    for item in output: 
        f.write('new_event_{}\n'.format(item))
    f.close()
    if save_clusters_to_file: 
        f = open(save_clusters_to_file, 'w')
        for cluster in clusters: 
            for member in cluster:
                string = ''.join(['{}, '.format(item) for item in member])[:-2]
                f.write('{}\n'.format(string))
        f.write('\n')
        f.close()
    if save_centroids_to_file and centroids: 
        f = open(save_centroids_to_file, 'w')
        for centroid in cluster_centroids: 
            string = ''.join(['{}, '.format(item) for item in centroid])[:-2]
            f.write('{}\n'.format(string))
        f.close()

def find_in_linkset(index, linkset): 
    for i, item in enumerate(linkset): 
        if index in item: return i
    return -1

def linkify(dataset, link, start, end, link_type): 
    not_link = [item for item in range(start, end) if item not in link]
    if len(not_link) == 0: return [link_type]
    link_avg = sum(link) / len(link)
    nlnk_avg = sum(not_link) / len(not_link)
    not_link = [dataset[i] for i in not_link]
    if link_avg < nlnk_avg: 
        return [link_type] + not_link
    return not_link + [link_type]

def save(data, destination): 
    assert(sum([(1 if '\t' in item else 0) for item in data]) == 0)
    handler = open(destination, 'w')
    output = ''.join(['{}\t'.format(item) for item in data])[:-1]
    handler.write(output)
    if data != []: handler.write('\n')
    handler.close()
    print('Saved {} items...'.format(len(data)))

def types_to_raw_output(original_dataset, linkset, type_file, destination): 
    type_handler = open(type_file, 'r')
    types = [item.strip() for item in type_handler.readlines()]
    type_handler.close()
    output = []
    for i, item in enumerate(original_dataset): 
        index = find_in_linkset(i, linkset)
        if index > -1: 
            output.append(types[index])
        else: output.append(item)
    save(output, destination)
    return output

def types_to_dataset(original_dataset, linkset, type_file, destination): 
    type_handler = open(type_file, 'r')
    output = []
    types = [item.strip() for item in type_handler.readlines()]
    type_handler.close()
    offset = 0 # Used to skip un-needed iterations of the loop
    for i, item in enumerate(original_dataset): 
        #if i % 1000 == 0: print(i, len(original_dataset), len(output))
        if i % 10000 == 0: 
            save(output, destination)
        if i < offset: 
            continue
        index = find_in_linkset(i, linkset)
        if index > -1 and len(linkset[index]) >= 5: 
            link = linkset[index]
            start, end = min(link), max(link)
            with_link = linkify(original_dataset, link, start, end, types[index])
            assert(len(with_link) < end - start)
            output.extend(with_link)
            offset = end + 1
        else: 
            output.append(item)
            offset += 1
        print(len(output), i, len(output) < i)
        if index > -1: print('types_to_dataset', end - start, len(with_link), i)
    save(output, destination)
    return output


def ttd2(original_dataset, linkset, type_file, destination): 
    type_handler = open(type_file, 'r')
    output = []
    types = [item.strip() for item in type_handler.readlines()]
    type_handler.close()
    i = 0
    while i < len(original_dataset): 
        print(i, len(output), i > len(output))
        index = find_in_linkset(i, linkset)
        if index > -1: 
            print('found at index', i, linkset[index])
            link = linkset[index]
            start, end = min(link), max(link)
            expandable = linkify(original_dataset, link, start, end, types[index])
            assert(len(expandable) <= end - start)
            output.extend(expandable)
            i += end + 1
        else: 
            output.append(original_dataset[i])
            i += 1
    save(output, destination)
    return output

def load_parameter_from_shell_script(script_path, parameter): 
    f = open(script_path, 'r')
    data = f.read()
    f.close()
    if parameter+'=' in data: 
        start_index = data.index(parameter+'=') + len(parameter+'=')
        end_index = start_index + 1
        while end_index < len(data) and data[end_index] != '\n': end_index += 1
        return data[start_index:end_index]
    return None

if __name__ == '__main__':
    k3_test_root = load_parameter_from_shell_script('run.sh', 'K3_TEST_ROOT')
    test_files = ['/ptb.train.txt', '/ptb.valid.txt', '/ptb.test.txt']
    ntf = []
    for item in test_files: ntf.append(k3_test_root + item)
    ground = integrate.load_ground(ntf)
    destination = load_parameter_from_shell_script('run.sh', 'LINKSET')
    integrate.naive_integrate(load_parameter_from_shell_script('run.sh', 'DELTAS_FILE'), ground, load_parameter_from_shell_script('run.sh', 'WORD2ID_FILE'), destination, 1000, 3)
    linkset = load_linkset(destination)
    #cluster_types_2(ground, linkset, load_parameter_from_shell_script('run.sh', 'CLUSTER_FILE'), 16, centroids=True)
    #types_to_raw_output(ground, linkset, load_parameter_from_shell_script('run.sh', 'CLUSTER_FILE'), load_parameter_from_shell_script('run.sh', 'RAW_OUTPUT'))
    #ttd2(ground, linkset, load_parameter_from_shell_script('run.sh', 'CLUSTER_FILE'), load_parameter_from_shell_script('run.sh', 'FINAL_OUTPUT'))




