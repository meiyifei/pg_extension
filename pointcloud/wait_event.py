#!/usr/bin/python
# -*- coding:utf-8 -*-
#Author:Mei

import paramiko
import psycopg2
import datetime
import time

def wait_event_is_null(str,a=[],temp=[]):
    if str not in temp:
        a.append(0)

#记录等待事件的实时数据
def wirte_wait_event(conn,count,start_time,Activity=[],IO=[],LWLock=[],Lock=[],BufferPin=[],Client=[],Extension=[],Timeout=[],IPC=[],x_arry=[]):
    cur = conn.cursor()
    while (datetime.datetime.now() < start_time):
        time.sleep(1)
    time.sleep(1)
    for i in range(1, count + 1):
        cur.execute("truncate profile_log;")
        cur.execute("select pg_wait_sampling_reset_profile ();")
        conn.commit()
        cur.execute("SELECT write_profile_log ();")
        cur.execute("select event_type,sum(count) from profile_log group by event_type order by event_type;");
        rows_event = cur.fetchall()
        # 判断等待事件在某次记录中是否不存在
        temp = []
        for i in rows_event:
            if (i[0] == 'Activity'):
                Activity.append(i[1])
                temp.append('Activity')
            if (i[0] == 'IO'):
                IO.append(i[1])
                temp.append('IO')
            if (i[0] == 'LWLock'):
                LWLock.append(i[1])
                temp.append('LWLock')
            if (i[0] == 'Lock'):
                Lock.append(i[1])
                temp.append('Lock')
            if (i[0] == 'BufferPin'):
                BufferPin.append(i[1])
                temp.append('BufferPin')
            if (i[0] == 'Client'):
                Client.append(i[1])
                temp.append('Client')
            if (i[0] == 'Extension'):
                Extension.append(i[1])
                temp.append('Extension')
            if (i[0] == 'Timeout'):
                Timeout.append(i[1])
                temp.append('Extension')
            if (i[0] == 'IPC'):
                IPC.append(i[1])
                temp.append('IPC')

        wait_event_is_null('Activity', Activity, temp)
        wait_event_is_null('IO', IO, temp)
        wait_event_is_null('LWLock', LWLock, temp)
        wait_event_is_null('Lock', Lock, temp)
        wait_event_is_null('BufferPin', BufferPin, temp)
        wait_event_is_null('Client', Client, temp)
        wait_event_is_null('Extension', Extension, temp)
        wait_event_is_null('Timeout', Timeout, temp)
        wait_event_is_null('IPC', IPC, temp)
        start_time = datetime.datetime.now().strftime('%H:%M:%S')
        x_arry.append(start_time)
        time.sleep(1)
    conn.close()

#将等待事件的数据写到文件中
def data_transfer(file_name,wait_event_name=[]):
    with open(file_name, 'wt') as f:
        for i in wait_event_name:
            f.write(str(i))
            f.write('\n')
    f.close()

if __name__== "__main__":
    Activity = []
    IO = []
    LWLock = []
    Lock = []
    BufferPin = []
    Client = []
    Extension = []
    IPC = []
    Timeout = []
    x_time=[]
    #记录等待事件的开始时间
    start_time = datetime.datetime(2019, 7, 26, 17,49,0)
    #标识测试的结束时间
    count = 300
    #初始化数据库连接对象
    conn = psycopg2.connect(database="test", user="flying", password="postgres", host="192.168.6.9", port="3432")
    # 记录等待事件的实时数据
    wirte_wait_event(conn,count,start_time,Activity,IO,LWLock,Lock,BufferPin,Client,Extension,IPC,Timeout,x_time)
    #将等待事件的数据写到文件中
    data_transfer("C:\\Users\\admin\\Desktop\\event_Activity.txt",Activity)
    data_transfer("C:\\Users\\admin\\Desktop\\event_IO.txt",IO)
    data_transfer("C:\\Users\\admin\\Desktop\\event_LWLock.txt",LWLock)
    data_transfer("C:\\Users\\admin\\Desktop\\event_Lock.txt", Lock)
    data_transfer("C:\\Users\\admin\\Desktop\\event_BufferPin.txt", BufferPin)
    data_transfer("C:\\Users\\admin\\Desktop\\event_Client.txt", Client)
    data_transfer("C:\\Users\\admin\\Desktop\\event_Extension.txt",Extension)
    data_transfer("C:\\Users\\admin\\Desktop\\event_IPC.txt", IPC)
    data_transfer("C:\\Users\\admin\\Desktop\\event_Timeout.txt",Timeout)
    data_transfer("C:\\Users\\admin\\Desktop\\x_time.txt", x_time)


















