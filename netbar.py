#!/usr/bin/python3
import os
import re
import socket
import time
from subprocess import getstatusoutput
import pickle

import tkinter as tk
import psutil

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


class NetBar:
    # 四种颜色的状态条
    # 两种模式 0: 上传下载以及总量 1: 上传下载以及c/m占用

    def __init__(self, refresh=1000, install=True):
        self.local_ip = self.get_local_ip()
        self.refresh_time = refresh  # 刷新时间间隔（ms）
        self.bar = None
        self.label = None
        self.x = 0
        self.y = 0
        self.skip_map = [('GreenYellow', 'black'), ('#F5BB00', 'white'), ('DeepSkyBlue', 'Ivory'), ('Violet', 'Ivory')]
        self.config_path = os.path.join(ROOT_PATH, 'netBar.pkl')
        self.config = self.obtain_config()  # {'mode': 0, 'skin': 0, 'x': 0, 'y': 0}
        self.install_app(install)

    def install_app(self, install):
        if install:
            name = 'NetBar'
            content = '''[Desktop Entry]
            Encoding=UTF-8
            Name={}
            Comment=NetStatus
            Exec=python3 {}
            Icon={}
            Categories=Application;
            Version={}
            Type=Application
            Terminal=false\n'''.format(
                name,
                os.path.abspath(__file__),
                os.path.join(ROOT_PATH, 'wm.png'),
                0.1
            )
            launcher_path = os.path.join(os.environ['HOME'], '.local/share/applications/%s.desktop' % name)
            with open(launcher_path, 'w') as f:
                f.write(content)

    def obtain_config(self):
        # 检查是否有配置文件
        if not os.path.exists(self.config_path):
            return {'mode': 0, 'skin': 0, 'x': 0, 'y': 0}
        with open(self.config_path, 'rb') as f:
            return pickle.load(f)

    def get_local_ip(self):
        # 获取本机的内网ip
        local_ip = ""
        try:
            socket_objs = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
            ip_from_ip_port = [(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in socket_objs][0][1]
            ip_from_host_name = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if
                                 not ip.startswith("127.")][:1]
            local_ip = [l for l in (ip_from_ip_port, ip_from_host_name) if l][0]
        except Exception as e:
            print("get_local_ip found exception : %s" % e)
        return local_ip if ("" != local_ip and None != local_ip) else socket.gethostbyname(socket.gethostname())

    def _get_shell_result_(self, cmd):
        return getstatusoutput(cmd)

    def format_net_data(self, data_tuple: tuple):
        rt, total = data_tuple  # 5755137,5.4 MiB
        total = ''.join([total.split(' ')[0], total.split(' ')[1][:1]])
        return int(rt), total

    def extract_up_and_down_num(self, raw):
        # 先使用local ip 判断是那个网卡， 再取出 上传下载发包数据
        t = time.time()
        all_net = raw.split('\n\n')
        # print(len(all_net))

        # 找到内网ip对应的网卡数据
        aim_net = ''
        for net in all_net:
            if self.local_ip in net:
                aim_net = net
                break

        # ubuntu RX bytes:80372113232 (80.3 GB)  TX bytes:40502434753 (40.5 GB)
        # deepin  RX packets 38333  bytes 34082486 (32.5 MiB)
        # deepin  TX packets 35947  bytes 5591979 (5.3 MiB)
        up_data = re.findall(r'TX.*?bytes.*?(\d+) \((.*?)\)', aim_net)
        down_data = re.findall(r'RX.*?bytes.*?(\d+) \((.*?)\)', aim_net)
        # up_data = re.findall(r'TX.*?bytes.*?(\d+)', aim_net, re.S)
        if not up_data or not down_data:
            raise Exception('获取网速数据错误')
        up_rt, up_total = self.format_net_data(up_data[0])
        down_rt, down_total = self.format_net_data(down_data[0])
        return up_rt, up_total, down_rt, down_total, t

    def humanize(self, flow):
        '''人性化显示流量单位'''
        n = 0
        while flow >= 1000:
            flow /= 1024
            n += 1
        if n == 2:
            return '{:.1f}'.format(flow) + 'MB'
        else:
            return '{:.0f}'.format(flow) + ('B', 'KB')[n]

    def get_up_down_data(self):
        # 获取上传和下载的速度
        _, ifconfig1 = self._get_shell_result_('ifconfig')
        # print(_, ifconfig)
        up_rt1, up_total1, down_rt1, down_total1, t1 = self.extract_up_and_down_num(ifconfig1)
        # print(up_rt, up_total, down_rt, down_total)
        time.sleep(0.5)
        _, ifconfig2 = self._get_shell_result_('ifconfig')
        up_rt2, up_total2, down_rt2, down_total2, t2 = self.extract_up_and_down_num(ifconfig2)
        down = (down_rt2 - down_rt1) / (t2 - t1)
        down = '↓ {}'.format(self.humanize(down))
        up = (up_rt2 - up_rt1) / (t2 - t1)
        up = '↑ {}'.format(self.humanize(up))
        # print(down, up)
        up_total2, down_total2 = 'U: %s' % up_total2, 'D: %s' % down_total2
        return up, down, up_total2, down_total2

    def get_cpu_and_memory(self):
        # 获取cpu/m
        c_percent = psutil.cpu_percent(interval=1)
        m_percent = psutil.virtual_memory().percent
        return 'C: %s%%' % c_percent, 'M: %s%%' % m_percent

    def refresh_net_data(self):
        up, down, up_total, down_total = self.get_up_down_data()
        if self.config['mode'] == 0:
            text = ' '.join([up, down, up_total, down_total])
        elif self.config['mode'] == 1:
            c_percent, m_percent = self.get_cpu_and_memory()
            text = ' '.join([up, down, c_percent, m_percent])
        else:
            raise Exception('mode error!')
        self.label.config(text=text, width=len(text))
        # text_value_adj.set(text)
        #
        # def fresh():
        #     return self.refresh_net_data(self.bar, self.label)
        self.bar.after(self.refresh_time, self.refresh_net_data)

    def get_tk_bar(self):
        config = self.config

        bar = tk.Tk()
        self.bar = bar
        bar.geometry('+{}+{}'.format(self.config['x'], self.config['y']))  # 窗口初始位置
        bar.overrideredirect(True)  # 去掉标题栏
        bar.wm_attributes('-topmost', 1)  # 置顶窗口

        # text_value_adj = tk.StringVar()  # 操作label值变化
        bg = self.skip_map[config['skin']][0]
        fg = self.skip_map[config['skin']][1]
        label = tk.Label(bar, text='   starting net bar...   ', bg=bg, fg=fg)
        # label = tk.Label(bar, textvariable=text_value_adj)
        # text_value_adj.set('   starting net bar...   ')
        label.pack()
        self.label = label
        # time.sleep(2)
        label.bind('<B1-Motion>', self.bar_move)
        label.bind('<Button-1>', self.bar_click)
        label.bind('<Double-Button-1>', self.bar_change_skin)
        label.bind('<Double-Button-3>', self.bar_exit)
        label.bind('<Button-3>', self.bar_change_mode)

        bar.after(self.refresh_time, self.refresh_net_data)
        return bar

    def bar_move(self, e):
        '''移动窗口'''
        if e.x_root < self.bar.winfo_screenwidth() - 10:
            new_x = e.x - self.x + self.bar.winfo_x()
            new_y = e.y - self.y + self.bar.winfo_y()
            if new_x < 10:
                new_x = 0
            if new_x > self.bar.winfo_screenwidth() - self.bar.winfo_width() - 10:
                new_x = self.bar.winfo_screenwidth() - 4
            if new_y < 10:
                new_y = 0
            if new_y > self.bar.winfo_screenheight() - self.bar.winfo_height() - 10:
                new_y = self.bar.winfo_screenheight() - self.bar.winfo_height()
            self.bar.geometry('+{}+{}'.format(new_x, new_y))
            self.config['x'], self.config['y'] = new_x, new_y

    def bar_click(self, e):
        # '''左键单击窗口时获得鼠标位置，辅助移动窗口'''
        self.x = e.x
        self.y = e.y

    def bar_change_skin(self, e):
        # 改变状态条的颜色
        curr_skin = self.config['skin']
        next_skin = 0 if len(self.skip_map) - 1 == curr_skin else curr_skin + 1
        # print('++++', next_skin)
        self.config['skin'] = next_skin
        bg = self.skip_map[next_skin][0]
        fg = self.skip_map[next_skin][1]
        self.label.config(bg=bg, fg=fg)

    def bar_change_mode(self, e):
        # 右键单击(暂时只有两种模式)
        self.config['mode'] = 1 if self.config['mode'] == 0 else 0

    def bar_exit(self, e):
        # 退出关闭bar
        self.config['x'] = self.bar.winfo_x()
        self.config['y'] = self.bar.winfo_y()
        with open(self.config_path, 'wb') as f:
            pickle.dump(self.config, f)
        exit()

    def run(self):
        try:
            bar = self.get_tk_bar()
            bar.mainloop()
        except KeyboardInterrupt:
            print('\nctrl+c, exit...')
            self.bar_exit('exit')
            exit()


if __name__ == '__main__':
    nb = NetBar()
    nb.run()
    # print(os.environ['HOME'])
