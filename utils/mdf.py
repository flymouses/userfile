# coding=utf-8
import os

import psutil


class Node(object):

    def __init__(self, path, size, child_nodes):
        self._path = path
        self._size = size
        self._child_nodes = child_nodes


class DirNode(Node):

    def __init__(self, path):
        super(DirNode, self).__init__(path, 0, enum(path, ex_mounts))

    def __str__(self):
        return 'DIR {} {}'.format(self._size, self._path)


class FileNode(Node):

    def __init__(self, path):
        super(FileNode, self).__init__(path, os.stat(path).st_size, list())

    def __str__(self):
        return 'File {} {}'.format(self._size, self._path)


def enum(path, ex_mounts):
    if os.path.isdir(path):
        rs = list()
        for node in os.listdir(path):
            file_path = os.path.join(path, node)
            if os.path.islink(file_path):
                continue
            if os.path.isdir(file_path):
                if file_path in ex_mounts:
                    continue
                else:
                    rs.append(DirNode(file_path))
            elif os.path.isfile(file_path):
                rs.append(FileNode(file_path))
        return rs
    else:
        return list()


target_point = '/'
ex_mounts = {p.mountpoint for p in psutil.disk_partitions()} - {target_point}
ex_mounts.add('/proc')
ex_mounts.add('/sys')

print(ex_mounts)

for node in enum(target_point, ex_mounts):
    print(node)
