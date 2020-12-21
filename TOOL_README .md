
mysql 自动化运维工具

修订记录

| 作者 | 版本 | 时间       | 备注       |
| ---- | ---- | ---------- | ---------- |
| 张全针 | v1.0 | 2020/04/09 | mysql日志清理功能          |
| 张全针 | v1.1 | 2020/04/20 | 修复bug添加功能          |
| 张全针 | v2.0 | 2020/05/15 | 修复bug添加功能          |
| 张全针 | v3.0 | 2020/05/29 | 添加mysqldump功能         |
| 张全针 | v4.0 | 2020/06/04 | 添加xtrabackup功能         |
| 张全针 | v4.1 | 2020/06/12 | 部分新需求bug更新         |

## 定位
        给MC公司内部人员使用，提供自动化运维功能，提高工作效率


## 先决条件

        (1).执行环境与目标环境打通ssh连接        
        (2).数据库用户需赋权，如下
                1.mysql5.5 5.6 5.7 用以下语句赋权
                GRANT ALL PRIVILEGES ON *.* TO '用户名'@'%' IDENTIFIED BY '用户密码' WITH GRANT OPTION;
                2.mysql8.0需使用以下语句赋权，并使用mysql_native_password身份验证模式
                create user '用户名'@'%' IDENTIFIED BY '用户密码';
                grant all privileges on *.* to '用户名'@'%' WITH GRANT OPTION;
                ALTER USER '用户名'@'%' IDENTIFIED WITH mysql_native_password BY '用户密码';

        (3).使用mysqldump时，请保证两端都已启动同版本数据库
        (4).使用xtrabackup时，请保证目标端已存在同版本数据库软件，并将相关版本的xtrabackup介质包放在本地xtrabackup目录下，名字为<percona-xtrabackup-2.4.tar.gz> 或 <percona-xtrabackup-8.0.tar.gz>



## 支持的操作系统和数据库版本配对
        操作系统支持：rehl5，rehl6，rehl7
        数据库版本支持：mysql各主流版本(由于新版本对redo文件格式的改动，物理备份暂时不支持8.0.20版本)





## 使用说明




### python运行环境

本地需安装 python 3 64位


        1. 进入脚本目录
        pip install -r requirements.txt    #安装项目python依赖包pymysql,prettytable与paramiko。  #第一次安装时用
    
        如果网速慢，可以用以下命令安装，使用国内的PIP源

   ```cx_Oracle
   pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt
   ```




## 代码说明

| 文件或目录       | 功能                 | 备注                                                         |
| --------------- | -------------------- | ------------------------------------------------------------ |
| mysql_ops.py      | 命令行主入口         |                                                             |
| method.py       | 主要功能和函数方法    |                                                              |
| ops_mysql.log   | 脚本输出结果日志  |                                                              |

## 主程序的使用
python mysql_ops.py

### 命令行参数介绍

          mysql ops
           
           -h, --help            show this help message and exit
           -o OBJECT, --object OBJECT
                                   mysqldump及xtrabackup备份恢复对象:全库：full| 
                                   单库：数据库名| 
                                   多库：数据库名之间逗号隔开(尚不支持mysqldump)|
                                   单表：数据库名.表名
                                   多表：数据库A名.表B名,数据库C名.表D名
           -i {check_db,mysql_clean,mysqldump,xtrabackup}, --item {check_db,mysql_clean,mysqldump,xtrabackup}
                                   check_db:检查数据库|
                                   mysql_clean:mysql日志清理|
                                   mysqldump:逻辑备份恢复
                                   xtrabackup：物理备份恢复

### 参数文件config.cfg填写


        [mysql_db_config]                                 --数据库及操作系统登录信息填写(必备参数)
        host=192.168.239.51
        db_user=root
        db_port=3306
        db_password=mysql
        os_port=22
        os_user=root
        os_password=hzmcdba



        [target_db_config]                                 --使用mysqldump功能时，填写目标数据库及操作系统登录信息;使用xtrabackup功能时,需填写目标端操作系统登录信息，数据库参数与源端一致即可
        host=192.168.239.52
        db_user=root
        db_port=1234
        db_password=mysql
        os_port=22
        os_user=root
        os_password=hzmcdba


        [xtrabackup_config]                                --使用xtrabackup功能时，所需的参数，请确保两端的*_dmp_dir参数空间充足
                                                        (source_dmp_dir 需不小于当前数据库的大小，target_dmp_dir约为当前数据库的2倍空间大小)，以便能够成功备份
        source_socket=/mysql/product/mysql56/data/mysql.sock
        source_dmp_dir=/tmp
        source_cnf_dir=/etc/my3306.cnf
        target_data_dir=/mysql56/data
        target_dmp_dir=/tmp
        target_base_dir=/mysql/app/mysql56


### 使用举例

