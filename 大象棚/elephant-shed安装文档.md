# 		elephant-shed安装文档

## 一、安装说明

​	从https://packages.credativ.com/public/postgresql/yum/获取yum源(包含部分elephant-shed相关的依赖包)，除了上面的yum源还需要很多依赖的RPM包，可以从https://yum.postgresql.org/获得。方便使用这里已经打包好，可以从FTP服务器上下载，也可以下载打包好的压缩包离线安装。

## 二、相关依赖包的获取

### 安装FTP客户端

```bash
-- 安装FTP客户端
[root@test2 ~]# yum -y install ftp
```

### 从FTP服务器获取依赖包(也可以直接下载压缩包)

```bash
-- 获取依赖的RPM包
-- name:ftp  password:空
[root@test2 ~]# ftp 192.168.2.226
Connected to 192.168.2.226 (192.168.2.226).
220 (vsFTPd 3.0.2)
Name (192.168.2.226:root): ftp
331 Please specify the password.
Password:
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> cd pub
250 Directory successfully changed.
ftp> ls
227 Entering Passive Mode (192,168,2,226,132,102).
150 Here comes the directory listing.
-rw-r--r--    1 0        0        265466084 Sep 03 03:04 elephant-shed.tar.gz
226 Directory send OK.
ftp> get elephant-shed.tar.gz
local: elephant-shed.tar.gz remote: elephant-shed.tar.gz
227 Entering Passive Mode (192,168,2,226,255,243).
150 Opening BINARY mode data connection for elephant-shed.tar.gz (265466084 bytes).
226 Transfer complete.
265466084 bytes received in 11.7 secs (22647.17 Kbytes/sec)
ftp> exit
221 Goodbye.

-- 解压到/opt/
[root@test2 ~]# tar -xzvf elephant-shed.tar.gz -C /opt/
[root@test2 ~]# ls /opt/elephant-shed/
pgadmin4-web  pgbackrest  pgbadger
```

### 配置本地YUM源

```bash
-- 安装elephant-shed需要依赖
-- 由于这里依赖过多，这里配置本地的yum源
[root@test2 ~]#yum -y install createrepo
[root@test2 ~]#createrepo /opt/elephant-shed/pgadmin4-web
[root@test2 ~]#createrepo /opt/elephant-shed/pgbackrest
[root@test2 ~]#createrepo /opt/elephant-shed/pgbadger

-- 配置本地的yum源，修改/etc/yum.repos.d/local.repo并添加下面的内容
[pgadmin4-web]
name=pgamdin4-web_yum
baseurl=file:///opt/elephant-shed/pgadmin4-web
gpgcheck=0
enabled=1

[pgbackrest]
name=pgbackrest_yum
baseurl=file:///opt/elephant-shed/pgbackrest
gpgcheck=0
enabled=1

[pgbadger]
name=pgbadger_yum
baseurl=file:///opt/elephant-shed/pgbadger
gpgcheck=0
enabled=1

-- 配置完成后清空缓存
[root@test2 ~]#yum clean all
[root@test2 ~]#yum list
```

### 安装elephant-shed

```bash
-- 安装yum源
[root@test2 ~]# yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
[root@test2 ~]# yum install https://packages.credativ.com/public/postgresql/yum/credativ-repo.rpm

-- 如果是RedHat还需要激活额外的存储库
subscription-manager repos --enable=rhel-7-server-extras-rpms
subscription-manager repos --enable=rhel-7-server-optional-rpms

-- 选择PostgreSQL版本进行安装
[root@test2 ~]#yum install postgresql11-server postgresql11-contrib postgresql-common

-- 安装elephant-shed
[root@test2 ~]#yum install elephant-shed
```

