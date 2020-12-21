# -*- coding:utf-8 -*-
import time

from connection_mc.mysql_conn import get_dict,get_all,run_noprint,more_sql
from connection_mc.ssh_input import ssh_input_noprint
from method import log,res_table,get_version



# get os usage info
@log
def os_dir_use(os_args):
    fs_set = ssh_input_noprint(os_args,"df -hP")
    space_param = []
    for space in fs_set[1:]:
        space_tmp = space.split(' ')
        space = [x.replace('\n','') for x in space_tmp if x != ''][0:6]
        if space!=[]:
            space_param.append(space)
    print("\nINFO:\n操作系统目录使用情况如下:\n")
    dir_title = ["Filesystem","Size" ,"Used" ,"Avail" ,"Use%" ,"Mounted on"]
    dir_table = res_table(space_param,dir_title)
    print(dir_table)
    return space_param
    
# get base_dir and data_dir
@log
def mysql_dir_use(mysql_args,os_args):
    dirs = get_all(mysql_args,"show global variables where variable_name in ('basedir','datadir')")

    get_dirs = []
    for dir in dirs:
        dir = list(dir)
        size = ''
        if dir[1]!='':
            size = ssh_input_noprint(os_args,"du -sh %s|awk '{print $1}'"%dir[1])[0].replace('\n','')
        else:
            size = 0
        dir.append(size)
        get_dirs.append(dir)
    print("\nINFO:\nMySQL软件及数据目录使用情况如下:\n")
    dir_title = ["Directory_name","Directory_path","Size"]
    dir_table = res_table(get_dirs,dir_title)
    print(dir_table)
    return get_dirs

# get info for binlog
@log
def bin_log(mysql_args,os_args):
    logbin = get_all(mysql_args,"show global variables where Variable_name in ('log_bin')")[0][1]
    db_version = get_version(mysql_args)
    if logbin == 'ON':
        binlog = get_all(mysql_args,"show global variables where \
        variable_name in ('log_bin','LOG_BIN_BASENAME','expire_logs_days','binlog_format','sync_binlog',\
        'log_bin_index','binlog_cache_size','max_binlog_cache_size','max_binlog_size','Binlog_cache_disk_use','Binlog_cache_use')")
        if db_version != '5.5':
            bin_dir = get_all(mysql_args,"show global variables where\
            variable_name in ('log_bin_basename')")
            cmd = "ls -lhs --time-style '+%%Y/%%m/%%d %%H:%%M:%%S' %s*|awk '{print $9,$7,$8,$1}'"%bin_dir[0][1]
            bin_size = ssh_input_noprint(os_args,cmd)
            bin_set = []
            for space in bin_size:
                space = [x for x in space.split(' ') if x != '']
                if space!=[]:
                    bin_set.append(space)
        else:
            bin_set = [('None', 'None')]
            bin_size = [('None', 'None')]
    else:
        binlog = [('log_bin', 'OFF')]
        bin_dir = [('None', 'None')]
        bin_size = [('None', 'None')]
        bin_set = [('None', 'None')]
    print("\nINFO:\nMySQL Binlog日志参数如下：")
    binlog_title = ["Variable_name","Value"]

    binlog_table = res_table(binlog,binlog_title)
    print(binlog_table)
    if binlog[2][1] == '0' and logbin =='ON':
        print("\n小结:\nLOG_BIN参数值为ON，且expire_logs_days参数值为0,建议设置保留时间.")
    if bin_set!=[('None', 'None')]:
        print("\nINFO:\nMySQL Binlog空间使用情况如下")
        binlog_dir_title = ["Binlog_path","Use_date","Use_time","Size"]
        binlog_dir_table = res_table(bin_set,binlog_dir_title)
        print(binlog_dir_table)

    return binlog,bin_set,bin_size

#clean the log file:
@log
def clean_log_file(os_args,log_file_path):
    clean_time =  time.strftime("%Y%m%d%H%M%S",time.localtime())
    ssh_input_noprint(os_args,f"tail -10000 {log_file_path} >>{log_file_path}_bak_{clean_time}")
    ssh_input_noprint(os_args,f"rm -f {log_file_path}")
    return 'cleanned'

