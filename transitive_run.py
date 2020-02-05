import os, subprocess, shutil, new_link, random

def mkdir(path): 
    try: os.mkdir(path)
    except FileExistsError: pass

def run_network(training_data, network_save_path, probability_file, word2id_file, testing_data, perplexity_file, increase_by, layer_mult, lr_degrade_pt, window_length): 
    #python3 ptb_word_lm.py --data_path=$K3_TRAIN_ROOT --save_path=$K3_TRAIN_ROOT/$INDEX --probs=$PROBABILITY_FILE --word2id=$WORD2ID_FILE --test=$K3_TEST_ROOT --perplex=$PERPLEXITY_FILE
    args = ['--data_path={}'.format(training_data), '--save_path={}'.format(network_save_path), \
            '--probs={}'.format(probability_file), '--word2id={}'.format(word2id_file), \
            '--test={}'.format(testing_data), '--perplex={}'.format(perplexity_file), '--increase={}'.format(increase_by), '--lmult={}'.format(layer_mult), \
            '--lr_degr={}'.format(lr_degrade_pt)] 
    full_command = ['python3', 'ptb_word_lm.py'] + args
    subprocess.run(full_command)

def build_delta_files(probability_file_proto, delta_file_proto): 
    args = [probability_file_proto, delta_file_proto]
    full_command = ['python3', 'deltify.py'] + args
    subprocess.run(full_command)

def shuffle_list(l): 
    indices = []
    while len(indices) < len(l): 
        i = random.randint(0, len(l) - 1)
        if i not in indices: indices.append(i)
    return [l[i] for i in indices]

def expand_new_dataset(incoming_dataset_dir, outgoing_dataset_dir, incoming_ground_file, outgoing_ground_file, n): 
    # Load old ground truth AND the old dataset
    ground = new_link.load_ground_truth(incoming_ground_file)
    dataset = new_link.load_dataset(incoming_dataset_dir)
    gd_list = [] # (ground_item, [data]), ...
    accum = []
    current = ground[0]
    
    # For each item in the dataset, collect the events that are part of the current activity type
    # Each event-set is placed in a list called gd_list (ground-data list)
    for g, d in zip(ground, dataset): 
        #print(g, d, accum, current)
        if g == current: accum.append(d)
        else: 
            gd_list.append((current, accum))
            current, accum = g, [d]
    if len(accum) > 0: 
        gd_list.append((g, accum))
    
    # Re-build the old dataset, but build up the ground dataset (!) 
    new_dataset, new_ground = [], []
    gd_list *= n
    gd_list = shuffle_list(gd_list)
    for g, d in gd_list: 
        print('g, d =', g, d)
        new_dataset.extend(d)
        new_ground.extend([g] * len(d))
    print(len(new_dataset))
    
    # Write out the results
    string = 'Incoming files:\n{}\n{}\n\nOutgoing files:\n{}\n{}'.format(incoming_dataset_dir, incoming_ground_file, outgoing_dataset_dir, outgoing_ground_file)
    print(string)
    f = open('deleteme', 'w')
    f.write(string)
    f.close()
    new_link.save_dataset(new_dataset, outgoing_dataset_dir)
    new_link.save_ground_truth(new_ground, outgoing_ground_file)

def run_for_single_layer(input_training_data_dir, input_testing_data_dir, network_save_path, probs_proto, words2id_proto, perplex_proto, deltas_proto, incoming_types_file, window_length, lookahead_length, \
                         output_training_dir, output_testing_dir, input_training_ground_file, output_training_ground_file, output_testing_ground_file, linkset_file, outgoing_types_file, copy_dataset, increase_by, \
                         layer_mult, learning_rate_decay, cluster_threshold):
    for i in range(lookahead_length): 
        network = os.path.join(network_save_path, str(i + 1))
        mkdir(network)
        # input_training_data_dir, network, probability_file_proto, word2id_file_proto, input_testing_data_dir, perplexity_file_proto, increase, layer_mult, lr_degrade_pt, window_length
        run_network(input_training_data_dir, network.format(i+1), probs_proto.format(i+1), words2id_proto.format(i+1), input_testing_data_dir, perplex_proto.format(i+1), increase_by, layer_mult, \
                    learning_rate_decay, window_length)
    build_delta_files(probs_proto, deltas_proto)
    # input_testing_data_dir, delta_file_proto, destination, word2id_file_proto, perplexity_file_proto, window_length, lookahead_length
    new_link.generate_links(input_testing_data_dir, deltas_proto, linkset_file, words2id_proto, perplex_proto, window_length, lookahead_length)
    # input_testing_data_dir, input_training_ground_file, outgoing_types_file, final_linkset, output_testing_data_dir, output_testing_ground_file
    new_link.integrate_links(input_testing_data_dir, input_training_ground_file, outgoing_types_file, linkset_file, output_testing_dir, output_testing_ground_file, cluster_threshold)
    # output_testing_data_dir, output_training_data_dir, output_testing_ground_file, output_training_ground_file, copy_dataset
    expand_new_dataset(output_testing_dir, output_training_dir, output_testing_ground_file, output_training_ground_file, copy_dataset)

