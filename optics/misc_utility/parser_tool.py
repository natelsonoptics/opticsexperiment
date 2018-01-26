
def parse(i):
    magic_values = ['\x13', '\x11', '\r', 'aw,', '\x00', '!', '\n', '%', ')', '\x01', 'a', 'w', '\x04']
    for j in magic_values:
        i = i.replace(j, '')
    if i:
        i = i.split(',')
        return [float(j) for j in i]