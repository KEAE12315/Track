## 轨迹分析API

由三部分构成: 重要位置提取, 危险程度打分, 轨迹预测.

### 原理说明

#### 1. 聚类部分

采用多级聚类的方式, 从一系列轨迹中提取用户经常停留的, 比较重要的位置.

第一步: 采用基于区域一致性的聚类方法, 以轨迹点之间的速度和距离作为指标, 提取出用户经常停留的驻足点(Stay Points).

第二步: 因为用户在不同时间段都有可能经过同一个地方, 导致第一步提取出来的驻足点多有重复. 这一步采用基于密度的DBSCAN算法对上一步的驻足点进行聚类, 得到不重复的重要位置(Landmark).

#### 2. 打分部分

#### 3. 预测部分

训练: 利用上一部分得到的重要位置, 将原来密集的轨迹点转化为对应的离散重要位置序列. 将这个重要位置序列作为LSTM的输入进行训练.

预测: 保证数据长度与训练一致的情况下, 输入一串重要位置序列的GPS坐标, 得到一个预测的经纬度坐标.

### API使用说明

#### 1. 轨迹提取(仅有post方法)
URL: http://127.0.0.1:5000/extraction/
| Key | Value | 轨迹提取输入参数说明 |
| :- | :- | :- |
| user_path	| string | 用户轨迹文件地址
| sp_roh	| float	 | 连接权值阈值，值越大，驻足点越少
| sp_phi	| int	 | 数量阈值，值越大，驻足点点越少
| lm_eps	| int	 | 连接权值阈值，值越大，重要位置点越少
| lm_minPts	| int	 | 数量阈值，值越大，重要位置点越少

| Key | Value | 轨迹提取输出参数说明 |
| :- | :- | :- |
| stay points	| list of dict | 驻足点列表
| landmarks	| list of dict | 重要位置列表

> **示例**：
>
> 输入json：`{ "user_path": "dataset/001", "sp_roh": 0.3, "sp_phi": 3, "lm_eps": 4, "lm_minPts": 1}`
>
> 输出json：
>
>```{
> "msg": "SUCCESS: Complete the calculation!", 
>
> "results": {
>
>     "landmarks": [
>
>   {
>
>​    "latitude": 40.01382, 
>
>​    "longitude": 116.306485
>
>   }, …]
>
>"stay points": [
>
>   {
>
>​    "latitude": 40.014126, 
>
>​    "longitude": 116.306242
>
>   }, …]
>
>"status": 200
>
>}
>```


> 备注:  
> 
> 1. 直接传轨迹json文件太大，服务器会不接受，结果为空。因此只能传送路径过去，docker运行时需要挂载文件目录，不然找不到。
> 2. docker运行命令：
>    docker run -it -v<实际轨迹文件位置>:<传过去的user path> -p 127.0.0.1:5001:5000 extraction
> 3. 用户轨迹请确保为json文件，格式为：
>    [{"lat":39.977998,"lon":116.326704,"days":39750.4621527778},…]
>    其中days是用来算时间差的，只在乎相对值，单位为天。所有轨迹都相对一个时间点得到days.

#### 2. 危险程度打分(仅有POST方法)

URL: http://127.0.0.1:5000/analyze/

| Key | Value | 轨迹提取输入参数说明 |
| :- | :- | :- |
| landmarks_path	| string | 轨迹提取算法中，提取出的landmark文件位置
| dangerAeras	| list of dict	 | 危险区域坐标
| dangerPhi	| float	 | 危险区域距离阈值/km: 多近会被判断为有危险倾向
| activityAeras	| list of dict	 | 活动举办地坐标
| activityPhi	| float	 | 活动举办地距离阈值/km: 多近会被判断为有危险倾向

特别的, 如果没有提供landmarks_path, 但是提供了轨迹提取所需要的参数, 服务器会据此自动提取出重要位置. 如果已经提供了landmarks_path, 那么就算提供了提取所需要的参数也不会重新提取.

> 格式说明
> 1. landmarks文件为json文件, 内容为[{"lat":39.977998,"lng":116.326704},…]
> 2. dangerAeras, activityAeras为list of dict, 同上所示.

#### 3. 轨迹预测(POST和GET)

URL: http://127.0.0.1:5000/train/
借口说明: post方法, 训练LSTM模型; get方法, 获得预测结果.

| Key | Value | POST方法输入参数说明 |
| :- | :- | :- |
| user_path      | string | 用户轨迹文件地址                         |
| landmarks_path | string | 轨迹提取算法中，提取出的landmark文件位置 |
| input_n        | int    | 输入的轨迹点数                           |
| output_n       | int    | 预测的轨迹点数                           |

| Key | Value | POST方法输出参数说明 |
| :- | :- | :- |
|      |       | 无，返回msg字符串表示运算是否成功 |

| Key | Value | GET方法输入参数说明 |
| :- | :- | :- |
| data | list of list[ [lat,lon], …] | 输入的轨迹点，请保证数量跟训练时一样 |

| Key | Value | GET方法输出参数说明 |
| :- | :- | :- |
| results | list of list | 预测的轨迹点。之所以是list of list，是考虑到多输出的情况 |

> 备注：
> 1. 用户轨迹文件要求同上
> 2. 先用post训练，再get预测。一旦训练完成，就可以只用get预测了。这样可以解耦。
> 3. docker运行命令参照前面。
