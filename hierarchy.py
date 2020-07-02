import os, links, lstm, compress, time


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
    print('desired output', desired_output_dir)
    network_proto = os.path.join(os.path.join(desired_output_dir, networks_dir), 'lookahead={}')
    probabilities_proto = os.path.join(os.path.join(desired_output_dir, probabilities_dir), 'lookahead={}')
    deltas_proto = os.path.join(os.path.join(desired_output_dir, deltas_dir), 'lookahead={}')
    vocabulary_file = os.path.join(desired_output_dir, vocab_file)
    lstm.run_after_file_prep(training_data, network_proto, probabilities_proto, deltas_proto, vocabulary_file, window_size, lookahead_size, batch_size, num_epochs, 
                             epoch_increment, embedding_size, num_layers)
    
    # Build the links
    thresholds_file = os.path.join(desired_output_dir, thresholds_file)
    linkset_file = os.path.join(desired_output_dir, linkset_file)
    linktypes_file = os.path.join(desired_output_dir, linktypes_file)
    typeforms_file = os.path.join(desired_output_dir, typeforms_file)
    output_uncompressed = os.path.join(desired_output_dir, output_uncompressed)
    links.build_links(training_data, probabilities_proto, vocabulary_file, thresholds_file, linkset_file, linktypes_file, typeforms_file, 
                      previous_type_forms, output_uncompressed, lookahead_size, threshold)
    
    # Compress the new dataset
    output_dir = os.path.join(desired_output_dir, output_dir)
    compress.compress_dataset(training_data, linkset_file, linktypes_file, output_dir, test_percent, valid_percent);print(output_dir, typeforms_file)
    
    return output_dir, typeforms_file


def run_for_many_layers(training_data, output_directory, window_size, lookahead_size, batch_size, epoch_increment, embedding_size, \
                        num_layers, num_network_layers, layerwise_layer_increment, layerwise_embed_mult, layerwise_epoch_increment='auto',
                        num_epochs=8, threshold=.6): 
    old_typeforms = None
    for i in range(num_layers): 
        layer_dir = os.path.join(output_directory, 'Layer {}'.format(i + 1))
        old_training_data = training_data
        training_data, old_typeforms = run_for_single_layer(training_data, old_typeforms, layer_dir, window_size, lookahead_size, \
                                                            batch_size, epoch_increment, round(embedding_size), round(num_network_layers), \
                                                            round(num_epochs) if type(num_epochs) != str else num_epochs, threshold)
        num_network_layers += layerwise_layer_increment
        embedding_size *= layerwise_embed_mult
        if layerwise_epoch_increment == 'auto': 
            num_epochs = lstm.estimate_epochs(num_epochs, old_training_data, training_data)
        else: num_epochs += layerwise_epoch_increment
        print(training_data, old_typeforms)


if __name__ == '__main__':
    #run_for_single_layer('/media/eoin/BigDisk/kyoto3/interleaved train', None, '/media/eoin/BigDisk/new test', 10, 10, 50, 1, 100, 3, 20)
    #run_for_single_layer('/media/eoin/BigDisk/new test/output', '/media/eoin/BigDisk/new test/type forms', '/media/eoin/BigDisk/newer test', 10, 10, 50, 1, 100, 3, 20)
    run_for_many_layers('/media/eoin/BigDisk/kyoto3/interleaved train', '/media/eoin/BigDisk/test', 10, 10, 50, 1, 120, 5, 4, 0, 1.02)


