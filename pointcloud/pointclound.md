# 			pointcloud调研文档

## 一、pgpointcloud介绍

​	`pgpointcloud`是`PostgreSQL`中的一个存储点云数据(LIDAR)的插件，专门为了处理LIDAR数据而设计的。LIDAR传感器在扫描周围空间的时候会产生大量的点，而这些点除了包含XYZ坐标还可能包含其他更多纬度的信息。而每个维度可以是任意的数据类型。因此没有固定的类型来存储LIDAR数据，`pgpointcloud`使用"schema document"类型来描述LIDAR传感器上报的数据，格式与PDAL库的标准一致。 

## 二、pgpointcloud使用

### 一、点云对象

#### 	PcPoint

​	`PcPoint`是点云的基本类型，可以使用`PC_AsText(pcpoint)` 函数以JSON形式呈现该点。

```
-- pcid 引用的是pointcloud_formats中的pcid
-- pt   定义了每个维度的具体含义
{
    "pcid":1,
    "pt":[0.01,0.02,0.03,4]
}
```

#### PcPatch

​	如果在数据库中去单独存储每个`PcPoint`会浪费资源，我们可以根据实际情况将LIDAR传感器收集到的一组数据放到一个`PcPatch`中。我们也可以用`PC_AsText(pcpatch)`函数 以JSON的格式输出。

```
{
    "pcid" : 1,
     "pts" : [
               [0.02, 0.03, 0.05, 6],
               [0.02, 0.03, 0.05, 8]
             ]
}
```

#### 表

​	通常，您只会创建用于存储`PcPatch`对象的表，并使用`PcPoint`对象作为过渡对象进行过滤，但可以创建两种类型的表。`PcPatch`和`PcPoint`列都需要一个参数，指示`pcid`将用于解释列的参数。 

```sql
-- This example requires the schema entry from the previous
-- section to be loaded so that pcid==1 exists.

-- A table of points
CREATE TABLE points (
    id SERIAL PRIMARY KEY,
    pt PCPOINT(1)
);

-- A table of patches
CREATE TABLE patches (
    id SERIAL PRIMARY KEY,
    pa PCPATCH(1)
);
```

在创建`pointcloud`扩展后，系统会提供一张系统表和试图:

```sql
tsdb=# \d
              List of relations
 Schema |        Name        | Type  | Owner  
--------+--------------------+-------+--------
 public | pointcloud_columns | view  | flying
 public | pointcloud_formats | table | flying
(2 rows)

-- pointcloud_columns 显示数据库中所有包含点云对象列
-- pointcloud_formats 保存所有的PCID条目和模式文档
```

### 二、pointclound函数

#### 一、PcPoint函数

##### 1、pc_makepoint(pcid interger,vals float8[])  return pcpoint;

```sql
-- 函数的作用：给定一个有效的pcid模式号和一个与模式匹配的双精度数组，构造一个新的模式pcpoint
tsdb=# \df pc_makepoint
                                    List of functions
 Schema |     Name     | Result data type |          Argument data types          | Type 
--------+--------------+------------------+---------------------------------------+------
 public | pc_makepoint | pcpoint          | pcid integer, vals double precision[] | func
(1 row)


-- 创建一个四维模式
INSERT INTO pointcloud_formats (pcid, srid, schema) VALUES (1, 4326,
'<?xml version="1.0" encoding="UTF-8"?>
<pc:PointCloudSchema xmlns:pc="http://pointcloud.org/schemas/PC/1.1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <pc:dimension>
    <pc:position>1</pc:position>
    <pc:size>4</pc:size>
    <pc:description>X coordinate as a long integer. You must use the
                    scale and offset information of the header to
                    determine the double value.</pc:description>
    <pc:name>X</pc:name>
    <pc:interpretation>int32_t</pc:interpretation>
    <pc:scale>0.01</pc:scale>
  </pc:dimension>
  <pc:dimension>
    <pc:position>2</pc:position>
    <pc:size>4</pc:size>
    <pc:description>Y coordinate as a long integer. You must use the
                    scale and offset information of the header to
                    determine the double value.</pc:description>
    <pc:name>Y</pc:name>
    <pc:interpretation>int32_t</pc:interpretation>
    <pc:scale>0.01</pc:scale>
  </pc:dimension>
  <pc:dimension>
    <pc:position>3</pc:position>
    <pc:size>4</pc:size>
    <pc:description>Z coordinate as a long integer. You must use the
                    scale and offset information of the header to
                    determine the double value.</pc:description>
    <pc:name>Z</pc:name>
    <pc:interpretation>int32_t</pc:interpretation>
    <pc:scale>0.01</pc:scale>
  </pc:dimension>
  <pc:dimension>
    <pc:position>4</pc:position>
    <pc:size>2</pc:size>
    <pc:description>The intensity value is the integer representation
                    of the pulse return magnitude. This value is optional
                    and system specific. However, it should always be
                    included if available.</pc:description>
    <pc:name>Intensity</pc:name>
    <pc:interpretation>uint16_t</pc:interpretation>
    <pc:scale>1</pc:scale>
  </pc:dimension>
  <pc:metadata>
    <Metadata name="compression">dimensional</Metadata>
  </pc:metadata>
</pc:PointCloudSchema>');

-- 用法
tsdb=# select pc_makepoint(1,array[-1,1,2,3]);
              pc_makepoint              
----------------------------------------
 01010000009CFFFFFF64000000C80000000300
(1 row)
```

