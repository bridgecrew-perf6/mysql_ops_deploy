import pytest

from method import check_db,parse_conn
from connection.mysql_conn import run_noprint
from mysql_clean.mysql_clean import mysql_clean,general_log
from mysql_clean.mysql_clean_method import os_dir_use



conn_str = "root/mysql@192.168.239.52:3001"
dmp_dir = "/tmp"
mode = 'DEFUALT'
sync_obj = 'zqz,zmy,zqzz'
sys_user = 'oracle'
sys_passwd = 'oracle'
mysql_args = parse_conn(conn_str)
profile_list = ['DEFAULT','PROFILE_TEST','PROFILE_TEST1']
os_args = ['192.168.239.52',22,'mysql','mysql']
# def test_crt_dir():
#     assert create_dir(conn_str,dmp_dir,mode)  == 'create dir s'
#check_expdp(conn_str,mode,sync_obj,sys_user,sys_passwd,args)
# res = default_info(sync_obj,conn_str,mode)
# print (res)

# if __name__ == "__main__":
#     pytest.main()
os_dir_use(os_args)