#### 1.在mysql8.0版本执行mysqlclean功能的完整输出：

          python.exe .\mysql_ops.py  -i mysql_clean
     
          INFO:
          MySQL软件及数据目录使用情况如下:
    
          +----------------+--------------------------------------------+------+
          | Directory_name |               Directory_path               | Size |
          +----------------+--------------------------------------------+------+
          |    basedir     |    /mysql_data_8.0/mysql8.0/app/mysql/     | 2.5G |
          +----------------+--------------------------------------------+------+
          |    datadir     | /mysql_data_8.0/mysql8.0/app/mysqldb/data/ | 99M  |
          +----------------+--------------------------------------------+------+
    
          INFO:
          MySQL Binlog日志参数如下：
          +-----------------------+----------------------------------------------------------------+
          |     Variable_name     |                             Value                              |
          +-----------------------+----------------------------------------------------------------+
          |   binlog_cache_size   |                             32768                              |
          +-----------------------+----------------------------------------------------------------+
          |     binlog_format     |                              ROW                               |
          +-----------------------+----------------------------------------------------------------+
          |    expire_logs_days   |                               0                                |
          +-----------------------+----------------------------------------------------------------+
          |        log_bin        |                               ON                               |
          +-----------------------+----------------------------------------------------------------+
          |    log_bin_basename   |    /mysql_data_8.0/mysql8.0/app/mysqldb/binlog/mysql-binlog    |
          +-----------------------+----------------------------------------------------------------+
          |     log_bin_index     | /mysql_data_8.0/mysql8.0/app/mysqldb/binlog/mysql-binlog.index |
          +-----------------------+----------------------------------------------------------------+
          | max_binlog_cache_size |                      18446744073709547520                      |
          +-----------------------+----------------------------------------------------------------+
          |    max_binlog_size    |                           1073741824                           |
          +-----------------------+----------------------------------------------------------------+
          |      sync_binlog      |                               0                                |
          +-----------------------+----------------------------------------------------------------+
    
          INFO:
          MySQL Binlog空间使用情况如下
          +-----------------------------------------------------------------+------------+----------+------+
          |                           Binlog_path                           |  Use_date  | Use_time | Size |
          +-----------------------------------------------------------------+------------+----------+------+
          | /mysql_data_8.0/mysql8.0/app/mysqldb/binlog/mysql-binlog.000003 | 2020/04/09 | 14:02:06 | 4.0K |
          |                                                                 |            |          |      |
          +-----------------------------------------------------------------+------------+----------+------+
          | /mysql_data_8.0/mysql8.0/app/mysqldb/binlog/mysql-binlog.000004 | 2020/04/09 | 16:48:26 | 8.4M |
          |                                                                 |            |          |      |
          +-----------------------------------------------------------------+------------+----------+------+
          |  /mysql_data_8.0/mysql8.0/app/mysqldb/binlog/mysql-binlog.index | 2020/04/09 | 14:02:06 | 4.0K |
          |                                                                 |            |          |      |
          +-----------------------------------------------------------------+------------+----------+------+
    
          INFO:
          MySQL数据库规模统计:
          +--------------------+----------------+-----------------+-----------------+
          |   DATABASE_NAME    | DATA_SIZE (MB) | INDEX_SIZE (MB) | TOTAL_SIZE (MB) |
          +--------------------+----------------+-----------------+-----------------+
          | information_schema |      0.00      |       0.00      |       0.00      |
          +--------------------+----------------+-----------------+-----------------+
          |       mysql        |      2.15      |       0.29      |       2.44      |
          +--------------------+----------------+-----------------+-----------------+
          | performance_schema |      0.00      |       0.00      |       0.00      |
          +--------------------+----------------+-----------------+-----------------+
          |        sys         |      0.01      |       0.00      |       0.01      |
          +--------------------+----------------+-----------------+-----------------+
          |        zqz         |     26.60      |       0.00      |      26.60      |
          +--------------------+----------------+-----------------+-----------------+
    
          INFO:
          MySQL Undo log空间使用情况如下
          +----------------------------------------------------+------------+----------+------+
          |                    Undolog_path                    |  Use_date  | Use_time | Size |
          +----------------------------------------------------+------------+----------+------+
          | /mysql_data_8.0/mysql8.0/app/mysqldb/undo/undo_001 | 2020/04/09 | 16:48:27 | 11M  |
          |                                                    |            |          |      |
          +----------------------------------------------------+------------+----------+------+
          | /mysql_data_8.0/mysql8.0/app/mysqldb/undo/undo_002 | 2020/04/09 | 16:48:27 | 11M  |
          |                                                    |            |          |      |
          +----------------------------------------------------+------------+----------+------+
    
          INFO:
          目前MySQL错误日志大小如下：
          +------------------------------------------------------+-----------+-----------------------------+
          |                    Error_log_path                    | Size (MB) |            Advice           |
          +------------------------------------------------------+-----------+-----------------------------+
          | /mysql_data_8.0/mysql8.0/app/mysqldb/data/master.err |    0.0    | Do not need clean error log |
          +------------------------------------------------------+-----------+-----------------------------+
    
          INFO:
          MySQL通用日志参数如下：
          +-------------------+------------------------------------------------------------+
          |   Variable_name   |                           Value                            |
          +-------------------+------------------------------------------------------------+
          |    general_log    |                             ON                             |
          +-------------------+------------------------------------------------------------+
          |  general_log_file | /mysql_data_8.0/mysql8.0/app/mysqldb/log/mysql-general.log |
          +-------------------+------------------------------------------------------------+
          |     log_output    |                         FILE,TABLE                         |
          +-------------------+------------------------------------------------------------+
          |  Size of file(MB) |                           0.625                            |
          +-------------------+------------------------------------------------------------+
          | Size of table(MB) |                            1.5                             |
          +-------------------+------------------------------------------------------------+
    
          INFO:
          MySQL慢日志参数如下：
          +---------------------+---------------------------------------------------------+
          |    Variable_name    |                          Value                          |
          +---------------------+---------------------------------------------------------+
          |      log_output     |                        FILE,TABLE                       |
          +---------------------+---------------------------------------------------------+
          |    slow_query_log   |                            ON                           |
          +---------------------+---------------------------------------------------------+
          | slow_query_log_file | /mysql_data_8.0/mysql8.0/app/mysqldb/log/mysql-slow.log |
          +---------------------+---------------------------------------------------------+
          |   Size of file(MB)  |                          1.629                          |
          +---------------------+---------------------------------------------------------+
          |  Size of table(MB)  |                          0.125                          |
          +---------------------+---------------------------------------------------------+