# error log clean
@log
def err_log(mysql_args,os_args):
    log_dir = get_all(mysql_args,"show global variables where variable_name in ('datadir','log_error');")
    if './' in log_dir[1][1]:
        errlog = (log_dir[0][1]+log_dir[1][1]).replace('./','/').replace('//','/')
    else:
        errlog = log_dir[1][1]
    errlog_size = round(int(ssh_input_noprint(os_args,f"du -sk {errlog}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
    if errlog_size > 2048:
        advice = "Need clean error log"
    else:
        advice = "Do not need clean error log"
    print("\nINFO:\n目前MySQL错误日志大小如下：")
    title = ['Error_log_path','Size (MB)','Advice']
    before_err_res = [[errlog,errlog_size,advice]]

    before_errlog_table = res_table(before_err_res,title)
    print(before_errlog_table)

    if advice == "Need clean error log":
        print("\nINFO:\n清理MySQL错误日志：")
        clean_log_file(os_args,errlog)
        run_noprint(mysql_args,"flush logs")
        print("\nINFO:\nMySQL错误日志清理完毕.")
        err_log(mysql_args,os_args)

    return before_err_res


# general log clean for mysql
@log
def general_log(mysql_args,os_args):
    generallog = get_all(mysql_args,"show global variables where variable_name in ('general_log','general_log_file','log_output')")
    data_dir = get_all(mysql_args,"show global variables like 'datadir'")
    log_on,log_path,log_param = generallog
    print("\nINFO:\nMySQL通用日志参数如下：")
    title = ['Variable_name','Value']

    if log_on[1] == 'OFF':
        generallog_table = res_table(generallog,title)
        print (generallog_table)
        print("\nINFO:\n该MySQL数据库未开启通用日志，无需清理.")
    else:
        if 'NONE' in log_param[1]:
            generallog_table = res_table(generallog,title)
            print (generallog_table)
            print("\nINFO:\n该MySQL数据库输出存在NONE，无需清理.") 
        elif log_param[1] == 'FILE':
            log_size = round(int(ssh_input_noprint(os_args,f"du -sk {log_path[1]}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
            generallog.append(('Size of file(MB)',log_size))
            generallog_table = res_table(generallog,title)
            print (generallog_table)
            if log_size > 1024:
                print("\nINFO:\n清理MySQL通用日志：")
                clean_log_file(os_args,log_path[1])
                run_noprint(mysql_args,"flush general logs")
                print("\nINFO:\nMySQL通用日志清理完毕.")
                general_log(mysql_args,os_args)
        elif log_param[1] == 'TABLE':
            table_file_path = f"{data_dir[0][1]}/mysql/general_log.CSV".replace('//','/')
            table_size = round(int(ssh_input_noprint(os_args,f"du -sk {table_file_path}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
            generallog.append(('Size of table(MB)',table_size))
            generallog_table = res_table(generallog,title)
            print (generallog_table)
            if table_size > 1024:
                print("\nINFO:\n清理MySQL通用日志表：")
                more_sql(mysql_args,['drop table IF EXISTS  mysql.mc_general_log_old','set global general_log=off','rename table mysql.general_log to mysql.mc_general_log_old',
                'create table mysql.general_log like mysql.mc_general_log_old','set global general_log=on','drop table IF EXISTS mysql.mc_general_log_old'])
                print("\nINFO:\nMySQL通用日志表清理完毕.")
                general_log(mysql_args,os_args)
        elif 'FILE' in log_param[1] and 'TABLE' in log_param[1]:

            log_size = round(int(ssh_input_noprint(os_args,f"du -sk {log_path[1]}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
            generallog.append(('Size of file(MB)',log_size))
            table_file_path = f"{data_dir[0][1]}/mysql/general_log.CSV".replace('//','/')
            table_size = round(int(ssh_input_noprint(os_args,f"ls -l {table_file_path}|awk '{{print $5}}'")[0].replace('\n',''))/1024/1024,3)
            generallog.append(('Size of table(MB)',table_size))
            generallog_table = res_table(generallog,title)
            print (generallog_table)
            if log_size > 1024:
                print("\nINFO:\n清理MySQL通用日志：")
                clean_log_file(os_args,log_path[1])
                run_noprint(mysql_args,"flush general logs")
                print("\nINFO:\nMySQL通用日志清理完毕.")
                
            if table_size > 1024:
                print("\nINFO:\n清理MySQL通用日志表：")
                more_sql(mysql_args,['drop table IF EXISTS mysql.mc_general_log_old','set global general_log=off','rename table mysql.general_log to mysql.mc_general_log_old',
                'create table mysql.general_log like mysql.mc_general_log_old','set global general_log=on','drop table IF EXISTS mysql.mc_general_log_old'])
                print("\nINFO:\nMySQL通用日志表清理完毕.")
            if table_size > 1024 or log_size > 1024:
                print ("\nINFO:\nMySQL通用日志参数如下:")
                generallog_aft = get_all(mysql_args,"show global variables where variable_name in ('general_log','general_log_file','log_output')")
                log_size_aft = round(int(ssh_input_noprint(os_args,f"du -sk {log_path[1]}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
                generallog_aft.append(('Size of file(MB)',log_size_aft))
                table_size_aft = round(int(ssh_input_noprint(os_args,f"du -sk {table_file_path}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
                generallog_aft.append(('Size of table(MB)',table_size_aft))
                generallog_table_aft = res_table(generallog_aft,title)
                print (generallog_table_aft)
        

    return "clean general log ok"


# slow log clean for mysql
@log
def slow_log(mysql_args,os_args):
    slowlog = get_all(mysql_args,"show global variables where variable_name in ('slow_query_log','slow_query_log_file','log_output')")
    data_dir = get_all(mysql_args,"show global variables like 'datadir'")
    log_param,log_on,log_path = slowlog
    print("\nINFO:\nMySQL慢日志参数如下：")
    title = ['Variable_name','Value']

    if log_on[1] == 'OFF':
        slowlog_table = res_table(slowlog,title)
        print (slowlog_table)
        print("\nINFO:\n该MySQL数据库未开启慢日志，无需清理.")
    else:
        if 'NONE' in log_param[1]:
            slowlog_table = res_table(slowlog,title)
            print (slowlog_table)
            print("\nINFO:\n该MySQL数据库输出存在NONE，无需清理.") 
        elif log_param[1] == 'FILE':
            log_size = round(int(ssh_input_noprint(os_args,f"du -sk {log_path[1]}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
            slowlog.append(('Size of file(MB)',log_size))
            slowlog_table = res_table(slowlog,title)
            print (slowlog_table)
            if log_size > 1024:
                print("\nINFO:\n清理MySQL慢日志：")
                clean_log_file(os_args,log_path[1])
                run_noprint(mysql_args,"flush slow logs")
                print("\nINFO:\nMySQL慢日志清理完毕.")
                slow_log(mysql_args,os_args)
        elif log_param[1] == 'TABLE':
            table_file_path = f"{data_dir[0][1]}/mysql/slow_log.CSV".replace('//','/')
            table_size = round(int(ssh_input_noprint(os_args,f"ls -l {table_file_path}|awk '{{print $5}}'")[0].replace('\n',''))/1024/1024,3)
            slowlog.append(('Size of table(MB)',table_size))
            slowlog_table = res_table(slowlog,title)
            print (slowlog_table)
            if table_size > 1024:
                print("\nINFO:\n清理MySQL慢日志表：")
                more_sql(mysql_args,['drop table IF EXISTS  mysql.mc_slow_log_old','set global slow_query_log=off','rename table mysql.slow_log to mysql.mc_slow_log_old',
                'create table mysql.slow_log like mysql.mc_slow_log_old','set global slow_query_log=on','drop table IF EXISTS  mysql.mc_slow_log_old'])
                print("\nINFO:\nMySQL慢日志表清理完毕.")
                slow_log(mysql_args,os_args)
        elif 'FILE' in log_param[1] and 'TABLE' in log_param[1]:

            log_size = round(int(ssh_input_noprint(os_args,f"du -sk {log_path[1]}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
            slowlog.append(('Size of file(MB)',log_size))
            table_file_path = f"{data_dir[0][1]}/mysql/slow_log.CSV".replace('//','/')
            table_size = round(int(ssh_input_noprint(os_args,f"ls -l {table_file_path}|awk '{{print $5}}'")[0].replace('\n',''))/1024/1024,3)
            slowlog.append(('Size of table(MB)',table_size))
            slowlog_table = res_table(slowlog,title)
            print (slowlog_table)
            if log_size > 1024:
                print("\nINFO:\n清理MySQL慢日志：")
                clean_log_file(os_args,log_path[1])
                run_noprint(mysql_args,"flush slow logs")
                print("\nINFO:\nMySQL慢日志清理完毕.")
                
            if table_size > 1024:
                print("\nINFO:\n清理MySQL慢日志表：")
                more_sql(mysql_args,['drop table IF EXISTS  mysql.mc_slow_log_old','set global slow_query_log=off','rename table mysql.slow_log to mysql.mc_slow_log_old',
                'create table mysql.slow_log like mysql.mc_slow_log_old','set global slow_query_log=on','drop table IF EXISTS mysql.mc_slow_log_old'])
                print("\nINFO:\nMySQL慢日志表清理完毕.")
            if table_size > 1024 or log_size > 1024:
                print ("\nINFO:\nMySQL慢日志参数如下:")
                slowlog_aft = get_all(mysql_args,"show global variables where variable_name in ('slow_query_log','slow_query_log_file','log_output')")
                log_size_aft = round(int(ssh_input_noprint(os_args,f"du -sk {log_path[1]}|awk '{{print $1}}'")[0].replace('\n',''))/1024,3)
                slowlog_aft.append(('Size of file(MB)',log_size_aft))
                table_size_aft = round(int(ssh_input_noprint(os_args,f"ls -l {table_file_path}|awk '{{print $5}}'")[0].replace('\n',''))/1024/1024,3)
                slowlog_aft.append(('Size of table(MB)',table_size_aft))
                slowlog_table_aft = res_table(slowlog_aft,title)
                print (slowlog_table_aft)
    

    return "clean slow log ok"


# undo file for mysql
@log
def undo_log(mysql_args,os_args):
    #log_dir = get_all(mysql_args,"show global variables where variable_name in ('datadir','innodb_undo_directory','innodb_max_undo_log_size','innodb_undo_tablespaces')")
    # if './' in log_dir[2][1]:
    #     undolog_dir = (log_dir[0][1]+log_dir[2][1]).replace('./','/').replace('//','/')
    # else:
    #     undolog_dir = log_dir[2][1]
    # size_cmd = "ls -lhs --time-style '+%%Y/%%m/%%d %%H:%%M:%%S' %s/*|awk '{{print $9,$7,$8,$1}}'"%(undolog_dir)
    # undolog_size = ssh_input_noprint(os_args,size_cmd)
    # undo_set = []
    # for space in undolog_size:
    #     space = [x for x in space.split(' ') if x != '']
    #     if space!=[]:
    #         undo_set.append(space)
    # print("\nINFO:\nMySQL Undo log空间使用情况如下")
    # undolog_dir_title = ["Undolog_path","Use_date","Use_time","Size"]
    # undolog_dir_table = res_table(undo_set,undolog_dir_title)
    # print(undolog_dir_table)
    undo_info =  get_all(mysql_args,"show global variables like '%undo%'")
    title =  ['Variable_name','Value']
    undo_table = res_table(undo_info,title)
    print("\nINFO:\nMySQL Undo 日志参数如下")
    print(undo_table)
    return undo_info

# the size of database for mysql
@log
def schema_info(mysql_args):
    get_schema_sql = "select table_schema, truncate(sum(data_length)/1024/1024,2) as data_size_MB,\
        truncate(sum(index_length)/1024/1024,2) as index_size_MB,\
        (truncate(sum(data_length)/1024/1024,2))+((truncate(sum(index_length)/1024/1024,2))) as sum_size_MB\
        from information_schema.tables\
        group by table_schema\
        order by sum_size_MB desc"
    info_res = get_all(mysql_args,get_schema_sql)
    print ("\nINFO:\nMySQL数据库规模统计:")
    title = ['DATABASE_NAME','DATA_SIZE (MB)','INDEX_SIZE (MB)','TOTAL_SIZE (MB)']
    schema_table = res_table(info_res,title)
    print(schema_table)