##### 2、pc_astext(p pcpoint)

```sql
-- 函数的作用：在该点返回数据的JSON版本
tsdb=# select pc_astext('01010000009CFFFFFF64000000C80000000300'::pcpoint);
         pc_astext          
----------------------------
 {"pcid":1,"pt":[-1,1,2,3]}
(1 row)
```

##### 3、pc_pcid(p pcpoint)

```sql
-- 函数的作用：返回该点的pcid
tsdb=# select pc_pcid('01010000009CFFFFFF64000000C80000000300'::pcpoint);
 pc_pcid 
---------
       1
(1 row)
```

##### 4、pc_get(pt pcpoint,dimname text)

```sql
-- 函数作用:返回指定维度的数值。维度名称必须存在于模式中。
tsdb=# select pc_get('01010000009CFFFFFF64000000C80000000300'::pcpoint,'x');
 pc_get 
--------
     -1
(1 row)
```

##### 5、pc_memsize(pt pcpoint)

```sql
-- 函数的作用:返回指定的pcpoint在内存中的大小
tsdb=# select pc_memsize('01010000009CFFFFFF64000000C80000000300'::pcpoint);
 pc_memsize 
------------
         25
(1 row)
```

#### 二、PcPatch函数

##### 1、pc_patch(pts pcpoint[]) return pcpatch

```sql
-- 函数的作用:将一组pcpoint集合放到pcpatch中
tsdb=# select pc_patch(array[pc_makepoint(1,array[1,2,3,4])::pcpoint,pc_makepoint(1,array[1,6,5,4])::pcpoint]);
                                                                                      pc_patch                        
                                                              
----------------------------------------------------------------------------------------------------------------------
--------------------------------------------------------------
 01010000000100000002000000030E00000078DA4B6160604801620004B800C9031000000078DA3BC1C0C010C1C4C0000007AE0123030E0000007
8DAD3616460F802C40005420123030C00000078DA636160610000001C0009
(1 row)
```

##### 2、pc_makepatch(pcid integer,vals float8 [])

```sql
-- 函数作用:给定一个有效的pcid模式号和一个与模式匹配的双精度数组，构造一个新的模式pcpatch。数组大小必须是维数的倍数。

tsdb=# select pc_makepatch(1,array[-1,2,3,4,-1,2,3,5,-1,2,3,6]);
                                                                                     pc_makepatch                     
                                                                
----------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------
 01010000000100000003000000030F00000078DA9BF3FFFFFF39500C0044760ACC030E00000078DA3BC1C0C070028A0112CC0259030E00000078D
AD3616460D081620004410088030E00000078DA6361606560630000003E0010
(1 row)
```

##### 3、pc_numpoints(p pcpatch)

```sql
-- 函数的作用:返回pcpatch中pcpoint的个数
tsdb=# select pc_numpoints(pa) from patches;
 pc_numpoints 
--------------
            3
(1 row)
```

##### 4、pc_pcid(p pcpatch)

```sql
-- 函数的作用:返回该pcpatch对应的pcid
tsdb=# select pc_pcid(pa) from patches limit 1;
 pc_pcid 
---------
       1
(1 row)
```

##### 5、pc_astext(p pcpatch)

```sql
-- 函数的作用:返回该pcpatch中的JSON版本数据
tsdb=# select pc_astext(pa) from patches limit 1;
                      pc_astext                      
-----------------------------------------------------
 {"pcid":1,"pts":[[-1,2,3,4],[-1,2,3,5],[-1,2,3,6]]}
(1 row)
```

##### 6、ps_summary(p pcpatch)

```sql
-- 函数的作用:返回该pcpatch的JSON格式摘要
tsdb=# select pc_summary(pa) from patches limit 1;
                                                                                                                                                                            
 {"pcid":1, "npts":3, "srid":4326, "compr":"dimensional","dims":[{"pos":0,"name":"X","size":4,"type":"int32_t","compr"
:"zlib","stats":{"min":-1,"max":-1,"avg":-1}},{"pos":1,"name":"Y","size":4,"type":"int32_t","compr":"zlib","stats":{"m
in":2,"max":2,"avg":2}},{"pos":2,"name":"Z","size":4,"type":"int32_t","compr":"zlib","stats":{"min":3,"max":3,"avg":3}
},{"pos":3,"name":"Intensity","size":2,"type":"uint16_t","compr":"zlib","stats":{"min":4,"max":6,"avg":5}}]}
(1 row)
```

