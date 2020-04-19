import os
import time
import shutil
import tempfile
import json
from django.utils import timezone
import datetime
import django
import argparse
import traceback

if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "box_dashboard.settings")
    django.setup()


def migrate_snapshot(host_snapshot_id):
    from apiv1.models import HostSnapshot, BackupTaskSchedule
    from django.db import transaction
    from django.utils import timezone
    """
    将主机快照点迁移到新的计划中
    比host_snapshot 开始时间早的点，删除
    比host_snapshot 开始时间后的点，迁移至新计划
    :param host_snapshot: 开始迁移的快照点
    :return: 
    """
    host_snapshot = HostSnapshot.objects.get(id=host_snapshot_id)
    print_msg('migrate_snapshot flag host snapshot {} {} {}'.format(host_snapshot.id, host_snapshot.host.name,
                                                                host_snapshot.name))
    assert host_snapshot.schedule
    for ds in host_snapshot.disk_snapshots.all():
        assert ds.parent_snapshot is None
    delete_hs = HostSnapshot.objects.filter(host=host_snapshot.host,
                                            deleted=False,
                                            start_datetime__lt=host_snapshot.start_datetime).order_by('id')
    migrate_hs = HostSnapshot.objects.filter(host=host_snapshot.host,
                                             deleted=False,
                                             start_datetime__gte=host_snapshot.start_datetime).order_by('id')
    for hs in delete_hs:
        print_msg('will delete host snapshot {} {}'.format(hs.id, hs.name))
    for hs in migrate_hs:
        print_msg('will migrate host snapshot {} {}'.format(hs.id, hs.name))
    while True:
        raw_input = input('Please check, Continue or Quit [y/n]:')
        if raw_input == 'y':
            break
        elif raw_input == 'n':
            return
    print_msg('Start migrate')
    with transaction.atomic():
        for hs in delete_hs:
            hs.deleted = True
            hs.save(update_fields=['deleted'])
        new_schedules = dict()  # {'old_schedule_id':'new_schedule_object'}
        for hs in migrate_hs:
            nsc = new_schedules.get(hs.schedule.id)
            if not nsc:
                nsc = BackupTaskSchedule.objects.create(
                    name=hs.schedule.name,
                    backup_source_type=hs.schedule.backup_source_type,
                    enabled=False,
                    cycle_type=hs.schedule.cycle_type,
                    created=timezone.now(),
                    host=hs.schedule.host,
                    ext_config=hs.schedule.ext_config,
                    storage_node_ident=hs.schedule.storage_node_ident
                )
                new_schedules[hs.schedule.id] = nsc
            hs.schedule = nsc
            hs.save(update_fields=['schedule'])
        for sc_id, _ in new_schedules.items():
            sc = BackupTaskSchedule.objects.get(id=sc_id)
            sc.deleted = True
            sc.save(update_fields=['deleted'])
    print_msg('Migrate successful')


def delete_cdp_files(file_path):
    import os
    from apiv1.models import DiskSnapshot
    from apiv1.snapshot import GetSnapshotList

    _query_cache = dict()
    with open(file_path) as rf:
        for line in rf:
            line = line.strip('\n').strip()
            print_msg('*********** begin process {}'.format(line))
            if not os.path.exists(line):
                print_msg('path {} not exists, skip'.format(line))
                continue
            ident, _ = os.path.splitext(os.path.basename(line))
            try:
                disk_snapshot = DiskSnapshot.objects.get(ident=ident)
            except DiskSnapshot.DoesNotExist:
                print_msg('disk_snapshot ident {} DoesNotExist, skip'.format(ident))
                continue
            print_msg('find disk_snapshot {}'.format(disk_snapshot))
            host_snapshot = GetSnapshotList.get_host_snapshot_by_disk_snapshot(disk_snapshot, _query_cache)
            if host_snapshot and host_snapshot.partial:
                disk_snapshot.merged = True
                disk_snapshot.save(update_fields=['merged'])
                os.remove(line)
            else:
                print_msg('host_snapshot {} {} not partial, skip'.format(host_snapshot.id, host_snapshot.start_datetime))
                continue
            print_msg('*********** end process {}'.format(line))


def waite_user_confirm(msg):
    print_msg(msg)
    while True:
        raw_input = input('Please check, Continue or Quit [y/n]:')
        if raw_input == 'y':
            break
        elif raw_input == 'n':
            return False
    return True


