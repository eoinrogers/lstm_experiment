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

if __name__ == '__main__':
    g = load_ground_labels('k3_ground_non_interleaved.txt')
    train = open('test_data/ptb.train.txt', 'r')
    valid = open('test_data/ptb.valid.txt', 'r')    
    test = open('test_data/ptb.test.txt', 'r')
    d = [item for item in train.read().strip().split()] + [item for item in valid.read().strip().split()] + [item for item in test.read().strip().split()]
    train.close(); valid.close(); test.close()

    l = load_linkset('/media/eoin/BigDisk/lstm/outputs/lstm_linkset.txt')

    activs = linkset_to_activities(g, l)
    write_out(activs, 0, 'outputs/clusters.txt')

    import hierarchy as h

    h.types_to_raw_output(d, l, h.load_parameter_from_shell_script('run.sh', 'CLUSTER_FILE'), h.load_parameter_from_shell_script('run.sh', 'RAW_OUTPUT'))
    h.ttd2(g, l, h.load_parameter_from_shell_script('run.sh', 'CLUSTER_FILE'), h.load_parameter_from_shell_script('run.sh', 'FINAL_OUTPUT'))


