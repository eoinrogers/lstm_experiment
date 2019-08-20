import argparse, reader, os, sys

file_names = 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()

def getargs():
    parser = argparse.ArgumentParser('Build low-level (untyped) links between up to two events')
    parser.add_argument('dataset', help='Path to the dataset directory (note this should be a directory, not a file)', type=str)
    parser.add_argument('input', help='Prototype for the path to the input file', type=str)
    parser.add_argument('output', help='Prototype for the path to output file', type=str)
    parser.add_argument('word2id', help='Prototype for the path to the word2id file', type=str)
    parser.add_argument('-w', '--window_length', help='Window length', type=int, default=30)
    parser.add_argument('-l', '--lookahead', help='Lookahead length', type=int, default=10)
    args = parser.parse_args()
    return (args.dataset, args.input, args.output, args.word2id, args.window_length, args.lookahead)

def get_most_likely(pvect, word2id, number): 
    pvect = pvect[:]
    output = []
    print( max(pvect), len(pvect))
    for i in range(number): 
        most_probable = pvect.index(max(pvect))
        largest = pvect.pop(most_probable)
        output.append(word2id[most_probable])
    return output, largest

def compare_to_lookahead_in_order(most_likely, lookahead): 
    for item in most_likely: 
        if item in lookahead: return lookahead.index(item)

def print_progress(current, total, size=20): 
    n = round((current / total) * size)
    sys.stdout.write('|{}{}|\r'.format('#' * n, ' ' * (size-n)))

def process_single_lookahead(dataset, window_length, word2id_path, incoming_path, outgoing_path, lookahead_length, n = 3): 
    output = open(outgoing_path, 'w')
    word2id_dict = reader.readin_word2id(word2id_path)
    word2id = [None for item in range(len(word2id_dict))]
    for item in word2id_dict: word2id[word2id_dict[item]] = item
    for i, line in enumerate(open(incoming_path, 'r')): 
        #print_progress(i, len(dataset))
        line = [float(i.strip()) for i in line.split(',')]
        most_likely, probability = get_most_likely(line, word2id, n)
        lookahead = dataset[i:i+1+lookahead_length]
        j = compare_to_lookahead_in_order(most_likely, lookahead)
        if j == None: continue
        j += i + 1 + lookahead_length
        output.write('{} {} {}\n'.format(i, j, probability))

def main(): 
    global file_names
    d, i, o, w2i, wl, ll = getargs()
    n = 1
    incoming = i.format(n)
    outgoing = o.format(n)
    word2id = w2i.format(n)
    dataset = []
    for f in file_names: 
        dataset.extend(open(os.path.join(d, f), 'r').read().split())
    while os.path.exists(incoming): 
        print(incoming)
        process_single_lookahead(dataset, wl, word2id, incoming, outgoing, ll)
        n += 1
        incoming = i.format(n)
        outgoing = o.format(n)

main()
