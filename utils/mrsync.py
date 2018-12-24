import subprocess
import platform
import sys

if __name__ == '__main__':
    all_platform = [
        'vmware',
        'xencenter',
        'huaweixen',
        'hype_v',
        'sangfor'
    ]
    pf = sys.argv[-1]
    if pf not in all_platform:
        print('need platform info, all platform : %s' % all_platform)
    else:
        os = platform_info = platform.platform()
        host = 'root@172.16.6.23'
        dst_dir = '/home/sprt/%s/%s/sys/' % (pf, os)
        cmd = 'rsync -ahS --ignore-errors --partial --safe-links --delete --delete-during --force --no-whole-file'
        cmd += ' --rsync-path="rm -rf %s && mkdir -p %s && rsync" /sys/ %s:%s' % (dst_dir, dst_dir, host, dst_dir)
        print(cmd)
        p = process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        for c in iter(lambda: process.stdout.read(1), ''):  # replace '' with b'' for Python 3
            sys.stdout.write(c)
        p.wait()
