#!/usr/bin/env python
# coding: utf-8

from bitmap import BitMap
import os
import uuid
import xsorted
import csv
import argparse
import functools
import logging
import time
import tempfile
from functools import partial
from itertools import islice
import subprocess
import shutil

logging.basicConfig(handlers=(logging.StreamHandler(),), level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

_logger = logging.getLogger(__name__)


class Mergehash(object):
    def __init__(self, disk_bytes):
        bitmap_size = (disk_bytes + 64 * 1024 - 1) // (64 * 1024)
        self.task_bitmap = BitMap(bitmap_size)

    def merage_one2other_hash(self, one_hash_path, other_hash_path):
        u"""将父级的hash 合并到已有的子级hash文件中去
        :param one_hash_path:
        :param other_hash_path:
        :return:
        """
        self._check_file_path(one_hash_path)
        self._check_file_path(other_hash_path)
        with open(other_hash_path, 'r') as cf:
            reader = csv.DictReader(cf, fieldnames=['offset', 'num', 'val'])
            for line in reader:
                self.set_bitmap(int(line['offset'], 16) // 0x80)
        with open(other_hash_path, 'a') as cf:
            with open(one_hash_path, 'r') as pf:
                reader = csv.DictReader(pf, fieldnames=['offset', 'num', 'val'])
                for line in reader:
                    result = self.check_bitmap(int(line['offset'], 16) // 0x80)
                    if not result:
                        writer = csv.DictWriter(cf, fieldnames=['offset', 'num', 'val'])
                        writer.writerow(line)
        return True

    def meraged_save_new_hash(self, file_save_path, args):
        u""" 文件合并,生成新的hash文件
        :param file_save_path: 文件要保存的地址 , 传入格式 str
        :param args: 要合并的文件 , 传入格式 [str,str..]
        :return:
        """
        base_dir = os.path.dirname(file_save_path)
        extra_save_path = os.path.join(base_dir, '{}_tmp.hash'.format(uuid.uuid4().hex))
        try:
            with open(extra_save_path, 'w') as extra_save_file:
                for one_file_path in args:
                    if one_file_path.startswith('cdp|'):
                        self.set_by_cdp(one_file_path)
                    else:
                        self.set_by_normal(one_file_path, extra_save_file)
            self.sort_hash(extra_save_path, file_save_path)
        finally:
            if os.path.exists(extra_save_path):
                os.remove(extra_save_path)
        return file_save_path

    def generator_line(self, files):
        for hash_file in files:
            if hash_file.startswith('cdp|'):
                self.set_by_cdp(hash_file)
            else:
                with open(hash_file, buffering=8 * 1024 ** 2) as f:
                    for line in f:
                        offset_str, _ = line.split(',', 1)
                        offset = int(offset_str, 16)
                        offset_block = offset // 0x80
                        if not self.task_bitmap.test(offset_block):
                            self.task_bitmap.set(offset_block)
                            yield (offset, line)

    def meraged_save_new_hash__generator(self, file_save_path, hash_files):
        base_dir = os.path.dirname(file_save_path)
        tmp_dir = os.path.join(base_dir, 'sort_{}'.format(uuid.uuid4().hex))
        os.makedirs(tmp_dir)
        try:
            self.split(partial(self.dump, dir_name=tmp_dir),
                       self.generator_line(hash_files),
                       key=lambda item: item[0])
            self.merge_sort(tmp_dir, file_save_path)
        except Exception as e:
            _logger.error('meraged_save_new_hash__generator e:{}'.format(e), exc_info=True)
            try:
                os.remove(file_save_path)
            except Exception:
                pass
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # 切分成小的有序文件
    @staticmethod
    def split(dump, iterable, partition_size=1024000, key=None, reverse=False):
        return xsorted._split(dump, partition_size, iterable, key, reverse)

    def merge_sort(self, src_dir, dst_path):
        sort_cmd = r"""sort -t',' -k1 -n -m {}/tmp*""".format(src_dir)
        trans_cmd = r"""awk -F ',' '{$1="";print $0}'"""
        merge_sort_cmd = r"""{} | {} > {}""".format(sort_cmd, trans_cmd, dst_path)
        _logger.info('merge_sort :{}'.format(merge_sort_cmd))
        returncode, stdout, stderr = self.execute(merge_sort_cmd)
        assert returncode == 0, '{}|{}|{}'.format(returncode, stdout, stderr)

    @staticmethod
    def execute(cmd):
        with subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                              universal_newlines=True) as p:
            stdout, stderr = p.communicate()
        return p.returncode, stdout, stderr

    def dump(self, partition, dir_name):
        """
        Dump the given partition to an external source.

        The default implementation is to pickle the list of objects to a temporary file.

        :param partition: The partition of objects to dump.

        :return: Unique id which can be used to reload the serialized partition. In the case of the
                 default implementation this is the path to the temporary file.
        """
        with tempfile.NamedTemporaryFile(delete=False, mode='w+t', dir=dir_name, buffering=8 * 1024 ** 2) as fileobj:
            fileobj.write(''.join(str(line[0]) + ',' + line[1] for line in partition))
            return fileobj.name

    @staticmethod
    def sorter():
        return xsorted.xsorter(load=_load, dump=_dump, partition_size=1024000)

    def meraged_save_new_hash_new(self, file_save_path, args):
        base_dir = os.path.dirname(file_save_path)
        extra_save_path = os.path.join(base_dir, '{}_tmp.hash'.format(uuid.uuid4().hex))
        try:
            with open(extra_save_path, 'w') as extra_save_file:
                for one_file_path in args:
                    if one_file_path.startswith('cdp|'):
                        self.set_by_cdp(one_file_path)
                    else:
                        self.set_by_normal_new(one_file_path, extra_save_file)
            self.sort_hash_new(extra_save_path, file_save_path)
        finally:
            if os.path.exists(extra_save_path):
                os.remove(extra_save_path)
        return file_save_path

    def set_by_cdp(self, cdp_info):
        u""" 当文件为 cdp文件的时候，只进行块站位，不进行文件写入
        :param cdp_info:
        :return:
        """
        cdp_path_list = cdp_info.split('|')
        cdp_path = cdp_path_list[1]
        cdp_timestamp = cdp_path_list[2]
        get_bitmap = cdpFile.get_bitmap(cdp_path, cdp_timestamp)
        self.task_bitmap.bitmap = self.merge_bit_maps(self.task_bitmap.bitmap, get_bitmap)

    def merge_bit_maps(self, *args):
        u"""合并位图
        :param args:
        :return:
        """
        _len = 0
        for index, bit_map in enumerate(args):
            if index == 0:
                _len = len(bit_map)
            else:
                assert len(bit_map) == _len, 'bit map len must be same!'
        return bytearray(map(self._reduce, zip(*args)))

    @staticmethod
    def _reduce(args):
        return functools.reduce(lambda x, y: x | y, args)

    def set_by_normal(self, one_file_path, extra_save_file):
        u""" 当为普通文件的时候 进行块站位与写入临时文件中
        :param one_file_path:
        :param extra_save_file:
        :return:
        """
        with open(one_file_path, 'r') as fp:
            reader = csv.DictReader(fp, fieldnames=['offset', 'num', 'val'])
            for line in reader:
                status = self.set_bitmap(int(line['offset'], 16) // 0x80)
                if status:
                    writer = csv.DictWriter(extra_save_file, fieldnames=['offset', 'num', 'val'])
                    writer.writerow(line)

    def set_by_normal_new(self, one_file_path, extra_save_file):
        u""" 当为普通文件的时候 进行块站位与写入临时文件中
        :param one_file_path:
        :param extra_save_file:
        :return:
        """
        with open(one_file_path, 'r') as fp:
            for line in fp:
                offset = int(line.split(',')[0], 16) // 0x80
                if not self.task_bitmap.test(offset):
                    self.task_bitmap.set(offset)
                    extra_save_file.write(line)

    @staticmethod
    def sort_hash(extra_path, new_path, remove=True):
        u"""排序
        :param extra_path: 排序前的文件地址  new_past 保存后进行删除
        :param new_path: 排序后文件的保存地址
        :return:
        """
        with open(extra_path, mode='rt') as op:
            with open(new_path, mode='wt') as np:
                reader = csv.DictReader(op, fieldnames=['offset', 'num', 'val'])
                sorted_items = xsorted.xsorter(partition_size=102400)(reader, key=lambda item: int(item['offset'], 16))
                writer = csv.DictWriter(np, fieldnames=['offset', 'num', 'val'])
                writer.writerows(sorted_items)
        if remove:
            os.remove(extra_path)

    @staticmethod
    def sort_hash_new(extra_path, new_path, remove=True):
        u"""排序
        :param extra_path: 排序前的文件地址  new_past 保存后进行删除
        :param new_path: 排序后文件的保存地址
        :return:
        """
        with open(extra_path, mode='rt') as op:
            with open(new_path, mode='wt') as np:
                sorted_items = xsorted.xsorter(load=_load, dump=_dump, partition_size=102400)(op, key=lambda item: int(
                    item.split(',')[0], 16))
                for line in sorted_items:
                    np.write(line)
        if remove:
            os.remove(extra_path)

    def check_bitmap(self, chunk_number):
        u"""检查是否可用
        :param chunk_number: 块号
        :return:
        """
        result = None
        try:
            result = self.task_bitmap.test(chunk_number)
        except Exception as e:
            raise xlogging.raise_system_error(r'不可用', 'chunk_number Error:{} chunk_number:{}'.format(e, chunk_number),
                                              1)
        return result

    def set_bitmap(self, chunk_number):
        u"""设置此块号
        :param chunk_number:块号
        :return:
        """
        if not self.check_bitmap(chunk_number):
            self.task_bitmap.set(chunk_number)
            return True
        else:
            return False

    @staticmethod
    def _check_file_path(path):
        u"""文件路径检测
        :param path:
        :return:
        """
        if not os.path.exists(path):
            raise xlogging.raise_system_error(r'地址不可用', 'Path Error:{} is not existed'.format(path), 1)


# 获取命令行参数
def get_cmd_args():
    args_parser = argparse.ArgumentParser(
        description="python MergeHash.py --size size --new_path path --mer_paths paths")
    args_parser.add_argument("--size", help="bitmap size")
    args_parser.add_argument("--new_path", help="New address to save")
    args_parser.add_argument("--mer_paths", help="will go merged dirs who splited by ',' of str ")
    cmd_args = args_parser.parse_args()
    return cmd_args


def _dump(partition):
    """
    Dump the given partition to an external source.

    The default implementation is to pickle the list of objects to a temporary file.

    :param partition: The partition of objects to dump.

    :return: Unique id which can be used to reload the serialized partition. In the case of the
             default implementation this is the path to the temporary file.
    """
    with tempfile.NamedTemporaryFile(delete=False, mode='w+t') as fileobj:
        for item in partition:
            fileobj.write(item)
        return fileobj.name


def _load(partition_id):
    """
    Load a partition from an external source.

    The default implementation yields items loaded and unpickled from a temporary file. After all
    items have been loaded the temporary file is removed.

    :param partition_id: Unique identifier which can be used to reload the partition. In the case
                         of the default implemenation this is the path to the temporary file to
                         load.

    :return: iterable which is loaded from the external source using partition_id.
    """
    if os.path.exists(partition_id):
        try:
            with open(partition_id, 'rt') as fileobj:
                return fileobj.readlines()
        finally:
            os.unlink(partition_id)
    else:
        raise StopIteration()


def gen_big_hash(file_size):
    import time
    line_size = 50
    line_count = file_size // line_size
    disk_size = line_count * 1024 * 64
    file_name = 'bighash'
    st = time.time()
    print('start gen big hash file_size:{}, line count:{} file_name:{} '.format(file_size, line_count, file_name))
    with open(file_name, 'w') as f:
        for line in range(line_count):
            f.write("0x{:x},256,852a956d761490d5119dbd557121db18eb8e97d7\n".format(line * 128))
    print('cost time:{}'.format(time.time() - st))
    return disk_size, file_name


def test_gen_big_hash():
    cProfile.run('gen_big_hash(10 * 1024 **3)', filename='test_gen_big_hash.stats')


def test_meraged_save_new_hash():
    cProfile.run("Mergehash(1407374852096).meraged_save_new_hash('bighash_sorted', ['bighash'])",
                 filename='meraged_save_new_hash.stats')


def test_meraged_save_new_hash_new():
    statement = "Mergehash(1407374852096).meraged_save_new_hash_new('bighash_sorted_new', ['bighash'])"
    cProfile.run("Mergehash(1407374852096).meraged_save_new_hash_new('bighash_sorted_new', ['bighash'])",
                 filename='meraged_save_new_hash_new.stats')


def generate_hash(use_new=True):
    hash_file_size = 1 * 1024 ** 3
    line_count = hash_file_size // 50  # 一行50个字节
    disk_size = line_count * 64 * 1024
    TIME_STR = datetime.datetime.now().strftime('%Y_%m_%dT%H_%M_%S')
    hash_file = 'bighash'
    statement_format = "Mergehash({disk_size}).{func_name}('{sorted_hash_file}', ['{hash_file}'])"
    current_dir = os.path.dirname(os.path.realpath(__file__))
    if use_new:
        sorted_hash_file = 'bighash_sorted_new{}'.format(TIME_STR)
        func_name = 'meraged_save_new_hash__generator'
    else:
        sorted_hash_file = 'bighash_sorted_{}'.format(TIME_STR)
        func_name = 'meraged_save_new_hash'

    statement_format = statement_format.format(disk_size=disk_size, func_name=func_name,
                                               sorted_hash_file=os.path.join(current_dir, sorted_hash_file),
                                               hash_file=hash_file)

    cProfile.run(statement_format, filename='{}.stats'.format(func_name))


def test_read():
    with open('bighash') as f:
        count = 0
        for line in f:
            count += 1
        print(count)


def test_write():
    c = '*' * 50 + '\n'
    with open('bigfile_test_write', 'w') as f:
        f.writelines(c for _ in range((10 * 1024 ** 3) // 50))


def test_read_write():
    with open('bigfile_test_write') as rf:
        with open('bigfile_test_write_new', 'w') as wf:
            for line in rf:
                wf.write(line)


if __name__ == '__main__':
    # args = get_cmd_args()
    # set_bitmap_size = int(args.size)
    # file_save_path = args.new_path
    # filepath = args.mer_paths.split(',')
    # testy = Mergehash(set_bitmap_size)
    # import os
    #
    # if os.environ.get('use_new', 'n') == 'y':
    #     testy.meraged_save_new_hash_new(file_save_path, filepath)
    # else:
    #     testy.meraged_save_new_hash(file_save_path, filepath)

    # with open('/home/bighash', 'w') as f:
    #     for i in range((10 * (1024 ** 4)) // (64 * 1024)):
    #         a = "{:x},256,852a956d761490d5119dbd557121db18eb8e97d7\n".format(i)
    #         f.write(a)

    import cProfile
    import datetime

    st = time.time()
    TIME_STR = datetime.datetime.now().strftime('%Y_%m_%dT%H_%M_%S')
    # cProfile.run('gen_big_hash(1 * 1024 **3)', filename='gen_big_hash.out')

    # cProfile.run("Mergehash(1407374852096).meraged_save_new_hash('/home/bighash1_sorted', ['/home/bighash1'])",
    #              filename='bighash1_sorted.out')

    # cProfile.run("Mergehash(1407374852096).meraged_save_new_hash_new('/home/bighash1_sorted_new', ['/home/bighash1'])",
    #              filename='bighash1_sorted_new.out')

    # gen_big_hash(1024 ** 3)
    # cProfile.run('test_read()', filename='test_read.stats')
    # cProfile.run('test_write()', filename='test_write.stats')
    generate_hash()
    # test_read()
    # test_read_write()
    print('time cost:{}'.format(time.time() - st))
