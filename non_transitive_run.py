import gen_links, integrate_links as intlks, subprocess, random, os

def run_network(training_data, network_save_path, probability_file_proto, word2id_file_proto, testing_data, perplexity_file_proto, increase_by, layer_mult, lr_degrade_pt): 
    #python3 ptb_word_lm.py --data_path=$K3_TRAIN_ROOT --save_path=$K3_TRAIN_ROOT/$INDEX --probs=$PROBABILITY_FILE --word2id=$WORD2ID_FILE --test=$K3_TEST_ROOT --perplex=$PERPLEXITY_FILE
    args = ['--data_path={}'.format(training_data), '--save_path={}'.format(network_save_path), \
            '--probs={}'.format(probability_file_proto), '--word2id={}'.format(word2id_file_proto), \
            '--test={}'.format(testing_data), '--perplex={}'.format(perplexity_file_proto), '--increase={}'.format(increase_by), '--lmult={}'.format(layer_mult), \
            '--lr_degr={}'.format(lr_degrade_pt)] 
    full_command = ['python3', 'ptb_word_lm.py'] + args
    subprocess.run(full_command)

def build_delta_files(probability_file_proto, delta_file_proto): 
    args = [probability_file_proto, delta_file_proto]
    full_command = ['python3', 'deltify.py'] + args
    subprocess.run(full_command)

# args.dataset, args.input, args.output, args.word2id, args.perplexity, args.window_length, args.lookahead
def generate_links(testing_data, delta_file_proto, ll_links_file_proto, word2id_file_proto, perplexity_file_proto, window_length, lookahead_length): 
    args = [testing_data, delta_file_proto, ll_links_file_proto, word2id_file_proto, perplexity_file_proto, \
            window_length, lookahead_length]
    gen_links.main(args)

# args.dataset, args.linkproto, args.ground, args.destination, args.newdata, args.newground
def integrate_links(testing_data, ll_links_file_proto, incoming_types_file, outgoing_types_file, ground_file, final_linkset, new_dataset_dir, new_ground_file, \
                    min_occur_threshold, sizeacct): 
    args = [testing_data, ll_links_file_proto, incoming_types_file, outgoing_types_file, ground_file, final_linkset, new_dataset_dir, new_ground_file, \
            min_occur_threshold, sizeacct]
    print('fncdsk')
    intlks.main(args)

def mkdir(path): 
    try: os.mkdir(path)
    except FileExistsError: pass

def shuffle_list(l): 
    indices = []
    while len(indices) < len(l): 
        i = random.randint(0, len(l) - 1)
        if i not in indices: indices.append(i)
    return [l[i] for i in indices]

# Write out a randomised repeat of the new (output) dataset to realise John's idea for this layer. 
def expand_new_dataset(incoming_dataset_dir, outgoing_dataset_dir, incoming_ground_file, outgoing_ground_file, n): 
    # Load old ground truth AND the old dataset
    ground = intlks.load_ground_truth(incoming_ground_file)
    dataset = gen_links.load_dataset(incoming_dataset_dir)
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
        new_dataset.extend(d)
        new_ground.extend([g] * len(d))
    print(len(new_dataset))
    
    # Write out the results
    string = 'Incoming files:\n{}\n{}\n\nOutgoing files:\n{}\n{}'.format(incoming_dataset_dir, incoming_ground_file, outgoing_dataset_dir, outgoing_ground_file)
    print(string)
    f = open('deleteme', 'w')
    f.write(string)
    f.close()
    intlks.save_dataset(new_dataset, outgoing_dataset_dir)
    intlks.save_ground_truth(new_ground, outgoing_ground_file)

def copy_dataset(incoming_dataset_dir, outgoing_dataset_dir, incoming_ground_file, outgoing_ground_file): 
    for fname in 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split(): 
        subprocess.run(['cp', os.path.join(incoming_dataset_dir, fname), os.path.join(outgoing_dataset_dir, fname)])
    subprocess.run(['cp', incoming_ground_file, outgoing_ground_file])