##### 7、pc_uncompress(p pcpatch)

```sql
-- 函数的作用：返回pcpatch未压缩的版本
tsdb=# select pc_uncompress(pa) from patches;
                                                 pc_uncompress                                                  
----------------------------------------------------------------------------------------------------------------
 010100000000000000030000009CFFFFFFC80000002C01000004009CFFFFFFC80000002C01000005009CFFFFFFC80000002C0100000600
(1 row)
```

##### 8、pc_union(p patch[])

```sql
-- 函数的作用:将pcpatch条目的结果集合并为单个pcpatch
tsdb=# select pc_union(pa) from patches;
                                                                             pc_union                                 
                                            
----------------------------------------------------------------------------------------------------------------------
--------------------------------------------
 010100000001000000060000000105000000069CFFFFFF0210000000080000000000000000C8C8C80000C8C8031200000078DAD3616460D041C27
B98203400135D01A002080000000400000064450059
(1 row)
```

##### 9、pc_intersects(p1 pcpatch,p2 pcpatch)

```sql
-- 函数的作用:如果p1的边界与p2的边界相交，则返回true
tsdb=# SELECT PC_Intersects('01010000000000000001000000C8CEFFFFF8110000102700000A00'::pcpatch,'01010000000000000001000000C8CEFFFFF8110000102700000A00'::pcpatch);
 pc_intersects 
---------------
 t
(1 row)
```

##### 10、pc_explode(p pcpatch)

```sql
--函数的作用:设置返回功能，将补丁转换为补丁中每个点的一个点记录的结果集
tsdb=# select pc_explode(pa) from patches where id=2;
               pc_explode               
----------------------------------------
 01010000009CFFFFFF000000002C0100000400
 01010000009CFFFFFFC8000000BC0200000500
 01010000009CFFFFFFC80000002C0100000900
(3 rows)

tsdb=# select pc_astext(pc_explode(pa)) from patches where id=2;
         pc_astext          
----------------------------
 {"pcid":1,"pt":[-1,0,3,4]}
 {"pcid":1,"pt":[-1,2,7,5]}
 {"pcid":1,"pt":[-1,2,3,9]}
(3 rows)
```

##### 11、pc_patchmax(p pcpatch,dimname text)

```sql
-- 函数的作用:返回该pcpatch指定的某个维度的最大值
tsdb=# select pc_patchmax(pa,'Z') from patches where id=2;
 pc_patchmax 
-------------
           7
(1 row)

-- 如果不指定某个维度，则返回的记录是每个维度的最大值的一个pcpoint
tsdb=# select pc_astext(pc_patchmax(pa)) from patches where id=2;
         pc_astext          
----------------------------
 {"pcid":1,"pt":[-1,2,7,9]}
(1 row)
```

##### 12、pc_patchmin(p pcpatch,dimname text)

```sql
-- 函数的作用:返回该pcpatch指定的某个维度的最小值
tsdb=# select pc_patchmin(pa,'Z') from patches where id=2;
 pc_patchmin 
-------------
           3
(1 row)

-- 如果不指定某个维度，则返回的记录是每个维度的最小值的一个pcpoint
tsdb=# select pc_astext(pc_patchmin(pa)) from patches where id=2;
         pc_astext          
----------------------------
 {"pcid":1,"pt":[-1,0,3,4]}
(1 row)
```

##### 13、pc_patchavg(p pcpatch，dimname text)

```sql
-- 函数的作用:返回该pcpatch指定维度的平均值
tsdb=# select pc_patchavg(pa,'Z') from patches where id=2;
 pc_patchavg 
-------------
        4.33
(1 row)

-- 如果不指定某个维度，则返回的记录是每个维度的平均值的一个pcpoint
tsdb=# select pc_astext(pc_patchavg(pa)) from patches where id=2;
            pc_astext             
----------------------------------
 {"pcid":1,"pt":[-1,1.33,4.33,6]}
(1 row)
```

##### 14、pc_filtergreaterthan(p pcpatch,dimname text,float8 value)

```sql
-- 函数的作用:返回该pcpatch中大于指定维度的指定值的pcpoint
tsdb=# select pc_astext(pc_filtergreaterthan(pa,'Z',3)) from patches where id=2;
           pc_astext           
-------------------------------
 {"pcid":1,"pts":[[-1,2,7,5]]}
(1 row)
```

##### 15、pc_filterlessthan(p pcpatch,dimname text,float8 value)