#### 2.在mysql5.6 版本使用mysqldump多表备份恢复的完整输出：

           python.exe .\mysql_ops.py -i mysqldump -o hzmc.zqz,hzmc.zqz1

           INFO:开始解析参数文件

           INFO:对象hzmc.zqz 在目标库已存在，是否重命名？ Y/N y

           INFO:目标库对象hzmc.zqz 已重命名为hzmc.zqz_old_20200529142951

           INFO:对象hzmc.zqz 大小约为1MB,目标环境磁盘空间充足，开始执行mysqldump

           INFO:hzmc.zqz 数据导入完成.

           INFO:对象hzmc.zqz1 在目标库已存在，是否重命名？ Y/N y

           INFO:目标库对象hzmc.zqz1 已重命名为hzmc.zqz1_old_20200529142956

           INFO:对象hzmc.zqz1 大小约为1MB,目标环境磁盘空间充足，开始执行mysqldump

           INFO:hzmc.zqz1 数据导入完成.


#### 3.在mysql5.6 版本使用xtrabackup多表备份恢复的完整输出：

           python.exe .\mysql_ops.py -i xtrabackup -o test.zqz,test.ZQZ
           
           INFO:开始解析参数文件

           INFO:源端开始配置xtrabackup软件

           INFO: 192.168.239.51 开始上传xtrabackup介质文件

           INFO: 192.168.239.51 xtrabackup介质文件上传完成

           INFO: 192.168.239.51 开始解压配置xtrabackup介质包

           INFO: 192.168.239.51 xtrabackup介质包解压配置完成

           INFO: 192.168.239.51 xtrabackup软件可用

           INFO:目标端开始配置xtrabackup软件

           INFO: 192.168.239.52 开始上传xtrabackup介质文件

           INFO: 192.168.239.52 xtrabackup介质文件上传完成

           INFO: 192.168.239.52 开始解压配置xtrabackup介质包

           INFO: 192.168.239.52 xtrabackup介质包解压配置完成

           INFO: 192.168.239.52 xtrabackup软件可用

           INFO:源端xtrabackup备份完成

           INFO:开始往目标端传输物理备份文件


           xtrabackup.xbstream                             0%    0     0.0KB/s   --:-- ETA
           xtrabackup.xbstream                             8% 6928KB   6.8MB/s   00:10 ETA
           xtrabackup.xbstream                            24%   19MB   7.3MB/s   00:08 ETA
           xtrabackup.xbstream                            54%   42MB   8.9MB/s   00:04 ETA
           xtrabackup.xbstream                            87%   68MB  10.6MB/s   00:00 ETA
           xtrabackup.xbstream                           100%   78MB  17.8MB/s   00:04


           INFO:目标端/mysql56/data 已存在文件,将其备份后重新创建

           INFO:目标端开始解压备份流文件

           INFO:目标端解压备份流文件完成

           INFO:目标端开始应用备份流文件日志

           INFO:目标端应用备份流文件日志完成

           INFO:目标端生成mysql配置文件完成

           INFO:目标端开始启动数据库

           NFO:目标端数据库启动完成.