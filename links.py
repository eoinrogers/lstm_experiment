import lstm
import random # To allocate random centroids when clustering
import sys


def load_column_across_all_probability_files(probabilities_proto, lookahead_size, column_index,
                                             filter_negative, verbose, iterations):
    # TODO this could almost certainly be made faster. Could we stick everything into a big
    # NumPy matrix and transpose it? 
    output = []
    if verbose: 
        print('Gathering data to compute thresholds for event {}... '.format(column_index), 
               end='')
        sys.stdout.flush()
    for lookahead_index in range(lookahead_size): 
        data = lstm.load_query_results_fast(probabilities_proto, lookahead_index + 1)
        for batch in data: 
            for i, row in enumerate(batch): 
                if not filter_negative or row[column_index] >= 0: output.append(row[column_index])
    
    if verbose: print('Done!')
    return output


def partition_dataset(dataset, centroids): 
    output = [[] for i in centroids]
    for item in dataset: 
        distances = [abs(item - centroid) for centroid in centroids]
        best_index = distances.index(min(distances))
        output[best_index].append(item)
    return output


def k_means(dataset, k, iterations, verbose, column_index): 
    centroids = [random.choice(dataset) for i in range(k)]
    
    for i in range(iterations): 
        # Partition the dataset according to the centroids
        partition_assignments = partition_dataset(dataset, centroids)
        
        # Compute new centroids by averaging each (non-empty) partition
        centroids = [sum(partition) / len(partition) for partition in partition_assignments if len(partition) > 0]
        
        # Pick a new random centroid if we had an empty partition
        if len(centroids) < k: 
            n = centroids[0]
            while n in centroids: n = random.choice(dataset)
            centroids.append(n)
        
        # Print progress if requested
        if verbose: 
            print('\rComputing theshold for event {}: {}%'.format(column_index, round((i / iterations) * 100)), 
                  end='')
            sys.stdout.flush()
        
    if verbose: print('\rComputing threshold for event {}: 100%'.format(column_index))
    
    return centroids


def load_thresholds(path): 
    return [float(threshold) for threshold in lstm.load_vocab(path)]


def compute_thresholds_k_means(vocabulary, probabilities_proto, lookahead_size, k, iterations, filter_negative=True,
                               verbose=True, destination=None): 
    if k < 2: raise ValueError('k must be at least two for k-means clustering')
    output = []
    vocab_size = len(vocabulary)
    
    # Compute a threshold for each item in the vocabulary as the average of the two largest centroids produced
    # by a k-means clustering
    for column_index in range(vocab_size): 
        column = load_column_across_all_probability_files(probabilities_proto, lookahead_size, column_index, filter_negative,
                                                          verbose, iterations)
        centroids = k_means(column, k, iterations, verbose, column_index)
        centroids.sort()
        threshold = (centroids[-1] + centroids[-2]) / 2
        output.append(threshold)
    
    if destination is not None: 
        string = ''.join(['{} '.format(threshold) for threshold in output])
        f = open(destination, 'w')
        f.write(string[:-1])
        f.close()
    
    return output


def add_link(linkset, one, two): 
    # Check to see if one or two are present in any of the existing links, and if so record the index of those links
    first = None
    second = None
    for i, link in enumerate(linkset):
        if one in link: first = i
        if two in link: second = i
    
    # If one is already in the linkset, but two isn't, add two to the link that one is in
    if first is not None and second is None:
        linkset[first].append(two)
    
    # If two is already in the linkset, but one isn't, add one to the link that two is in
    elif first is None and second is not None:
        linkset[second].append(one)
    
    # If one and two are both missing from the linkset, create a new link containing them
    elif first is None and second is None: 
        linkset.append([one, two])
    
    # Finally, if one and two are both present in the linkset, but in different links, remove the two links, 
    # combine them into a new link, and add the new link to the linkset
    elif first is not None and second is not None: 
        if first != second: 
            new_link = list(set(linkset[first] + linkset[second]))
            linkset = [link for i, link in enumerate(linkset) if i != first and i != second]
            linkset.append(new_link)