```sql
-- 函数的作用:返回该pcpatch中小于指定维度的指定值的pcpoint
tsdb=# select pc_astext(pc_filterlessthan(pa,'Z',5)) from patches where id=2;
                pc_astext                 
------------------------------------------
 {"pcid":1,"pts":[[-1,0,3,4],[-1,2,3,9]]}
(1 row)
```

##### 16、pc_filterbetween(p  pcpatch,dimname text,float8 value1,float8 value2)

```sql
-- 函数的作用:返回该pcpatch中介于指定维度给出的两个值
tsdb=# select pc_astext(pc_filterbetween(pa,'Z',2,4)) from patches where id=2;
                pc_astext                 
------------------------------------------
 {"pcid":1,"pts":[[-1,0,3,4],[-1,2,3,9]]}
(1 row)
```

##### 17、pc_filterequals(p pcpatch,dimname text,float8 value)

```
-- 函数的作用:返回该pcpatch中等于指定维度的指定大小的pcpoint
tsdb=# select pc_astext(pc_filterequals(pa,'Z',3)) from patches where id=2;
                pc_astext                 
------------------------------------------
 {"pcid":1,"pts":[[-1,0,3,4],[-1,2,3,9]]}
(1 row)
```

##### 18、pc_compress(p pcpatch,global_compression_scheme text,compression_config text)

```sql
-- 函数的作用:使用手动指定的方案压缩补丁。compression_config语义取决于全局压缩方案。
-- 允许的全局压缩方案是：
         auto -- 由pcid决定
         laz -- 不支持压缩配置
		维度配置是此列表中以逗号分隔的每维度压缩列表
            auto -- determined automatically, from values stats
            zlib -- deflate compression
            sigbits -- significant bits removal
            rle -- run-length encoding
tsdb=# select pc_astext(pc_compress(pa,'auto','zlib')) from patches where id=2;
                      pc_astext                      
-----------------------------------------------------
 {"pcid":1,"pts":[[-1,0,3,4],[-1,2,7,5],[-1,2,3,9]]}
(1 row)
```

##### 19、pc_pointn(p pcpatch,n int4)

```sql
-- 函数的作用：返回该pcpatch中指定的某个pcpoint
tsdb=# select pc_astext(pc_pointn(pa,2)) from patches where id=2;
         pc_astext          
----------------------------
 {"pcid":1,"pt":[-1,2,7,5]}
(1 row)

```

##### 20、pc_issorted(p pcpatch,dimnames text[],strict boolean default true)

```sql
-- 函数的作用：检查pcpatch是否按照给定的字典顺序排序
tsdb=# select pc_issorted(pa,array['X','Y','Z','Intensity']) from patches;
 pc_issorted 
-------------
 t
 f
(2 rows)
```

##### 21、pc_sort(p pcpatch,dimnames text[])

```sql
-- 函数的作用:返回按照给定的字典顺序排序的pcpatch副本
tsdb=# select pc_astext(pa) from patches;
                      pc_astext                      
-----------------------------------------------------
 {"pcid":1,"pts":[[-1,2,3,4],[-1,2,3,5],[-1,2,3,6]]}
 {"pcid":1,"pts":[[-1,0,3,4],[-1,2,7,5],[-1,2,3,9]]}
(2 rows)

tsdb=# select pc_astext(pc_sort(pa,array['X','Y','Z','Intensity'])) from patches;
                      pc_astext                      
-----------------------------------------------------
 {"pcid":1,"pts":[[-1,2,3,4],[-1,2,3,5],[-1,2,3,6]]}
 {"pcid":1,"pts":[[-1,0,3,4],[-1,2,3,9],[-1,2,7,5]]}
(2 rows)
```

##### 22、pc_range(p patch,start int4,n int4)

```sql
-- 函数的作用:从该pcpatch中指定的起始位置开始返回n包含n个pcpoint的pcpatch
tsdb=# select pc_astext(pc_range(pa,1,1)) from patches where id=2; 
           pc_astext           
-------------------------------
 {"pcid":1,"pts":[[-1,0,3,4]]}
(1 row)
```

##### 23、pc_setpcid(p pcpatch,pcid int4,def float8 default 0.0)

```sql
-- 给定有效的pcid，如果该pcpatch中有在新的模式中，但不在原来的模式中，将用def代替这些没有维度的值

tsdb=# select pc_astext(pc_setpcid(pc_makepatch(1,array[1,2,3,4,5,6,7,8]),2,9));
                 pc_astext                  
--------------------------------------------
 {"pcid":2,"pts":[[1,2,3,4,9],[5,6,7,8,9]]}
(1 row)
```

##### 24、pc_transform(p pcpatch,pcid int4 def float8 default 0.0)

