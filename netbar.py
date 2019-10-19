#!/usr/bin/python3
import re
import socket
from subprocess import getstatusoutput


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
        # print(rt, total)
        return rt, total

    def extract_up_and_down_num(self, raw):
        # 先使用local ip 判断是那个网卡， 再取出 上传下载发包数据
        all_net = raw.split('\n\n')
        # print(len(all_net))

        # 找到内网ip对应的网卡数据
        aim_net = ''
        for net in all_net:
            if self.local_ip in net:
                aim_net = net
                break
        print(aim_net)

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
        return up_rt, up_total, down_rt, down_total

    def get_up_down_data(self):
        # 获取上传和下载的速度
        _, ifconfig = self._get_shell_result_('ifconfig')
        # print(_, ifconfig)
        self.extract_up_and_down_num(ifconfig)

    def get_tk_bar(self):
        return

    def run(self):
        self.get_up_down_data()
        pass


if __name__ == '__main__':
    nb = NetBar()
    # print(nb.get_local_ip())
    nb.run()
