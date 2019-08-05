#!/usr/bin/python
# -*- coding:utf-8 -*-
# Author:Mei

import paramiko
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
import time
import psycopg2
import datetime


#计算TPS
def TPS(conn,start_time,time_count,xact=[],time_interval=[]):
    cur = conn.cursor()
    while (datetime.datetime.now() < start_time):
        time.sleep(1)
    if (datetime.datetime.now() > start_time):
        for i in range(1, time_count+1):
            cur.execute("SELECT xact_commit + xact_rollback  AS xact_total FROM pg_stat_database WHERE datname='test';")
            conn.commit()
            rows_event = cur.fetchall()
            x = rows_event[0][0]
            time.sleep(1)
            cur.execute("SELECT xact_commit + xact_rollback  AS xact_total FROM pg_stat_database WHERE datname='test';")
            conn.commit()
            rows_event = cur.fetchall()
            y = rows_event[0][0]
            xact.append((y - x))
            start_time = datetime.datetime.now().strftime('%H:%M:%S')
            time_interval.append(start_time)
    conn.close()

#加载等待事件数据
def load_data(Activity=[],IO=[],LWLock=[],Lock=[],BufferPin=[],Client=[],Extension=[],IPC=[],Timeout=[],x_time=[]):
    f_Activity = open('C:\\Users\\admin\\Desktop\\event_Activity.txt', 'r')
    for Activity_type in f_Activity.readlines():
        Activity.append(float(Activity_type))

    f_IO = open('C:\\Users\\admin\\Desktop\\event_IO.txt', 'r')
    for IO_type in f_IO.readlines():
        IO.append(float(IO_type))

    f_LWLock = open('C:\\Users\\admin\\Desktop\\event_LWLock.txt', 'r')
    for LWLock_type in f_LWLock.readlines():
        LWLock.append(float(LWLock_type))

    f_Lock = open('C:\\Users\\admin\\Desktop\\event_Lock.txt', 'r')
    for Lock_type in f_Lock.readlines():
        Lock.append(float(Lock_type))

    f_BufferPin = open('C:\\Users\\admin\\Desktop\\event_BufferPin.txt', 'r')
    for BufferPin_type in f_BufferPin.readlines():
        BufferPin.append(float(BufferPin_type))

    f_Client = open('C:\\Users\\admin\\Desktop\\event_Client.txt', 'r')
    for Client_type in f_Client.readlines():
        Client.append(float(Client_type))

    f_Extension = open('C:\\Users\\admin\\Desktop\\event_Extension.txt', 'r')
    for Extension_type in f_Extension.readlines():
        Extension.append(float(Extension_type))

    f_IPC = open('C:\\Users\\admin\\Desktop\\event_IPC.txt', 'r')
    for IPC_type in f_IPC.readlines():
        IPC.append(float(IPC_type))

    f_Timeout = open('C:\\Users\\admin\\Desktop\\event_Timeout.txt', 'r')
    for Timeout_type in f_Timeout.readlines():
        Timeout.append(float(Timeout_type))

    f_x_time = open('C:\\Users\\admin\\Desktop\\x_time.txt', 'r')
    for x_time_type in f_x_time.readlines():
        x_time.append(x_time_type)

if __name__ == "__main__":
    Activity = []
    IO = []
    LWLock = []
    Lock = []
    BufferPin = []
    Client = []
    Extension = []
    IPC = []
    Timeout = []
    x_time = []
    xact = []
    time_interval = []
    # 指定测试起始时间
    start_time = datetime.datetime(2019,7,26,17,49,0)
    #测试时间(大体上为压测时间)
    time_count=300
    # 初始化数据库连接对象
    conn = psycopg2.connect(database="test", user="flying", password="postgres", host="192.168.6.9", port="3432")
    TPS(conn,start_time,time_count,xact,time_interval)
    #加载等待事件数据
    load_data(Activity,IO,LWLock,Lock,BufferPin,Client,Extension,IPC,Timeout,x_time)
    #/刻画y轴的大小
    max_size=[];
    max_size.append(max(Activity))
    max_size.append(max(IO))
    max_size.append(max(IPC))
    max_size.append(max(LWLock))
    max_size.append(max(Lock))
    max_size.append(max(BufferPin))
    max_size.append(max(Extension))
    max_size.append(max(Timeout))
    max_size.append(max(Client))

    max_count=max(max_size)

    #指定画布大小
    plt.figure(figsize=(40, 10))

    #tps
    tps = plt.subplot(2,1,1)
    tps.plot(time_interval, xact, color='b')
    #指定x轴的间隔
    tps.set_xticks(time_interval[::10])
    tps.set_xlabel("datetime", fontsize=14)
    tps.set_ylabel("TPS", fontsize=14)
    tps.set_title("Database_TPS", fontsize=18)

    wait_event = plt.subplot(2,1,2)
    wait_event.plot(time_interval,Activity,'b',label='Activity')
    wait_event.plot(time_interval,Client,'g',label='Client')
    wait_event.plot(time_interval,LWLock,'r',label='LWLock')
    wait_event.plot(time_interval,Lock, 'c',label='Lock')
    wait_event.plot(time_interval, Extension, 'g:',label='Extension')
    wait_event.plot(time_interval, Timeout, 'y',label='Timeout')
    wait_event.plot(time_interval,IPC, 'k',label='IPC')
    wait_event.plot(time_interval, IO, 'm',label='IO')
    wait_event.plot(time_interval,BufferPin, 'b:',label='BufferPin')
    wait_event.set_xticks(time_interval[::10])
    my_y_ticks = np.arange(0,max_count,100)
    wait_event.set_xlabel("datetime", fontsize=14)
    wait_event.set_ylabel("Wait_Event_count", fontsize=14)
    wait_event.set_title("Database_Wait_Event", fontsize=18)
    plt.legend()
    plt.yticks(my_y_ticks)
    plt.show()