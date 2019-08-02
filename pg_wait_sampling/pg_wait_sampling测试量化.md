# 	pg_wait_sampling调研文档

​	主要测试不同等待事件类型对数据库性能(TPS)的影响,下面是整个测试流程。

### 环境信息

|   系统   |     IP      | postgresql | 内存  | CPU    |
| :------: | :---------: | :--------: | :---: | ------ |
| rhel 7.5 | 192.168.6.9 |    11.3    | 256GB | 2x28核 |

### 测试准备

#### 	1、安装pg_wait_sampling插件

​	见  `pg_wait_sampling`安装文档

#### 	2、创建测试库和相关的表

```
create database test;
#profile_log用于记录每次等待事件的数据
create table profile_log;
```

#### 	  3、初始化压测数据(1000万)

```
[postgres@node6 bin]$ ./pgbench -i -F 100 -s 100 -p3432 -Uflying -h192.168.6.9 test
```

#### 4、创建write_profiel_log()函数

​	write_profile_log函数的作用是每次将等待事件数据记录到profile_log表中去

```
CREATE OR REPLACE FUNCTION write_profile_log () RETURNS integer AS $$ DECLARE result integer ; BEGIN 
	INSERT INTO profile_log SELECT current_timestamp , event_type , event , SUM ( count ) FROM pg_wait_sampling_profile WHERE event IS NOT NULL GROUP BY event_type , event ; 
	GET DIAGNOSTICS result = ROW_COUNT ;
    PERFORM pg_wait_sampling_reset_profile (); 
    RETURN result ; 
    END $$ LANGUAGE 'plpgsql' ;
```

### 测试流程

​	测试脚本为TPS.py和wait_event.py，需要指定测试的起始时间和结束时间以及压测的时间，根据环境信息修改好脚本之后即可运行脚本开始测试。

```
#压测，压测时间根据脚本中指定的测试时间做适当的调整
[postgres@node6 bin]$ ./pgbench -M simple -p 3432 -U flying -P 1 -n -r -c 56 -j 56 test -T 330
```

### 测试结果

​	测试结果图:https://i.loli.net/2019/07/26/5d3aad5eeb80b91912.png

​	根据测试结果图，可以看出等待事件类型中的LWLock、Lock以及IO与TPS有着明显关系，当系统中这些等待事件类型的数量上升时，TPS会降低，反之则会升高。而本次测试中有的等待事件类型例如`Extension`等，由于测试环境的限制并没有很大的变化。