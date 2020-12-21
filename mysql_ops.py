#!/usr/bin/env python
import argparse
import functools
import json
import logging
import sys

from configparse.config_parse import get_config,get_xtrabak_config
from method import check_db,parse_conn
from mysql_clean.mysql_clean import mysql_clean
from xtrabackup.xtrabackup import xtrabackup
from mysql_dump.mysqldump_method import mysqldump


# logging

logging.basicConfig(
    format="%(levelname)s\t%(asctime)s\t%(message)s", filename="ops_mysql.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# main

def main():

    parser = argparse.ArgumentParser(description="mysql ops")
    # parser.add_argument("-c","--conn_str",type=str,help="输入你的数据库连接串：用户名/密码@ip:数据库端口")
    # parser.add_argument("-u","--user",type=str,default='oracle',
    #                     help="操作系统mysql用户,默认为'mysql'")
    # parser.add_argument("-p","--password",type=str,default='',
    #                     help="操作系统mysql用户密码")
    # parser.add_argument("-P","--ssh_port",type=int,default=22,
    #                     help="操作系统ssh的端口号,默认为22")
    parser.add_argument("-o","--object",type=str,default='',
                        help="mysqldump备份恢复对象:全库：full|\
                            单库：数据库名|\
                            多库：数据库名之间逗号隔开（尚不支持mysqldump）|\
                            单表：数据库名.表名\
                            多表：数据库A名.表B名,数据库C名.表D名")

    parser.add_argument("-i","--item",choices=['check_db','mysql_clean','mysqldump','xtrabackup'],
                        help="check_db:检查数据库|mysql_clean:mysql日志清理|mysqldump:逻辑备份恢复|xtrabackup:物理备份恢复")

    args = parser.parse_args()
    
    item = args.item
    print("INFO:开始解析参数文件")
    mysql_args,os_args = get_config('mysql_db_config')

    if item == "check_db":
        mysql_args,os_args = get_config('mysql_db_config')
        check_db(mysql_args)
    elif item == 'mysql_clean':
        mysql_clean(mysql_args,os_args)
    elif item == 'mysqldump':
        tag_args,tag_os_args = get_config('target_db_config')
        obj = args.object
        if obj == '':
            print('\nWARNING:无效的备份恢复对象')
        else:
            mysqldump(mysql_args,tag_args,tag_os_args,obj)
    elif item == 'xtrabackup':
        obj = args.object
        tag_args,tag_os_args = get_config('target_db_config')
        xtra_args = get_xtrabak_config()
        if obj == '':
            print('\nWARNING:无效的备份恢复对象')
        else:
            xtrabackup(mysql_args,os_args,tag_os_args,xtra_args,obj,tag_args)




    

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(e)
        sys.exit(1)
