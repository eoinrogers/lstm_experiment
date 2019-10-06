import struct, integrate_links, os

def raw_white_bmp(width, height): 
    total_pixels = width * height
    padding = 0 if ((width * 3) % 4) == 0 else 4 - ((width * 3) % 4)
    white_pixel = b'\xff\xff\xff'
    row = (white_pixel * width) + (b'\0' * padding)
    pixel_data = row * height
    pixel_data_length = len(pixel_data)
    dib_header = struct.pack('<I', width) + struct.pack('<I', height) + struct.pack('<H', 1) + struct.pack('<H', 24)
    dib_header += struct.pack('<I', 0) + struct.pack('<I', pixel_data_length) + struct.pack('<I', 2835) + struct.pack('<I', 2835)
    dib_header += struct.pack('<I', 0) + struct.pack('<I', 0)
    dib_length = len(dib_header) + 4
    dib_header = struct.pack('<I', dib_length) + dib_header
    bmp_header = b'BM' + struct.pack('<I', 14 + pixel_data_length + dib_length)
    bmp_header += struct.pack('<H', 0) + struct.pack('<H', 0)
    bmp_header += struct.pack('<I', 14 + dib_length)
    return bmp_header + dib_header + pixel_data

class Bitmap:
    def __init__(self, width, height, background): 
        self.width = width
        self.height = height
        self.background = background
        self.__px = {}
    def set_pixel(self, x_offset, y_offset, colour): 
        if colour != self.background: self.__px[(x_offset, y_offset)] = colour
    def get_pixel(self, x_offset, y_offset): 
        if (x_offset, y_offset) in self.__px: return self.__px[(x_offset, y_offset)]
        return self.background
    def mk_pixels(self): 
        self.__colours = {}
        for colour in list(self.__px.values()) + [self.background]:
            colour_bytes = []
            colour_list = list(colour)
            colour_list.reverse()
            for i in colour_list: colour_bytes.append(i)
            self.__colours[colour] = colour_bytes
        print(self.__colours)
    def save(self, destination): 
        total_pixels = self.width * self.height
        padding = 0 if ((self.width * 3) % 4) == 0 else 4 - ((self.width * 3) % 4)
        self.mk_pixels()
        row_length = (3 * self.width) + padding
        pixel_data_length = row_length * self.height
        dib_header = struct.pack('<I', self.width) + struct.pack('<I', self.height) + struct.pack('<H', 1) + struct.pack('<H', 24)
        dib_header += struct.pack('<I', 0) + struct.pack('<I', pixel_data_length) + struct.pack('<I', 2835) + struct.pack('<I', 2835)
        dib_header += struct.pack('<I', 0) + struct.pack('<I', 0)
        dib_length = len(dib_header) + 4
        dib_header = struct.pack('<I', dib_length) + dib_header
        bmp_header = b'BM' + struct.pack('<I', 14 + pixel_data_length + dib_length)
        bmp_header += struct.pack('<H', 0) + struct.pack('<H', 0)
        bmp_header += struct.pack('<I', 14 + dib_length)
        bitmap = bmp_header + dib_header
        pixels = []
        background = self.__colours[self.background]
        for row in range(self.height): 
            print(row / self.height, self.height * self.width)
            for col in range(self.width):
                corrected_row = self.height - 1 - row
                if (col, corrected_row) in self.__px: colour = self.__colours[self.__px[(col, corrected_row)]]
                else: colour = background
                pixels.extend(colour)
            if padding > 0: pixels.extend([0] * padding)
        bitmap = bitmap + bytes(pixels)
        output = open(destination, 'wb')
        output.write(bitmap)
        output.close()

