# -*- coding:utf-8 -*-
import functools
import re
import logging

from prettytable import PrettyTable,ALL

from connection_mc.ssh_input import ssh_input_noprint
from connection_mc.mysql_conn import run_noprint,get_dict,get_all

# logging
logging.basicConfig(format="%(levelname)s\t%(asctime)s\t%(message)s",filename="ops_mysql.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Decorator
def log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug('\ncall %s():' % func.__name__)
        return func(*args, **kwargs)
    return wrapper

# put res to a prettytable
@log
def res_table(res,title):
    t= PrettyTable(title)
    t.hrules = ALL
    for i in res:
        i = list(i)
        for index,m in enumerate(i):
            if isinstance(m,str):
                if len(m) > 100:
                    n = re.findall(r'.{50}',m)
                    m = '\n'.join(n)
                    i[index] = m
        t.add_row(i)

    return t

# 获取版本
@log
def get_version(mysql_args):
    check_version = "select version()"
    db_version = get_all(mysql_args,check_version)[0][0]
    return db_version[0:3]


# check db
@log
def check_db(mysql_args):
    db_version = get_version(mysql_args)
    if db_version in ['5.5','5.6']:
        check_db_sql = "show global variables where variable_name in ('version','port','server_id','default_storage_engine','autocommit','tx_isolation')"
    else:
        check_db_sql = "show global variables where variable_name in ('version','port','server_id','default_storage_engine','autocommit','transaction_isolation')"

    db_res = get_all(mysql_args, check_db_sql)
    db_title = ["Variable_name","Value"]
    print(f"\nINFO:检查数据库信息 \nIP:{mysql_args[0]} PORT:{mysql_args[2]}:")

    db_table = res_table(db_res,db_title)
    print(db_table)
    return 0

# parse the string for conn
@log
def parse_conn(conn_str):
    
    args = re.split('[/@:]',conn_str)

    return args
    
