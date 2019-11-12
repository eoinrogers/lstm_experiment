import non_transitive_run as run, time

__search_space = ([], [], [], None)

def names(): 
    global __search_space
    return __search_space[0]

def values(): 
    global __search_space
    return __search_space[1]

def index(): 
    global __search_space
    return __search_space[2]

def defaults(): 
    global __search_space
    return __search_space[3]

def set_defaults(v): 
    global __search_space
    __search_space = (names(), values(), index(), v)

def add_parameter(name, vals): 
    if name in names(): 
        i = names().index(name)
        n = names()
        n = n[:i] + [name] + n[i+1:]
        v = values()
        v = v[:i] + [vals] + v[i+1:]
        p = index()
        p = p[:i] + [0] + p[i+1:]
    else: 
        names().append(name)
        values().append(vals)
        index().append(0)

def increment_index(): 
    v, i = values(), index()
    print('fdskj')
    for pos in range(len(v)): 
        oldi = i[pos]
        newi = (oldi + 1) % len(v[pos])
        i = i[:pos] + [newi] + i[pos+1:]
        if newi > oldi: break
    global __search_space
    __search_space = (names(), v, i, defaults())

def get_grid_position(): 
    output = {}
    n, v, i = names(), values(), index()
    for pos in range(len(n)): 
        output[n[pos]] = v[pos][i[pos]]
    increment_index()
    return output

def get_dest_dir(): 
    n, v, i = names(), values(), index()
    output = '/media/eoin/BigDisk/run'
    for pos in range(len(n)): 
        output += '_{}={}'.format(n[pos], v[pos][i[pos]])
    return output

def add_dict(one, two): 
    output = {}
    for item in one: output[item] = one[item]
    for item in two: output[item] = two[item]
    return output

def single_iteration(function, name_arg, name_value): 
    current_config = get_grid_position()
    print(defaults)
    inputs = add_dict(defaults(), current_config)
    inputs = add_dict(inputs, { name_arg : name_value })
    function(**inputs)

def main(default_inputs, search_inputs, function, name_arg): 
    for item in search_inputs: 
        val = search_inputs[item]
        add_parameter(item, val)
    set_defaults(default_inputs)
    length = 1
    for i in values(): 
        length *= len(i)
    print(length, names(), values(), index())
    for i in range(length): 
        directory = get_dest_dir()
        print('Name will be {}'.format(directory), index())
        #time.sleep(5)
        single_iteration(function, name_arg, directory)
    print('Grid search complete')

# name_arg = working_dir
if __name__ == '__main__':
    defaults_dict = { 'input_training_data_dir' : '/home/eoin/programming/newlstm/experiment_thing/train_data', 'input_testing_data_dir' : '/home/eoin/programming/newlstm/experiment_thing/test_data', \
                 'input_training_ground_file' : '/media/eoin/BigDisk/kyoto3/k3_ground_non_interleaved.txt', 'num_layers' : 4, \
                 'purge_old' : False, 'copy_dataset' : 5, 'ask_before_deleting' : False }
    search = { 'num_layers' : [4], 'window_length' : [40, 20], 'lookahead_length' : [10], 'min_occur_threshold' : [10], 'sizeacct' : [True], \
               'layer_increase' : [0], 'increase_by' : [0], 'lr_degrade_pt' : [.9], 'lr_degrade_inc' : [0] }
    main(defaults_dict, search, run.main, 'working_dir')


