import links

def compress_single_link(dataset, linkset, link_type, index, lookup_table): 
    # Get the link in question
    link = linkset[index]
    
    # Take the subsection from the dataset that contains the entire new link
    start = min(link)
    end = max(link)
    subsect = link[lookup_table[start]:lookup_table[end]+1]
    
    # Decide if we should put the new event at the start or end of the 
    # subsection, and place it there
    indicies = [i for i in range(start, end+1) if i not in link]
    link = [item - start for item in link]
    subsect = [item for i, item in enumerate(subsect) if i not in link]
    average_link = sum(link) / len(link)
    average_subsect = (sum(subsect) / len(subsect)) if len(subsect) > 0 else 0
    subsect = [item + start for item in subsect]
    subsect = [dataset[lookup_table[item]] for item in subsect]
    if average_link > average_subsect: # Place the event at the end
        output = subsect + [link_type]
        before = False
    else: # Place the event at the start
        output = [link_type] + subsect
        before = True
    
    # Update the lookup_table
    for i, idx in enumerate(indicies): 
        lookup_table[idx] = start + i + (1 if before else 0)
    
    # Return the output
    return dataset[:start] + output + dataset[end+1:]


def compress_dataset(dataset_directory, raw_links_file, link_types_file, output_directory, test_pc, valid_pc): 
    print('Compressing dataset for training the next layer...', end=' ')
    links.sys.stdout.flush()
    dataset = links.lstm.load_dataset(dataset_directory)
    linkset = links.load_linkset(raw_links_file)
    linktypes = links.load_link_types(link_types_file)
    start = len(dataset)
    
    lookup_table = [i for i in range(len(dataset))]
    
    for i in range(len(linkset)): 
        dataset = compress_single_link(dataset, linkset, linktypes[i], i, lookup_table)
    
    test_length = round(len(dataset) * test_pc)
    valid_length = round(len(dataset) * valid_pc)
    train_length = len(dataset) - test_length - valid_length
    
    train_dataset = dataset[:train_length]
    valid_dataset = dataset[train_length:train_length+valid_length]
    test_dataset = dataset[train_length+valid_length:]
    
    for data, filename in zip([train_dataset, valid_dataset, test_dataset], links.lstm.file_names): 
        full_path = links.lstm.os.path.join(output_directory, filename)
        f = open(full_path, 'w')
        string = ''.join(['{} '.format(item) for item in data])[:-1]
        f.write(string)
        f.close()
    
    print('Done!')


if __name__ == '__main__':
    compress_dataset('/media/eoin/BigDisk/kyoto3/interleaved train', '/media/eoin/BigDisk/blah/raw_links', '/media/eoin/BigDisk/blah/link_types', '/media/eoin/BigDisk/blah/new_dataset', .1, .2)


