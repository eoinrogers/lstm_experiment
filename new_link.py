import os, reader

def load_delta_file(path): 
    fh = open(path, 'r')
    output = fh.read()
    output = output.split('\n')
    fh.close()
    empty = []
    for i in range(len(output)): 
        if output[i] == '': 
            empty.append(i)
            continue
        temp = [float(item.strip()) for item in output[i].split(',')]
        output[i] = temp
    for i in empty: output.pop(i)
    return output

file_names = 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()

def load_dataset(directory_path): 
    global file_names
    output = []
    for f in file_names: 
        fh = open(os.path.join(directory_path, f), 'r')
        data = fh.read()
        fh.close()
        output += data.split()
    return output

def save_dataset(dataset, path, train_pc=.7, test_pc=.2, valid_pc=.1): 
    global file_names
    i = round(len(dataset) * train_pc)
    j = round(len(dataset) * test_pc)
    train_string = ''.join(['{} '.format(item) for item in dataset[:i]])[:-1]
    test_string = ''.join(['{} '.format(item) for item in dataset[i:i+j]])[:-1]
    valid_string = ''.join(['{} '.format(item) for item in dataset[i+j:]])[:-1]
    strings = [train_string, valid_string, test_string]
    for i in range(3): 
        full_path = os.path.join(path, file_names[i])
        handler = open(full_path, 'w')
        handler.write(strings[i])
        handler.close()

def shuffle_dataset(dataset_directory_path, train_pc=.7, test_pc=.2, valid_pc=.1): 
    dataset = load_dataset(dataset_directory_path)
    save_dataset(dataset, dataset_directory_path, train_pc, test_pc, valid_pc)

def k_means(values, k, iterations): 
    centroids = values[:k]
    for itr in range(iterations): 
        clusters = [[] for i in centroids]
        for v in values: 
            distances = [abs(v - c) for c in centroids]
            clusters[distances.index(min(distances))].append(v)
        centroids = [sum(cluster) / len(cluster) for cluster in clusters]
        centroids.sort()
    return centroids

def compute_threshold(values, k, iterations): 
    assert(k >= 2)
    centroids = k_means(values, k, iterations)
    assert(len(centroids) >= 2)
    centroids.sort()
    return (centroids[-2] + centroids[-1]) / 2

def insert_link(linkset, one, two, printme = False): 
    '''
    If linkset is a list of links (i.e. it is a list of (sub)lists, where each sublist represents a single 
    link, and each element of the sublist is an index into the dataset indicating link membership), and 
    one and two are both event indicies, add one and two to the correct link in the linkset (i.e. we can 
    add them by adding one of them to an existing link, creating a new link with just them as members, 
    or by combining two existing links together. 
    '''
    if printme: 
        print('insert_link() arguments:', linkset, one, two);sys.stdout.flush()
    ones = [one in item for item in linkset]
    twos = [two in item for item in linkset]
    if sum(ones) == 0: 
        if ones == twos: linkset.append([one, two]) # Missing both
        else: linkset[twos.index(True)].append(one) # Missing one
    else: 
        if sum(twos) == 0: linkset[ones.index(True)].append(two) # Missing two
        elif ones != twos: 
            i, j = ones.index(True), twos.index(True)
            o, t = linkset[i], linkset[j]
            linkset = [item for k, item in enumerate(linkset) if k not in [i, j]]
            linkset.append(o + t) 
    return linkset

def save_linkset(linkset, destination, min_length=0): 
    '''
    Save a given linkset to the given file. 
    '''
    #print(linkset)
    handler = open(destination, 'w')
    for link in linkset: 
        if len(link) < min_length: continue
        link.sort()
        line = ''.join(['{}, '.format(item) for item in link])[:-2]
        line += '\n'
        handler.write(line)
    handler.close()

def read_activity(path): 
    f = open(path, 'r')
    for activity in f:
        if activity == '': continue 
        activity = [int(item.strip()) for item in activity.split(',')]
        yield activity

def load_existing_linkset(path): 
    output = []
    for item in read_activity(path): output.append(item)
    return output

def compute_thresholds(dataset, k, iterations): 
    output = []
    for i in range(len(dataset[0])): 
        print(i, end=' ')
        column = [dataset[j][i] for j in range(len(dataset))]
        threshold = compute_threshold(column, k, iterations)
        threshold = max(threshold, 0) # There shouldn't ever really be non-zero thresholds, but just in case let's get rid of them
        print(threshold)
        output.append(threshold)
    return output