'''def set_pixel(bmp, pixel, colour, background=None, increment=None): 
    w, h = pixel
    img_width, img_height = struct.unpack('<I', bmp[0x12:0x16])[0], struct.unpack('<I', bmp[0x16:0x1A])[0]
    if w >= img_width or h >= img_height or w < 0  or h < 0: raise Exception('Width and height must be in the range 0..{} and 0..{} respectively. Got values (w, h) = ({}, {})'.format(img_width, img_height, w, h))
    h = img_height - 1 - h # This is to account for the fact that bitmaps are stupid, and store images in a bottom-up fashion... 
    if background != None: 
        background = list(background)
        background.reverse()
        background_pixel = b''
        for i in background: background_pixel += struct.pack('<B', i)
        background = background_pixel
    pixel_data_offset = struct.unpack('<I', bmp[0xA:0xE])[0]
    padding = 0 if ((img_width * 3) % 4) == 0 else 4 - ((img_width * 3) % 4)
    pixel_length = (struct.unpack('<H', bmp[0x1C:0x1E])[0] // 8)
    row_length = (pixel_length * img_width) + padding
    offset_within_pd = (row_length * h) + (w * pixel_length)
    offset = pixel_data_offset + offset_within_pd
    new_pixel = b''
    colour = list(colour)
    colour.reverse()
    if background == None or increment == None or bmp[offset:offset+3] == background: 
        increment = 0
    for i in colour: new_pixel += struct.pack('<B', i + increment)
    if len(new_pixel) != pixel_length: raise Exception('Invalid colour {}: must be of length {}'.format(colour, pixel_length))
    bmp = bmp[:offset] + new_pixel + bmp[offset+len(new_pixel):]
    return bmp'''

def set_pixel(bmp, pixel, colour, background=None, increment=None): 
    if background == None or increment == None or bmp.get_pixel(*pixel) == background: 
        bmp.set_pixel(pixel[0], pixel[1], colour)
    else: 
        colour = bmp.get_pixel(*pixel)
        rounder = lambda x, increment: min(x, 255) if increment > 0 else max(x, 0)
        colour = tuple([rounder(item + increment, increment) for item in colour])
        bmp.set_pixel(pixel[0], pixel[1], colour)
    return bmp

'''def set_block(bmp, block_top_left, block_bottom_right, colour): 
    img_width, img_height = struct.unpack('<I', bmp[0x12:0x16])[0], struct.unpack('<I', bmp[0x16:0x1A])[0]
    pixel_data_offset = struct.unpack('<I', bmp[0xA:0xE])[0]
    padding = 0 if ((img_width * 3) % 4) == 0 else 4 - ((img_width * 3) % 4)
    pixel_length = (struct.unpack('<H', bmp[0x1C:0x1E])[0] // 8)
    row_length = (pixel_length * img_width) + padding
    lcolour = list(colour)
    lcolour.reverse()
    colour_binary = b''
    block_top_left = (max(0, min(block_top_left[0], img_width)), max(0, min(block_top_left[1], img_height)))
    block_top_left = (block_top_left[0], img_height - 1 - block_top_left[1])
    block_bottom_right = (max(0, min(block_bottom_right[0], img_width)), max(0, min(block_bottom_right[1], img_height)))
    block_bottom_right = (block_bottom_right[0], img_height - 1 - block_bottom_right[1])
    #print(block_top_left, block_bottom_right, img_width, img_height)
    for i in lcolour: colour_binary += struct.pack('<B', i)
    if len(colour_binary) != pixel_length: raise Exception('Invalid colour {}: must be of length {}'.format(colour, pixel_length))
    width = block_bottom_right[0] - block_top_left[0]
    colour_pixels = colour_binary * width
    colour_length = len(colour_pixels)
    for h in range(block_top_left[1], block_bottom_right[1], -1): 
        if h >= img_width: break
        w = block_top_left[0]
        offset_within_pd = (row_length * h) + (pixel_length * w)
        offset = pixel_data_offset + offset_within_pd
        bmp = bmp[:offset] + colour_pixels + bmp[offset+colour_length:]
    return bmp'''

def set_block(bmp, block_top_left, block_bottom_right, colour): 
    for x in range(block_top_left[0], block_bottom_right[0]+1): 
        for y in range(block_top_left[1], block_bottom_right[1]+1): 
            bmp.set_pixel(x, y, colour)
    return bmp

