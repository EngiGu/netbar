#!/usr/bin/python3
import re
import socket
import time
from subprocess import getstatusoutput
import tkinter as tk


class NetBar:
    def __init__(self):
        self.local_ip = self.get_local_ip()
        pass

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
        return up, down, up_total2, down_total2

    def refresh_net_data(self, bar, label):
        up, down, up_total, down_total = self.get_up_down_data()
        text = ' '.join([up, down, up_total, down_total])
        print(text)
        label.config(text=text, width=len(text))
        # text_value_adj.set(text)

        def fresh():
            return self.refresh_net_data(bar, label)

        bar.after(1000, fresh)

    def get_tk_bar(self):
        bar = tk.Tk()
        bar.overrideredirect(True)  # 去掉标题栏
        bar.wm_attributes('-topmost', 1)  # 置顶窗口
        skins = [('GreenYellow', 'black'), ('#F5BB00', 'white'),
                 ('DeepSkyBlue', 'Ivory'), ('Violet', 'Ivory')]

        text_value_adj = tk.StringVar()  # 操作label值变化

        label = tk.Label(bar, text='   starting net bar...   ', )
        # label = tk.Label(bar, textvariable=text_value_adj)
        # text_value_adj.set('   starting net bar...   ')
        label.pack()
        time.sleep(2)
        bar.after(1000, self.refresh_net_data(bar, label))
        return bar

    def run(self):
        # self.get_up_down_data()
        bar = self.get_tk_bar()
        print(666666666)
        bar.mainloop()


# class Bar:
#     def __init__(self):
#         pass
#
#     def get_tk_bar(self):
#         bar = tk.Tk()
#         bar.overrideredirect(True)  # 去掉标题栏
#         bar.wm_attributes('-topmost', 1)  # 置顶窗口
#         skins = [('GreenYellow', 'black'), ('#F5BB00', 'white'),
#                  ('DeepSkyBlue', 'Ivory'), ('Violet', 'Ivory')]
#         l = tk.Label(bar, text='   starting net bar...   ', )
#         l.pack()
#
#         bar.mainloop()
#
#
#         return


if __name__ == '__main__':
    nb = NetBar()
    print(nb.get_local_ip())
    nb.run()
    # b = Bar()
    # b.get_tk_bar()
