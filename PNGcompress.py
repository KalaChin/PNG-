import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Spinbox
from PIL import Image
from threading import Thread, Lock

# 图片压缩函数，接收压缩质量作为参数
def compress_image(input_path, output_path, quality=85):
    try:
        with Image.open(input_path) as img:
            img.save(output_path, "PNG", optimize=True, quality=quality)
        return True
    except FileNotFoundError:
        print(f"文件未找到：{input_path}")
        return False
    except OSError as e:
        print(f"图像文件可能被截断或损坏：{input_path}, 错误信息：{e}")
        return False

# 图形界面类
class CompressApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("图片压缩工具")
        self.geometry("700x500")
        # 初始化变量
        self.input_files = []  # 存放待压缩图片的路径
        self.output_dir = ""  # 存放压缩后图片的目录
        self.thread_count = tk.IntVar(value=1)  # 用于选择的线程数
        self.output_dir = ""  # 初始化输出目录变量

        # UI初始化方法
        self.init_ui()

    def init_ui(self):
        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=10)
        # 选择输入文件按钮
        self.btn_select_files = ttk.Button(buttons_frame, text="选择文件", command=self.select_input_files)
        self.btn_select_files.pack(side=tk.LEFT,padx=10,pady=10)

        # 选择输出文件夹按钮
        self.btn_output_folder = ttk.Button(buttons_frame, text="输出路径", command=self.select_output_folder)
        self.btn_output_folder.pack(side=tk.LEFT,padx=10,pady=10)
        
        # 创建并排的两个按钮
        self.btn_start_compression = ttk.Button(buttons_frame, text="开始压缩",command=self.start_compression)
        self.btn_start_compression.pack(side=tk.LEFT, padx=10,pady=10)

        self.btn_open_output_path = ttk.Button(buttons_frame, text="打开输出路径",command=self.open_output_folder)
        self.btn_open_output_path.pack(side=tk.LEFT, padx=10,pady=10)
        # 压缩质量选项
        self.quality_label = ttk.Label(self, text="压缩质量(1-100):")
        self.quality_label.pack(pady=10)
        self.quality_var = tk.IntVar(value=85)  # 默认压缩质量为85
        self.quality_entry = ttk.Entry(self, textvariable=self.quality_var)
        self.quality_entry.pack(pady=10)

        # 多线程压缩选项
        self.thread_count_label = tk.Label(self, text="选择线程数(1-10): ")
        self.thread_count_label.pack()
        self.thread_count_spinbox = Spinbox(self, from_=1, to=10, textvariable=self.thread_count)
        self.thread_count_spinbox.pack() 
        # 创建文件列表框和进度显示的框架
        self.file_list_frame = tk.Frame(self)
        self.file_list_frame.pack(pady=10, fill=tk.BOTH, expand=True)       
        # 创建一个滚动条
        scrollbar = tk.Scrollbar(self.file_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建序号列表框
        self.index_listbox = tk.Listbox(self.file_list_frame, width=5, yscrollcommand=scrollbar.set)
        self.index_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建文件列表框
        self.file_listbox = tk.Listbox(self.file_list_frame, width=50, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建进度列表框
        self.progress_listbox = tk.Listbox(self.file_list_frame, width=20, yscrollcommand=scrollbar.set)
        self.progress_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 设置滚动条命令来同步三个列表的滚动
        scrollbar.config(command=self.on_scrollbar)

        # 绑定鼠标滚轮事件以同步滚动
        self.index_listbox.bind("<MouseWheel>", lambda event: self.on_mousewheel(event, self.file_listbox, self.progress_listbox))
        self.file_listbox.bind("<MouseWheel>", lambda event: self.on_mousewheel(event, self.index_listbox, self.progress_listbox))
        self.progress_listbox.bind("<MouseWheel>", lambda event: self.on_mousewheel(event, self.index_listbox, self.file_listbox))

    def on_scrollbar(self, *args):
        # 更新三个列表框的滚动位置
        self.index_listbox.yview(*args)
        self.file_listbox.yview(*args)
        self.progress_listbox.yview(*args)

    def on_mousewheel(self, event, *others):
        # 同步鼠标滚轮滚动
        for other in others:
            other.yview_scroll(int(-1*(event.delta/120)), "units")


    def select_input_files(self):
        # 使用filedialog询问打开多个文件，返回文件路径的元组
        files = filedialog.askopenfilenames(title="选择图片", filetypes=[("PNG images", "*.png"), ("JPEG images", "*.jpg"), ("All files", "*.*")])
        if files:  # 如果用户选择了文件
            self.input_files = list(files)  # 更新类变量存储文件路径
            self.update_file_list()  # 更新GUI中的文件列表显示
    def update_file_list(self):
        self.index_listbox.delete(0, tk.END)
        self.file_listbox.delete(0, tk.END)
        self.progress_listbox.delete(0, tk.END)
        for i, file in enumerate(self.input_files, 1):  # Start counting from 1
            self.index_listbox.insert(tk.END, i)
            self.file_listbox.insert(tk.END, file)
            self.progress_listbox.insert(tk.END, "待压缩")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_dir = folder  
    def start_compression(self):
        # 获取质量
        quality = self.quality_var.get()

        # 如果用户没有选择文件或输出目录，则给出提示
        if not self.input_files or not self.output_dir:
            messagebox.showwarning("警告", "请选择输入文件和输出目录。")
            return
        if not (1 <= quality <= 100):
            messagebox.showwarning("警告", "压缩质量必须在1到100之间。")
            return
        if (self.thread_count.get() > 10):
            messagebox.showwarning("警告", "线程数过高,请确保CPU占用率不超过80%。\n 点击确定强行开始，关闭提示框取消。")
            return
        # 初始化计数器和锁
        self.completed_count = 0
        self.lock = Lock()

        # 计算每个线程需要处理的文件数量
        files_per_thread = max(1, len(self.input_files) // self.thread_count.get())
        remaining_files = len(self.input_files)

        # 创建并启动线程
        for i in range(self.thread_count.get()):
            start_index = i * files_per_thread
            end_index = start_index + min(files_per_thread, remaining_files)
            file_chunk = self.input_files[start_index:end_index]
            remaining_files -= len(file_chunk)
            thread = Thread(target=self.compress_task, args=(file_chunk, quality, start_index))
            thread.start()

    def compress_task(self, file_chunk, quality, start_index):
        for offset, file_path in enumerate(file_chunk):
            index = start_index + offset
            self.update_status(index, "压缩中")  # 更新状态
            output_path = os.path.join(self.output_dir, os.path.basename(file_path))
            result = compress_image(file_path, output_path, quality)
            status = "压缩完成" if result else "失败"
            self.update_status(index, status)  # 更新状态
            with self.lock:
                self.completed_count += 1
                if self.completed_count == len(self.input_files):
                    self.after(0, lambda: messagebox.showinfo("完成", "所有文件压缩完成！"))
    def update_status(self, index, status):
        def _update():
            self.progress_listbox.delete(index)
            self.progress_listbox.insert(index, status)
        self.after(0, _update)
    def open_output_folder(self):
        # 检查输出目录路径是否已设置
        if not self.output_dir:
            messagebox.showerror("错误", "输出路径未设置！")
            return
        # 打开输出路径的文件夹
        if os.path.exists(self.output_dir):
            if os.name == 'nt':  # 如果是Windows系统
                os.startfile(self.output_dir)
        else:
            messagebox.showerror("错误", "输出路径不存在！")

# 应用程序的入口点
if __name__ == "__main__":
    app = CompressApp()
    app.mainloop()
