def process_single(index, single, dictionary): 
    for i, item in enumerate(single): 
        if item == '1': 
            dictionary[i].append(index)

def load_ground_labels(path): 
    for line in open(path, 'r'): pass
    ground = line.strip().split()
    output = { number : [] for number in range(len(ground[0])) }
    for i in range(len(ground)): 
        process_single(i, ground[i], output)
    return output

def load_linkset(path): 
    handler = open(path, 'r')
    output = []
    for line in handler: 
        line = line.strip().split(',')
        line = [int(item.strip()) for item in line]
        output.append(line)
    handler.close()
    return output

def sort_into_activity(indicies, events): 
    output = []
    working = []
    previous = -1
    for item in indicies: 
        if previous == item - 1: working.append(events[item])
        else: 
            output.append(working)
            working = [events[item]]
        previous = item
    if len(working) != 0: output.append(working)
    return output

def sort_into_activities(dictionary, events): 
    index = 0
    output = []
    while index in dictionary: 
        output.append(sort_into_activity(dictionary[index], events))
        index += 1
    return output

def link_to_activity(dictionary, link): 
    counts = []
    for i in range(len(dictionary)): 
        items = dictionary[i]
        count = 0
        for item in items: 
            if item in link: count += 1
        counts.append(count)
    return counts.index(max(counts))

def linkset_to_activities(dictionary, linkset): 
    output = []
    for link in linkset: output.append(link_to_activity(dictionary, link))
    return output

def write_out(activities, baseline, destination): 
    handler = open(destination, 'w')
    for i in activities: 
        index = i + baseline
        handler.write('new_event_{}\n'.format(index))
    handler.close()

def seperate_links(ground_is, ground_vs): 
    output = []
    working = []
    previous = ground_is[0] - 1
    for index in range(len(ground_is)): 
        if ground_is[index] == previous + 1: 
            working.append(ground_is[index])
        else: 
            output.append([ground_vs[item] for item in working])
            working = [ground_is[index]]
        previous = ground_is[index]
    if len(working) > 0: output.append([ground_vs[item] for item in working])
    return output

def seperate_all_links(ground_dict, events): 
    output = {}
    for item in ground_dict: 
        output[item] = seperate_links(ground_dict[item], events)
    return output

def combine_discrete(dataset): 
    output = []
    for item in dataset:
        if item[-1].isnumeric(): 
            sub_item = item.split('_')
            new_item = ''.join(['{}_'.format(i) for i in sub_item[:-1]])[:-1]
            output.append(new_item)
        else: output.append(item)
    return output

def stats(dataset): 
    output = {}
    for item in dataset: 
        if item in output: output[item] += 1
        else: output[item] = 1
    for item in output: 
        print('{}: {}'.format(item, output[item]))
    return output

if __name__ == '__main__':
    g = load_ground_labels('k3_ground_non_interleaved.txt')
    train = open('test_data/ptb.train.txt', 'r')
    valid = open('test_data/ptb.valid.txt', 'r')    
    test = open('test_data/ptb.test.txt', 'r')
    d = [item for item in train.read().strip().split()] + [item for item in valid.read().strip().split()] + [item for item in test.read().strip().split()]
    d = combine_discrete(d)
    train.close(); valid.close(); test.close()

    l = load_linkset('/media/eoin/BigDisk/lstm/outputs/lstm_linkset.txt')
    l2 = [[d[i] for i in range(min(link), max(link)+1)] for link in l]
    print(l2)

    activs = linkset_to_activities(g, l)
    write_out(activs, 0, 'outputs/clusters.txt')
    activ2links = {}
    for i in range(len(activs)): 
        act_id = activs[i]
        link = l2[i]
        if act_id in activ2links: activ2links[act_id].append(link)
        else: activ2links[act_id] = [link]
    for i in range(len(activ2links)): 
        print('Links for activity {}:'.format(i))
        for lk in activ2links[i]: print(lk)

    import hierarchy as h

    h.types_to_raw_output(d, l, h.load_parameter_from_shell_script('run.sh', 'CLUSTER_FILE'), h.load_parameter_from_shell_script('run.sh', 'RAW_OUTPUT'))
    h.ttd2(g, l, h.load_parameter_from_shell_script('run.sh', 'CLUSTER_FILE'), h.load_parameter_from_shell_script('run.sh', 'FINAL_OUTPUT'))