def process_single_file(linkset, window_length, dataset, deltas, offset, k, iterations): 
    thresholds = [.5] * len(deltas[0]) #compute_thresholds(deltas, k, iterations)
    print(len(dataset))
    for idx in range(len(dataset)): 
        other_idx = idx + offset # Index of offset into the lookahead window
        if other_idx >= len(dataset) or other_idx >= len(deltas): break
        actual = dataset[other_idx] # Word ID for the event type we are trying to predict
        prediction = deltas[other_idx][actual] # Probability of the word ID, according to the network
        t = thresholds[actual]
        #print(idx, offset, other_idx, prediction, t)
        if prediction >= t: 
            #print(idx, offset, other_idx, actual, prediction, t, len(thresholds))
            #input()
            linkset = insert_link(linkset, idx, other_idx)
            #print(linkset)
    return linkset

def new_event_num(dataset): 
    output = 0
    for item in dataset: 
        if item.startswith('new_event_'): 
            n = int(item[len('new_event_'):]) + 1
            if n > output: output = n
    return output

def same_cluster(dataset, one, two): 
    one_members = [dataset[i] for i in one]
    two_members = [dataset[i] for i in two]
    count_one = 0
    for i in one_members: 
        if i in two_members: count_one += 1
    count_one /= len(one)
    count_two = 0
    for i in two_members:
        if i in one_members: count_two += 1
    count_two /= len(two)
    return count_one > .5 and count_two > .5

def filter_clusters(linkset, clusters, threshold): 
    cluster_counts = {}
    for cluster in clusters: 
        if cluster not in cluster_counts: cluster_counts[cluster] = 1
        else: cluster_counts[cluster] += 1
    for_removal = [i for i in range(len(clusters)) if cluster_counts[clusters[i]] < threshold]
    linkset = [link for i, link in enumerate(linkset) if i not in for_removal]
    clusters = [cluster for i, cluster in enumerate(clusters) if i not in for_removal]
    return linkset, clusters

def cluster_linkset(linkset, dataset, do_filter=0): 
    clusters = [i for i in range(len(linkset))]
    for one in range(len(clusters)): 
        for two in range(len(clusters)): 
            if one != two and clusters[one] != clusters[two]:
                name = min(clusters[one], clusters[two])
                if same_cluster(dataset, linkset[one], linkset[two]): clusters[one] = clusters[two] = name
    if do_filter > 0: 
        linkset, clusters = filter_clusters(linkset, clusters, do_filter)
    # Rename from 0..max_clusters - 1
    num_clusters = len(set(clusters))
    for i in range(num_clusters - 1, -1, -1): 
        n = max(clusters)
        for j in range(len(clusters)): 
            if clusters[j] == n: clusters[j] = i
    return zip(linkset, clusters)

def save_types(clustered_linkset, destination, event_num): 
    fh = open(destination, 'w')
    for link, cluster in clustered_linkset: 
        line = 'new_event_{}: '.format(event_num + cluster) + ''.join([str(item) + ', ' for item in link])[:-2]
        fh.write('{}\n'.format(line))
    fh.close()

def load_types(path): 
    fh = open(path, 'r')
    output = []
    for item in fh: 
        event, link = item.strip().split(':')
        event = event.strip()
        link = [int(i.strip()) for i in link.strip().split(',')]
        output.append((link, event))
    fh.close()
    return output

def swap_dataset_events_with_link_events(dataset, clustered_linkset): 
    dataset = dataset[:]
    for link, event in clustered_linkset: 
        for l in link: dataset[l] = event
    return dataset

def compress_dataset(dataset, ground_truth, clustered_linkset): 
    dataset = dataset[:]
    all_links = []
    new_events = {}
    new_ground_truths = {}
    for link, event in clustered_linkset:
        all_links.extend(link)
        position = round(sum(link) / len(link))
        while position in new_events: position += 1
        new_events[position] = event
        g = []
        for i in link: 
            g.extend(ground_truth[i])
        new_ground_truths[position] = list(set(g))
    idxs = [i for i in range(len(dataset)) if i not in all_links]
    print(idxs, new_events, len(clustered_linkset), len(new_events))
    new_dataset = []
    new_ground = []
    for i in range(len(dataset)): 
        if i in new_events: 
            new_dataset.append(new_events[i])
            new_ground.append(new_ground_truths[i])
        if i in idxs: 
            new_dataset.append(dataset[i])
            new_ground.append(ground_truth[i])
    return new_dataset, new_ground