```sql
-- 函数的作用:类似于pc_setpcid，但不同的地方在于PC_Transform如果新模式中的维度解释，缩放或偏移不--- 同，则可以更改（转换）补丁数据。
tsdb=# select pc_astext(pc_transform(pc_makepatch(1,array[1,2,3,4,5,6,7,8]),3,9));
                  pc_astext                   
----------------------------------------------
 {"pcid":3,"pts":[[1,2,3,4,10],[5,6,7,8,10]]}
(1 row)
```

##### 25、pc_memsize(p pcpatch)

```sql
-- 函数的作用:返回pcpatch在内存中的大小
tsdb=# select pc_memsize(pa) from patches;
 pc_memsize 
------------
        174
        178
(2 rows)


```

#### 三、OGC“众所周知的二元”函数

##### 1、pc_asbinary(p pcpoint)

```sql
-- 函数的作用:返回OGC"众所周知的二进制"格式
tsdb=# select pc_asbinary(pt) from points where id=1;
                             pc_asbinary                              
----------------------------------------------------------------------
 \x01010000a0e6100000000000000000f03f00000000000000400000000000000840
(1 row)
```

##### 2、pc_envelopeasbinary(p pcpatch)

```sql
-- 函数的作用:为pcpatch2D边界返回二进制格式
tsdb=# select pc_envelopeasbinary(pa) from patches where id=2;
                                                                                         pc_envelopeasbinary                             
                                                             
-----------------------------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------
 \x0103000020e61000000100000005000000000000000000f0bf0000000000000000000000000000f0bf0000000000000040000000000000f0bf00000000000000400000
00000000f0bf0000000000000000000000000000f0bf0000000000000000
(1 row)
```

##### 3、pc_boundingdiaonalasbinary(p pcpatch)

```sql
-- 函数的作用：为该pcpatch的边界对角线返回二进制格式
tsdb=# select pc_boundingdiagonalasbinary(pa) from patches where id=2;
                                                 pc_boundingdiagonalasbinary                                                  
------------------------------------------------------------------------------------------------------------------------------
 \x01020000a0e610000002000000000000000000f0bf00000000000000000000000000000840000000000000f0bf00000000000000400000000000001c40
(1 row)
```

### 三、PostGIS集成

​	`pointcloud_postgis`扩展添加了一些功能，允许您将`PostgreSQL Pointcloud`与`PostGIS`一起使用，将`PcPoint`和`PcPatch`转换为`Geometry`并对点云数据进行空间过滤。`pointcloud_postgis`依赖于`postgis`和`pointcloud`,所以需要先安装这两个插件：

```sql
-- 创建扩展
CREATE EXTENSION postgis;
CREATE EXTENSION pointcloud;
CREATE EXTENSION pointcloud_postgis;(编译pointclound时最好使用--with-cunit指定位置否则可能不会有这个扩展,编译时注意看有没有pointcloud_postgis.sql文件生成)

-- 插入测试数据
tsdb=# INSERT INTO points (pt)
SELECT PC_MakePoint(1, ARRAY[x,y,z,intensity])
FROM (
  SELECT
  -127+a/100.0 AS x,
    45+a/100.0 AS y,
         1.0*a AS z,
          a/10 AS intensity
  FROM generate_series(1,100) AS a
) AS values;

tsdb=# INSERT INTO patches (pa) SELECT PC_Patch(pt) FROM points GROUP BY id/10;
```

#### 一、pointcloud_postgis 功能测试

##### 	1、pc_intersects

```sql
tsdb=# \df pc_intersects;
                             List of functions
 Schema |     Name      | Result data type |  Argument data types   | Type 
--------+---------------+------------------+------------------------+------
 public | pc_intersects | boolean          | geometry, pcpatch      | func
 public | pc_intersects | boolean          | p1 pcpatch, p2 pcpatch | func
 public | pc_intersects | boolean          | pcpatch, geometry      | func

-- pc_intersects(g pcpatch,g geometry)
-- pc_intersects(g geometry,g pcpatch)
-- 函数的作用:如果patch的边界和几何体相交，则返回true

-- 测试y=x+2
tsdb=# SELECT PC_Intersects('SRID=4326;POINT(0 2)'::geometry, pc_makepatch(1,array[-1,1,0,0,1,3,0,0]));
 pc_intersects 
---------------
 t
(1 row)
```

##### 	2、pc_intersection

```sql
-- 函数的作用:返回patch中与几何体相交的点
SELECT PC_AsText(PC_Explode(PC_Intersection(
      pa,
      'SRID=4326;POLYGON((-126.451 45.552, -126.42 47.55, -126.40 45.552, -126.451 45.552))'::geometry
)))
FROM patches WHERE id = 7;

             pc_astext
--------------------------------------
 {"pcid":1,"pt":[-126.44,45.56,56,5]}
 {"pcid":1,"pt":[-126.43,45.57,57,5]}
 {"pcid":1,"pt":[-126.42,45.58,58,5]}
 {"pcid":1,"pt":[-126.41,45.59,59,5]}
```

