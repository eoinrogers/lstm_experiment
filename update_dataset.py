import os, argparse

file_names = 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()

def load_dataset(folder_path): 
    dataset = []
    for f in file_names: 
        dataset.extend(open(os.path.join(folder_path, f), 'r').read().split())
    return dataset

def update_dataset_for_single_lookahead(dataset, input_file_path, output_folder_path): 
    print(input_file_path)
    dataset = dataset[:]
    for line in open(input_file_path, 'r'): 
        line = line.strip().split()
        i, j, name = int(line[0]), int(line[1]), line[-1]
        dataset[i] = name
        dataset[j] = name
    third = len(dataset) // 3
    bigger = len(dataset) - (third * 2)
    train_dataset = dataset[:bigger]
    test_dataset = dataset[bigger:bigger+third]
    valid_dataset = dataset[bigger+third:bigger+(third*2)]
    train_string = ''.join(['{} '.format(item) for item in train_dataset])[:-1]
    test_string = ''.join(['{} '.format(item) for item in test_dataset])[:-1]
    valid_string = ''.join(['{} '.format(item) for item in valid_dataset])[:-1]
    strings = [train_string, test_string, valid_string]
    names = 'ptb.train.txt ptb.test.txt ptb.valid.txt'.split()
    for i in range(len(names)): 
        fh = open(os.path.join(output_folder_path, names[i]), 'w')
        fh.write(strings[i])
        fh.close()

def getargs(): 
    parser = argparse.ArgumentParser('Convert datasets for the next layer up')
    parser.add_argument('dataset', help='Folder containing the original dataset to be abstracted over', type=str)
    parser.add_argument('input', help='Path to file containing links', type=str)
    parser.add_argument('output', help='Folder to be written to', type=str)
    args = parser.parse_args()
    return (args.dataset, args.input, args.output)

def main(): 
    dataset, inputs, outputs = getargs()
    dataset = load_dataset(dataset)
    update_dataset_for_single_lookahead(dataset, inputs, outputs)

if __name__ == '__main__': 
    main()


