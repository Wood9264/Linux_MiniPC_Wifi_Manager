#!/usr/bin/env python3

import subprocess
import time
import re
import os

def run_command(command):
    """执行命令并返回输出"""
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout

def is_connected_to_wifi():
    """检查是否已连接到任何WiFi"""
    # 多种方法检测WiFi连接状态
    
    # 方法1: 检查nmcli设备状态
    output1 = run_command("nmcli -t -f DEVICE,STATE device | grep -i wifi")
    if "connected" in output1:
        return True
    
    # 方法2: 检查iwconfig输出
    output2 = run_command("iwconfig wlan0 2>/dev/null | grep -i 'essid'")
    if output2 and "ESSID:\"\"" not in output2 and "off/any" not in output2:
        return True
    
    # 方法3: 检查连接列表
    output3 = run_command("nmcli -t -f DEVICE,TYPE,STATE connection show --active")
    if "wifi:activated" in output3 or "802-11-wireless:activated" in output3:
        return True
    
    # 方法4: 检查IP地址
    output4 = run_command("ip addr show wlan0 2>/dev/null | grep 'inet '")
    if output4 and not output4.strip().startswith("10.42.0"):  # 排除热点IP (通常是10.42.0.x)
        return True
        
    return False

def is_hotspot_active():
    """检查是否已开启热点"""
    # 方法1: 检查活动连接
    output1 = run_command("nmcli -t -f NAME,DEVICE,TYPE connection show --active")
    if ("Hotspot" in output1 and "802-11-wireless" in output1) or ("raspberrypi" in output1 and "802-11-wireless" in output1):
        return True
    
    # 方法2: 检查AP模式
    output2 = run_command("iwconfig wlan0 2>/dev/null | grep -i 'mode'")
    if "Mode:Master" in output2:
        return True
    
    # 方法3: 检查热点IP地址 (通常是10.42.0.1)
    output3 = run_command("ip addr show wlan0 2>/dev/null | grep 'inet 10.42.0'")
    if output3:
        return True
        
    return False

def scan_for_wifi(target_ssid):
    """扫描并检查特定WiFi是否存在"""
    print(f"正在扫描WiFi网络: {target_ssid}...")
    
    output = run_command("sudo iwlist wlan0 scan 2>/dev/null")
    if f'ESSID:"{target_ssid}"' in output:
        print(f"✓ 成功找到目标WiFi: {target_ssid}")
        return True
    
    print(f"✗ 未找到目标WiFi: {target_ssid}")
    return False

def connect_to_wifi(ssid, password):
    """连接到指定WiFi"""
    print(f"正在连接到WiFi: {ssid}...")
    
    # 如果热点已开启，先停止
    if is_hotspot_active():
        stop_hotspot()
        time.sleep(3)
    
    # 检查连接状态
    current_ssid = get_current_ssid()
    if current_ssid == ssid:
        print(f"✓ 已经连接到目标WiFi: {ssid}，无需重新连接")
        return True
    
    # 检查是否已保存该连接
    if ssid in run_command("nmcli -t -f NAME connection show"):
        run_command(f"nmcli connection up '{ssid}'")
    else:
        run_command(f"nmcli device wifi connect '{ssid}' password '{password}'")
    
    # 验证连接
    time.sleep(5)
    if is_connected_to_wifi():
        current_ssid = get_current_ssid()
        print(f"✓ 已成功连接到WiFi: {current_ssid}")
        return True
    else:
        print(f"✗ 连接到WiFi失败: {ssid}")
        return False

def create_hotspot(ssid, password):
    """创建WiFi热点"""
    print(f"正在创建热点: {ssid}...")
    
    # 检查是否已有该热点配置
    if ssid in run_command("nmcli -t -f NAME connection show"):
        run_command(f"nmcli connection up '{ssid}'")
    else:
        # 创建新的热点
        run_command(f"nmcli device wifi hotspot ssid '{ssid}' password '{password}'")
    
    time.sleep(5)
    if is_hotspot_active():
        print(f"✓ 热点已成功创建: {ssid}")
        return True
    else:
        print(f"✗ 创建热点失败: {ssid}")
        return False