def build_links_for_offset(linkset, thresholds, dataset, vocabulary, input_file_proto, lookahead_index): 
    # Open file for reading input
    incoming = open(input_file_proto.format(lookahead_index), 'r')
    
    # Build the links for this offset by iterating through the entire dataset
    for one, vector in enumerate(incoming):
        # one will be the index of the end of the sliding window, two will be the index in the lookahead window
        two = one + lookahead_index
        if two >= len(dataset): return
        
        # Get the current dataset label (i.e. the 'correct' answer) 
        label = dataset[two]
        label_vocab_idx = vocabulary.index(label)
        
        # Get the current probability vector, and see if the probability assigned to the current 
        # 'correct' event type (the label) exceeds the associated threshold
        vector = [float(item) for item in vector.strip().split()]
        assert(len(thresholds) == len(vector))
        if vector[label_vocab_idx] >= thresholds[label_vocab_idx]: 
            add_link(linkset, one, two)


def save_links(linkset, location): 
    f = open(location, 'w')
    for link in linkset: 
        string = ''.join(['{} '.format(item) for item in link])
        f.write(string[:-1] + '\n')
    f.close()


def load_linkset(location): 
    f = open(location, 'r')
    output = []
    for line in f: 
        line = line.strip().split()
        if len(line) > 0: 
            output.append([int(item) for item in line])
    return output


def build_links_internal(input_file_proto, output_file, dataset, thresholds, vocabulary, lookahead_size, verbose=True):
    linkset = []
    for lookahead_index in range(1, lookahead_size+1): 
        if verbose: 
            print('Building links for offset {}... '.format(lookahead_index), end='')
            sys.stdout.flush()
        build_links_for_offset(linkset, thresholds, dataset, vocabulary, input_file_proto, lookahead_index)
        if verbose: print('Done!')
    save_links(linkset, output_file)


def get_link_contents(linkset, dataset): 
    output = []
    for link in linkset: 
        new_link = []
        for index in link:
            new_link.append(dataset[index])
        output.append(new_link)
    return output


def activity_similarity(one, two): 
    # What percentage of elements in one also appear in two?
    one_in_two = 0
    for item in set(one): 
        if item in set(two): one_in_two += two.count(item)
    one_in_two /= len(one)
    
    # What percentage of elements in two also appear in one?
    two_in_one = 0
    for item in set(two): 
        if item in set(one): two_in_one += one.count(item)
    two_in_one /= len(two)
    
    # Return the smaller of these two percentages
    return min(one_in_two, two_in_one)


def find_canonical(clusters, threshold): 
    output = []
    flattened = []
    for cluster in clusters: flattened += cluster
    flattened = list(set(flattened))
    for item in flattened: 
        present = [item in cluster for cluster in clusters]
        if sum(present) >= len(clusters) * threshold: output.append(item)
    return output


def should_combine(clusters, index_one, index_two, threshold): 
    # True if all members of the clusters at index_one and index_two have at least threshold % in common
    proposed_cluster = clusters[index_one] + clusters[index_two]
    for member_one in proposed_cluster: 
        for member_two in proposed_cluster: 
            if member_one == member_two: continue
            if activity_similarity(member_one, member_two) < threshold: return False
    return True


def preliminary_cluster_dataset(dataset, linkset_contents, output_file, threshold=.5, verbose=True):
    # Display progress if requested
    if verbose: 
        print('Clustering links into types...', end=' ')
        sys.stdout.flush()
    
    # Initially, give each link its own cluster
    clusters = [[link] for link in linkset_contents]
    
    # Iterate through all possible pairs of activites, and combine them if they are sufficently similar
    # Continue this process until no more changes can be made
    made_changes = True
    while made_changes:
        made_changes = False
        i = 0
        while i < len(clusters): 
            j = 0
            while j < len(clusters): 
                if i >= len(clusters): break
                if i != j: 
                    if should_combine(clusters, i, j, threshold): 
                        one = clusters[i]
                        two = clusters[j]
                        #print('Combining {} and {}'.format(one, two))
                        clusters.pop(i)
                        clusters.pop(j-1 if j > i else j)
                        clusters.append(one + two)
                        made_changes = True
                j += 1
            i += 1
    
    # Write the output to the given file
    output = open(output_file, 'w')
    for link in linkset_contents: 
        index = None
        for i, cluster in enumerate(clusters): 
            if link in cluster: index = i
        assert(index != None)
        output.write('{}\n'.format(index))
    output.close()
    
    if verbose: print('Done!')


