

list_a=[100,200,1,2,3,4]
import os
from subprocess import Popen,PIPE
#
def f1(list_a):
    list_a = sorted(list_a)
    res = 0
    for i,m in enumerate(list_a):
        diff_list = [m]
        for j,n in enumerate(list_a[i+1:]):
         #   print(n,m,n-m,j)
            if n-m == j+1:
                diff_list.append('1')
        if len(diff_list) > res:
            res = len(diff_list)
    return res


def f2():
    path_list = [path  for path in os.listdir('C:\F_Drive\github\mysql_ops\connection_mc') if path.split('.')[-1] == 'zip']
    tmp = 0
    dir_tmp = {}
    for path in path_list:
        os.chdir('C:\F_Drive\github\mysql_ops\connection_mc')
        res = os.path.getctime(path)
        dir_tmp[res] = path
        if res>tmp:
            tmp = res
    return dir_tmp[tmp]

        

    

if __name__ == "__main__":
    # list_a=[100,200,1,2,3,4]
    # print(f1(list_a))
    print(f2())