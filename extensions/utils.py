def make_extension_list(extension_data, limit=5000):
    extension_list = []
    if not extension_data:
        return extension_list
    extension_data = extension_data.replace(' ', '')
    ext_size = 0
    for data in extension_data.split(','):
        data = data.split('-')
        if len(data) > 1:
            try:
                data = [int(_) for _ in data]
            except ValueError:
                continue
            extension_begin, extension_end = data
            ext_size += extension_end - extension_begin
            if ext_size > limit:
                return []
            for extension in range(extension_begin, extension_end + 1):
                extension_list.append(str(extension))
        else:
            try:
                assert int(data[0])
            except ValueError:
                continue
            extension_list.extend(data)
        ext_size = len(extension_list)
        if ext_size > limit:
            return []
    return sorted(extension_list)


def make_extension_range(extension_list):
    extension_range = ''
    firstIndex = None
    lastIndex = None
    firstItem = True
    for extension in sorted(extension_list):
        if firstIndex is None:
            firstIndex = extension
        else:
            if int(lastIndex) != (int(extension) - 1):
                if firstIndex == lastIndex:
                    if firstItem:
                        firstItem = False
                    else:
                        extension_range += ', '
                    extension_range += f'{firstIndex}'
                else:
                    if firstItem:
                        firstItem = False
                    else:
                        extension_range += ', '
                    extension_range += f'{firstIndex}-{lastIndex}'
                firstIndex = extension
        lastIndex = extension
    if firstIndex and lastIndex:
        if firstIndex == lastIndex:
            if firstItem:
                firstItem = False
            else:
                extension_range += ', '
            extension_range += f'{firstIndex}'
        else:
            if firstItem:
                firstItem = False
            else:
                extension_range += ', '
            extension_range += f'{firstIndex}-{lastIndex}'
    return extension_range