def load_ground_truth(path): 
    handler = open(path, 'r')
    for line in handler: 
        line = line.strip()
    handler.close()
    line = [[int(i) for i in range(len(item)) if item[i] == '1'] for item in line.split()]
    return line

def save_ground_truth(ground_truth, destination): 
    mkgrdstr = lambda item, length: ''.join(['1' if i in item else '0' for i in range(length)])
    length = max([max(i) for i in ground_truth]) + 1
    handler = open(destination, 'w')
    guide = ''.join(['{} '.format(i) for i in range(length)])[:-1]
    handler.write('{}\n'.format(guide))
    ground_strings = [mkgrdstr(i, length) for i in ground_truth]
    output = ''.join(['{} '.format(i) for i in ground_strings])[:-1]
    handler.write(output)
    handler.close()

param_k = 2
param_iterations = 100

def generate_links(input_testing_data_dir, delta_file_proto, destination, word2id_file_proto, perplexity_file_proto, window_length, lookahead_length):
    global param_k, param_iterations 
    linkset = []
    for offset in range(1, lookahead_length + 1): 
        print('Offset {}'.format(offset))
        deltas = load_delta_file(delta_file_proto.format(offset))
        dataset = reader.ptb_raw_data(input_testing_data_dir, word2id_file_proto.format(offset))
        dataset = dataset[0] + dataset[1] + dataset[2]
        linkset = process_single_file(linkset, window_length, dataset, deltas, offset, param_k, param_iterations)
        save_linkset(linkset, destination)

def integrate_links(input_testing_data_dir, input_training_ground_file, outgoing_types_file, final_linkset, output_testing_data_dir, output_testing_ground_file,
                    cluster_threshold=0): 
    dataset = load_dataset(input_testing_data_dir)
    event = new_event_num(dataset)
    linkset = load_existing_linkset(final_linkset)
    old_ground_truth = load_ground_truth(input_training_ground_file)
    number = new_event_num(dataset)
    save_types(cluster_linkset(linkset, dataset, cluster_threshold), outgoing_types_file, number)
    clustered = load_types(outgoing_types_file)
    swapped = swap_dataset_events_with_link_events(dataset, clustered)
    compressed_dataset, new_ground_truth = compress_dataset(swapped, old_ground_truth, clustered)
    save_dataset(compressed_dataset, output_testing_data_dir)
    save_ground_truth(new_ground_truth, output_testing_ground_file)

#    generate_links(input_testing_data_dir, delta_file_proto, ll_links_file_proto, word2id_file_proto, perplexity_file_proto, window_length, lookahead_length)
#    integrate_links(input_testing_data_dir, ll_links_file_proto, incoming_types_file, outgoing_types_file, input_training_ground_file, final_linkset, output_testing_data_dir, \
#                    output_testing_ground_file, min_occur_threshold, sizeacct)

#generate_links('/home/eoin/programming/newlstm/experiment_thing/test_data', '/media/eoin/BigDisk/run_num_layers=4_window_length=40_lookahead_length=10_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 1/deltas/offset_{}', '/media/eoin/BigDisk/run_num_layers=4_window_length=40_lookahead_length=10_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 1/linkset.txt', '/media/eoin/BigDisk/run_num_layers=4_window_length=40_lookahead_length=10_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 1/misc/word2ids/offset_{}', '', 40, 10)
#integrate_links('/home/eoin/programming/newlstm/experiment_thing/test_data', '/media/eoin/BigDisk/kyoto3/k3_ground_non_interleaved.txt', '/media/eoin/BigDisk/run_num_layers=4_window_length=40_lookahead_length=10_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 1/typeinfo.txt', '/media/eoin/BigDisk/run_num_layers=4_window_length=40_lookahead_length=10_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 1/linkset.txt', '/media/eoin/BigDisk/run_num_layers=4_window_length=40_lookahead_length=10_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 1/test', '/media/eoin/BigDisk/run_num_layers=4_window_length=40_lookahead_length=10_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 1/test_ground.txt')