def compute_canonical_cluster_forms(incoming, outgoing, linkset_contents, threshold):  
    # Start off by enumerating the preliminary clusters found
    incoming = open(incoming, 'r')
    clusters = [int(item) for item in incoming.readlines()]
    incoming.close()
    prelims = list(set(clusters))
    
    # Now, compute the canonical forms of each cluster, and write to a file
    output = open(outgoing, 'w')
    for cluster in prelims: 
        # First get all instances of the cluster in the linkset
        instances = [linkset_contents[i] for i in range(len(linkset_contents)) if clusters[i] == cluster]
        
        # Find the canonical form of the cluster, and write to a file
        canonical = find_canonical(instances, threshold)
        output.write('{}: {}\n'.format(cluster, ''.join(['{} '.format(item) for item in canonical])))
    
    output.close()


def load_type_forms(path): 
    output = {}
    for line in open(path, 'r'): 
        if line.strip() == '': continue
        name, values = line.strip().split(':')
        values = values.split()
        output[name] = values
    return output


def save_type_forms(type_forms, destination): 
    f = open(destination, 'w')
    for type_name in type_forms: 
        string = '{}: {}\n'.format(type_name, ''.join(['{} '.format(item) for item in type_forms[type_name]]))
        f.write(string)
    f.close()


def load_link_types(path): 
    file_handler = open(path, 'r')
    output = [item.strip() for item in file_handler.readlines()]
    file_handler.close()
    return output


def save_link_types(link_types, destination): 
    file_handler = open(destination, 'w')
    for link_type in link_types: 
        file_handler.write('{}\n'.format(link_type))
    file_handler.close()


def check_previous_clusters(link_types, canonical_type_forms, previous_type_forms, threshold, verbose):
    if previous_type_forms is None: return
    
    # Display progress if requested
    if verbose: 
        print('Comparing to types found in the previous layer...', end=' ')
        sys.stdout.flush()
    
    # Check to see if any types found on previous layers match any newly found types
    current_types = load_type_forms(canonical_type_forms)
    previous_types = load_type_forms(previous_type_forms)
    changes = {}
    for previous in previous_types: 
        for current in current_types: 
            if activity_similarity(previous_types[previous], current_types[current]) >= threshold: 
                changes[current] = previous
    
    # Change the type names in the current_types dictionary, and save it to file
    new_current_types = {}
    for current in current_types: 
        if current in changes: new_current_types[changes[current]] = current_types[current]
        else: new_current_types[current] = current_types[current]
    save_type_forms(new_current_types, canonical_type_forms)
    
    # Finally, change the contents of the link types file
    lt = load_link_types(link_types)
    new_link_types = [(item if item not in changes else changes[item]) for item in lt]
    save_link_types(new_link_types, link_types)
    
    if verbose: print('Done!')


