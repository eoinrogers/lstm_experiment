import os, numpy as np, tensorflow as tf

file_names = 'ptb.train.txt ptb.valid.txt ptb.test.txt'.split()

def load_dataset(path): 
    global file_names
    output = []
    for f in file_names:
        fh = open(os.path.join(path, f), 'r')
        output.extend(fh.read().split())
        fh.close()
    return output

def apply_sliding_window(dataset, destination, window_length): 
    event_types = list(set(dataset))
    one_hot_encode = lambda event: ''.join(['1' if event == event_types[i] else '0' for i in range(len(event_types))])
    ohe_many = lambda events, prefix: (('0' * ((window_length - len(events)) * len(event_types))) if prefix else '') \
        + ''.join([one_hot_encode(item) for item in events]) + \
        (('0' * ((window_length - len(events)) * len(event_types))) if not prefix else '')
    handler = open(destination, 'w')
    for i in range(len(dataset)): 
        start_before = i - window_length if i - window_length >= 0 else 0
        end_before = i
        before = ohe_many(dataset[start_before:end_before], True)
        start_after = i + 1 if i + 1 < len(dataset) else len(dataset) - 1
        end_after = i + window_length if i + window_length < len(dataset) else len(dataset) - 1
        after = ohe_many(dataset[start_after:end_after], False)
        handler.write('{} {} {}\n'.format(before, after, one_hot_encode(dataset[i])))
    handler.close()

def load_for_training(path): 
    Xs, Ys = [], []
    with open(path, 'r') as handler: 
        for line in handler: 
            line = line.strip().split()
            if len(line) != 3: continue
            before = [float(i) for i in line[0]]
            after = [float(i) for i in line[1]]
            ground = [float(i) for i in line[2]]
            Xs.append(before + after)
            Ys.append(ground)
        return np.array(Xs, dtype=np.float32), np.array(Ys, dtype=np.float32)

def build_network(dataset, window_length, encoding_length): 
    event_count = len(set(dataset));print(event_count)
    input_vector_length = event_count * (window_length * 2)
    current = input_vector_length
    layer_dimensions = []
    while current > encoding_length: 
        layer_dimensions.append(current)
        current //= 2
    if layer_dimensions[-1] != encoding_length: layer_dimensions.append(encoding_length)
    current = layer_dimensions[-1] * 2
    while current < event_count: 
        layer_dimensions.append(current)
        current *= 2
    if layer_dimensions[-1] != event_count: layer_dimensions.append(event_count)
    print(layer_dimensions)
    network = tf.keras.models.Sequential()
    encoding_layer = None
    for i in range(1, len(layer_dimensions)): 
        print('{}, input_shape=({},)'.format(layer_dimensions[i], layer_dimensions[i-1]))
        layer = tf.keras.layers.Dense(layer_dimensions[i], input_shape=(layer_dimensions[i-1],), activation=('tanh' if i < len(layer_dimensions) - 1 else 'softmax'))
        network.add(layer)
        if layer_dimensions[i] == encoding_length: encoding_layer = layer
    return network, encoding_layer

d = load_dataset('/home/eoin/programming/newlstm/experiment_thing/test_data')
apply_sliding_window(d, 'w2v_data.txt', 5)
x, y = load_for_training('w2v_data.txt')
print(x.shape, y.shape)
n, e = build_network(d, 5, 20)
n.compile(optimizer='sgd', loss='categorical_crossentropy', metrics=['accuracy'])
n.fit(x, y, epochs=10, batch_size=10)
print(e.output[0][:])