##### 	3、geometry(pcpoint)

```sql
-- 函数的作用:将pcpoint转换为PostGIS几何等效项
tsdb=# select st_astext(geometry(pc_makepoint(1,array[-126,34,23,7])));
      st_astext       
----------------------
 POINT Z (-126 34 23)
(1 row)
```

##### 	4、pc_envelopegeometry(pcpatch)

```sql
-- 函数的作用:以PostGIS Polygon 2D形式返回pcpatch的2D 边界
tsdb=# select st_astext(pc_envelopegeometry(pa)) from patches limit 1;
              st_astext              
-------------------------------------
 POLYGON((-1 2,-1 2,-1 2,-1 2,-1 2))
(1 row)

-- 在patches表上创建索引的方法
tsdb=# create index on patches using gist(pa);
ERROR:  data type pcpatch has no default operator class for access method "gist"
HINT:  You must specify an operator class for the index or define a default operator class for the data type.

tsdb=# create index on patches using gist(pc_envelopegeometry(pa));
CREATE INDEX
```

##### 	5、pc_boundingdiagonalgeometry(pcpatch)

```sql
-- 函数的作用:返回pcpatch的边界对角线，这是一个LineString（2D），一个LineString Z或一个LineString M或一个LineString ZM，基于补丁中Z和M维度的存在。此功能对于在修补程序列上创建索引很有用。

-- 创建索引
tsdb=# CREATE INDEX ON patches USING GIST(PC_BoundingDiagonalGeometry(pa) gist_geometry_ops_nd);
CREATE INDEX
```

### 四、压缩

​	由于LIDAR数据量一般非常大，有时候为了处理这些大数据量，可以在模式文档中声明首选的压缩方法。例如：

```yaml
<pc:metadata>
  <Metadata name="compression">dimensional</Metadata>
</pc:metadata>
```

​	目前支持四种压缩方法:

- None,根据模式文档中描述的类型和格式将`pcpoint`和`pcpatch`存储为字节数组。
- Dimensional,存储`pcpoint`时和None相同，存储`pcpatch`时会存储为维度数据数组的集合，并适当的压缩。尺寸压缩对于更小的`pcpatch`来说是最有意义的，因为小的`pcpatch`往往具有更均匀的尺寸。
- LAZ,必须构建具有LAZPERF支持的Pointcloud才能使用LAZ压缩 

如果未声明`<pc:metadata>`压缩，则假定压缩为“none”。

##### 	Dimensional Compression 

`Dimensional Compression`压缩首先将`pcpatch`表示从包含M个维度值的N个点的列表翻转到包含N个值的M个维度的列表。 例如:

```
{"pcid":1,"pts":[
      [-126.99,45.01,1,0],[-126.98,45.02,2,0],[-126.97,45.03,3,0],
      [-126.96,45.04,4,0],[-126.95,45.05,5,0],[-126.94,45.06,6,0]
     ]}
     
{"pcid":1,"dims":[
      [-126.99,-126.98,-126.97,-126.96,-126.95,-126.94],
      [45.01,45.02,45.03,45.04,45.05,45.06],
      [1,2,3,4,5,6],
      [0,0,0,0,0,0]
     ]}
```

​	这种压缩的潜在好处是，每个维度具有完全不同的分布特性，并且适合不同的方法。在本例中，第四维(强度)可以`run-length encoding`通过(6个0中的一个运行)进行高度压缩。第一和第二维度相对于它们的大小具有相对较低的变异性，可以通过删除重复的位来压缩。 

​	`Dimensional Compression` 目前支持三种压缩方案:

- run-length encoding :用于具有低可变性的维度 
- common bits removal :用于在窄位范围内具有可变性的维度 
- 使用zlib进行原始deflate压缩，用于不适合其他方案的维度

### 五、二进制格式

​	为了保留转储文件和网络传输中的一些紧凑性，二进制格式需要保留其本机压缩。所有二进制格式在输出之前都是十六进制编码 。

​	`point`和`patch`二进制格式有公共头部：

- 字节序标识，允许架构之间的可移植性 

- pcid编号，用于查找`pointcloud_formats`表中的架构信息

  `patch`二进制格式具有其他标准标头信息 :

- 压缩数，表示如何解释数据

- `patch`中包含的`point`数量

#### point的二进制格式

```
byte:     endianness (1 = NDR, 0 = XDR)
uint32:   pcid (key to POINTCLOUD_SCHEMAS)
uchar[]:  pointdata (interpret relative to pcid)
```

#### patch的二进制格式

##### 未压缩

```
byte:         endianness (1 = NDR, 0 = XDR)
uint32:       pcid (key to POINTCLOUD_SCHEMAS)
uint32:       0 = no compression
uint32:       npoints
pointdata[]:  interpret relative to pcid
```