def mk_line_function(one, two): 
    return lambda x, y: (two[1] - one[1]) * (x - one[0]) - (two[0] - one[0]) * (y - one[1])

def draw_four_corners(bmp, top_left, top_right, bottom_left, bottom_right, background, colour, increment): 
    print(top_left, top_right, bottom_left, bottom_right)
    f = mk_line_function(top_left, top_right)
    below_top_line = lambda x, y: f(x, y) <= 0
    g = mk_line_function(bottom_left, top_left)
    right_of_left_line = lambda x, y: g(x, y) <= 0
    h = mk_line_function(bottom_right, top_right)
    left_of_right_line = lambda x, y: h(x, y) >= 0
    j = mk_line_function(bottom_left, bottom_right)
    above_bottom_line = lambda x, y: j(x, y) >= 0
    in_triangle = lambda x, y: below_top_line(x, y) and right_of_left_line(x, y) and left_of_right_line(x, y) and above_bottom_line(x, y)
    for width in range(min(top_left[0], bottom_left[0]), max(top_right[0], bottom_right[0])+1): 
        for height in range(min(top_left[1], top_right[1]), max(bottom_left[1], bottom_right[1])+1): 
            if in_triangle(width, height): bmp = set_pixel(bmp, (width, height), colour, background, increment)
    return bmp

'''def draw_blocks_for_single_ground_channel(bmp, top_blocks, bottom_blocks, width_per_block, colour, ground, channel_id): 
    img_width, img_height = struct.unpack('<I', bmp[0x12:0x16])[0], struct.unpack('<I', bmp[0x16:0x1A])[0]
    horizontal_offset = 0
    for item in ground:
        print(horizontal_offset)
        item = [i for i in range(len(item)) if item[i] == '1']
        if horizontal_offset > img_width: break 
        if channel_id in item: 
            bmp = set_block(bmp, (horizontal_offset, top_blocks), (horizontal_offset+width_per_block, bottom_blocks), colour)
        horizontal_offset += width_per_block
    return bmp'''

def draw_blocks_for_single_ground_channel(bmp, top_blocks, bottom_blocks, width_per_block, colour, ground, channel_id): 
    img_width, img_height = bmp.width, bmp.height
    horizontal_offset = 0
    in_block = False
    working_top_left = None
    for item in ground:
        print(horizontal_offset)
        item = [i for i in range(len(item)) if item[i] == '1']
        if horizontal_offset > img_width: break 
        #if channel_id in item: 
        #    bmp = set_block(bmp, (horizontal_offset, top_blocks), (horizontal_offset+width_per_block, bottom_blocks), colour)
        if not in_block and channel_id in item: 
            in_block = True
            working_top_left = (horizontal_offset, top_blocks)
        elif in_block and channel_id not in item: 
            in_block = False
            bmp = set_block(bmp, working_top_left, (horizontal_offset + width_per_block, bottom_blocks), colour)
        horizontal_offset += width_per_block
    return bmp

def draw_ground(bmp, height_per_block, width_per_block, top_row, colour, ground): 
    num_channels = len(ground[0])
    bottom_row = top_row + (height_per_block * num_channels)
    for i in range(num_channels): 
        print('Channel', i)
        bmp = draw_blocks_for_single_ground_channel(bmp, top_row + (i * height_per_block), top_row + height_per_block + (i * height_per_block), width_per_block, colour, ground, i)
    return bmp

def get_colour(event_type, colour): 
    if type(colour) == tuple: return colour
    return colour[event_type]

def prepare_layer(types, width_per_event, top, bottom, colour): 
    output = []
    for name, candidate, count, indexes in types: 
        this_colour = get_colour(name, colour)
        points = []
        for start, end in indexes: 
            start *= width_per_event
            end *= width_per_event
            end += width_per_event
            top_end = start + width_per_event
            output.append([this_colour, (start, top), (top_end, top), (start, bottom), (end, bottom)])
    return output