def stop_hotspot():
    """停止热点"""
    if is_hotspot_active():
        print("正在停止热点...")
        # 获取热点连接名称
        output = run_command("nmcli -t -f NAME,DEVICE,TYPE connection show --active")
        lines = output.strip().split('\n')
        for line in lines:
            if "802-11-wireless" in line and ("Hotspot" in line or "raspberrypi" in line):
                hotspot_conn = line.split(':')[0]
                run_command(f"nmcli connection down '{hotspot_conn}'")
                print(f"✓ 已停止热点: {hotspot_conn}")
                time.sleep(2)  # 给一些时间让网卡释放
                return True
    return False

def get_current_ssid():
    """获取当前连接的WiFi SSID"""
    try:
        # 方法1: 尝试使用nmcli获取
        output1 = run_command("nmcli -t -f ACTIVE,SSID device wifi list | grep yes")
        if output1:
            return output1.split(':')[1].strip()
    except:
        pass
    
    try:
        # 方法2: 使用iwconfig
        output2 = run_command("iwconfig wlan0 2>/dev/null | grep ESSID")
        match = re.search(r'ESSID:"([^"]*)"', output2)
        if match and match.group(1):
            return match.group(1)
    except:
        pass
    
    try:
        # 方法3: 尝试从NetworkManager连接中获取
        output3 = run_command("nmcli -t -f NAME,TYPE connection show --active | grep wireless")
        if output3:
            return output3.split(':')[0]
    except:
        pass
    
    return "未知网络"

def main():
    """主程序循环"""
    target_ssid = "miaomiaomiao"     # 目标WiFi名称
    target_password = "233233233"    # 目标WiFi密码
    
    hotspot_ssid = "raspberrypi"     # 热点名称
    hotspot_password = "233233233"   # 热点密码
    
    print("===== WiFi管理程序已启动 =====")
    print(f"目标WiFi: {target_ssid}")
    print(f"热点名称: {hotspot_ssid}")
    
    while True:
        try:
            print("\n" + "="*50)
            print("开始检查WiFi状态")
            print("="*50)
            
            # 检查当前连接状态和热点状态
            current_ssid = get_current_ssid() if is_connected_to_wifi() else "未连接"
            hotspot_status = is_hotspot_active()
            
            print(f"当前WiFi状态: {current_ssid}")
            print(f"热点状态: {'已开启 - ' + hotspot_ssid if hotspot_status else '未开启'}")
            
            # 判断是否连接到目标WiFi
            if current_ssid != target_ssid:
                print(f"[操作] 当前未连接到目标WiFi: {target_ssid}")
                
                # 扫描目标WiFi是否可用
                target_wifi_available = scan_for_wifi(target_ssid)
                
                if target_wifi_available:
                    # 如果目标WiFi可用，关闭热点并连接
                    print(f"[操作] 找到目标WiFi，准备连接: {target_ssid}")
                    
                    # 如果当前连接到其他WiFi，断开
                    if current_ssid != "未连接" and current_ssid != "未知网络":
                        print(f"[操作] 断开当前WiFi: {current_ssid}")
                        run_command(f"nmcli connection down '{current_ssid}'")
                    
                    # 连接到目标WiFi
                    connect_to_wifi(target_ssid, target_password)
                else:
                    # 如果目标WiFi不可用，开启热点
                    print(f"[操作] 未找到目标WiFi，检查热点状态")
                    
                    if not hotspot_status:
                        print(f"[操作] 热点未开启，准备创建热点: {hotspot_ssid}")
                        create_hotspot(hotspot_ssid, hotspot_password)
                    else:
                        print(f"[操作] 热点已开启: {hotspot_ssid}，保持现状")
            else:
                print(f"[状态] 已连接到目标WiFi: {target_ssid}，保持连接")
            
            print("\n[等待] 30秒后继续检查...")
            time.sleep(30)
        except Exception as e:
            print(f"[错误] 发生异常: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(10)

if __name__ == "__main__":
    # 检查是否有root权限
    if os.geteuid() != 0:
        print("此程序需要root权限运行")
        print("请使用 'sudo python3 wifi_manager.py' 运行此程序")
        exit(1)
    
    main()