##### Dimensional压缩

```
byte:          endianness (1 = NDR, 0 = XDR)
uint32:        pcid (key to POINTCLOUD_SCHEMAS)
uint32:        2 = dimensional compression
uint32:        npoints
dimensions[]:  dimensionally compressed data for each dimension

-- 每个维度的二进制格式
byte:           dimensional compression type (0-3)  //压缩的类型
uint32:         size of the compressed dimension in bytes //压缩尺寸的大小
data[]:         the compressed dimensional values

-- 压缩类型
no compression = 0,
run-length compression = 1,
significant bits removal = 2,
deflate = 3
```

1、no compression

​	如果没有压缩，值将会按顺序出现

2、run-length compression

​	数据流由一组对组成：一个表示run-length的字节值，以及一个表示重复值的数据值。 

```
 byte:          number of times the word repeats
 word:          value of the word being repeated
 ....           repeated for the number of runs
```

3、significant bits removal

​	重要的位移除从两个单词开始。第一个字只给出了“有效”的位数，即从任何给定字中移除公共位之后剩余的位数。第二个字是公共位的位掩码，最后的可变位清零。 

```
 word1:          number of variable bits in this dimension
 word2:          the bits that are shared by every word in this dimension
 data[]:         variable bits packed into a data buffer
```

4、deflate

​	在简单压缩方案失败的情况下，使用zlib将通用压缩应用于维度。数据区是一个原始的zlib缓冲区，适合直接传递给inflate（）函数。输入缓冲区的大小在公共维度标题中给出。通过将维度字大小乘以补丁中的点数，可以从补丁元数据中导出输出缓冲区的大小。 

#### patch二进制(LAZ)

```
byte:          endianness (1 = NDR, 0 = XDR)
uint32:        pcid (key to POINTCLOUD_SCHEMAS)
uint32:        2 = LAZ compression
uint32:        npoints
uint32:        LAZ data size
data[]:        LAZ data
-- 使用LAZPERF库将LAZ数据缓冲区读入LAZ缓冲区
```

### 六、如何将数据导入pointcloud

​	简单来说有两种，来自WKB和来自PDAL

#### 来自WKB

​	如果您正在编写自己的加载系统并想要写入Pointcloud类型，请以未压缩格式创建众所周知的二进制输入。如果您的架构指示您的补丁存储已压缩，Pointcloud将在存储之前自动压缩补丁，因此您可以在未压缩的WKB中创建补丁，而无需担心特定内部压缩方案的细微差别。

​	创建WKB补丁时要注意的唯一问题是：确保您编写的数据根据模式调整大小（使用指定的维度类型）; 确保数据的字节顺序与修补程序的声明字节顺序相匹配。

### 来自PDAL

##### 构建并安装PDAL

