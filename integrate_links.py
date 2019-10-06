import gen_links, argparse, os, math

def getargs(): 
    parser = argparse.ArgumentParser('Combine links based on perplexity and probability measures.')
    parser.add_argument('dataset', help='Path to the dataset directory (note this should be a directory, not a file)', type=str)
    parser.add_argument('linkproto', help='Prototype for the files containing the candidate links written out by gen_links.py', type=str)
    parser.add_argument('input_typeinfo', hep='Path to the previous typeinfo file, which is used to determine the types of links. Can be set to NULL if none exist', type=str)
    parser.add_argument('output_typeinfo', hep='Path to write the new typeinfo file to', type=str)
    parser.add_argument('ground', help='Path to the ground truth file', type=str)
    parser.add_argument('destination', help='Path to a \'final\' linkset file that will contain the links chosen to be written into the new dataset', type=str)
    parser.add_argument('newdata', help='Path to the directory that the new dataset shold be written into', type=str)
    parser.add_argument('newground', help='Path to write the new ground truth into', type=str)
    parser.add_argument('min_num', help='Minimum number an event needs to occur to be accepted', type=int)
    parser.add_argument('sizeacct', help='Take the size of the link into account when integrating', type=bool)
    args = parser.parse_args()
    return args.dataset, args.linkproto, args.input_typeinfo, args.output_typeinfo, args.ground, args.destination, args.newdata, args.newground, args.min_num, args.sizeacct

def load_ground_truth(path): 
    handler = open(path, 'r')
    for line in handler: 
        line = line.strip()
    handler.close()
    line = [[int(i) for i in range(len(item)) if item[i] == '1'] for item in line.split()]
    return line

def load_typeinfo(path): 
    handler = open(path, 'r')
    output = {}
    for line in handler: 
        line = [item.strip() for item in line.strip()]
        if len(line) == 3: line.append(1)
        if len(line) != 4: continue
        output['{} {}'.format(line[0], line[1])] = line[2], line[3]
    handler.close()
    return output

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

def sum_probability(t, candidates, sizeacct): 
    i, j, p = t
    for k, l, q in candidates[j]: 
        if l == j:
            if sizeacct: return (p + q) * ((j - i) / 400)
            else: return p + q

def build_final_linkset(candidates, sizeacct): 
    best = {}
    for i in candidates:
        l = candidates[i]
        ps = [sum_probability(item, candidates, sizeacct) for item in l]
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

def remove_uncommon_candidate_events(output, type_dict, contval, threshold): 
    temp = [item for item in type_dict.values()]
    names = [item[0] for item in temp]
    counts = [item[1] for item in temp]
    cand2new = {}
    rejections = 0
    accepts = 0
    print('before', output.count(None))
    for i in range(len(output)): 
        if type(output[i]) == tuple: 
            original_value, sibling_index, type_value = output[i]
            count = counts[names.index(type_value)]
            if count < threshold: 
                rejections += 1
                output[i] = original_value
            elif type_value.startswith('candidate_event_'): 
                if type_value in cand2new: 
                    cand2new[type_value][1].append((i, sibling_index))
                    type_value = cand2new[type_value][0]
                else: 
                    ne = 'new_event_{}'.format(contval)
                    contval += 1
                    cand2new[type_value] = ne, [(i, sibling_index)]
                    type_value = ne
                output[i] = type_value
                output[sibling_index] = None #type_value
                accepts += 1
    type_dict = { cand2new[temp[i][0]][0] : (names[i], counts[i], cand2new[temp[i][0]][1]) for i in range(len(temp)) if counts[i] >= threshold } 
    print('Threshold = {}, rejections = {}, accepts = {}'.format(threshold, rejections, accepts))
    return output, type_dict

def build_new_dataset(dataset, linkset, ground_truth, typeinfo, threshold): 
    events = load_typeinfo(typeinfo) if typeinfo != 'NULL' else {}
    if len(linkset) == 0: return dataset[:], ground_truth, events
    print('Before compression:', len(dataset))
    contval = 0
    for i in dataset: 
        if i.startswith('new_event_'): 
            n = int(i.split('_')[-1])
            if n >= contval: contval = n + 1
    candval = contval
    output = dataset[:]
    for i, j, p in linkset: 
        assert(dataset[i] != None and dataset[j] != None)
        contents_one = '{} {}'.format(dataset[i], dataset[j])
        contents_two = '{} {}'.format(dataset[j], dataset[i])
        if contents_one in events: 
            link_type = events[contents_one][0]
            events[contents_one] = (events[contents_one][0], events[contents_one][1]+1)
        elif contents_two in events: 
            link_type = events[contents_two][0]
            events[contents_two] = (events[contents_two][0], events[contents_two][1]+1)
        else: 
            link_type = 'candidate_event_{}'.format(candval)
            events[contents_one] = (link_type, 1)
            candval += 1
        output[i] = (output[i], j, link_type)
    print('After compression:', len([item for item in output if item != None]))
    output, new_events = remove_uncommon_candidate_events(output, events, contval, threshold)
    new_ground_truth = [item for item, corresponding_event in zip(ground_truth, output) if corresponding_event != None]
    print(new_events)
    print('After compression:', len([item for item in output if item != None]))
    return ([item for item in output if item != None], new_ground_truth, new_events)

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
    mkgrdstr = lambda item, length: ''.join(['1' if i in item else '0' for i in range(length)])
    length = max([max(i) for i in ground_truth]) + 1
    handler = open(destination, 'w')
    guide = ''.join(['{} '.format(i) for i in range(length)])[:-1]
    handler.write('{}\n'.format(guide))
    ground_strings = [mkgrdstr(i, length) for i in ground_truth]
    output = ''.join(['{} '.format(i) for i in ground_strings])[:-1]
    handler.write(output)
    handler.close()

def save_typeinfo(type_dict, destination): 
    handler = open(destination, 'w')
    for t in type_dict:
        handler.write('{} {} {} {}\n'.format(t, type_dict[t][0], type_dict[t][1], type_dict[t][2]))
    handler.close()

def main(args=None): 
    datadir, linkproto, input_typeinfo, output_typeinfo, grdpath, destpath, newdir, newgrd, min_num, sizeacct = getargs() if args == None else args
    dataset = gen_links.load_dataset(datadir)
    ground_truth = load_ground_truth(grdpath)
    candidates = {}
    n = 1
    linkset_path = linkproto.format(n)
    print('kdsfljl', datadir)
    print('Loading data...', end=' ')
    while os.path.exists(linkset_path): 
        update_candidate_dict_for_single_file(linkset_path, candidates)
        n += 1
        linkset_path = linkproto.format(n)
    print('Done!')
    linkset = build_final_linkset(candidates, sizeacct)
    save_linkset(linkset, destpath)
    x = build_new_dataset(dataset, linkset, ground_truth, input_typeinfo, min_num)
    #print('x')
    new_dataset, new_ground_truth, new_types = x
    save_dataset(new_dataset, newdir)
    save_ground_truth(new_ground_truth, newgrd)
    save_typeinfo(new_types, output_typeinfo)

if __name__ == '__main__':
    main()


