# -*- coding:utf-8 -*-

import functools
import re
import time
import logging

from prettytable import PrettyTable,ALL
from method import log,get_version
from connection_mc.ssh_input import ssh_input_noprint,ssh_ftp,ssh_scp
from connection_mc.mysql_conn import run_noprint,get_dict,get_all
from xtrabackup.xtrabackup_method import xtrabackup_install,get_xtrabackup_cmd,target_xtra



# 使用xtrabackup物理备份恢复mysql
@log
def xtrabackup(src_args,src_os_args,tag_os_args,xtra_args,obj,tag_args):
    source_socket,source_dmp_dir,source_cnf_dir,target_data_dir,target_dmp_dir,target_base_dir = xtra_args
    print("\nINFO:源端开始配置xtrabackup软件")
    version = get_version(src_args)
    install_res = xtrabackup_install(src_os_args,version)
    if install_res == "xb install s":
        print("\nINFO:目标端开始配置xtrabackup软件")
        t_install_res = xtrabackup_install(tag_os_args,version)
        if t_install_res == "xb install s":
            xtrabackup_cmd = get_xtrabackup_cmd(src_args,xtra_args,obj)
            xtrabackup_res = ''.join(ssh_input_noprint(src_os_args,xtrabackup_cmd))
            if 'completed OK' in xtrabackup_res:
                print("\nINFO:源端xtrabackup备份完成")
                print("\nINFO:开始往目标端传输物理备份文件")
                ssh_scp(src_os_args,tag_os_args,f"{source_dmp_dir}/xtrabackup.xbstream",f"{target_dmp_dir}/xtrabackup.xbstream")
                target_xtra_res = target_xtra(tag_os_args,xtra_args,tag_args)
                return target_xtra_res
            else:
                print("\nINFO:源端xtrabackup备份失败，详情请查看ops_mysql.log")
                return 'xtrabackup f'
        else:
            return t_install_res
    else:
        return t_install_res
                

