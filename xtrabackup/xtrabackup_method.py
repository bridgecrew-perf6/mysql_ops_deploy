# -*- coding:utf-8 -*-

import functools
import re
import time
import logging

from prettytable import PrettyTable,ALL
from method import log
from connection_mc.ssh_input import ssh_input_noprint,ssh_ftp
from connection_mc.mysql_conn import run_noprint,get_dict,get_all



# 上传及配置percona_xtrabackup 软件
@log
def xtrabackup_install(os_args,version):
    if version == '8.0':
        soft_name = 'xtrabackup\percona-xtrabackup-8.0.tar.gz'
    else:
        soft_name = 'xtrabackup\percona-xtrabackup-2.4.tar.gz'
    ssh_input_noprint(os_args,'rm -rf /usr/local/xtrabackup')
    ssh_input_noprint(os_args,'mkdir -p /usr/local/xtrabackup')
    print(f"\nINFO: {os_args[0]} 开始上传xtrabackup介质文件")
    ssh_ftp(os_args,'/usr/local/xtrabackup/percona-xtrabackup.tar.gz',soft_name,'put')
    print(f"\nINFO: {os_args[0]} xtrabackup介质文件上传完成")
    print(f"\nINFO: {os_args[0]} 开始解压配置xtrabackup介质包")
    ssh_input_noprint(os_args,'cd /usr/local/xtrabackup/\ntar -zxf percona-xtrabackup.tar.gz')
    ssh_input_noprint(os_args,'cd /usr/local/xtrabackup/percona-xtrabackup*/\nmv * /usr/local/xtrabackup')
    print(f"\nINFO: {os_args[0]} xtrabackup介质包解压配置完成")

    check_res = ''.join(ssh_input_noprint(os_args,'/usr/local/xtrabackup/bin/xtrabackup -v'))
    if 'version' in check_res:
        print(f"\nINFO: {os_args[0]} xtrabackup软件可用")
        return 'xb install s'
    else:
        print(f"\nWARNING: {os_args[0]} xtrabackup软件不可用")
        return 'xb install f'

# 生成xtrabackup命令
@log
def get_xtrabackup_cmd(src_args,xtra_args,obj):
    s_ip, s_db_user, s_db_port, s_db_pwd = src_args

    source_socket,source_dmp_dir,source_cnf_dir,target_data_dir,target_dmp_dir,target_base_dir = xtra_args
    s_db_pwd = s_db_pwd.replace('!','\\!')
    if obj != 'full':
        obj = obj.replace(',',' ')
        xtrabackup_cmd = f"/usr/local/xtrabackup/bin/xtrabackup --defaults-file={source_cnf_dir} -u{s_db_user} -p{s_db_pwd}  -S{source_socket} --databases='{obj} mysql performance_schema sys' --backup --stream=xbstream --target-dir=/tmp > {source_dmp_dir}/xtrabackup.xbstream"
    elif obj == 'full':
        xtrabackup_cmd = f"/usr/local/xtrabackup/bin/xtrabackup --defaults-file={source_cnf_dir} -u{s_db_user} -p{s_db_pwd}  -S{source_socket}  --backup --stream=xbstream --target-dir=/tmp > {source_dmp_dir}/xtrabackup.xbstream"
    
    return xtrabackup_cmd

    
# 目标端执行创建目录，解压备份及恢复
@log
def target_xtra(tag_os_args,xtra_args,tag_args):
    source_socket,source_dmp_dir,source_cnf_dir,target_data_dir,target_dmp_dir,target_base_dir = xtra_args
    host,db_username,db_port,db_password = tag_args
    check_dir = ''.join(ssh_input_noprint(tag_os_args,f'ls {target_data_dir}'))
    if 'No such file or directory' in check_dir:
        ssh_input_noprint(tag_os_args,f'mkdir  -p {target_data_dir}')
    else:
        print(f"\nINFO:目标端{target_data_dir} 已存在文件,将其备份后重新创建")
        rename_time = time.strftime("%Y%m%d%H%M%S",time.localtime())
        ssh_input_noprint(tag_os_args,f'mv {target_data_dir} {target_data_dir}.bak_{rename_time}\nmkdir  -p {target_data_dir}')

    print("\nINFO:目标端开始解压备份流文件")
    ssh_input_noprint(tag_os_args,f'cd {target_dmp_dir}\n/usr/local/xtrabackup/bin/xbstream -x < xtrabackup.xbstream  -C {target_data_dir}')
    print("\nINFO:目标端解压备份流文件完成")

    print("\nINFO:目标端开始应用备份流文件日志")
    apply_res = ''.join(ssh_input_noprint(tag_os_args,f'cd {target_dmp_dir}\n/usr/local/xtrabackup/bin/xtrabackup --prepare --target-dir={target_data_dir}'))
    if 'completed OK' in apply_res:
        print("\nINFO:目标端应用备份流文件日志完成")
        ssh_input_noprint(tag_os_args,f"chown -R mysql:mysql {target_data_dir}")
        cnf_str = '''
[mysqld]
basedir=%s
datadir=%s
port=%s
socket=%s/mysql_%s.socket
        '''%(target_base_dir,target_data_dir,db_port,target_data_dir,db_port)
        ssh_input_noprint(tag_os_args,f"echo '{cnf_str}'>/etc/my_xtrabak_{db_port}.cnf")
        print("\nINFO:目标端生成mysql配置文件完成")
        print("\nINFO:目标端开始启动数据库")
        ssh_input_noprint(tag_os_args,f"nohup {target_base_dir}/bin/mysqld_safe --defaults-file=/etc/my_xtrabak_{db_port}.cnf --user=mysql > /dev/null 2>&1 >>/tmp/startmysql{tag_os_args[0]}_xtra.log &")
        time.sleep(10)
        start_res = ''.join(ssh_input_noprint(tag_os_args,f'cat /tmp/startmysql{tag_os_args[0]}_xtra.log '))
        if ' ended '  not in start_res or start_res == '':
            print(f"\nNFO:目标端数据库启动完成.")
            ssh_input_noprint(tag_os_args,f'rm -f /tmp/startmysql{tag_os_args[0]}_xtra.log')
            return 'start success'
        else:
            print(f"\nWARNING:目标端数据库启动失败，详情请查看ops_mysql.log")
            ssh_input_noprint(tag_os_args,f'rm -f /tmp/startmysql{tag_os_args[0]}_xtra.log')
            return 'start failed'

    else:
        print("\nWARNING:目标端应用备份流文件日志失败，详情请查看ops_mysql.log")
        return 'apply f'
