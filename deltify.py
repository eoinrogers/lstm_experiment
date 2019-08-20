import os

def deltify_file(path, destination): 
    output = open(destination, 'w')
    with open(path, 'r') as handler: 
        previous = None
        print('Computing deltas from {} to {}'.format(path, destination))
        for line in handler: 
            line = [float(item.strip()) for item in line.strip().split(',')]
            if previous == None: 
                vector = line
            else: vector = [line[i] - previous[i] for i in range(len(line))]
            string = ''.join(['{}, '.format(item) for item in vector])[:-2]
            output.write('{}\n'.format(string))
            previous = line
        output.close()

def deltify_directory(incoming, outgoing): 
    n = 1
    current = incoming.format(n)
    while os.path.exists(current): 
        deltify_file(current, outgoing.format(n))
        n += 1
        current = incoming.format(n)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3: 
        print('Usage:\n python3 {} <input folder format string> <output folder format string>'.format(__file__), file=sys.stderr)
        exit(1)
    deltify_directory(sys.argv[1], sys.argv[2])


