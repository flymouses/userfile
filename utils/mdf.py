# coding=utf-8
import os
import subprocess
import logging
import argparse
import json

import psutil


class Cache():

    def __init__(self, path):
        self._path = path
        self._cache = self._load()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._dump()

    def get_value(self, key):
        return self._cache.get(key, None)

    def set_value(self, key, value):
        _logger.debug('cache set {}:{}'.format(key, value))
        self._cache.update({key: value})

    def _load(self):
        try:
            with open(self._path) as f:
                content = json.load(f)
        except:
            with open(self._path, 'w') as f:
                pass
            content = dict()
        return content

    def _dump(self):
        try:
            with open(self._path, 'w') as f:
                json.dump(self._cache, f)
        except Exception as e:
            _logger.debug('_dump_cache error:{}'.format(e))


def format_size(bytes, precision=2):
    bytes = int(bytes)
    if bytes < 1024:
        return '{}B'.format(bytes)
    elif 1024 <= bytes < 1024 ** 2:
        return '{:.{precision}f}KB'.format(bytes / 1024, precision=precision)
    elif 1024 ** 2 <= bytes < 1024 ** 3:
        return '{:.{precision}f}MB'.format(bytes / 1024 ** 2, precision=precision)
    elif 1024 ** 3 <= bytes < 1024 ** 4:
        return '{:.{precision}f}GB'.format(bytes / 1024 ** 3, precision=precision)
    elif 1024 ** 4 <= bytes < 1024 ** 5:
        return '{:.{precision}f}TB'.format(bytes / 1024 ** 4, precision=precision)
    elif 1024 ** 5 <= bytes:
        return '{:.{precision}f}PB'.format(bytes / 1024 ** 4, precision=precision)

    return '{}B'.format(bytes)


def execute_cmd_and_return_code(cmd):
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True) as p:
        stdout, stderr = p.communicate()
    _logger.debug('cmd:{} {}|{}|{}'.format(cmd, p.returncode, stdout, stderr))
    if p.returncode != 0:
        return p.returncode, stderr
    else:
        return p.returncode, stdout


class Node(object):

    def __init__(self, path, size, level, child_nodes):
        self._path = path
        self._size = size
        self._child_nodes = child_nodes
        self._level = level

    def __str__(self):
        return '{}\- {:<8} {}'.format('   ' * self._level, format_size(self._size), self._path)


class DirNode(Node):

    def __init__(self, path, ex_dirs, cache, level):
        cnodes = enum(path, ex_dirs, cache, level + 1)
        super(DirNode, self).__init__(path, self.get_size(path, ex_dirs, cache), level, cnodes)

    def get_size(self, path, ex_dirs, cache):
        content = cache.get_value(path)
        st_mtime_new = os.stat(path).st_mtime
        if content:
            size, st_mtime = content.split('|')
            if float(st_mtime) != st_mtime_new:
                _logger.debug('get {} size, use new'.format(path))
            else:
                _logger.debug('get {} size, use cache'.format(path))
                return int(size)

        rev, size = self.get_size_from_cmd(path, ex_dirs)
        if rev:
            cache.set_value(path, '{}|{}'.format(size, st_mtime_new))

        return size

    def get_size_from_cmd(self, path, ex_dirs):
        ex_str = ' '.join(['--exclude={}'.format(_dir) for _dir in ex_dirs])
        code, info = execute_cmd_and_return_code('du -b -s {} {}'.format(path, ex_str))
        if code == 0:
            size_str, _ = info.strip().split()
            return True, int(size_str)
        else:
            return False, 0


class FileNode(Node):

    def __init__(self, path, level):
        self.level = level
        super(FileNode, self).__init__(path, os.stat(path).st_size, level, list())


def enum(path, ex_dirs, cache, level=0):
    _logger.debug('enum path:{} level:{}'.format(path, level))
    if os.path.isdir(path) and level <= deep_level:
        rs = list()
        for node in os.listdir(path):
            file_path = os.path.join(path, node)
            if os.path.islink(file_path):
                _logger.debug('enum file_path {} is link, continue'.format(file_path))
                continue
            if os.path.isdir(file_path):
                if file_path in ex_dirs:
                    continue
                else:
                    rs.append(DirNode(file_path, ex_dirs, cache, level))
            elif os.path.isfile(file_path):
                rs.append(FileNode(file_path, level))
        return sorted(rs, key=lambda x: x._size, reverse=True)
    else:
        return list()


def print_node(node):
    print(node)
    for cnode in node._child_nodes:
        print_node(cnode)


def get_args():
    parse = argparse.ArgumentParser('python mdf.py', description='Analyze the size of the directory')
    parse.add_argument('dir', help='dir')
    parse.add_argument('--d', help='deep level, default is 0', type=int, default=0)
    parse.add_argument('--l',
                       help='log level, default is INFO, choices {}'.format(','.join(logging._nameToLevel.keys())),
                       default='INFO')

    return parse.parse_args()


if __name__ == '__main__':
    parse = get_args()
    target_point, deep_level, log_level = parse.dir, parse.d, parse.l

    logging.basicConfig(level=logging.getLevelName(log_level.upper()), handlers=(logging.StreamHandler(),))
    _logger = logging.getLogger('mdf')

    _logger.debug('input args:{}|{}|{}'.format(target_point, deep_level, log_level))
    ex_mounts = {p.mountpoint for p in psutil.disk_partitions()} - {target_point}
    ex_mounts.add('/proc')
    ex_mounts.add('/sys')

    with Cache('/tmp/mdf.cache') as cache:
        for node in enum(target_point, ex_mounts, cache):
            print_node(node)
