import reader, os

def gen_data(path): 
    f = open(path, 'r')
    for line in f: 
        data = [float(item.strip()) for item in line.strip().split(',')]
        yield data
    f.close()

def load_ground(path): 
    if type(path) == list: 
        output = []
        for item in path: output.extend(load_ground(item))
        return output
    f = open(path, 'r')
    data = f.read()
    data = data.replace('\n', '<eos>')
    return data.strip().split()

def save_linkset(linkset, destination, min_length=0): 
    '''
    Save a given linkset to the given file. 
    Each link is represented as a comma-seprated list, with its 
    own line. min_length can be used to filter small links, which
    may be spurious. 
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

def insert_link(linkset, one, two, printme = False): 
    '''
    If linkset is a list of links (i.e. it is a list of (sub)lists, where each sublist represents a single 
    link, and each element of the sublist is an index into the dataset indicating link membership), and 
    one and two are both event indicies, add one and two to the correct link in the linkset (i.e. we can 
    add them by adding one of them to an existing link, creating a new link with just them as members, 
    or by combining two existing links together. 
    '''
    if printme: # Used for debugging 
        print('insert_link() arguments:', linkset, one, two);sys.stdout.flush()
    
    # Make 2 boolean lists, one for the one argument, one for the two argument. 
    # They should contain True if the corresponding link contains the index. 
    # There should be zero or one Trues in each list maximum. 
    ones = [one in item for item in linkset]
    twos = [two in item for item in linkset]
    assert((sum(ones) == 0 or sum(ones) == 1) and (sum(twos) == 0 or sum(twos) == 1))
    
    # If the one argument is nowhere in the linkset, see if the two argument is (and if it is, 
    # add one to that link), or create a new link consisting of just one and two. 
    # Otherwise, the one argument already exists in the linkset. If two does not exist, we 
    # need to add two to one's link. Otherwise, we combine one and two's link
    # together. 
    if sum(ones) == 0: 
        if ones == twos: linkset.append([one, two]) # Missing both
        else: linkset[twos.index(True)].append(one) # Missing one
    else: 
        if sum(twos) == 0: linkset[ones.index(True)].append(two) # Missing two
        elif ones != twos: # Combine links 
            i, j = ones.index(True), twos.index(True) # Get the index of one and two's links 
            o, t = linkset[i], linkset[j] # Copy the two relevant linksets
            linkset = [item for k, item in enumerate(linkset) if k not in [i, j]] # Remove them
            linkset.append(o + t) # Combine and re-add 
    return linkset

def save_matrix(matrix, destination):
    f = open(destination, 'w')
    for row in matrix: 
        output = ''.join(['{}, '.format(item) for item in row])[:-2]
        f.write('{}\n'.format(output))
    f.close()

def sort_ids_by_probability(input_vector, n): 
    '''
    Get the indexes of the top n largest values in input_vector
    '''
    output = []
    input_vector = input_vector[:] # Don't destroy the object on the caller. 
    while len(output) < n: 
        largest = input_vector.index(max(input_vector))
        output.append(largest)
        input_vector = [item for i, item in enumerate(input_vector) if i != largest]
    return output

def naive_integrate_single_lookahead(linkset, path, ground, word2id, lookahead_offset, destination, save_per, n): 
    '''
    Update the linkset by determining links added by a single LSTM. We build a link 
    between events X and Y if X is the last event in the sliding window, Y appears
    in the lookahead window at an offset of O, and the LSTM for offset O predicted 
    Y within its top n predictions.
    Arguments: 
    linkset: the current linkset, in the form of a list of lists. Each sublist is
     a single link, consisting of indexes into the dataset.
    path: path to the LSTMs probabilities. 
    ground: The ground truth, as produced by the load_ground() function
    word2id: Python dictionary mapping event names (words) to offsets within the 
     output layer of the LSTM
    lookahead_offset: integer value for the offset within the lookahead
    destination: output file to write the linkset to
    save_per: How frequently the function should save as it progresses. For example, if set
     to 1000, the function will save once every 1000 iterations. Everything is saved at the
     end of a run regardless of what this is set to. 
    n: The number used as described above. For example, if this is 3, we build a link between
     X and Y if the network predicted Y in the top 3 predictions when given an input window
     ending with X. 
    '''
    print(lookahead_offset, end=' ')
    for i, vector in enumerate(gen_data(path)): # Iterate through each probability vector produced by the LSTM
        if i % save_per == 0: save_linkset(linkset, destination) # Write to output if save_per requires it
        if i + lookahead_offset >= len(ground): break # If we've run past the end of the lookahead, exit the loop
        most_likely = sort_ids_by_probability(vector, n) # Find the top n most likely predictions of the LSTM
        ground_item = word2id[ground[i+lookahead_offset-1]] # The the current offset for the `correct answer' in the output layer
        
        # If the `correct answer' appears in the most_likely list, add a link between the current lookahead
        # offset and the last value in the sliding window. 
        if ground_item in most_likely: linkset = insert_link(linkset, i, i + lookahead_offset)
    save_linkset(linkset, destination) # Save the full linkset when finished 
    return linkset

def get_perplexities(perplexity_proto): 
    output = []
    lookahead_offset = 1
    while os.path.exists(perplexity_proto.format(lookahead_offset)): 
        f = open(perplexity_proto.format(lookahead_offset), 'r')
        perplexity = float(f.read().strip())
        output.append(perplexity)
        lookahead_offset += 1
    return output

def naive_integrate(path_proto, ground, word2id_proto, destination, save_per, n): 
    '''
    Build linksets without using perplexity: we build a link between events X and Y if
    X is the last event in the sliding window, Y appears in the lookahead window at an
    offset of O, and the LSTM for offset O predicted Y within its top n predictions.
    Arguments:
    path_proto: Path to the probabilities for each LSTM. The path for all probability files
     should be the same except for a number representing the offset. This number should be 
     replaced by a {} in this argument so the function can find all the LSTMs
    ground: The ground truth, as produced by the load_ground() function
    word2id_proto: Path to a file to link word IDs (offsets in the output layer) to word
     values. The path for all word2id files should be the same except for a number representing
     the offset. This number should be replaced by {} in this argument so the function can
     find all the LSTMs.
    destination: output file to write the linkset to
    save_per: How frequently the function should save as it progresses. For example, if set
     to 1000, the function will save once every 1000 iterations. Everything is saved at the
     end of a run regardless of what this is set to. 
    n: The number used as described above. For example, if this is 3, we build a link between
     X and Y if the network predicted Y in the top 3 predictions when given an input window
     ending with X. 
    Returns:
    A linkset: a list of lists, where each sublist consists of numbers which are indexes into
     the dataset. Each sublist represents a single link. 
    '''
    lookahead_offset = 1
    path = path_proto.format(lookahead_offset)
    linkset = []
    while os.path.exists(path): # Keep iterating until we have come to a lookahead offset that does not exist 
        word2id = reader.readin_word2id(word2id_proto.format(lookahead_offset)) # Load the associated word2id 
        linkset = naive_integrate_single_lookahead(linkset, path, ground, word2id, lookahead_offset, destination, save_per, n) # Integrate for this lookahead
        print(len(linkset)) # Display the length of the linkset (i.e. tell us how many links we have)
        
        # Increment the lookahead offset and get the name for the next expected probability file. 
        lookahead_offset += 1
        path = path_proto.format(lookahead_offset)
    return linkset

def perplexity_integrate(perplexity_proto, path_proto, data, word2id_proto, destination, save_per): 
    inverted_perplexities = [1 / perplexity for perplexity in get_perplexities(perplexity_proto)]
    sum_inverted_perplexities = sum(inverted_perplexities)
    output = []
    first_iteration = True
    for lookahead_offset in range(1, len(inverted_perplexities)+1): 
        print(lookahead_offset, len(output))
        path = path_proto.format(lookahead_offset)
        word2id = reader.readin_word2id(word2id_proto.format(lookahead_offset))
        for i, vector in enumerate(gen_data(path)): 
            if i + lookahead_offset >= len(data): break
            if i % save_per == 0: save_matrix(output, destination)
            if first_iteration: output.append([item * inverted_perplexities[lookahead_offset-1] for item in vector])
            else: output[i] = [output[i][idx] + (vector[idx] * inverted_perplexities[lookahead_offset-1]) for idx in range(len(vector))]
        first_iteration = False
    output.reverse()
    output = [[subitem / sum(inverted_perplexities[:i+1]) for subitem in item] for i, item in enumerate(output)]
    output.reverse()
    save_matrix(output, destination)
    return output

if __name__ == '__main__':
    data = load_ground(['/media/eoin/BigDisk/kyoto3/lstm_original/ptb.test.txt', '/media/eoin/BigDisk/kyoto3/lstm_original/ptb.train.txt', '/media/eoin/BigDisk/kyoto3/lstm_original/ptb.valid.txt'])
    destination = 'test_linkset.txt'
    #naive_integrate('/media/eoin/BigDisk/working/lstm_k3_probs_{}', data, '/media/eoin/BigDisk/working/lstm_k3_word2id_{}', destination, 1000, 3)
    #perplexity_integrate('/media/eoin/BigDisk/working/lstm_k3_perplexity_{}', '/media/eoin/BigDisk/working/lstm_k3_probs_{}', data, '/media/eoin/BigDisk/working/lstm_k3_word2id_{}', 'perplexity_output.csv', 1000)


