import gen_links, integrate_links as intlks, subprocess, random, os

def run_network(training_data, network_save_path, probability_file_proto, word2id_file_proto, testing_data, perplexity_file_proto): 
    #python3 ptb_word_lm.py --data_path=$K3_TRAIN_ROOT --save_path=$K3_TRAIN_ROOT/$INDEX --probs=$PROBABILITY_FILE --word2id=$WORD2ID_FILE --test=$K3_TEST_ROOT --perplex=$PERPLEXITY_FILE
    args = ['--data_path={}'.format(training_data), '--save_path={}'.format(network_save_path), \
            '--probs={}'.format(probability_file_proto), '--word2id={}'.format(word2id_file_proto), \
            '--test={}'.format(testing_data), '--perplex={}'.format(perplexity_file_proto)] 
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
def integrate_links(testing_data, ll_links_file_proto, ground_file, final_linkset, new_dataset_dir, new_ground_file): 
    args = [testing_data, ll_links_file_proto, ground_file, final_linkset, new_dataset_dir, new_ground_file]
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

def expand_new_dataset(incoming_dataset_dir, outgoing_dataset_dir, incoming_ground_file, outgoing_ground_file, n=5): 
    ground = intlks.load_ground_truth(incoming_ground_file)
    dataset = gen_links.load_dataset(incoming_dataset_dir)
    gd_list = [] # (ground_item, [data]), ...
    accum = []
    current = ground[0]
    for g, d in zip(ground, dataset): 
        if g == current: accum.append(d)
        else: 
            gd_list.append((g, accum))
            current, accum = g, [d]
    if len(accum) > 0: 
        gd_list.append((g, accum))
    new_dataset, new_ground = [], []
    gd_list *= n
    gd_list = shuffle_list(gd_list)
    for g, d in gd_list: 
        new_dataset.extend(d)
        new_ground.extend([g] * len(d))
    intlks.save_dataset(new_dataset, outgoing_dataset_dir)
    intlks.save_ground_truth(new_ground, outgoing_ground_file)

def run_for_single_layer(input_training_data_dir, input_testing_data_dir, network_save_path, probability_file_proto, word2id_file_proto, perplexity_file_proto, \
                         delta_file_proto, ll_links_file_proto, window_length, lookahead_length, output_training_data_dir, output_testing_data_dir, \
                         input_training_ground_file, output_training_ground_file, output_testing_ground_file, final_linkset): 
    for i in range(lookahead_length): 
        network = os.path.join(network_save_path, str(i + 1))
        mkdir(network)
        run_network(input_training_data_dir, network, probability_file_proto, word2id_file_proto, input_testing_data_dir, perplexity_file_proto)
    build_delta_files(probability_file_proto, delta_file_proto)
    generate_links(input_testing_data_dir, delta_file_proto, ll_links_file_proto, word2id_file_proto, perplexity_file_proto, window_length, lookahead_length)
    integrate_links(input_testing_data_dir, ll_links_file_proto, input_training_ground_file, final_linkset, output_testing_data_dir, output_training_ground_file)
    expand_new_dataset(output_testing_data_dir, output_training_data_dir, output_training_ground_file, output_testing_ground_file)

def main(input_training_data_dir, input_testing_data_dir, input_training_ground_file, working_dir, num_layers, window_length, lookahead_length): 
    for i in range(num_layers): 
        i += 1
        full_path = os.path.join(working_dir, 'Layer {}'.format(i))
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
        output_training_dir = os.path.join(full_path, 'train')
        output_testing_dir = os.path.join(full_path, 'test')
        output_training_ground_file = os.path.join(full_path, 'train_ground.txt')
        output_testing_ground_file = os.path.join(full_path, 'test_ground.txt')
        linkset_file = os.path.join(full_path, 'linkset.txt')
        run_for_single_layer(input_training_data_dir, input_testing_data_dir, os.path.join(full_path, 'misc/networks'), \
                             probs_proto, word2ids_proto, perplex_proto, deltas_proto, ll_proto, window_length, lookahead_length, \
                             output_training_dir, output_testing_dir, input_training_ground_file, output_training_ground_file, \
                             output_testing_ground_file, linkset_file)
        input_training_data_dir = output_training_dir
        input_testing_data_dir = output_testing_dir
        input_training_ground_file = output_training_ground_file

if __name__ == '__main__':
    #main('/home/eoin/programming/newlstm/experiment_thing/train_data', '/home/eoin/programming/newlstm/experiment_thing/test_data', \
    #     '/media/eoin/BigDisk/kyoto3/k3_ground_non_interleaved.txt', '/media/eoin/BigDisk/hierarchy', 5, 20, 10)
    main('/media/eoin/BigDisk/hierarchy/Layer 1/train', '/media/eoin/BigDisk/hierarchy/Layer 1/test', '/media/eoin/BigDisk/hierarchy/Layer 1/test_ground.txt', '/media/eoin/BigDisk/hierarchy', 5, 20, 10)

