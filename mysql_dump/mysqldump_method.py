# -*- coding:utf-8 -*-

import functools
import re
import time
import logging

from prettytable import PrettyTable,ALL
from method import log
from connection_mc.ssh_input import ssh_input_noprint
from connection_mc.mysql_conn import run_noprint,get_dict,get_all




#获取mysql命令目录
@log
def get_bin_dir(db_args):
    bin_dir = get_all(db_args," show variables like 'basedir'")[0][1]
    return (bin_dir+'/bin').replace('//','/')

# 查看主库备份数据大小
@log
def get_size(db_args,obj):
    if obj=='full':
        get_size_sql ='''select sum(t.sum_size_MB) \
        from (select (truncate(sum(data_length)/1024/1024,2))+((truncate(sum(index_length)/1024/1024,2))) \
            as sum_size_MB from 	  information_schema.tables group by table_schema order by sum_size_MB desc) as t'''
    elif '.' not in obj:
        get_size_sql = '''select (truncate(sum(data_length)/1024/1024,2))+((truncate(sum(index_length)/1024/1024,2))) \
            as sum_size_MB from information_schema.tables where table_schema='%s' \
                group by table_schema order by sum_size_MB desc'''%obj
    else:
        dbn,tbn = obj.split('.')
        get_size_sql = '''select (truncate(sum(data_length)/1024/1024,2))+((truncate(sum(index_length)/1024/1024,2))) \
            as sum_size_MB from information_schema.tables where table_schema='%s' \
               and  table_name = '%s' group by table_schema order by sum_size_MB desc'''%(dbn,tbn)

    get_size = get_all(db_args,get_size_sql)[0][0]
    return get_size

# 获取datadir以及所在磁盘大小
@log
def get_datadir_free(db_args,os_args):
    data_dir = get_all(db_args," show variables like 'datadir'")[0][1]
    datadir_free = ssh_input_noprint(os_args,f"df -m {data_dir}|awk '{{ print $4}}'")[-1]
    return datadir_free

# 生成mysqldump命令
@log
def get_mysqldump_cmd(src_args,tag_args,tag_os_args,obj):
    s_ip, s_db_user, s_db_port, s_db_pwd = src_args
    t_ip, t_db_user, t_db_port, t_db_pwd = tag_args
    s_db_pwd = s_db_pwd.replace('!','\\!')
    t_db_pwd = t_db_pwd.replace('!','\\!')
    t_bin_dir = get_bin_dir(tag_args)
    if '.' in obj:
        db_name,table_name = obj.split('.')
        run_noprint(tag_args,f"create database if not exists {db_name}")
        mysqldump_cmd = f"{t_bin_dir}/mysqldump -u{s_db_user} -p{s_db_pwd} -h{s_ip} -P{s_db_port}  {db_name} {table_name} | mysql -u{t_db_user} -p{t_db_pwd} -h{t_ip} -P{t_db_port} -D{db_name}"
    elif obj == 'full':
        mysqldump_cmd = f"{t_bin_dir}/mysqldump -u{s_db_user} -p{s_db_pwd} -h{s_ip} -P{s_db_port} --single-transaction  --master-data=2 --set-gtid-purged=off -E -R --all-databases | mysql  -u{t_db_user} -p{t_db_pwd} -h{t_ip} -P{t_db_port}"
    else:
        run_noprint(tag_args,f"create database if not exists {obj}")
        mysqldump_cmd = f"{t_bin_dir}/mysqldump -u{s_db_user} -p{s_db_pwd} -h{s_ip} -P{s_db_port} --database {obj} | mysql  -u{t_db_user} -p{t_db_pwd} -h{t_ip} -P{t_db_port}"
    return mysqldump_cmd


    
# 查询备份表在目标库是否存在，若存在，可先备份
@log
def check_table(tag_args,tag_os_args,obj):
    dbname,tbname = obj.split('.')
    t_ip, t_db_user, t_db_port, t_db_pwd = tag_args
    t_db_pwd = t_db_pwd.replace('!','\\!')
    bin_dir = get_bin_dir(tag_args)
    check_tb_cmd = f"{bin_dir}/mysql -e 'show tables' -u{t_db_user} -p{t_db_pwd} -h{t_ip} -P{t_db_port} -D{dbname} |grep -w {tbname}"
    res = ssh_input_noprint(tag_os_args,check_tb_cmd)
    if res == []:
        return 'tb no exist'
    else:
        rename_yn = input(f'\nINFO:对象{obj} 在目标库已存在，是否重命名？ Y/N ').upper()
        if rename_yn == 'Y':
            rename_time = time.strftime("%Y%m%d%H%M%S",time.localtime())
            rename_tnb = f"{obj}_old_{rename_time}"
            rename_sql = f"rename table {obj} to {rename_tnb}"
            run_noprint(tag_args,rename_sql)
            print(f"\nINFO:目标库对象{obj} 已重命名为{rename_tnb}")
        else:
            print(f"\nINFO:目标库已存在对象{obj} 将被覆盖.")
        return 'tb exist'






@log
def mysqldump(src_args,tag_args,tag_os_args,obj):
    run_res = ''
    if '.' not in obj:
        size = int(get_size(src_args,obj))
        data_dir_free = int(get_datadir_free(tag_args,tag_os_args))
        if size < data_dir_free*0.8:
            print(f"\nINFO:对象大小{obj}约为{size}MB,目标环境磁盘空间充足，开始执行mysqldump")
            mysqldump_cmd = get_mysqldump_cmd(src_args,tag_args,tag_os_args,obj)

            imp_res = ssh_input_noprint(tag_os_args,mysqldump_cmd)
            if 'ERROR' in ''.join(imp_res):
                print("\nERROR:数据导入出错!")
                print(''.join(imp_res))
                run_res = 'mysqldump f'
            else:
                print(f"\nINFO:{obj} 数据导入完成.")
                run_res = 'mysqldump s'
        else:
            print(f"\nINFO:对象大小{obj}约为{size}MB,目标环境磁盘空间不足")
            run_res =  'no free'
    else:
        obj_list = obj.split(',')
        for obj in obj_list:
            size = int(get_size(src_args,obj))
            data_dir_free = int(get_datadir_free(tag_args,tag_os_args))
            
            if size < data_dir_free*0.8:
                check_table(tag_args,tag_os_args,obj)
                print(f"\nINFO:对象{obj} 大小约为{size}MB,目标环境磁盘空间充足，开始执行mysqldump")
                mysqldump_cmd = get_mysqldump_cmd(src_args,tag_args,tag_os_args,obj)
                imp_res = ssh_input_noprint(tag_os_args,mysqldump_cmd)
                if 'ERROR' in ''.join(imp_res):
                    print("\nERROR:数据导入出错!")
                    print(''.join(imp_res))
                    run_res = 'mysqldump f'
                else:
                    print(f"\nINFO:{obj} 数据导入完成.")
                    run_res = 'mysqldump s'
                    
            else:
                print(f"\nINFO:对象大小{obj}约为{size}MB,目标环境磁盘空间不足")
                run_res = 'no free'

      
    return run_res