​	要构建和安装PDAL，请查看[PDAL开发文档](https://www.pdal.io/development)。

​	安装PDAL后，您就可以将PDAL导入到PostgreSQL PointCloud中了！

##### 运行 `pdal pipeline`

​	PDAL包括一个[命令行程序](http://www.pointcloud.org/apps.html)，它允许简单的格式转换和更复杂的转换“管道”。在`pdal translate`做简单的格式转换。为了将数据加载到Pointcloud中，我们通过调用使用“PDAL管道” `pdal pipeline`。管道将格式阅读器和格式编写器与可以将点更改或分组在一起的过滤器组合在一起。 

​	PDAL管道是JSON文件，它声明读取器，过滤器和写入器形成将应用于LIDAR数据的处理链。

​	要执行管道文件，请通过以下`pdal pipeline`命令运行它：

```bash
pdal pipeline --input pipelinefile.json
```

简单的示例管道，它读取LAS文件并写入PostgreSQL Pointcloud数据库。 

```
{
  "pipeline":[
    {
      "type":"readers.las",
      "filename":"/home/lidar/st-helens-small.las",
      "spatialreference":"EPSG:26910"
    },
    {
      "type":"filters.chipper",
      "capacity":400
    },
    {
      "type":"writers.pgpointcloud",
      "connection":"host='localhost' dbname='pc' user='lidar' password='lidar' port='5432'",
      "table":"sthsm",
      "compression":"dimensional",
      "srid":"26910"
    }
  ]
}
```

​	为了得到更加紧凑的`patch`,在将无序数据从LIDAR文件转换为数据库中的数据时可以通过过滤器，最常见的过滤器是切片。

​	同样，从PostgreSQL Pointcloud读取数据使用Pointcloud阅读器和某种文件编写器。此示例从数据库读取并写入CSV文本文件： 

```
{
  "pipeline":[
    {
      "type":"readers.pgpointcloud",
      "connection":"host='localhost' dbname='pc' user='lidar' password='lidar' port='5432'",
      "table":"sthsm",
      "column":"pa",
      "spatialreference":"EPSG:26910"
    },
    {
      "type":"writers.text",
      "filename":"/home/lidar/st-helens-small-out.txt"
    }
  ]
}
```

可以用where条件限制读取的内容，从而到达只从表中提取部分内容的效果：

```
{
  "pipeline":[
    {
      "type":"readers.pgpointcloud",
      "connection":"host='localhost' dbname='pc' user='lidar' password='lidar' port='5432'",
      "table":"sthsm",
      "column":"pa",
      "spatialreference":"EPSG:26910",
      "where":"PC_Intersects(pa, ST_MakeEnvelope(560037.36, 5114846.45, 562667.31, 5118943.24, 26910))",
    },
    {
      "type":"writers.text",
      "filename":"/home/lidar/st-helens-small-out.txt"
    }
  ]
}
```

##### PDAL pgpointcloud读/写器选项

写选项:

- **connection** :PostgreSQL数据库连接字符串。 
- **table** :创建数据库表以将`patch`写入 。
- **schema**：用于创建表的模式。 
- **column**：要在修补程序表中使用的列名。 
- **compression** ：要使用的patch压缩格式。
- **overwrite** :替换任何现有的表 。
- **srid**：在[Optional：4326]中存储数据的空间参考ID
- **pcid**：用于点云架构的现有PCID 。
- **pre_sql**：在管道运行之前，读取并执行此SQL文件或命令。
- **post_sql**：管道运行后，读取并执行此SQL文件或命令。

读选项:

- **connection** :PostgreSQL数据库连接字符串 。
- **table**：从中读取`patch`的数据库表。
- **schema**：从中读取表的模式。 
- **column**：要读取的`patch`表中的列名称。
- **where** ：SQL where子句约束查询 
- **spatialreference**：覆盖声明为SRID的数据库 

## 三、pointcloud性能测试

### 一、pointcloud插入速度

```sql
-- 创建测试数据库
create database tsdb;

-- 创建测试表
tsdb=# create table pointcloud_test(
id serial primary key,
pa pcpatch(1),
info text);
CREATE TABLE
```

插入速度测试:(插入100万数据)

```bash
-- 测试脚本
vi test.sql
insert into pointcloud_test(pa,info) values(pc_makepatch(1,array[random()*100,random()*100,random()*100,random()*10]),'pointcloud_test');

-- pgbench 压测
pgbench -M prepared -n -r -P 1 -f test.sql -c 50 -j 50 -t 20000  -h192.168.2.220 -Uflying  -p5432 tsdb

transaction type: test.sql
scaling factor: 1
query mode: prepared
number of clients: 50
number of threads: 50
number of transactions per client: 20000
number of transactions actually processed: 1000000/1000000
latency average = 13.842 ms
latency stddev = 9.461 ms
tps = 3586.628319 (including connections establishing)
tps = 3587.456731 (excluding connections establishing)
statement latencies in milliseconds:
        13.840  insert into pointcloud_test(pa,info) values(pc_makepatch(1,array[random()*100,random()*100,random()*100,random()*10]),'pointcloud_test');
```

### 二、pointcloud查询速度

```sql
-- 没有索引场景下(查询速度)

tsdb=# explain (analyze,verbose) select pc_astext(pa),info,st_distance(pc_envelopegeometry(pa),pc_makepatch(1,array[87.93,98.07,8.0,7])::geometry) as distance from pointcloud_test where st_distance(pc_envelopegeometry(pa),pc_makepatch(1,array[87.93,98.07,8.0,7])::geometry)<1;
                                                                                                                                                        QUERY PLAN                          
                                                                                                                               
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------------------------------
 Seq Scan on public.pointcloud_test  (cost=0.00..129729.94 rows=333406 width=56) (actual time=3.067..4325.326 rows=352 loops=1)
   Output: pc_astext(pa), info, st_distance(st_geomfromewkb(pc_envelopeasbinary(pa)), '0103000020E61000000100000005000000EC51B81E85FB554015AE47E17A845840EC51B81E85FB554015AE47E17A845840EC5
1B81E85FB554015AE47E17A845840EC51B81E85FB554015AE47E17A845840EC51B81E85FB554015AE47E17A845840'::geometry)
   Filter: (st_distance(st_geomfromewkb(pc_envelopeasbinary(pointcloud_test.pa)), '0103000020E61000000100000005000000EC51B81E85FB554015AE47E17A845840EC51B81E85FB554015AE47E17A845840EC51B81
E85FB554015AE47E17A845840EC51B81E85FB554015AE47E17A845840EC51B81E85FB554015AE47E17A845840'::geometry) < '1'::double precision)
   Rows Removed by Filter: 999648
 Planning Time: 2.810 ms
 Execution Time: 4325.487 ms
(6 rows)
```