def fix_cdp_5291():
    """
    fix issues 5291
    将不完整的主机快照下的cdp文件删除
    :return:
    """
    import os
    from apiv1.models import CDPTask, DiskSnapshotCDP

    _to_process_list = list()
    for cdp_task in CDPTask.objects.filter(host_snapshot__finish_datetime__isnull=False,
                                           host_snapshot__successful=True,
                                           host_snapshot__partial=True):
        for disk_snapshot_cdp in DiskSnapshotCDP.objects.filter(token__task=cdp_task,
                                                                disk_snapshot__merged=False):
            disk_snapshot = disk_snapshot_cdp.disk_snapshot
            print_msg('need process disk snapshot {}'.format(disk_snapshot))
            _to_process_list.append(disk_snapshot)

    if _to_process_list:
        if not waite_user_confirm('{} files need remove'.format(len(_to_process_list))):
            return
        for disk_snapshot in _to_process_list:
            disk_snapshot.merged = True
            disk_snapshot.save(update_fields=['merged'])
            try:
                os.remove(disk_snapshot.image_path)
            except FileNotFoundError:
                pass
    print_msg('fix end')


def _get_idents_from_qcow(file_path):
    import subprocess
    process = subprocess.Popen('qemu-img snapshot -l {}|grep -v Snapshot|grep -v TAG'.format(file_path),
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print_msg(process.returncode, stdout, stderr)
        return list()
    idents = list()
    stack = [None]
    for line in stdout.split('\n'):
        items = line.split()
        if len(items) == 7:
            ident = items[2]
            if ident == stack[-1]:
                idents.append(stack.pop())
            else:
                stack.append(ident)
    return idents


def _get_snapshots_from_qcow(file_path):
    return _idents_to_snapshots(_get_idents_from_qcow(file_path))


def _idents_to_snapshots(idents):
    from apiv1.models import DiskSnapshot
    rs = list()
    for ident in idents:
        try:
            disk_snapshot = DiskSnapshot.objects.get(ident=ident)
        except DiskSnapshot.DoesNotExist:
            pass
        else:
            rs.append(disk_snapshot)
    return rs


def _get_snapshots_from_cdp(filename):
    import os
    return _idents_to_snapshots([os.path.splitext(filename)[0]])


def analyze_snapshots(path, need_print=False):
    """
    pip install anytree
    yum -y install graphviz
    """
    import os
    from anytree import Node, RenderTree
    try:
        from anytree.exporter import DotExporter
    except:
        from anytree.exporter import JsonExporter

    path_node = Node(path)
    _all_nodes = {'root': path_node}
    count = 0

    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if filename.endswith('.qcow'):
            snapshots = _get_snapshots_from_qcow(file_path)
        elif filename.endswith('.cdp'):
            snapshots = _get_snapshots_from_cdp(filename)
        else:
            continue
        for snapshot in snapshots:
            if snapshot.parent_snapshot:
                parent_snapshot_key = 'snapshot_{}'.format(snapshot.parent_snapshot.ident)
                parent = _all_nodes.get(parent_snapshot_key, path_node)
            else:
                disk = snapshot.disk
                disk_key = 'disk_{}'.format(disk.ident)
                if disk_key in _all_nodes:
                    parent = _all_nodes[disk_key]
                else:
                    parent = Node(disk_key, parent=path_node)
                    _all_nodes[disk_key] = parent
            snapshot_key = 'snapshot_{}'.format(snapshot.ident)
            add_dict = {
                'filename': filename,
                'reference_tasks': snapshot.reference_tasks
            }
            snap_node = Node(snapshot_key, parent=parent, add_dict=add_dict)
            _all_nodes[snapshot_key] = snap_node
            count += 1

            # 更新子node的 parent
            for child_snapshot in snapshot.child_snapshots.all():
                child_snapshot_snapshot_key = 'snapshot_{}'.format(child_snapshot.ident)
                child_snapshot_node = _all_nodes.get(child_snapshot_snapshot_key)
                if child_snapshot_node:
                    child_snapshot_node.parent = snap_node

    if need_print:
        for pre, fill, node in RenderTree(path_node):
            print_msg("%s%s" % (pre, node.name))

    file_name = '/var/www/static/snapshot.png'
    file_name_dot = '/var/www/static/snapshot.dot'
    print_msg('analyze_snapshots end, {} snapshots found!'.format(count))
    print_msg('generate picture {}'.format(file_name))

    def mnodenamefunc(_node):
        if hasattr(_node, 'add_dict'):
            return '{}\n{}'.format(_node.name, '\n'.join(['{} {}'.format(k, v) for k, v in _node.add_dict.items()]))
        else:
            return _node.name

    try:
        DotExporter(path_node, nodenamefunc=mnodenamefunc).to_picture(file_name)
        DotExporter(path_node, nodenamefunc=mnodenamefunc).to_dotfile(file_name_dot)
    except Exception as e:
        print_msg('counld export dot {}'.format(e))
        json_file = '/var/www/static/node.json'
        print_msg('export to json file {}'.format(json_file))
        with open(json_file, 'w') as wf:
            JsonExporter(indent=2, sort_keys=True).write(path_node, wf)


def mnodenamefunc(_node):
    if hasattr(_node, 'add_dict'):
        return '{}\n{}'.format(_node.name, '\n'.join(['{} {}'.format(k, v) for k, v in _node.add_dict.items()]))
    else:
        return _node.name


def tree_json2png(file_path):
    from anytree.importer import JsonImporter
    from anytree.exporter import DotExporter

    importer = JsonImporter()
    with open(file_path) as rf:
        node = importer.read(rf)
    file_name = '/var/www/static/snapshot.png'
    print_msg('generate picture {}'.format(file_name))
    DotExporter(node, nodenamefunc=mnodenamefunc).to_picture(file_name)


def delete_qcow_files(host_snapshot_id, host_dir):
    import os
    import subprocess
    from apiv1.models import DiskSnapshot, HostSnapshot
    from apiv1.snapshot import GetSnapshotList
    all_files = list()
    for ds in HostSnapshot.objects.get(id=host_snapshot_id).disk_snapshots.all():
        snapshots = GetSnapshotList.query_snapshots_by_snapshot_object(ds, list())
        all_files.extend([sn.path for sn in snapshots])

    print_msg('need qcows {}'.format(all_files))

    delete_files = set()
    for file in os.listdir(host_dir):
        file_path = os.path.join(host_dir, file)
        if file.endswith('.qcow') and file_path not in all_files:
            delete_files.add(file_path)
        if file.endswith('.cdp') and file_path not in all_files:
            delete_files.add(file_path)

    print_msg('need delete {}'.format(delete_files))
    for file_path in delete_files:
        p = subprocess.Popen('rm -f {path};rm -f {path}*'.format(path=file_path), shell=True)
        p.wait()


def migrate_snapshotv2(host_snapshot_id):
    from apiv1.models import HostSnapshot, BackupTaskSchedule
    from django.db import transaction
    from django.utils import timezone
    """
    将主机快照点迁移到新的计划中
    only move visable
    :param host_snapshot: 开始迁移的快照点
    :return: 
    """
    host_snapshot = HostSnapshot.objects.get(id=host_snapshot_id)
    print_msg('migrate_snapshot flag host snapshot {} {} {}'.format(host_snapshot.id, host_snapshot.host.name,
                                                                host_snapshot.name))
    assert host_snapshot.schedule
    migrate_hs = HostSnapshot.objects.filter(host=host_snapshot.host,
                                             deleting=False,
                                             deleted=False,
                                             start_datetime__isnull=False,
                                             finish_datetime__isnull=False,
                                             successful=True,
                                             ).order_by('start_datetime')
    for hs in migrate_hs:
        print_msg('will migrate host snapshot {} {}'.format(hs.id, hs.name))
    while True:
        raw_input = input('Please check, Continue or Quit [y/n]:')
        if raw_input == 'y':
            break
        elif raw_input == 'n':
            return
    print_msg('Start migrate')
    with transaction.atomic():
        nsc = BackupTaskSchedule.objects.create(
            name=host_snapshot.schedule.name,
            backup_source_type=host_snapshot.schedule.backup_source_type,
            enabled=False,
            cycle_type=host_snapshot.schedule.cycle_type,
            created=timezone.now(),
            host=host_snapshot.schedule.host,
            ext_config=host_snapshot.schedule.ext_config,
            storage_node_ident=host_snapshot.schedule.storage_node_ident
        )
        for hs in migrate_hs:
            hs.schedule = nsc
            hs.save(update_fields=['schedule'])
    print_msg('Migrate successful')


# d_f = DiskSnapshot.objects.get(ident='2daa473e61654686ae1e2684ab56d9cf')
# while d_f:
#     if not d_f.is_cdp:
#         print_msg('not cdp : {}'.format(d_f))
#         d_f.
#         #break
#     else:
#         print_msg('{}'.format(d_f))
#     d_f = d_f.child_snapshots.first()


def get_ids(file_path):
    import re
    flag_str = '_check_parent_snapshot_object 2'
    flag_p = re.compile('\d+')
    rs = set()
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            index = line.index(flag_str)
            result = line[index + len(flag_str):index + len(flag_str) + 10]
            rs.add(flag_p.findall(result)[0])
    return rs


def get_ids1(file_path):
    import re
    flag_str = 'prev_snapshot_object invalid'
    flag_p = re.compile('\d+')
    rs = set()
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            index = line.index(flag_str)
            result = line[index + len(flag_str):index + len(flag_str) + 10]
            rs.add(flag_p.findall(result)[0])
    return rs


def finish_space_tasks(task_ids):
    from django.utils import timezone
    from apiv1.models import SpaceCollectionTask
    for task_id in task_ids:
        task = SpaceCollectionTask.objects.get(id=task_id)
        task.finish_datetime = timezone.now()
        task.save(update_fields=['finish_datetime'])


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


def _get_disk_name(disk_snapshot_ident, host_snapshot_ext_info):
    for disk_index_info in host_snapshot_ext_info['disk_index_info']:
        if disk_index_info['snapshot_disk_ident'] == disk_snapshot_ident:
            break
    else:
        return ''
    for disk in host_snapshot_ext_info['system_infos']['Disk']:
        if int(disk['DiskNum']) == int(disk_index_info['snapshot_disk_index']):
            break
    else:
        return ''
    return '{}[{}]'.format(disk['DiskName'], ','.join([name for name in (
        disk.get('DiskIndex', ''),
        disk.get('DiskMapperName', ''),
        disk.get('NativeGUID', ''),
    ) if name]))


# HostSnapshot.objects.filter(host__ident='', deleted=False, successful=True).order_by('start_datetime')

def get_inc_bytes_by_host_snapshot(host_snapshot, _disk_name_cache=None, need_print=False):
    import json
    import pprint
    _disk_name_cache = dict() if _disk_name_cache is None else _disk_name_cache

    _t_dict = {
        'host_sn': (host_snapshot.id, str(host_snapshot.start_datetime)),
        'host': (host_snapshot.host.ident, host_snapshot.host.display_name),
        'bytes': 0,
        'd_sn': list()
    }
    for disk_snapshot in host_snapshot.disk_snapshots.all():
        if disk_snapshot.inc_date_bytes != -1:
            _t_dict['bytes'] += disk_snapshot.inc_date_bytes
        if disk_snapshot.disk.ident in _disk_name_cache:
            name = _disk_name_cache[disk_snapshot.disk.ident]
        else:
            name = _get_disk_name(disk_snapshot.ident, json.loads(host_snapshot.ext_info))
            if name:
                _disk_name_cache[disk_snapshot.disk.ident] = name
        _t_dict['d_sn'].append((name,
                                'disk size {}'.format(format_size(disk_snapshot.bytes)),
                                'inc size {}'.format(format_size(disk_snapshot.inc_date_bytes)),
                                disk_snapshot.image_path,
                                disk_snapshot.ident))
    if need_print:
        _t_dict['bytes'] = format_size(_t_dict['bytes'])
        pprint.pprint(_t_dict)
    return _t_dict


def get_inc_bytes_by_host(host_ident, need_print=True):
    from apiv1 import models
    import pprint
    res = list()
    _disk_name_cache = dict()
    for host_snapshot in models.HostSnapshot.objects.filter(host__ident=host_ident,
                                                            deleted=False,
                                                            successful=True).order_by('start_datetime'):
        _t_dict = get_inc_bytes_by_host_snapshot(host_snapshot, _disk_name_cache)
        if _t_dict['bytes'] > 0:
            _t_dict['bytes'] = format_size(_t_dict['bytes'])
            res.append(_t_dict)
    if need_print:
        pprint.pprint(res)
    return res


def get_all_host_info(image_path):
    result = dict()
    for ident in os.listdir(image_path):
        result[ident] = get_inc_bytes_by_host(ident, False)

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fp:
        print_msg('generate all info to {}'.format(fp.name))
        fp.write(json.dumps(result, indent=4))


if os.path.exists('/home/test.bin'):
    # dd if=/dev/urandom of=test.bin bs=1M count=10
    test_bin = open('/home/test.bin', 'rb').read()
else:
    test_bin = bytes()


def generate_chain(max_length, disk_size=2 * 1024 ** 4):
    import uuid
    import datetime
    import random

    from box_dashboard import boxService
    import IMG

    qcow_dir = r'/home/mnt/nodes/b7f1e05d286d4aad933fd49ff8eeceb9'
    blk_size = 64 * 1024
    random_dir = os.path.join(qcow_dir,
                              'chain_{}_{}'.format(max_length, datetime.datetime.now().strftime(r'%Y%m%d%H%M')))
    shutil.rmtree(random_dir, ignore_errors=True)
    os.makedirs(random_dir)
    print_msg('random dir {}'.format(random_dir))

    chain_list = list()
    while len(chain_list) < max_length:
        ident = uuid.uuid4().hex
        path = os.path.join(random_dir, '{}.qcow'.format(ident))
        flag_str = r'PiD{:x} BoxDashboard|generate_chain {}'.format(os.getpid(), ident)

        new_ident = IMG.ImageSnapshotIdent(path, ident)
        handle = boxService.box_service.createNormalDiskSnapshot(
            new_ident, chain_list, disk_size, flag_str)
        offset = (random.randrange(0, disk_size - len(test_bin)) // blk_size) * blk_size
        print_msg('start write {} bytes to {} {}'.format(len(test_bin), new_ident, offset))
        boxService.box_service.getImgPrx().write(handle, offset, test_bin)
        boxService.box_service.closeNormalDiskSnapshot(handle, True)
        chain_list.append(new_ident)

    with open(os.path.join(random_dir, 'chain_{}.txt'.format(max_length)), 'w') as f:
        print_msg(chain_list, file=f)


def time_wrapper(func):
    def new_func(*args, **kwargs):
        t0 = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            print_msg('run func {} cost time {:.2f}'.format(func.__qualname__, time.time() - t0))

    return new_func


@time_wrapper
def delete_snapshot(path, ident):
    from box_dashboard import boxService
    import IMG
    boxService.box_service.deleteNormalDiskSnapshot(path, ident)


def update_hs2delete(host_snapshots):
    for host_snapshot in host_snapshots:
        host_snapshot.deleted = True
        host_snapshot.save(update_fields=['deleted'])
        host_snapshot.disk_snapshots.all().update(merged=True)


def delete_cluster_schedule(schedule_id):
    """
    15 集群备份2019-09-19 09:58:03 True
    16 集群备份2019-09-28 11:01:55 True
    17 集群备份2019-09-28 12:29:35 False
    """
    from apiv1.models import DiskSnapshot
    import uuid
    _image_paths = set()
    _host_snapshots = set()
    for disk_snapshot in DiskSnapshot.objects.filter(host_snapshot__cluster_schedule_id=schedule_id, merged=False):
        # for disk_snapshot in DiskSnapshot.objects.filter(host_snapshot__schedule_id=schedule_id, merged=False):
        _tmp = [disk_snapshot.ident]
        while _tmp:
            _disk_snapshot_ident = _tmp.pop()
            _disk_snapshot = DiskSnapshot.objects.get(ident=_disk_snapshot_ident)
            _image_paths.add(_disk_snapshot.image_path)
            for _disk_snapshot_1 in _disk_snapshot.child_snapshots.filter(
                    merged=False):
                _tmp.append(_disk_snapshot_1.ident)
    print_msg('find {} path'.format(len(_image_paths)))
    path = '/home/schedule_{}_{}'.format(schedule_id, uuid.uuid4().hex)
    print_msg('dump image paths to {}'.format(path))
    with open(path, 'w') as f:
        for _p in _image_paths:
            f.write('{}\n'.format(_p))


def delete_file(path):
    import subprocess
    print_msg('rm -rf {path}*'.format(path=path))
    p = subprocess.Popen('rm -rf {path}*'.format(path=path), shell=True)
    p.wait()


def delete_image_files(file_paths):
    from apiv1.models import DiskSnapshot, HostSnapshot
    for path in file_paths:
        DiskSnapshot.objects.filter(image_path=path).update(merged=True)
        delete_file(path)


def unfinish_space_tasks():
    from box_dashboard import xdata
    from apiv1.models import SpaceCollectionTask
    from datetime import datetime
    print_msg('统计时间:{}'.format(datetime.now()))
    for task_type in (SpaceCollectionTask.TYPE_DELETE_CDP_OBJECT,
                      SpaceCollectionTask.TYPE_DELETE_CDP_FILE,
                      SpaceCollectionTask.TYPE_DELETE_SNAPSHOT,
                      SpaceCollectionTask.TYPE_CDP_MERGE_SUB,
                      SpaceCollectionTask.TYPE_CDP_MERGE,
                      SpaceCollectionTask.TYPE_CDP_DELETE,
                      SpaceCollectionTask.TYPE_MERGE_SNAPSHOT,
                      SpaceCollectionTask.TYPE_NORMAL_DELETE,
                      SpaceCollectionTask.TYPE_NORMAL_MERGE
                      ):
        qset = SpaceCollectionTask.objects.filter(type=task_type, finish_datetime__isnull=True)
        print_msg('{} count {}'.format(xdata.get_type_name(SpaceCollectionTask.TYPE_CHOICES, task_type), qset.count()))
        host2counts = dict()
        for sp_task in qset:
            if not sp_task.host_snapshot:
                continue
            host = sp_task.host_snapshot.host
            if host.ident in host2counts:
                host2counts[host.ident][1] += 1
            else:
                host2counts[host.ident] = [host.name, 1]
        for info in sorted(host2counts.values(), key=lambda x: x[1], reverse=True):
            print_msg('   {}'.format(info))


def _fetch_files_from_ds(disk_snapshot, result_set):
    from apiv1.models import DiskSnapshot
    for ds in DiskSnapshot.objects.filter(disk=disk_snapshot.disk, merged=False):
        result_set.add(ds.image_path)


def _fetch_files(schedule_id):
    from apiv1.models import HostSnapshot
    _file_set = set()
    hs_list = list()
    for hs in HostSnapshot.objects.filter(deleted=False,
                                          successful=True,
                                          schedule_id=schedule_id).order_by('-start_datetime'):
        hs_list.append(hs.id)
        for ds in hs.disk_snapshots.filter(merged=False):
            _fetch_files_from_ds(ds, _file_set)
    return list(_file_set), hs_list


def _dump_file2file(file_paths, res_file):
    _tmp_list = list()
    for path in file_paths:
        if not os.path.exists(path):
            continue
        _tmp_list.append(
            (os.stat(path).st_ctime, path)

        )
    _tmp_list.sort(key=lambda x: x[0], reverse=True)
    with open(res_file, 'w') as wf:
        wf.write('最后修正时间    路径\n')
        wf.write('\n'.join('{} {}'.format(datetime.datetime.fromtimestamp(info[0]), info[1]) for info in _tmp_list))


def set_host_snapshot_deleted(hs_ids):
    from apiv1.models import HostSnapshot, SpaceCollectionTask
    HostSnapshot.objects.filter(id__in=hs_ids).update(deleted=True)
    SpaceCollectionTask.objects.filter(host_snapshot_id__in=hs_ids).update(finish_datetime=timezone.now())


def delete_schedule(schedule_id, user_checked=True):
    from apiv1.models import HostSnapshot, BackupTaskSchedule
    sc = BackupTaskSchedule.objects.get(id=schedule_id)
    if user_checked and not waite_user_confirm('删除主机 {} 计划 {}:{}'.format(sc.host.name,
                                                                         schedule_id, sc.name)):
        return
    _file_list, hs_list = _fetch_files(schedule_id)
    _t_file_path = '/tmp/delete_schedule_{}'.format(schedule_id)
    _dump_file2file(_file_list, _t_file_path)
    if user_checked and not waite_user_confirm('需要删除{}个文件，路径生成在{}，请确认是否需要删除'.format(len(_file_list), _t_file_path)):
        return
    delete_image_files(_file_list)
    set_host_snapshot_deleted(hs_list)


def delete_host_data(host_ident, user_checked=True):
    from apiv1.models import BackupTaskSchedule
    for bsc in BackupTaskSchedule.objects.filter(host__ident=host_ident):
        delete_schedule(bsc.id, user_checked)


def _get_cmd_args():
    parser = argparse.ArgumentParser(description='调用函数 python mutils -call fun_name -file file_path')
    parser.add_argument('call', help='func_name')
    parser.add_argument('file', help='file_name input file', default='')
    cmd_args = parser.parse_args()
    return cmd_args


def print_msg(msg):
    print('{} {}'.format(datetime.datetime.now(), msg))


if __name__ == '__main__':
    try:
        args = _get_cmd_args()
        if args.call == 'delete_host_data':
            with open(args.file) as rf:
                for line in rf:
                    host_ident = line.strip('\n').strip()
                    print_msg('delete_host_data {}'.format(host_ident))
                    delete_host_data(host_ident, False)
    except Exception as e:
        print_msg('run error {}'.format(e))
        print_msg(traceback.format_exc())
