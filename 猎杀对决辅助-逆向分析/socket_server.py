import socket
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime

DEFAULT_PORT = 8896

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP 服务器 (图形版)")
        self.root.geometry("850x700")

        self.running = False
        self.server_socket = None
        self.clients = []
        self.clients_lock = threading.Lock()
        self.history = []          # (addr_str, data, timestamp)
        self.msg_queue = queue.Queue()

        # ---------- 顶部 ----------
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(top_frame, text="监听端口:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        self.port_entry = tk.Entry(top_frame, textvariable=self.port_var, width=8)
        self.port_entry.pack(side=tk.LEFT, padx=5)

        self.start_btn = tk.Button(top_frame, text="启动", command=self.toggle_server)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = tk.Button(top_frame, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # ---------- 接收区域 ----------
        recv_frame = tk.LabelFrame(root, text="接收数据", padx=5, pady=5)
        recv_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        recv_enc_frame = tk.Frame(recv_frame)
        recv_enc_frame.pack(fill=tk.X, pady=2)
        tk.Label(recv_enc_frame, text="显示编码:").pack(side=tk.LEFT)
        self.recv_encoding = tk.StringVar(value="utf-8")
        enc_options = ["utf-8", "utf-16", "utf-16-be", "utf-16-le", "gbk", "gb18030", "gb2312", "big5", "ascii"]
        self.recv_enc_menu = ttk.Combobox(recv_enc_frame, textvariable=self.recv_encoding,
                                          values=enc_options, state="readonly", width=12)
        self.recv_enc_menu.pack(side=tk.LEFT, padx=5)
        self.recv_enc_menu.bind("<<ComboboxSelected>>", self.on_encoding_changed)

        self.log_text = scrolledtext.ScrolledText(recv_frame, wrap=tk.WORD, state="normal")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state="disabled")

        # ---------- 发送区域 ----------
        send_frame = tk.LabelFrame(root, text="发送数据", padx=5, pady=5)
        send_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 标签行
        label_row = tk.Frame(send_frame)
        label_row.pack(fill=tk.X, pady=2)
        tk.Label(label_row, text="发送内容:").pack(side=tk.LEFT)

        # 多行输入框（带滚动条）
        text_frame = tk.Frame(send_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self.send_text = scrolledtext.ScrolledText(text_frame, height=4, wrap=tk.WORD)
        self.send_text.pack(fill=tk.BOTH, expand=True)

        send_row2 = tk.Frame(send_frame)
        send_row2.pack(fill=tk.X, pady=2)
        tk.Label(send_row2, text="编码:").pack(side=tk.LEFT)
        self.send_encoding = tk.StringVar(value="utf-8")
        self.send_enc_menu = ttk.Combobox(send_row2, textvariable=self.send_encoding,
                                          values=enc_options, state="readonly", width=12)
        self.send_enc_menu.pack(side=tk.LEFT, padx=5)

        self.hex_send_var = tk.BooleanVar(value=False)
        self.hex_check = tk.Checkbutton(send_row2, text="Hex发送", variable=self.hex_send_var)
        self.hex_check.pack(side=tk.LEFT, padx=5)

        self.send_btn = tk.Button(send_row2, text="发送 (广播)", command=self.send_data)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.root.after(100, self.process_queue)

    # ---------- 编码切换 ----------
    def on_encoding_changed(self, event=None):
        self.refresh_display()

    def refresh_display(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        for addr_str, data, timestamp in self.history:
            display_text = self._format_received(addr_str, data, timestamp)
            self.append_log(display_text)

    def _format_received(self, addr_str, data, timestamp):
        enc = self.recv_encoding.get()
        lines = []
        lines.append(f"[{timestamp}] 来自 {addr_str}  {len(data)} 字节")
        lines.append(f"  Hex: {data.hex()}")
        try:
            text = data.decode(enc, errors="replace")
            lines.append(f"  Decoded ({enc}): {text}")
        except Exception as e:
            lines.append(f"  Decoded ({enc}) 解码失败: {e}")
        return "\n".join(lines)

    # ---------- 按钮回调 ----------
    def toggle_server(self):
        if not self.running:
            port_str = self.port_var.get().strip()
            if not port_str.isdigit():
                self.append_log("错误: 端口必须为数字")
                return
            port = int(port_str)
            if port < 1 or port > 65535:
                self.append_log("错误: 端口范围 1-65535")
                return
            self.start_server(port)
        else:
            self.stop_server()

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        self.history.clear()

    def send_data(self):
        if not self.running:
            self.append_log("服务器未启动，无法发送")
            return
        raw_input = self.send_text.get("1.0", tk.END).strip()
        if not raw_input:
            self.append_log("发送内容为空")
            return

        if self.hex_send_var.get():
            hex_str = raw_input.replace(" ", "")
            try:
                data = bytes.fromhex(hex_str)
            except ValueError:
                self.append_log("Hex解析失败，请检查输入是否合法（仅十六进制字符）")
                return
            enc_info = "hex"
        else:
            enc = self.send_encoding.get()
            try:
                data = raw_input.encode(enc)
            except Exception as e:
                self.append_log(f"编码失败: {e}")
                return
            enc_info = enc

        with self.clients_lock:
            if not self.clients:
                self.append_log("没有客户端连接")
                return
            for conn in self.clients[:]:
                try:
                    conn.sendall(data)
                except Exception as e:
                    self.append_log(f"发送给客户端失败: {e}")
        self.append_log(f"已广播 {len(data)} 字节 (编码: {enc_info})")

    # ---------- 服务器核心 ----------
    def start_server(self, port):
        self.running = True
        self.start_btn.config(text="停止", bg="red", fg="white")
        self.port_entry.config(state="disabled")

        self.server_thread = threading.Thread(target=self.accept_clients, args=(port,), daemon=True)
        self.server_thread.start()
        self.append_log(f"服务器启动，监听端口 {port}")

    def stop_server(self):
        self.running = False
        self.start_btn.config(text="启动", bg="SystemButtonFace", fg="black")
        self.port_entry.config(state="normal")

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

        with self.clients_lock:
            for conn in self.clients:
                try:
                    conn.close()
                except:
                    pass
            self.clients.clear()

        self.append_log("服务器已停止")

    def accept_clients(self, port):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)

            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.append_log(f"接受连接出错: {e}")
                    break

                with self.clients_lock:
                    self.clients.append(conn)
                addr_str = f"{addr[0]}:{addr[1]}"
                self.msg_queue.put(("log", f"✅ 客户端 {addr_str} 已连接 (当前连接数: {len(self.clients)})"))
                t = threading.Thread(target=self.handle_client, args=(conn, addr_str), daemon=True)
                t.start()

        except Exception as e:
            self.append_log(f"服务器异常: {e}")
        finally:
            if self.running:
                self.root.after(0, self.stop_server)

    def handle_client(self, conn, addr_str):
        try:
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.msg_queue.put(("recv", addr_str, data, timestamp))
        except ConnectionResetError:
            pass
        except ConnectionAbortedError:
            pass
        except Exception as e:
            if self.running:
                self.msg_queue.put(("log", f"客户端 {addr_str} 异常: {e}"))
        finally:
            conn.close()
            with self.clients_lock:
                if conn in self.clients:
                    self.clients.remove(conn)
            self.msg_queue.put(("log", f"❌ 客户端 {addr_str} 已断开 (剩余连接数: {len(self.clients)})"))

    # ---------- 队列处理 ----------
    def process_queue(self):
        try:
            while True:
                item = self.msg_queue.get_nowait()
                if item[0] == "recv":
                    _, addr_str, data, timestamp = item
                    self.display_received(addr_str, data, timestamp)
                elif item[0] == "log":
                    _, msg = item
                    self.append_log(msg)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def display_received(self, addr_str, data, timestamp):
        display_text = self._format_received(addr_str, data, timestamp)
        self.history.append((addr_str, data, timestamp))
        self.append_log(display_text)

    def append_log(self, text):
        """统一添加日志，无颜色"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()