# remote_desktop_server.py (服务端)
import socket
import pickle
import struct
import numpy as np
import cv2
import pyautogui
import threading
import time
import platform
import os
from mss import mss


class RemoteDesktopServer:
    def __init__(self, host='0.0.0.0', port=6000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []
        self.lock = threading.Lock()
        self.screen_width, self.screen_height = pyautogui.size()

        # 设置PyAutoGUI的安全保障
        pyautogui.FAILSAFE = False

    def start_server(self):
        """启动服务器并接受客户端连接"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"[*] 服务器启动成功，在 {self.host}:{self.port} 监听中...")

            # 启动屏幕广播线程
            broadcast_thread = threading.Thread(target=self.broadcast_screen)
            broadcast_thread.daemon = True
            broadcast_thread.start()

            # 接受客户端连接
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"[+] 接受来自 {address} 的连接")

                    # 发送屏幕信息
                    screen_info = {
                        'width': self.screen_width,
                        'height': self.screen_height
                    }
                    self.send_data(client_socket, pickle.dumps(screen_info))

                    # 创建线程处理客户端消息
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                    client_thread.daemon = True
                    client_thread.start()

                    # 添加客户端到列表
                    with self.lock:
                        self.clients.append(client_socket)

                except Exception as e:
                    if self.running:  # 只在服务器运行时显示错误
                        print(f"[!] 接受连接错误: {e}")
        except Exception as e:
            print(f"[!] 服务器启动错误: {e}")
        finally:
            self.stop()

    def stop(self):
        """停止服务器"""
        self.running = False

        # 关闭所有客户端连接
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()

        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        print("[*] 服务器已关闭")

    def handle_client(self, client_socket, address):
        """处理来自客户端的输入事件"""
        try:
            while self.running:
                # 接收客户端事件数据
                event_data = self.receive_data(client_socket)
                if not event_data:
                    break

                # 解析事件数据
                event = pickle.loads(event_data)

                # 处理不同类型的事件
                if event['type'] == 'mouse_move':
                    # 移动鼠标
                    x = int(event['x'])
                    y = int(event['y'])
                    try:
                        pyautogui.moveTo(x, y)
                    except Exception as e:
                        print(f"[!] 鼠标移动错误: {e}")

                elif event['type'] == 'mouse_click':
                    # 处理鼠标点击
                    x = int(event['x'])
                    y = int(event['y'])
                    button = event['button']

                    try:
                        # 先移动鼠标到目标位置
                        pyautogui.moveTo(x, y)

                        # 根据按钮类型执行点击
                        if button == 'left':
                            pyautogui.click(x, y, button='left')
                        elif button == 'right':
                            pyautogui.click(x, y, button='right')
                        elif button == 'middle':
                            pyautogui.click(x, y, button='middle')
                    except Exception as e:
                        print(f"[!] 鼠标点击错误: {e}")

                elif event['type'] == 'mouse_scroll':
                    # 处理鼠标滚轮
                    try:
                        # 滚动量
                        clicks = event['amount']
                        pyautogui.scroll(clicks * 100)  # 可以调整滚动的敏感度
                    except Exception as e:
                        print(f"[!] 鼠标滚轮错误: {e}")

                elif event['type'] == 'key_press':
                    # 处理键盘按下
                    try:
                        pyautogui.keyDown(event['key'])
                    except Exception as e:
                        print(f"[!] 键盘按下错误: {e}")

                elif event['type'] == 'key_up':
                    # 处理键盘释放
                    try:
                        pyautogui.keyUp(event['key'])
                    except Exception as e:
                        print(f"[!] 键盘释放错误: {e}")

        except Exception as e:
            print(f"[!] 客户端处理错误 {address}: {e}")
        finally:
            # 移除客户端
            with self.lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass
            print(f"[-] 客户端 {address} 断开连接")

    def broadcast_screen(self):
        """广播屏幕内容到所有连接的客户端"""
        # 设置压缩参数
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]  # 设置JPEG质量为70%，可调整以平衡质量和速度

        # 修复： 为每个线程创建一个单独的MSS实例
        sct = mss()

        # 根据平台确定屏幕监视器设置
        if platform.system() == 'Windows':
            monitor = {'top': 0, 'left': 0, 'width': self.screen_width, 'height': self.screen_height}
        else:
            monitor = sct.monitors[0]  # 尝试使用第一个监视器

        print(f"[*] 屏幕捕获设置: {monitor}")

        while self.running:
            try:
                # 捕获屏幕 - 使用pyautogui作为备选方案
                try:
                    screenshot = sct.grab(monitor)
                    img = np.array(screenshot)
                except Exception as e:
                    print(f"[!] MSS屏幕捕获失败，使用pyautogui备选方案: {e}")
                    # 备选方案：使用pyautogui
                    screenshot = pyautogui.screenshot()
                    img = np.array(screenshot)

                # 缩小图像以减少数据传输量
                scale_factor = 0.8  # 缩放比例，可以调整
                if scale_factor != 1.0:
                    new_width = int(img.shape[1] * scale_factor)
                    new_height = int(img.shape[0] * scale_factor)
                    img = cv2.resize(img, (new_width, new_height))

                # 编码图像为JPEG
                result, frame = cv2.imencode('.jpg', img, encode_param)
                data = frame.tobytes()

                # 广播到所有客户端
                with self.lock:
                    clients_copy = self.clients.copy()

                for client in clients_copy:
                    try:
                        self.send_data(client, data)
                    except Exception as e:
                        print(f"[!] 发送屏幕数据错误: {e}")
                        # 如果发送失败，下一次循环会处理

                # 控制帧率，避免过高的CPU使用率
                time.sleep(0.1)  # 降低到约10FPS，减轻网络和处理负担

            except Exception as e:
                print(f"[!] 屏幕广播错误: {e}")
                time.sleep(1)  # 错误后稍微延迟重试

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
        except Exception as e:
            print(f"[!] 接收数据错误: {e}")
            return None


# 如果直接运行此脚本，启动服务器
# if __name__ == "__main__":
server = RemoteDesktopServer()
def start_screen():
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n[*] 正在关闭服务器...")
        server.stop()
start_screen()