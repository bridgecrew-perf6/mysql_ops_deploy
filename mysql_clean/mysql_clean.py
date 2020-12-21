# -*- coding:utf-8 -*-

from mysql_clean.mysql_clean_method import mysql_dir_use,bin_log,err_log,general_log,slow_log,undo_log,schema_info,os_dir_use
from method import log

# clean the log for mysql
@log
def mysql_clean(mysql_args,os_args):
    os_dir_use(os_args)
    mysql_dir_use(mysql_args,os_args)
    bin_log(mysql_args,os_args)
    schema_info(mysql_args)
    undo_log(mysql_args,os_args)
    err_log(mysql_args,os_args)
    general_log(mysql_args,os_args)
    slow_log(mysql_args,os_args)

    return "clean complete"

