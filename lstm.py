from tensorflow import keras
import os, random, sys
import numpy as np


def build_lstm(vocab_length, embedding_size, window_length, layer_map):
    output = keras.Sequential()
    output.add(keras.layers.Embedding(vocab_length, embedding_size, input_length=window_length))
    for i, size in enumerate(layer_map): 
        if i != len(layer_map) - 1: output.add(keras.layers.LSTM(size, return_sequences=True))
        else: output.add(keras.layers.LSTM(size, return_sequences=False))
    output.add(keras.layers.Dense(vocab_length, activation='softmax'))
    output.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return output


'/media/eoin/BigDisk/kyoto3/interleaved train'

file_names = 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()


def load_dataset(location): 
    global file_names
    output = []
    for fname in file_names:
        path = os.path.join(location, fname)
        f = open(path, 'r')
        output += f.read().split()
        f.close()
    return output


def split_dataset(dataset, test_percent):
    length = round(len(dataset) * test_percent)
    start = random.randint(0, len(dataset) - 1 - length)
    test = dataset[start:start+length]
    train = dataset[:start] + dataset[start+length:]
    return train, test


def get_vocab(dataset): 
    return list(set(dataset))


def load_vocab(path): 
    vocab_file = open(path, 'r')
    vocabulary = vocab_file.read().strip().split()
    vocab_file.close()
    return vocabulary


def save_vocab(vocab, destination): 
    string = ''.join(['{} '.format(item) for item in vocab])
    f = open(destination, 'w')
    f.write(string[:-1])
    f.close()


def numberify_dataset(dataset, vocab):
    return [vocab.index(item) for item in dataset]


def estimate_epochs(old_epochs, old_dataset, current_dataset, max_mult=2, max_epochs=None):
    old_vocab = len(get_vocab(load_dataset(old_dataset)))
    current_vocab = len(get_vocab(load_dataset(current_dataset)))
    print(old_vocab, current_vocab)
    multiplier = current_vocab / old_vocab
    multiplier = min(multiplier, max_mult) if max_mult is not None else multiplier
    output = multiplier * old_epochs
    return min(output, max_epochs) if max_epochs is not None else output


# Expected input dimension for embedding: (batch_size, window_length)
class BatchGen(keras.utils.Sequence):
    def __init__(self, numberified_dataset, batch_size, window_size, lookahead_index, vocabulary):
        self.data = numberified_dataset
        self.batch_size = batch_size
        self.win_size = window_size
        self.idx = lookahead_index
        self.vocab = vocabulary
        self.vocab_size = len(self.vocab)
    def __len__(self): 
        output = len(self.data) // self.batch_size
        if len(self.data) > output * self.batch_size: return output + 1
        return output
    def __getitem__(self, batch):
        final_batch = self.__len__() - 1 == batch
        batch_size = (len(self.data) % self.batch_size) if final_batch else self.batch_size
        features = np.ndarray(shape=(batch_size, self.win_size))
        labels = np.ndarray(shape=(batch_size, self.vocab_size))
        
        for i in range(batch_size):
            for j in range(self.win_size): 
                features[i, j] = self.data[batch + i + j]
            label = self.data[batch + i + j + self.idx]
            labels[i, :] = [(1 if j == label else 0) for j in range(self.vocab_size)]
        return features, labels


def prepare_dataset(location, vocab_file):
    raw_dataset = load_dataset(location)
    vocabulary = get_vocab(raw_dataset)
    save_vocab(vocabulary, vocab_file)
    numberified_dataset = numberify_dataset(raw_dataset, vocabulary)
    return raw_dataset, vocabulary, numberified_dataset


def train_networks(numberified_dataset, vocabulary, epochs, batch_size, window_size, lookahead_size, embedding_size, num_layers,
                   destination_proto, epoch_increment=0):
    output = []
    for i in range(lookahead_size):
        lstm = build_lstm(len(vocabulary), embedding_size, window_size, [max(20, round(embedding_size * .2))] * num_layers)
        lstm.fit(BatchGen(numberified_dataset, batch_size, window_size, i, vocabulary), epochs=round(epochs))
        output.append(lstm)
        save_path = destination_proto.format(i + 1)
        lstm.save(save_path)
        epochs += epoch_increment
    return output


def load_network(destination_proto, lookahead_index):
    path = destination_proto.format(lookahead_index)
    return keras.models.load_model(path)



def load_networks(destination_proto, lookahead_size, verbose): 
    output = []
    for i in range(lookahead_size):
        if verbose: print('Loading network {}'.format(i + 1))
        output.append(load_network(destination_proto, i + 1))
    return output


def query_network(network, destination, numberified_dataset, batch_size, window_size, lookahead_index, vocabulary,
                  verbose):
    f = open(destination, 'w')
    if type(vocabulary) == str: # Allow users to pass the vocab file path, rather than the list
        vocabulary = load_vocab(vocabulary)
    batch_gen = BatchGen(numberified_dataset, batch_size, window_size, lookahead_index, vocabulary)
    for batch_num in range(len(batch_gen)):
        if verbose: print('\rPredicting with network {}: {}%'.format(lookahead_index, round((batch_num / len(batch_gen)) * 100)), end='')
        x, y = batch_gen[batch_num]
        predictions = network.predict(x)
        for row in predictions: 
            string = ''
            for col in row: string += '{} '.format(col)
            f.write(string[:-1] + '\n')
    if verbose: print('\rPredicting with network {}: 100%'.format(lookahead_index))
    f.close()