def rename_types(dataset, link_types_file, type_forms_file): 
    # Load the link types
    link_types = load_link_types(link_types_file)
    
    # Load the type forms
    type_forms = load_type_forms(type_forms_file)
    
    # Find the largest current new_event_* in the dataset
    newest_event = 0
    for item in dataset: 
        if item.startswith('new_event_'): 
            number = int(item.split('_')[2])
            if number >= newest_event: newest_event = number + 1
    print('The newest event is {}'.format(newest_event))
    
    # Assign the n types that aren't taken from the previous layer and assign the numbers 0..n-1 to them
    numerical = [int(item) for item in link_types if item.isnumeric()]
    numerical = list(set(numerical))
    numerical.sort()
    numerical = { number : i for i, number in enumerate(numerical) }
    
    # Iterate throught the link types and rename them if needed
    new_link_types = []
    for link in link_types: 
        if link.isnumeric(): 
            item = 'new_event_{}'.format(numerical[int(link)] + newest_event)
        else: item = link
        new_link_types.append(str(item))
    
    # Iterate through the type forms and rename then if needed
    new_link_forms = {}
    for name, canonical in type_forms.items():
        if name.isnumeric(): item = 'new_event_{}'.format(numerical[int(name)] + newest_event)
        else: item = name
        new_link_forms[item] = canonical
    
    # Save the new links
    save_link_types(new_link_types, link_types_file)
    save_type_forms(new_link_forms, type_forms_file)


def update_dataset(dataset, linkset_file, link_types_file): 
    # Load the link types and linkset
    linkset = load_linkset(linkset_file)
    link_types = load_link_types(link_types_file)
    
    # Replace each element of the dataset that is part of a link with the correct link type
    for i in range(len(dataset)): 
        for j in range(len(linkset)): 
            if i in linkset[j]: dataset[i] = link_types[j]
    
    # Return the new dataset
    return dataset


def cluster_and_change_dataset(dataset, links_file, link_types_file, type_forms_file, previous_forms_file, output, threshold=.5,
                               verbose=True): 
    linkset = load_linkset(links_file)
    linkset_contents = get_link_contents(linkset, dataset)
    
    # Cluster the dataset
    preliminary_cluster_dataset(dataset, linkset_contents, link_types_file, threshold, verbose)
    
    # Find the canonical forms of the clusters
    compute_canonical_cluster_forms(link_types_file, type_forms_file, linkset_contents, threshold)
    
    # Check to see if any of the types have been found previously
    check_previous_clusters(link_types_file, type_forms_file, previous_forms_file, threshold, verbose)
    
    # Change the contents of the dataset and links
    rename_types(dataset, link_types_file, type_forms_file)
    dataset = update_dataset(dataset, links_file, link_types_file)
    
    # Write the new dataset out
    if verbose: print('Writing data out...', end=' ')
    f = open(output, 'w')
    string = ''
    for item in dataset: string += '{} '.format(item)
    f.write(string[:-1])
    f.close()
    if verbose: print('Done!')


def build_links(data_directory, probabilities_proto, vocab_file, thresholds_file, raw_links_file, link_types_file, 
                type_forms_file, previous_type_forms_file, new_uncompressed_file, lookahead_size, threshold): 
    dataset = lstm.load_dataset(data_directory)
    vocabulary = lstm.load_vocab(vocab_file)
    compute_thresholds_k_means(vocabulary, probabilities_proto, lookahead_size, 2, 15, destination=thresholds_file)
    thresholds = load_thresholds(thresholds_file)
    build_links_internal(probabilities_proto, raw_links_file, dataset, thresholds, vocabulary, lookahead_size)
    cluster_and_change_dataset(dataset, raw_links_file, link_types_file, type_forms_file, previous_type_forms_file, 
                               new_uncompressed_file, threshold)


if __name__ == '__main__':
    data_dir = '/media/eoin/BigDisk/kyoto3/interleaved train'
    probabilities = '/media/eoin/BigDisk/blah/deltas/lookahead={}'
    vocab_file = '/media/eoin/BigDisk/blah/vocab'
    thresholds = '/media/eoin/BigDisk/blah/thresholds'
    raw_links = '/media/eoin/BigDisk/blah/raw_links'
    link_types = '/media/eoin/BigDisk/blah/link_types'
    canonical_type_forms = '/media/eoin/BigDisk/blah/canonical_type_forms'
    new_uncompressed_dataset = '/media/eoin/BigDisk/blah/new_dataset_uncompressed'
    lookahead_size = 10
    
    build_links(data_dir, probabilities, vocab_file, thresholds, raw_links, link_types, canonical_type_forms, None, 
                new_uncompressed_dataset, lookahead_size, .6)
    

