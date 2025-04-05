<div align="center">
  <h1>Linux_MiniPC_Wifi_Manager</h1>
  <p>一个Linux下的WiFi自动管理脚本，为Raspberry Pi和其他小型Linux设备设计。可以在WiFi断连时自动重连或启动热点，确保SSH和VNC能正常连接，不用外接屏幕和键鼠排查故障。</p>
</div>

# 执行逻辑

```pseudocode
while(1)
{
    if(未连接到目标wifi)
    {
        if(扫描到目标wifi)
        {
            关闭热点，连接目标wifi
        }
        else
        {
            开启热点
        }
    }
    延时30秒
}
```

# 安装及启动

```shell
git clone https://github.com/Woooooooooood/Linux_MiniPC_Wifi_Manager.git
cd Linux_MiniPC_Wifi_Manager/
sudo python3 wifi_manager.py
```

# 配置WiFi、热点的名称和密码

更改main函数中的`target_ssid`、`target_password`、`hotspot_ssid`、`hotspot_password`字符串即可。

# 开机自启

使用systemd可以实现脚本开机自启，配置前请测试一遍确保脚本功能正常

1. 创建systemd服务文件

   ```shell
   sudo nano /etc/systemd/system/wifi_manager.service
   ```

2. 配置服务文件内容

   将以下内容天添加到服务文件中：

   ```shell
   [Unit]
   Description=WiFi Manager Service
   After=multi-user.target
   
   [Service]
   Type=simple
   User=root
   WorkingDirectory=/home/rpi/Linux_MiniPC_Wifi_Manager
   ExecStart=/usr/bin/python3 /home/rpi/Linux_MiniPC_Wifi_Manager/wifi_manager.py
   Restart=on-failure
   RestartSec=5s
   
   [Install]
   WantedBy=multi-user.target
   ```

   配置说明：

   - `After=multi-user.target` - 保证在系统完全启动后执行
   - 没有添加网络相关依赖，所以即使无网络也会启动
   - `Type=simple` - 最常见的服务类型，程序启动即视为服务启动
   - `User` - 指定运行程序的用户
   - `WorkingDirectory` - 脚本所在目录，记得替换自己的用户名
   - `ExecStart` - 执行命令，记得替换自己的用户名
   - `Restart=on-failure` - 失败时自动重启
   - `RestartSec` - 重启前等待时间

3. 启用服务

   保存文件后，执行以下命令启用服务：

   ```shell
   sudo systemctl daemon-reload
   sudo systemctl enable wifi_manager.service
   sudo systemctl start wifi_manager.service
   ```


# 停止运行

使用systemd启动的Python程序不会显示终端界面，因为它是作为后台服务运行的。

## 临时结束脚本运行

要临时停止通过systemd启动的脚本，可以使用以下命令：

```shell
sudo systemctl stop wifi_manager.service
```

## 禁用服务（下次启动不会自动运行）

```shell
sudo systemctl disable wifi_manager.service
```