def main(input_training_data_dir, input_testing_data_dir, input_training_ground_file, working_dir, num_layers, window_length, lookahead_length, \
         copy_dataset=5, purge_old=True, ask_before_deleting=True, increase_by=0, layer_mult=1, lr_degrade=1, cluster_threshold=0): 
    if purge_old and os.path.isdir(working_dir): 
        if ask_before_deleting: 
            confirm = input('Are you sure you want to remove the old files? (Y/n): ')
            while confirm.lower() not in 'yn': confirm = input('Please type Y for yes or N for no: ')
        else: confirm = 'y'
        if confirm.lower() != 'y': 
            print('Exiting')
            exit()
        subprocess.run('rm -r {}'.format(working_dir).split())
    if not os.path.isdir(working_dir): 
        subprocess.run('mkdir {}'.format(working_dir).split())
    incoming_types_file = 'NULL'
    increase = 0
    layer_value = 1
    lr_value = 1
    for i in range(0, num_layers): 
        abort = i < 0
        i += 1
        full_path = os.path.join(working_dir, 'Layer {}'.format(i))
        if not abort: 
            if os.path.exists(full_path): 
                shutil.rmtree(full_path) 
            mkdir(full_path)
            for j in 'deltas misc test train'.split(): 
                mkdir(os.path.join(full_path, j))
            for j in 'networks perplexities probabilities word2ids'.split(): 
                mkdir(os.path.join(full_path, os.path.join('misc', j)))
        probs_proto = os.path.join(full_path, 'misc/probabilities/offset_{}')
        word2ids_proto = os.path.join(full_path, 'misc/word2ids/offset_{}')
        perplex_proto = os.path.join(full_path, 'misc/perplexities/offset_{}')
        deltas_proto = os.path.join(full_path, 'deltas/offset_{}')
        outgoing_types_file = os.path.join(full_path, 'typeinfo.txt')
        output_training_dir = os.path.join(full_path, 'train')
        output_testing_dir = os.path.join(full_path, 'test')
        output_training_ground_file = os.path.join(full_path, 'train_ground.txt')
        output_testing_ground_file = os.path.join(full_path, 'test_ground.txt')
        linkset_file = os.path.join(full_path, 'linkset.txt')
        if not abort: 
            run_for_single_layer(input_training_data_dir, input_testing_data_dir, os.path.join(full_path, 'misc/networks'), \
                                 probs_proto, word2ids_proto, perplex_proto, deltas_proto, incoming_types_file, window_length, \
                                 lookahead_length, output_training_dir, output_testing_dir, input_training_ground_file, \
                                 output_training_ground_file, output_testing_ground_file, linkset_file, outgoing_types_file, \
                                 copy_dataset, increase, layer_value, lr_value, cluster_threshold)
        input_training_data_dir = output_training_dir
        input_testing_data_dir = output_testing_dir
        input_training_ground_file = output_training_ground_file
        incoming_types_file = outgoing_types_file
        increase += increase_by
        layer_value *= layer_mult
        lr_value *= lr_degrade

if __name__ == '__main__':
    import time
    start_time = time.time()
    expand_new_dataset('/home/eoin/programming/newlstm/experiment_thing/test_data', '/home/eoin/programming/newlstm/experiment_thing/train2', \
                       '/media/eoin/BigDisk/kyoto3/k3_ground_non_interleaved.txt', '/home/eoin/programming/newlstm/experiment_thing/ground2.txt', 5);exit()
    main('/home/eoin/programming/newlstm/experiment_thing/train2', '/home/eoin/programming/newlstm/experiment_thing/test_data', \
         '/home/eoin/programming/newlstm/experiment_thing/ground2.txt', '/media/eoin/BigDisk/hierarchy', 4, 20, 10, purge_old=True, \
         increase_by=0, ask_before_deleting=True, layer_mult=1.5, lr_degrade=2)
    print('Done.\nThis took {} seconds'.format(time.time() - start_time))