def query_networks(network_destination_proto, output_destination_proto, numberified_dataset, window_size, lookahead_size, vocabulary,
                   batch_size=50, verbose=True):
    lstms = load_networks(network_destination_proto, lookahead_size, verbose)
    for lookahead_index in range(lookahead_size): 
        destination = output_destination_proto.format(lookahead_index + 1)
        query_network(lstms[lookahead_index], destination, numberified_dataset, batch_size, window_size, lookahead_index + 1, vocabulary, 
                      verbose)


def get_query_results_length_and_vocab(query_folder_proto, lookahead_index): 
    f = open(query_folder_proto.format(lookahead_index), 'r')
    line_count = 0
    vocab_count = 0
    contents = []
    for line in f: 
        line_count += 1
        line = [float(item) for item in line.strip().split()]
        if vocab_count == 0: vocab_count = len(line)
        contents.append(line)
    return line_count, vocab_count, contents


query_files = {}
query_counts = {}
query_vocabs = {}
def preload_query_files(query_folder_proto, lookahead_index): 
    global query_files, query_counts, query_vocabs
    
    if lookahead_index not in query_files: 
        counts, vocabs, contents = get_query_results_length_and_vocab(query_folder_proto, lookahead_index)
        query_files[lookahead_index] = np.array(contents)
        query_counts[lookahead_index] = counts
        query_vocabs[lookahead_index] = vocabs
 

def load_query_results_fast(query_folder_proto, lookahead_index, subsample_rate=.2): 
    global query_files, query_vocabs
    preload_query_files(query_folder_proto, lookahead_index)
    output = np.ndarray(shape=(1, query_vocabs[lookahead_index]))
    for line in query_files[lookahead_index]: 
        if random.random() <= subsample_rate:
            output[0, :] = line
            yield output


def deltify_single_lookahead(incoming_proto, outgoing_proto, lookahead_index, vocabulary, batch_size,
                             verbose): 
    # Build a vector to hold the previous probabilities
    previous = [0 for i in range(len(vocabulary))] 
    
    # Open the output file
    output = open(outgoing_proto.format(lookahead_index), 'w')
    
    # Display progress if requested
    if verbose: 
        print('Computing deltas for lookahead {}... '.format(lookahead_index), end='')
        sys.stdout.flush()
    
    # Iterate through each row
    for data in load_query_results_fast(incoming_proto, lookahead_index, batch_size): 
        for idx, row in enumerate(data):
            # Compute the delta for this row
            delta = []
            for i, col in enumerate(row): delta.append(col - previous[i])
            
            # Write the delta to a file
            string = ''.join(['{} '.format(item) for item in delta])
            output.write(string[:-1] + '\n')
            
            # Replace the previous vector
            previous = []
            for col in row: previous.append(col)
    
    # Display progress if requested
    if verbose: print('Done!')
    
    # Close the output file
    output.close()


def deltify(incoming_proto, outgoing_proto, lookahead_size, vocabulary, batch_size=50, verbose=True): 
    for lookahead_index in range(1, lookahead_size + 1): 
        deltify_single_lookahead(incoming_proto, outgoing_proto, lookahead_index, vocabulary, batch_size, verbose)


def run_after_file_prep(dataset_directory, saved_lstm_proto, raw_probabilities_proto, deltas_proto, vocab_file, window_size, lookahead_size, 
                        batch_size, num_epochs, epoch_increment, embedding_size, num_layers, do_train=True, do_deltify=True, verbose=True):
    # Read in the dataset and build a new vocabulary
    _, vocabulary, dataset = prepare_dataset(dataset_directory, vocab_file)
    
    # Build and train new LSTMs if asked
    if do_train: 
        train_networks(dataset, vocabulary, num_epochs, batch_size, window_size, lookahead_size, embedding_size, num_layers,
                       saved_lstm_proto, epoch_increment)
        query_networks(saved_lstm_proto, raw_probabilities_proto, dataset, window_size, lookahead_size, vocabulary, batch_size, verbose)
    
    # Build delta files if asked
    deltify(raw_probabilities_proto, deltas_proto, lookahead_size, vocabulary, batch_size, verbose)


if __name__ == '__main__':
    data_dir = '/media/eoin/BigDisk/kyoto3/interleaved train'
    networks = '/media/eoin/BigDisk/blah/lstms/lookahead={}'
    probabilities = '/media/eoin/BigDisk/blah/raw probabilities/lookahead={}'
    deltas = '/media/eoin/BigDisk/blah/deltas/lookahead={}'
    vocab_file = '/media/eoin/BigDisk/blah/vocab'
    window_size = 10
    lookahead_size = 10
    batch_size = 50
    num_epochs = 3
    epoch_increment = 1
    embedding_size = 100
    num_layers = 2
    
    run_after_file_prep(data_dir, networks, probabilities, deltas, vocab_file, window_size, lookahead_size, batch_size, num_epochs, 
                        epoch_increment, embedding_size, num_layers)

