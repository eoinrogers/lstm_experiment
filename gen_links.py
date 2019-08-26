import argparse, reader, os, sys

file_names = 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()

def getargs():
    parser = argparse.ArgumentParser('Build low-level (untyped) links between up to two events')
    parser.add_argument('dataset', help='Path to the dataset directory (note this should be a directory, not a file)', type=str)
    parser.add_argument('input', help='Prototype for the path to the input files', type=str)
    parser.add_argument('output', help='Prototype for the path to output files', type=str)
    parser.add_argument('word2id', help='Prototype for the path to the word2id files', type=str)
    parser.add_argument('perplexity', help='Prototype for the path to the perplexity files', type=str)
    parser.add_argument('-w', '--window_length', help='Window length', type=int, default=30)
    parser.add_argument('-l', '--lookahead', help='Lookahead length', type=int, default=10)
    parser.add_argument('-o', '--order', help='Ignore order when typing links', action='store_true')
    args = parser.parse_args()
    return (args.dataset, args.input, args.output, args.word2id, args.perplexity, args.window_length, args.lookahead, args.order)

def get_most_likely(pvect, word2id, lookahead_offset, perplexity): 
    pvect = [item * perplexity for item in pvect[:len(word2id)]]
    largest = max(pvect)
    index = pvect.index(largest)
    output = word2id[index]
    return output, largest

def print_progress(current, total, size=20): 
    n = round((current / total) * size)
    sys.stdout.write('|{}{}|\r'.format('#' * n, ' ' * (size-n)))

def update_type_labels(type_labels, one, two, order, contval):
    v1 = '{} {}'.format(one, two)
    v2 = '{} {}'.format(two, one)
    if v1 not in type_labels: 
        type_labels[v1] = 'new_event_{}'.format(contval)
        if not order: 
            type_labels[v2] = 'new_event_{}'.format(contval)
        contval += 1
    return type_labels, contval

def process_single_lookahead(dataset, window_length, word2id_path, perplexity_path, incoming_path, outgoing_path, lookahead_length, type_labels, lookahead_offset, order, contval): 
    output = open(outgoing_path, 'w')
    word2id_dict = reader.readin_word2id(word2id_path)
    word2id = [None for item in range(len(word2id_dict))]
    f = open(perplexity_path, 'r')
    perplexity = 1 / float(f.read().strip())
    f.close()
    for item in word2id_dict: word2id[word2id_dict[item]] = item
    for i, line in enumerate(open(incoming_path, 'r')): 
        print_progress(i, len(dataset))
        line = [float(i.strip()) for i in line.split(',')]
        most_likely, probability = get_most_likely(line, word2id, lookahead_offset, perplexity)
        lookahead = dataset[i+1:i+1+lookahead_length]
        j = i + lookahead_offset
        if j >= len(dataset) or dataset[j] != most_likely: continue
        type_labels, contval = update_type_labels(type_labels, dataset[i], dataset[j], order, contval)
        output.write('{} {} {} {}\n'.format(i, j, probability, type_labels['{} {}'.format(dataset[i], dataset[j])]))
    output.close()
    return type_labels, contval

def get_continue_value(dataset): 
    output = 0
    for item in dataset: 
        if item.startswith('new_event_'): 
            number = int(item.split('_')[-1])
            if item >= output: output = item + 1
    return output

def load_dataset(path): 
    global file_names
    output = []
    for f in file_names:
        fh = open(os.path.join(path, f), 'r')
        output.extend(fh.read().split())
        fh.close()
    return output

def main(): 
    d, i, o, w2i, perp, wl, ll, order = getargs()
    n = 1
    incoming = i.format(n)
    outgoing = o.format(n)
    word2id = w2i.format(n)
    perplexity = perp.format(n)
    type_labels = {}
    dataset = load_dataset(d)
    contval = get_continue_value(dataset)
    while os.path.exists(incoming): 
        print(incoming)
        type_labels, contval = process_single_lookahead(dataset, wl, word2id, perplexity, incoming, outgoing, ll, type_labels, n, order, contval)
        n += 1
        incoming = i.format(n)
        outgoing = o.format(n)
        word2id = w2i.format(n)
        perplexity = perp.format(n)

if __name__ == '__main__':
    main()