def run_for_single_layer(input_training_data_dir, input_testing_data_dir, network_save_path, probability_file_proto, word2id_file_proto, perplexity_file_proto, \
                         delta_file_proto, ll_links_file_proto, incoming_types_file, window_length, lookahead_length, output_training_data_dir, output_testing_data_dir, \
                         input_training_ground_file, output_training_ground_file, output_testing_ground_file, final_linkset, outgoing_types_file, min_occur_threshold, \
                         sizeacct, increase_by, copy_dataset, layer_mult, lr_degrade_pt): 
    increase = 0
    for i in range(lookahead_length): 
        network = os.path.join(network_save_path, str(i + 1))
        mkdir(network)
        run_network(input_training_data_dir, network, probability_file_proto, word2id_file_proto, input_testing_data_dir, perplexity_file_proto, increase, layer_mult, lr_degrade_pt)
        if increase_by > 0: increase += increase_by 
    build_delta_files(probability_file_proto, delta_file_proto)
    generate_links(input_testing_data_dir, delta_file_proto, ll_links_file_proto, word2id_file_proto, perplexity_file_proto, window_length, lookahead_length)
    integrate_links(input_testing_data_dir, ll_links_file_proto, incoming_types_file, outgoing_types_file, input_training_ground_file, final_linkset, output_testing_data_dir, \
                    output_testing_ground_file, min_occur_threshold, sizeacct)
    expand_new_dataset(output_testing_data_dir, output_training_data_dir, output_testing_ground_file, output_training_ground_file, copy_dataset)

def main(input_training_data_dir, input_testing_data_dir, input_training_ground_file, working_dir, num_layers, window_length, lookahead_length, min_occur_threshold, sizeacct, \
         layer_increase=1.2, increase_by=1, lr_degrade_pt=.6, lr_degrade_inc=.1, purge_old=True, copy_dataset=5): 
    if purge_old and os.path.isdir(working_dir): 
        subprocess.run('rm -r {}'.format(working_dir).split())
    if not os.path.isdir(working_dir): 
        subprocess.run('mkdir {}'.format(working_dir).split())
    assert(lr_degrade_pt >= 0  and lr_degrade_pt <= 1)
    incoming_types_file = 'NULL'
    lm = 1
    for i in range(0, num_layers): 
        abort = i < 1
        i += 1
        cd = copy_dataset + (i * 3) 
        full_path = os.path.join(working_dir, 'Layer {}'.format(i))
        if os.path.exists(full_path) and not abort: 
            os.remove(full_path) 
        mkdir(full_path)
        for j in 'deltas misc test train'.split(): 
            mkdir(os.path.join(full_path, j))
        for j in 'll_links networks perplexities probabilities word2ids'.split(): 
            mkdir(os.path.join(full_path, os.path.join('misc', j)))
        probs_proto = os.path.join(full_path, 'misc/probabilities/offset_{}')
        word2ids_proto = os.path.join(full_path, 'misc/word2ids/offset_{}')
        perplex_proto = os.path.join(full_path, 'misc/perplexities/offset_{}')
        deltas_proto = os.path.join(full_path, 'deltas/offset_{}')
        ll_proto = os.path.join(full_path, 'misc/ll_links/offset_{}')
        outgoing_types_file = os.path.join(full_path, 'typeinfo.txt')
        output_training_dir = os.path.join(full_path, 'train')
        output_testing_dir = os.path.join(full_path, 'test')
        output_training_ground_file = os.path.join(full_path, 'train_ground.txt')
        output_testing_ground_file = os.path.join(full_path, 'test_ground.txt')
        linkset_file = os.path.join(full_path, 'linkset.txt')
        if not abort: 
            run_for_single_layer(input_training_data_dir, input_testing_data_dir, os.path.join(full_path, 'misc/networks'), \
                                 probs_proto, word2ids_proto, perplex_proto, deltas_proto, ll_proto, incoming_types_file, window_length, lookahead_length, \
                                 output_training_dir, output_testing_dir, input_training_ground_file, output_training_ground_file, \
                                 output_testing_ground_file, linkset_file, outgoing_types_file, min_occur_threshold, sizeacct, increase_by, cd, lm, lr_degrade_pt)
        input_training_data_dir = output_training_dir
        input_testing_data_dir = output_testing_dir
        input_training_ground_file = output_training_ground_file
        incoming_types_file = outgoing_types_file
        lm *= layer_increase
        lr_degrade_pt = min(1, lr_degrade_pt + lr_degrade_inc)

if __name__ == '__main__':
    import time
    start_time = time.time()
    main('/home/eoin/programming/newlstm/experiment_thing/train_data', '/home/eoin/programming/newlstm/experiment_thing/test_data', \
         '/media/eoin/BigDisk/kyoto3/k3_ground_non_interleaved.txt', '/media/eoin/BigDisk/hierarchy', 2, 20, 10, 3, True, purge_old=False)
    print('Done.\nThis took {} seconds'.format(time.time() - start_time))
    #main('/media/eoin/BigDisk/hierarchy/Layer 1/train', '/media/eoin/BigDisk/hierarchy/Layer 1/test', '/media/eoin/BigDisk/hierarchy/Layer 1/test_ground.txt', '/media/eoin/BigDisk/hierarchy', 5, 20, 10)

