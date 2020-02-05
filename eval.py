def insert_item(output, numbers, item): 
    inum = int(item.strip().split('_')[-1])
    for i in range(len(numbers)): 
        if numbers[i] > inum: 
            numbers = numbers[:i] + [inum] + numbers[i:]
            output = output[:i] + [item] + output[i:]
            return output, numbers
    output.append(item)
    numbers.append(inum)
    return output, numbers

def assemble_new_events(dataset): 
    output = []
    numbers = []
    for item in dataset: 
        if item.startswith('new_event') and item not in output: 
            output, numbers = insert_item(output, numbers, item)
    return output

def correlation(dataset, event_type, ground, ground_id): 
    tn = tp = fn = fp = 0
    for i in range(len(dataset)): 
        event = dataset[i]
        grd = ground[i]
        if event == event_type:
            if ground_id in grd: tp += 1
            else: fp += 1
        else: 
            if ground_id in grd: fn += 1
            else: tn += 1
    return tn, tp, fn, fp

def largest_ground_id(ground): 
    biggest = 0
    for item in ground: 
        for subitem in item: 
            if subitem > biggest: biggest = subitem
    return biggest

def count_ground_occrence(ground, ground_id): 
    count = 0
    for item in ground: 
        if ground_id in item: count += 1
    return count

def precision(tn, tp, fn, fp):
    return tp / (tp + fp)

def recall(tn, tp, fn, fp): 
    return tp / (tp + fn)

def f1_score(tn, tp, fn, fp): 
    p = precision(tn, tp, fn, fp)
    r = recall(tn, tp, fn, fp)
    if p + r == 0: return 0.
    return 2 * ((p * r) / (p + r))

def raw_acc(tn, tp, fn, fp): 
    return (tp) / (fn + fp + tp + tn)

def run(dataset, ground, eval_function, combine=False, full_results=True): 
    events = assemble_new_events(dataset)
    grd_max = largest_ground_id(ground) + 1
    working = []
    count = 0
    avg = 0
    for event in events: 
        if full_results: print('{} & '.format(event.replace('_', '\\_')), end='')
        for grd in range(grd_max): 
            results = correlation(dataset, event, ground, grd)
            evaluation = eval_function(*results)
            if not combine and full_results: print('{} '.format(evaluation), end='')
            else: working.append(evaluation)
        if combine: 
            value = max(working)
            if full_results: print('{} \\\\'.format(value))
            working = []
            if value >= .5: count += 1
            avg += value
        else: print('')
    print(count / len(events), avg / len(events))

if __name__ == '__main__': 
    import integrate_links as il
    import os
    location = '/media/eoin/BigDisk/hierarchy'
    for i in range(4): 
        ground_path = os.path.join(location, 'Layer {}/train_ground.txt'.format(i+1))
        data_path = os.path.join(location, 'Layer {}/test'.format(i+1))
        ground = il.load_ground_truth(ground_path)
        dataset = il.gen_links.load_dataset(data_path)
        run(dataset, ground, precision, True, False)
    exit()
    for f in os.listdir('/media/eoin/BigDisk'): 
        if not f.startswith('run_num_layers'): continue
        print(f)
        ground = il.load_ground_truth(os.path.join(os.path.join('/media/eoin/BigDisk', f), 'Layer 1/train_ground.txt'))
        dataset = il.gen_links.load_dataset(os.path.join(os.path.join('/media/eoin/BigDisk', f), 'Layer 1/test'))
        run(dataset, ground, precision, True, False)


