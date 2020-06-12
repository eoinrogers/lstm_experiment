import os, links, lstm, compress


def mkdir(path): 
    path = path.split('/')
    absolute = path[0] == ''
    
    current = '/' if absolute else './'
    for item in path: 
        if item == '': continue
        current = os.path.join(current, item)
        if not os.path.exists(current):
            os.mkdir(current) 


networks_dir = 'lstms'
deltas_dir = 'deltas'
output_dir = 'new dataset'
probabilities_dir = 'raw probabilities'
output_dir = 'output'
output_uncompressed = 'output uncompressed'
vocab_file = 'vocabulary'
thresholds_file = 'thresholds'
linkset_file = 'linkset'
linktypes_file = 'link types'
typeforms_file = 'type forms'
test_percent = .1
valid_percent = .2


def run_for_single_layer(training_data, previous_type_forms, desired_output_dir, window_size, lookahead_size, batch_size, epoch_increment, 
                         embedding_size, num_layers, num_epochs, threshold=.6): 
    global vocab_file, thresholds_file, linkset_file, linktypes_file, typeforms_file, output_uncompressed, test_percent, valid_percent, \
           output_dir
    
    # Create the required directories
    required = [networks_dir, deltas_dir, output_dir, probabilities_dir]
    for directory in required: 
        mkdir(os.path.join(desired_output_dir, directory))
    
    # Train the LSTMs
    network_proto = os.path.join(os.path.join(desired_output_dir, networks_dir), 'lookahead={}')
    probabilities_proto = os.path.join(os.path.join(desired_output_dir, probabilities_dir), 'lookahead={}')
    deltas_proto = os.path.join(os.path.join(desired_output_dir, deltas_dir), 'lookahead={}')
    vocab_file = os.path.join(desired_output_dir, vocab_file)
    lstm.run_after_file_prep(training_data, network_proto, probabilities_proto, deltas_proto, vocab_file, window_size, lookahead_size, batch_size, num_epochs, 
                             epoch_increment, embedding_size, num_layers)
    
    # Build the links
    thresholds_file = os.path.join(desired_output_dir, thresholds_file)
    linkset_file = os.path.join(desired_output_dir, linkset_file)
    linktypes_file = os.path.join(desired_output_dir, linktypes_file)
    typeforms_file = os.path.join(desired_output_dir, typeforms_file)
    output_uncompressed = os.path.join(desired_output_dir, output_uncompressed)
    links.build_links(training_data, probabilities_proto, vocab_file, thresholds_file, linkset_file, linktypes_file, typeforms_file, 
                      previous_type_forms, output_uncompressed, lookahead_size, threshold)
    
    # Compress the new dataset
    output_dir = os.path.join(desired_output_dir, output_dir)
    compress.compress_dataset(training_data, linkset_file, linktypes_file, output_dir, test_percent, valid_percent)
    
    return output_dir, typeforms_file


if __name__ == '__main__':
    #run_for_single_layer('/media/eoin/BigDisk/kyoto3/interleaved train', None, '/media/eoin/BigDisk/new test', 10, 10, 50, 1, 100, 3, 20)
    run_for_single_layer('/media/eoin/BigDisk/new test/output', '/media/eoin/BigDisk/new test/type forms', '/media/eoin/BigDisk/newer test', 10, 10, 50, 1, 100, 3, 20)