def draw_triangles_for_single_link_layer(bmp, top, bottom, width_per_event, types, colour, background, increment): 
    # colour may be a lookup dict of the form { 'event_x' : (r, g, b) }, or just an (r, g, b) tuple
    working = prepare_layer(types, width_per_event, top, bottom, colour)
    for c, tl, tr, bl, br in working: 
        bmp = draw_four_corners(bmp, tl, tr, bl, br, background, c, increment)
    return bmp

def draw_layer_internal(bmp, bottom, event_height, event_width, triangle_height, ground_colour, triangle_colour, background, increment, ground, types): 
    bmp = draw_ground(bmp, event_height, event_width, bottom - (event_height * len(ground[0])), ground_colour, ground)
    print('Ground done')
    bottom -= (event_height * len(ground[0]))
    bmp = draw_triangles_for_single_link_layer(bmp, bottom - triangle_height, bottom, event_width, types, triangle_colour, background, increment)
    return bmp, bottom - triangle_height

def parse_py_tuple(string): 
    assert(string[0] == '(' and string[-1] == ')')
    string = string[1:-1]
    string = string.split(',')
    output = (int(string[0].strip()), int(string[1].strip()))
    return output

def parse_py_list(string): 
    assert(string[0] == '[' and string[-1] == ']')
    output = []
    string = string[1:-1]
    output = []
    in_tup = False
    working = ''
    for item in string: 
        if not in_tup and item == '(': 
            working = '('
            in_tup = True
        elif in_tup and item == ')': 
            working += ')'
            in_tup = False
            output.append(parse_py_tuple(working))
        elif in_tup: working += item
    return output

def parse_row(string): 
    row = string.strip().split()
    row = row[0], row[1], int(row[2]), ''.join(['{} '.format(item) for item in row[3:]])
    row = list(row[:3]) + [parse_py_list(row[3].strip())]
    return row

def draw_layer(bmp, bottom, event_height, event_width, triangle_height, ground_colour, triangle_colour, background, increment, ground_file, type_file): 
    f = open(ground_file, 'r')
    ground = f.readlines()[-1].strip().split()
    f.close()
    f = open(type_file, 'r')
    types = [parse_row(item.strip()) for item in f.readlines()]
    f.close()
    return draw_layer_internal(bmp, bottom, event_height, event_width, triangle_height, ground_colour, triangle_colour, background, increment, ground, types)

def make_diagram(initial_ground_file, ground_file_proto, types_file_proto, background, ground_colour, triangle_colour, event_height, event_width, triangle_height, increment, final_destination): 
    largest_layer = 1
    grnd_len = len(open(initial_ground_file, 'r').readlines()[-1].split())
    num_grnd = len(open(initial_ground_file, 'r').readlines()[-1].split()[0])
    while os.path.exists(ground_file_proto.format(largest_layer)): largest_layer += 1
    height = (1 + largest_layer) * ((event_height * num_grnd) + triangle_height)
    width = grnd_len * event_width
    print('Size: height = {}, width = {}'.format(height, width))
    output = Bitmap(width, height, background) #raw_white_bmp(width, height)
    n = 1
    current_types = types_file_proto.format(n)
    current_ground = initial_ground_file
    bottom = height - 1
    while current_types != None: 
        print(n, bottom)
        output, bottom = draw_layer(output, bottom, event_height, event_width, triangle_height, ground_colour, triangle_colour, background, increment, current_ground, current_types)
        current_ground = ground_file_proto.format(n)
        n += 1
        current_types = types_file_proto.format(n)
        if not (os.path.exists(current_ground) and os.path.exists(current_types)): current_types = None
        output.save(final_destination)  
        if ground_colour == (255, 0, 0): ground_colour = (0, 0, 255)
        else: ground_colour = (255, 0, 0)
    output.save(final_destination)

if __name__ == '__main__': 
    make_diagram('/media/eoin/BigDisk/kyoto3/k3_ground_non_interleaved.txt', '/media/eoin/BigDisk/hierarchy/Layer {}/train_ground.txt', '/media/eoin/BigDisk/hierarchy/Layer {}/typeinfo.txt', \
                 (255, 255, 255), (255, 0, 0), (200, 100, 100), 10, 10, 30, -10, 'lstm.bmp')

    
