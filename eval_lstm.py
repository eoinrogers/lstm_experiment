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

import os, hierarchy

probs_file = hierarchy.load_parameter_from_shell_script('run.sh', 'PROBABILITY_FILE')


def pre_load_everything(shell_script, probabilities, word2id, test_directory): 
    probs_files = hierarchy.load_parameter_from_shell_script(shell_script, probabilities)
    word2id_files = hierarchy.load_parameter_from_shell_script(shell_script, word2id)
    test_data = [os.path.join(test_directory, item) for item in 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()]
    data = []
    for item in test_data: 
        file_handler = open(item, 'r')
        file_contents = file_handler.read()
        data += [word.strip() for word in file_contents.split()]
        file_handler.close()
    return probs_files, word2id_files, data

def generate_lstm_predictions(probs_file, word2ids_file, lookahead_offset, n): 
    probabilities = probs_file.format(lookahead_offset)
    word2id_path = word2ids_file.format(lookahead_offset)
    word2id_dict = hierarchy.integrate.reader.readin_word2id(word2id_path)
    word2id = [None for item in range(len(word2id_dict))]
    for item in word2id_dict: word2id[word2id_dict[item]] = item
    with open(probabilities, 'r') as p: 
        for line in p: 
            vector = [float(item.strip()) for item in line.split(',')]
            top_n = hierarchy.integrate.sort_ids_by_probability(vector, n)
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
    probs_files, words2id_files, data = pre_load_everything('run.sh', 'PROBABILITY_FILE', 'WORD2ID_FILE', '/home/eoin/programming/lstm/test_data')
    offset = 1
    while os.path.exists(probs_files.format(offset)): 
        print('Offset: {}, Accuracy: {:.2f}%'.format(offset, eval_single_offset(probs_files, words2id_files, data, offset, 3)))
        offset += 1






