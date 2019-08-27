import gen_links, argparse, os, math

def getargs(): 
    parser = argparse.ArgumentParser('Combine links based on perplexity and probability measures.')
    parser.add_argument('dataset', help='Path to the dataset directory (note this should be a directory, not a file)', type=str)
    parser.add_argument('linkproto', help='Prototype for the files containing the candidate links written out by gen_links.py', type=str)
    parser.add_argument('ground', help='Path to the ground truth file', type=str)
    parser.add_argument('destination', help='Path to a \'final\' linkset file that will contain the links chosen to be written into the new dataset', type=str)
    parser.add_argument('newdata', help='Path to the directory that the new dataset shold be written into', type=str)
    parser.add_argument('newground', help='Path to write the new ground truth into', type=str)
    args = parser.parse_args()
    return args.dataset, args.linkproto, args.ground, args.destination, args.newdata, args.newground

def load_ground_truth(path): 
    handler = open(path, 'r')
    for line in handler: 
        line = line.strip()
    handler.close()
    line = [item.index('1') for item in line.split()]
    return line

def update_candidate_dict_for_single_file(path, candidates): 
    for line in open(path, 'r'): 
        line = line.strip().split()
        if len(line) != 3: continue
        i, j, p = int(line[0]), int(line[1]), float(line[2])
        if i in candidates: 
            candidates[i].append((i, j, p))
        else: 
            candidates[i] = [(i, j, p)]
        if j in candidates: 
            candidates[j].append((i, j, p))
        else: 
            candidates[j] = [(i, j, p)]

def sum_probability(t, candidates): 
    i, j, p = t
    for k, l, q in candidates[j]: 
        if l == j: return p + q

def build_final_linkset(candidates): 
    best = {}
    for i in candidates:
        l = candidates[i]
        ps = [sum_probability(item, candidates) for item in l]
        index = ps.index(max(ps))
        best[i] = (l[index][0], l[index][1], ps[index])
    links = {}
    for progress, item in enumerate(best):
        i, j, p = best[item]
        if i != item and best[i][0] == i and best[i][1] == j: 
            links[i] = (i, j, p)
        elif j != item and best[j][0] == i and best[j][1] == j: 
            links[j] = (i, j, p)
    output = []
    i = 0
    length = len(links)
    visited = 0
    print(links)
    while visited < length: 
        #gen_links.print_progress(visited, length)
        if i in links:
            if links[i][0] == i: 
                output.append(links[i])
            visited += 1
        i += 1
    return output

def save_linkset(linkset, path): 
    handler = open(path, 'w')
    for i, j, p in linkset: 
        handler.write('{} {} {}\n'.format(i, j, p))
    handler.close()

def build_new_dataset(dataset, linkset, ground_truth): 
    if len(linkset) == 0: return dataset[:]
    events = {}
    contval = 0
    for i in dataset: 
        if i.startswith('new_event_'): 
            n = int(i.split('_')[-1])
            if n >= contval: contval = n + 1
    output = dataset[:]
    for i, j, p in linkset: 
        assert(dataset[i] != None and dataset[j] != None)
        contents_one = '{} {}'.format(dataset[i], dataset[j])
        contents_two = '{} {}'.format(dataset[j], dataset[i])
        if contents_one in events: 
            link_type = events[contents_one]
        elif contents_two in events: 
            link_type = events[contents_two]
        else: 
            link_type = 'new_event_{}'.format(contval)
            events[contents_one] = link_type
            contval += 1
        output[i] = link_type
        output[j] = None
    print(events)
    new_ground_truth = [item for item, corresponding_event in zip(ground_truth, output) if corresponding_event != None]
    return [item for item in output if item != None], ground_truth

def save_dataset(dataset, path, train_pc=.6, test_pc=.2, valid_pc=.2): 
    i = round(len(dataset) * train_pc)
    j = round(len(dataset) * test_pc)
    assert(train_pc + test_pc + valid_pc == 1)
    train_string = ''.join(['{} '.format(item) for item in dataset[:i]])[:-1]
    test_string = ''.join(['{} '.format(item) for item in dataset[i:i+j]])[:-1]
    valid_string = ''.join(['{} '.format(item) for item in dataset[-j:]])[:-1]
    strings = [train_string, test_string, valid_string]
    for i in range(3): 
        full_path = os.path.join(path, gen_links.file_names[i])
        handler = open(full_path, 'w')
        handler.write(strings[i])
        handler.close()

def save_ground_truth(ground_truth, destination): 
    mkgrdstr = lambda item, length: ''.join(['1' if i == item else '0' for i in range(length)])
    length = max(ground_truth) + 1
    handler = open(destination, 'w')
    guide = ''.join(['{} '.format(i) for i in range(length)])[:-1]
    handler.write('{}\n'.format(guide))
    ground_strings = [mkgrdstr(i, length) for i in ground_truth]
    output = ''.join(['{} '.format(i) for i in ground_strings])[:-1]
    handler.write(output)
    handler.close()

def main(): 
    datadir, linkproto, grdpath, destpath, newdir, newgrd = getargs()
    dataset = gen_links.load_dataset(datadir)
    ground_truth = load_ground_truth(grdpath)
    candidates = {}
    n = 1
    linkset_path = linkproto.format(n)
    print('Loading data...', end=' ')
    while os.path.exists(linkset_path): 
        update_candidate_dict_for_single_file(linkset_path, candidates)
        n += 1
        linkset_path = linkproto.format(n)
    print('Done!')
    linkset = build_final_linkset(candidates)
    save_linkset(linkset, destpath)
    new_dataset, new_ground_truth = build_new_dataset(dataset, linkset, ground_truth)
    save_dataset(new_dataset, newdir)
    save_ground_truth(new_ground_truth, newgrd)

if __name__ == '__main__':
    main()


