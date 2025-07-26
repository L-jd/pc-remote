# remote_desktop_client.py (客户端)
import socket
import pickle
import struct
import numpy as np
import cv2
import threading
import time
import tkinter as tk
from PIL import Image, ImageTk
import sys


class RemoteDesktopClient:
    def __init__(self, server_host='192.168.1.100', server_port=6000):
        # 设置默认的服务器IP为192.168.1.100，请替换为你的实际服务器IP
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.running = False
        self.screen_width = 0
        self.screen_height = 0
        self.scale_factor = 1.0

        print(f"[*] 准备连接到服务器: {self.server_host}:{self.server_port}")

        # 用于屏幕更新的线程
        self.screen_thread = None

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title(f"远程桌面客户端 - 连接到 {server_host}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 创建显示远程屏幕的画布
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 绑定鼠标和键盘事件
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", lambda e: self.on_mouse_click(e, "left"))
        self.canvas.bind("<Button-2>", lambda e: self.on_mouse_click(e, "middle"))
        self.canvas.bind("<Button-3>", lambda e: self.on_mouse_click(e, "right"))
        self.canvas.bind("<MouseWheel>", self.on_mouse_scroll)
        self.root.bind("<Key>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)

        # 状态标签
        self.status_label = tk.Label(self.root, text="正在连接...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # 当前图像
        self.current_image = None

    def start(self):
        """启动客户端并连接到服务器"""
        # 创建连接线程
        connect_thread = threading.Thread(target=self.connect_to_server)
        connect_thread.daemon = True
        connect_thread.start()

        # 启动主循环
        self.root.mainloop()

    def connect_to_server(self):
        """连接到远程桌面服务器"""
        try:
            print(f"[*] 正在连接到服务器 {self.server_host}:{self.server_port}...")
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(30)  # 增加连接超时时间
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"[+] 已连接到服务器")

            print("[*] 正在等待接收屏幕信息...")
            # 接收屏幕信息
            screen_info_data = self.receive_data(self.client_socket)
            if screen_info_data:
                screen_info = pickle.loads(screen_info_data)
                self.screen_width = screen_info['width']
                self.screen_height = screen_info['height']

                print(f"[+] 接收到屏幕信息: {self.screen_width}x{self.screen_height}")

                # 调整窗口大小
                # 根据本地屏幕和远程屏幕比例调整适当的显示大小
                self.update_status(f"已连接到 {self.server_host} - 屏幕大小: {self.screen_width}x{self.screen_height}")

                # 设置初始窗口大小
                self.root.geometry(f"{min(self.screen_width, 1200)}x{min(self.screen_height, 800)}")

                # 启动屏幕接收线程
                self.running = True
                self.screen_thread = threading.Thread(target=self.receive_screen)
                self.screen_thread.daemon = True
                self.screen_thread.start()
            else:
                print("[!] 无法获取远程屏幕信息")
                self.update_status("无法获取远程屏幕信息")

        except socket.timeout:
            print(f"[!] 连接超时: 无法连接到 {self.server_host}:{self.server_port}")
            self.update_status(f"连接超时: 请检查服务器是否运行")
        except ConnectionRefusedError:
            print(f"[!] 连接被拒绝: 服务器 {self.server_host}:{self.server_port} 未运行或端口错误")
            self.update_status(f"连接被拒绝: 请检查服务器是否运行")
        except Exception as e:
            print(f"[!] 连接失败: {e}")
            self.update_status(f"连接失败: {e}")

    def receive_screen(self):
        """持续接收远程屏幕内容"""
        try:
            print("[*] 开始接收屏幕数据...")
            while self.running:
                # 接收屏幕数据
                screen_data = self.receive_data(self.client_socket)
                if not screen_data:
                    if self.running:  # 只在仍在运行时显示错误
                        print("[!] 接收到空数据，连接可能已断开")
                        self.update_status("连接已断开")
                    break

                # 解码图像
                img_array = np.frombuffer(screen_data, dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                # OpenCV使用BGR，转换为RGB用于Tkinter
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 更新GUI中的图像
                self.update_screen(frame)

        except Exception as e:
            if self.running:  # 只在仍在运行时显示错误
                print(f"[!] 接收屏幕错误: {e}")
                self.update_status(f"接收屏幕错误: {e}")
        finally:
            self.close_connection()

    def update_screen(self, frame):
        """更新画布上的图像"""
        try:
            # 获取画布的当前大小
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # 如果画布尚未调整大小，使用默认值
            if canvas_width <= 1:
                canvas_width = min(self.screen_width, 1200)
            if canvas_height <= 1:
                canvas_height = min(self.screen_height, 800)

            # 调整图像大小以适应画布
            frame_height, frame_width = frame.shape[:2]

            # 计算缩放比例
            scale_w = canvas_width / frame_width
            scale_h = canvas_height / frame_height
            scale = min(scale_w, scale_h)

            if scale < 1:
                # 缩小图像
                new_width = int(frame_width * scale)
                new_height = int(frame_height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
                self.scale_factor = scale
            else:
                self.scale_factor = 1.0

            # 转换为Tkinter图像
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image=image)

            # 更新画布
            self.canvas.config(width=image.width, height=image.height)

            # 保持对图像的引用，防止被垃圾回收
            self.current_image = photo

            # 清除画布并创建新图像
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)

        except Exception as e:
            print(f"[!] 更新屏幕错误: {e}")

    def update_status(self, message):
        """更新状态栏信息"""
        # 使用tkinter的after方法安全地更新UI
        self.root.after(0, lambda: self.status_label.config(text=message))

    def on_mouse_move(self, event):
        """处理鼠标移动事件"""
        if not self.running:
            return

        # 计算在远程屏幕上的实际坐标
        x = int(event.x / self.scale_factor)
        y = int(event.y / self.scale_factor)

        # 发送鼠标移动事件
        event_data = {
            'type': 'mouse_move',
            'x': x,
            'y': y
        }
        self.send_event(event_data)

    def on_mouse_click(self, event, button):
        """处理鼠标点击事件"""
        if not self.running:
            return

        # 计算在远程屏幕上的实际坐标
        x = int(event.x / self.scale_factor)
        y = int(event.y / self.scale_factor)

        # 发送鼠标点击事件
        event_data = {
            'type': 'mouse_click',
            'button': button,
            'x': x,
            'y': y
        }
        self.send_event(event_data)

    def on_mouse_scroll(self, event):
        """处理鼠标滚轮事件"""
        if not self.running:
            return

        # 在Windows上，event.delta是滚动量
        # 正数表示向上滚动，负数表示向下滚动
        delta = event.delta

        # 发送鼠标滚轮事件
        event_data = {
            'type': 'mouse_scroll',
            'amount': delta / 120  # 将Windows的delta值转换为合理的滚动单位
        }
        self.send_event(event_data)

    def on_key_press(self, event):
        """处理键盘按下事件"""
        if not self.running:
            return

        # 获取键名
        key = event.keysym

        # 发送键盘按下事件
        event_data = {
            'type': 'key_press',
            'key': key
        }
        self.send_event(event_data)

    def on_key_release(self, event):
        """处理键盘释放事件"""
        if not self.running:
            return

        # 获取键名
        key = event.keysym

        # 发送键盘释放事件
        event_data = {
            'type': 'key_up',
            'key': key
        }
        self.send_event(event_data)

    def send_event(self, event_data):
        """发送事件到服务器"""
        try:
            if self.client_socket:
                # 序列化事件数据
                data = pickle.dumps(event_data)
                self.send_data(self.client_socket, data)
        except Exception as e:
            print(f"[!] 发送事件错误: {e}")
            self.close_connection()

    def send_data(self, sock, data):
        """发送带有长度前缀的数据"""
        try:
            # 打包数据长度为网络字节序
            length = len(data)
            length_bytes = struct.pack('!I', length)
            # 发送长度
            sock.sendall(length_bytes)
            # 发送数据
            sock.sendall(data)
        except Exception as e:
            raise Exception(f"发送数据错误: {e}")

    def receive_data(self, sock):
        """接收带有长度前缀的数据"""
        try:
            # 接收4字节的长度前缀
            length_bytes = sock.recv(4)
            if not length_bytes or len(length_bytes) < 4:
                return None

            # 解包为整数
            length = struct.unpack('!I', length_bytes)[0]

            # 接收实际数据
            data = b''
            remaining = length
            while remaining > 0:
                chunk = sock.recv(min(remaining, 4096))
                if not chunk:
                    break
                data += chunk
                remaining -= len(chunk)

            if len(data) < length:
                print(f"[!] 警告: 接收到的数据不完整，预期 {length} 字节，实际接收 {len(data)} 字节")

            return data
        except socket.timeout:
            print(f"[!] 接收数据超时")
            return None
        except Exception as e:
            if self.running:  # 只在仍在运行时显示错误
                print(f"[!] 接收数据错误: {e}")
            return None

    def close_connection(self):
        """关闭与服务器的连接"""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            print("[*] 已关闭与服务器的连接")
        self.update_status("连接已关闭")

    def on_closing(self):
        """窗口关闭时的处理函数"""
        print("[*] 关闭客户端...")
        self.close_connection()
        self.root.destroy()
        sys.exit(0)


# 如果直接运行此脚本，启动客户端
#if __name__ == "__main__":
    # 默认使用硬编码的服务器IP，你也可以通过命令行参数覆盖
server_host = '127.0.0.1' # 在这里设置你的服务器IP地址

if len(sys.argv) > 1:
    server_host = sys.argv[1]

print(f"[*] 客户端启动，将连接到服务器: {server_host}")
#def desk():
client = RemoteDesktopClient(server_host=server_host)
client.start()