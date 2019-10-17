# Ground truth: /media/eoin/BigDisk/kyoto3/k3_ground_non_interleaved.txt
# Dataset: /home/eoin/programming/newlstm/experiment_thing/test_data
# https://stackoverflow.com/questions/3183149/most-efficient-way-to-calculate-levenshtein-distance

file_names = 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()
import os, math

def load_dataset(path): 
    global file_names
    output = []
    for f in file_names:
        fh = open(os.path.join(path, f), 'r')
        output.extend(fh.read().split())
        fh.close()
    return output

def load_ground_truth(path): 
    handler = open(path, 'r')
    for line in handler: 
        line = line.strip()
    handler.close()
    line = [[int(i) for i in range(len(item)) if item[i] == '1'] for item in line.split()]
    return line

def ground_length(ground): 
    biggest = 0
    for item in ground: 
        for subitem in item: 
            if subitem > biggest: biggest = subitem
    return biggest + 1

def edit_distance(a, b): 
    matrix = [[0 for i in range(len(b)+1)] for j in range(len(a)+1)]
    for i in range(1, len(a)+1): 
        matrix[i][0] = i
    for j in range(1, len(b)+1): 
        matrix[0][j] = j
    for j in range(1, len(b)+1): 
        for i in range(1, len(a)+1): 
            substitution = 0 if a[i-1] == b[j-1] else 1
            matrix[i][j] = min([matrix[i-1][j]+1, matrix[i][j-1]+1, matrix[i-1][j-1]+substitution])
    return matrix[-1][-1]

def description_length(sequence): 
    types = list(set(sequence))
    return len(sequence) * math.ceil(math.log(len(types), 2))

def edit_distance_fast(a, b, memoised): 
    string = '{}, {}'.format(a, b)
    if string not in memoised: memoised[string] = edit_distance(a, b)
    return memoised[string] 

def __compress_internal(sequence, pattern, window_size, memoised): 
    threshold = len(sequence) * .1
    if window_size > threshold: return sequence
    output = []
    skip = 0
    for i in range(0, len(sequence)-window_size): 
        if skip > 0: 
            skip -= 1
            continue
        window = sequence[i:i+window_size]
        if edit_distance_fast(pattern, window, memoised) < threshold: 
            output.append('new_event')
            skip = window_size
        else: output.append(sequence[i])
    output.extend(sequence[i+1:])
    return output

def compress_sequence(sequence, pattern, memoised): 
    max_window_len = round(len(sequence) * .1)
    min_window_len = round(len(pattern))
    window_size = max_window_len
    while window_size > min_window_len: 
        sequence = __compress_internal(sequence, pattern, window_size, memoised)
        max_window_len = round(len(sequence) * .1)
        window_size -= 1
        if window_size > max_window_len: window_size = max_window_len
    return sequence

'''def compress_sequence(sequence, pattern, memoised): 
    max_window_len = round(len(sequence) * .1)
    min_window_len = round(len(pattern) - 1)
    window_size = 2
    old_len = len(sequence) + 1
    while old_len > len(sequence): 
        old_len = len(sequence)
        sequence = __compress_internal(sequence, pattern, window_size, memoised)
        window_size += 1
    return sequence'''

def description_length_after_compression(sequence, pattern, memoised): 
    seq = compress_sequence(sequence, pattern, memoised)
    return description_length(seq + ['||'] + pattern), seq

def compression_rating(sequence, pattern, memoised): 
    dld = description_length(sequence)
    dlp = description_length(pattern)
    dlc, seq = description_length_after_compression(sequence, pattern, memoised)
    return dld / (dlp+dlc), seq

def extend_pattern(dataset, patterns, memoised): 
    one, two, best_compression = None, None, 0
    for i in range(len(patterns)-1): 
        percent = round((i / (len(patterns)-2))*100)
        print('{}%\r'.format(percent), end='')
        new_pattern = patterns[i] + patterns[i+1]
        compression, _ = compression_rating(dataset, new_pattern, memoised)
        if compression > best_compression: one, two, best_compression = patterns[i], patterns[i + 1], compression
    ones, twos = [], []
    for i in range(len(patterns)-1): 
        if patterns[i] == one and patterns[i+1] == two: 
            ones.append(i)
            twos.append(i + 1)
    return [((one + two) if i in ones else pattern) for i, pattern in enumerate(patterns) if i not in twos] 

def save_activities(patterns, destination): 
    handler = open(destination, 'w')
    written = []
    for pattern in patterns: 
        if len(pattern) == 1: continue
        string = ''.join(['{}, '.format(item) for item in pattern])[:-2]
        if string not in written: 
            handler.write('{}\n'.format(string))
            written.append(string)
    handler.close()

def run(dataset, destination, save_frequency=1): 
    patterns = [[item] for item in dataset]
    i = 0
    old_length = len(patterns)
    memoised_dict = {}
    while len(patterns) > 8: 
        print(i, len(patterns), len(memoised_dict))
        if destination != None and i % save_frequency == 0: save_activities(patterns, destination)
        patterns = extend_pattern(dataset, patterns, memoised_dict)
        if len(patterns) == old_length: break
        old_length = len(patterns)
        i += 1
    if destination != None: save_activities(patterns, destination)
    return patterns

ground = load_ground_truth('/media/eoin/BigDisk/kyoto3/k3_ground_non_interleaved.txt')
dataset = load_dataset('/home/eoin/programming/newlstm/experiment_thing/test_data')

run(dataset, '/media/eoin/BigDisk/cook_patterns2.txt')


