
import serial
import threading
import struct
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import io
import csv
import serial.tools.list_ports
import colormap

# 串口参数
BIN_SIZE = 32 * 32 * 2  # 2048 字节
BAUDRATE = 115200  # 固定波特率
CMAP_NAMES = ['经典', '涡流', '热力', '蓝紫', '黑红', '灰度', '反灰度']
CMAPS = [colormap.classicrgb, colormap.turborgb, colormap.hotrgb, 
         colormap.viridisrgb, colormap.infernorgb, colormap.greysrgb, colormap.greys_rrgb]

class ThermalBinLoader:
    def __init__(self, master):
        self.master = master
        self.master.title('热成像图像管理(最大100张)')
        self.file_list = []
        self.bin_data = {}  # {filename: 32x32 ndarray}
        self.current_image = None
        self.current_filename = None
        self.serial = None
        self.selected_port = tk.StringVar()
        self.selected_cmap = tk.StringVar(value='经典')
        self.setup_ui()
        self.refresh_ports()

    def setup_ui(self):
        # 串口设置框架
        self.serial_frame = ttk.LabelFrame(self.master, text='串口设置')
        self.serial_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 串口选择
        ttk.Label(self.serial_frame, text='串口:').pack(side=tk.LEFT, padx=5)
        self.port_cb = ttk.Combobox(self.serial_frame, textvariable=self.selected_port, width=15)
        self.port_cb.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        ttk.Button(self.serial_frame, text='刷新', command=self.refresh_ports).pack(
            side=tk.LEFT, padx=5)
        # 连接按钮
        ttk.Button(self.serial_frame, text='连接', command=self.connect_serial).pack(
            side=tk.LEFT, padx=5)

        # 主界面框架
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 文件列表
        self.listbox = tk.Listbox(self.main_frame, width=20)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        # 图像显示区域
        self.canvas = tk.Canvas(self.main_frame, width=240, height=240, bg='black')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 图像设置框架
        self.img_frame = ttk.LabelFrame(self.main_frame, text='图像设置')
        self.img_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        # 色表选择
        ttk.Label(self.img_frame, text='色表:').pack(padx=5, pady=5)
        self.cmap_cb = ttk.Combobox(self.img_frame, textvariable=self.selected_cmap,
                                   values=CMAP_NAMES, width=10)
        self.cmap_cb.pack(padx=5, pady=5)
        self.cmap_cb.bind('<<ComboboxSelected>>', self.update_colormap)

        # 按钮框架
        self.btn_frame = tk.Frame(self.master)
        self.btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(self.btn_frame, text='保存图片', command=self.save_image).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text='保存CSV', command=self.save_csv).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text='删除文件', command=self.delete_file).pack(
            side=tk.LEFT, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(self.master, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)

    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_cb['values'] = ports
        if ports and not self.selected_port.get():
            self.selected_port.set(ports[0])

    def connect_serial(self):
        """连接选中的串口"""
        if self.serial and self.serial.is_open:
            self.serial.close()
        
        try:
            port = self.selected_port.get()
            self.serial = serial.Serial(port, BAUDRATE, timeout=2)
            threading.Thread(target=self.scan_files, daemon=True).start()
        except Exception as e:
            messagebox.showerror('串口错误', str(e))

    def scan_files(self):
        """扫描串口中的文件"""
        try:
            self.progress['value'] = 0
            self.serial.write(b'ls\r\n')
            lines = self.serial.readlines()
            bin_files = []
            
            for line in lines:
                line = line.decode(errors='ignore')
                if 'File:' in line and line.strip().endswith('bytes'):  # 匹配格式 [FS] File: xxx.bin, Size: xxx bytes
                    try:
                        # 提取文件名部分
                        fname = line.split('File:')[1].split(',')[0].strip()
                        if fname.endswith('.bin'):
                            bin_files.append(fname)
                    except:
                        continue
            
            self.file_list = bin_files
            self.master.after(0, self.update_listbox)
            
            total_files = len(bin_files)
            for i, fname in enumerate(bin_files):
                self.progress['value'] = (i / total_files) * 100
                self.master.update_idletasks()
                
                self.serial.write(f'cat {fname}\r\n'.encode())
                prefix = self.serial.readline()
                print("prefix:", prefix.decode())
                data = self.serial.read(BIN_SIZE)
                print("size:", len(data))
                if len(data) == BIN_SIZE:
                    arr = struct.unpack('<1024H', data)
                    arr2d = [arr[i*32:(i+1)*32] for i in range(32)]
                    self.bin_data[fname] = arr2d
            
            self.progress['value'] = 100
            
        except Exception as e:
            messagebox.showerror('串口错误', str(e))

    def update_listbox(self):
        """更新文件列表"""
        self.listbox.delete(0, tk.END)
        for fname in self.file_list:
            self.listbox.insert(tk.END, fname)

    def on_select(self, event):
        """选择文件时的回调"""
        sel = self.listbox.curselection()
        if not sel:
            return
        fname = self.listbox.get(sel[0])
        self.current_filename = fname
        arr2d = self.bin_data.get(fname)
        if arr2d:
            img = self.array_to_image(arr2d)
            self.current_image = img
            self.show_image(img)

    def update_colormap(self, event=None):
        """更新色表"""
        if self.current_filename:
            arr2d = self.bin_data.get(self.current_filename)
            if arr2d:
                img = self.array_to_image(arr2d)
                self.current_image = img
                self.show_image(img)

    def array_to_image(self, arr2d):
        """将数组转换为图像"""
        # 找到最大最小值用于归一化
        min_val = min(min(row) for row in arr2d)
        max_val = max(max(row) for row in arr2d)
        range_val = max_val - min_val if max_val > min_val else 1
        
        # 创建原始灰度图像
        img = Image.new('L', (32, 32))
        pixels = []
        for row in arr2d:
            for val in row:
                # 归一化到0-180
                norm_val = int(((val - min_val) / range_val * 179))
                pixels.append(norm_val)
        img.putdata(pixels)
        
        # 双线性插值放大到240x240
        img = img.resize((320, 320), Image.BILINEAR)
        
        # 获取选中的色表
        cmap_idx = CMAP_NAMES.index(self.selected_cmap.get())
        cmap = CMAPS[cmap_idx]
        
        # 创建RGB图像并应用色表
        colored = Image.new('RGB', (320, 320))
        colored_pixels = []
        grey_pixels = list(img.getdata())
        
        for grey in grey_pixels:
            # print(grey)
            r = cmap[grey][0]
            g = cmap[grey][1]
            b = cmap[grey][2]
            colored_pixels.append((r, g, b))
        
        colored.putdata(colored_pixels)
        return colored

    def show_image(self, img):
        """显示图像"""
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete('all')
        # 居中显示图像
        self.canvas.create_image(120, 120, image=self.tk_img)

    def save_image(self):
        """保存图像为PNG"""
        if self.current_image:
            path = filedialog.asksaveasfilename(
                defaultextension='.png',
                filetypes=[('PNG图片', '*.png')],
                initialfile=self.current_filename.replace('.bin', '.png')
            )
            if path:
                self.current_image.save(path)
                messagebox.showinfo('保存成功', f'图像已保存至:\n{path}')

    def save_csv(self):
        """保存原始数据为CSV"""
        if self.current_filename:
            arr2d = self.bin_data.get(self.current_filename)
            if arr2d:
                path = filedialog.asksaveasfilename(
                    defaultextension='.csv',
                    filetypes=[('CSV文件', '*.csv')],
                    initialfile=self.current_filename.replace('.bin', '.csv')
                )
                if path:
                    with open(path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerows(arr2d)
                    messagebox.showinfo('保存成功', f'数据已保存至:\n{path}')
                    
    def delete_file(self):
        """删除当前选中的文件"""
        if not self.current_filename:
            messagebox.showwarning('警告', '请先选择要删除的文件')
            return
            
        if not self.serial or not self.serial.is_open:
            messagebox.showerror('错误', '串口未连接')
            return
            
        if messagebox.askyesno('确认删除', 
                             f'确定要删除文件 {self.current_filename} 吗？\n此操作不可恢复！'):
            try:
                # 发送删除命令
                self.serial.write(f'rm /{self.current_filename}\r\n'.encode())
                # 等待响应（可选）
                response = self.serial.readline()
                
                # 清除当前显示
                self.current_filename = None
                self.current_image = None
                self.canvas.delete('all')
                
                # 重新扫描文件列表
                threading.Thread(target=self.scan_files, daemon=True).start()
                
            except Exception as e:
                messagebox.showerror('删除失败', str(e))


def main():
    """程序入口函数"""
    # 创建主窗口
    root = tk.Tk()
    root.geometry('600x450')  # 设置默认窗口大小
    
    try:
        # 尝试设置窗口图标
        root.iconbitmap('thermal.ico')
    except:
        pass  # 如果图标文件不存在，忽略错误
    
    # 实例化主程序
    app = ThermalBinLoader(root)
    
    # 设置窗口关闭处理
    def on_closing():
        if app.serial and app.serial.is_open:
            app.serial.close()
        root.destroy()
    
    root.protocol('WM_DELETE_WINDOW', on_closing)
    
    # 启动主循环
    root.mainloop()


if __name__ == '__main__':
    main()
