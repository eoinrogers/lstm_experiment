'''
Offset: 1, Accuracy: 98.79%
Offset: 2, Accuracy: 97.85%
Offset: 3, Accuracy: 97.60%
Offset: 4, Accuracy: 97.37%
Offset: 5, Accuracy: 96.64%
Offset: 6, Accuracy: 96.62%
Offset: 7, Accuracy: 96.53%
Offset: 8, Accuracy: 96.15%
Offset: 9, Accuracy: 95.94%
Offset: 10, Accuracy: 95.95%
Offset: 11, Accuracy: 95.35%
Offset: 12, Accuracy: 95.78%
Offset: 13, Accuracy: 94.41%
Offset: 14, Accuracy: 94.48%
Offset: 15, Accuracy: 94.98%
Offset: 16, Accuracy: 95.05%
Offset: 17, Accuracy: 93.84%
Offset: 18, Accuracy: 93.86%
Offset: 19, Accuracy: 94.81%
Offset: 20, Accuracy: 94.47%
'''

import os, reader

def pre_load_everything(shell_script, probabilities, word2id, test_directory): 
    probs_files = '/media/eoin/BigDisk/run_num_layers=4_window_length=20_lookahead_length=20_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 4/misc/probabilities/offset_{}'
    word2id_files = '/media/eoin/BigDisk/run_num_layers=4_window_length=20_lookahead_length=20_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 4/misc/word2ids/offset_{}'
    test_data = [os.path.join(test_directory, item) for item in 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()]
    data = []
    for item in test_data: 
        file_handler = open(item, 'r')
        file_contents = file_handler.read()
        data += [word.strip() for word in file_contents.split()]
        file_handler.close()
    return probs_files, word2id_files, data

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

def generate_lstm_predictions(probs_file, word2ids_file, lookahead_offset, n): 
    probabilities = probs_file.format(lookahead_offset)
    word2id_path = word2ids_file.format(lookahead_offset)
    word2id_dict = reader.readin_word2id(word2id_path)
    word2id = [None for item in range(len(word2id_dict))]
    for item in word2id_dict: word2id[word2id_dict[item]] = item
    with open(probabilities, 'r') as p: 
        for line in p: 
            vector = [float(item.strip()) for item in line.split(',')]
            top_n = sort_ids_by_probability(vector, n)
            yield [word2id[index] for index in top_n]

def eval_single_offset(probs_file, word2ids_file, data, lookahead_offset, n): 
    i = lookahead_offset
    score = 0
    for predictions in generate_lstm_predictions(probs_file, word2ids_file, lookahead_offset, n):
        if i >= len(data): break
        ground = data[i]
        if ground in predictions: score += 1
        i += 1
    return (score / i) * 100

if __name__ == '__main__':
    probs_files, words2id_files, data = pre_load_everything('run.sh', 'PROBABILITY_FILE', 'WORD2ID_FILE', '/media/eoin/BigDisk/run_num_layers=4_window_length=20_lookahead_length=20_min_occur_threshold=10_sizeacct=True_layer_increase=0_increase_by=0_lr_degrade_pt=0.9_lr_degrade_inc=0/Layer 3/test')
    offset = 1
    while os.path.exists(probs_files.format(offset)): 
        print('Offset: {}, Accuracy: {:.2f}%'.format(offset, eval_single_offset(probs_files, words2id_files, data, offset, 3)))
        offset += 1
    if offset == 1: 
        import sys
        print('No networks found', file=sys.stderr)






