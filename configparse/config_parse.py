# -*- coding:utf-8 -*-
import os
import configparser




def get_config(item):
    config = configparser.ConfigParser()
    config.read("config.cfg")

    host = config.get(item,'host')
    db_username = config.get(item,'db_user')
    db_port = config.getint(item,'db_port')
    db_password = config.get(item,'db_password')

    os_username = config.get(item,'os_user')
    os_port = config.getint(item,'os_port')
    os_password = config.get(item,'os_password')

    db_args = [host,db_username,db_port,db_password]
    os_args = [host,os_port,os_username,os_password]
    return db_args,os_args


# 获取xtrabackup参数
def get_xtrabak_config():
    config = configparser.ConfigParser()
    config.read("config.cfg")

    source_socket = config.get('xtrabackup_config','source_socket')
    source_dmp_dir = config.get('xtrabackup_config','source_dmp_dir')
    source_cnf_dir = config.get('xtrabackup_config','source_cnf_dir')

    target_data_dir = config.get('xtrabackup_config','target_data_dir')
    target_dmp_dir = config.get('xtrabackup_config','target_dmp_dir')
    target_base_dir = config.get('xtrabackup_config','target_base_dir')

    return [source_socket,source_dmp_dir,source_cnf_dir,target_data_dir,target_dmp_dir,target_base_dir]