import subprocess
import time
import socket
import os
import platform


def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def test_appium_installation():
    """测试Appium是否可以正常启动"""
    try:
        result = subprocess.run(
            "appium --version",
            shell=True,
            capture_output=True,
            text=True
        )
        print(f"Appium版本: {result.stdout.strip()}")

        if is_port_in_use(4723):
            print("端口4723已被占用，可能已有Appium在运行。")
            return False

        test_process = subprocess.Popen(
            "appium",
            shell=True,
            stdout=subprocess.PIPE
        )
        time.sleep(5)
        test_process.terminate()

        return True
    except Exception as e:
        print(f"测试Appium安装时出错: {str(e)}")
        return False




def free_port(port):
    system = platform.system()

    try:

        result = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True, text=True)
        lines = result.strip().splitlines()
        pids = set()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                pid = parts[-1]
                pids.add(pid)

        for pid in pids:
            subprocess.run(f'taskkill /F /PID {pid}', shell=True)
            print(f"已终止 PID: {pid} 占用的端口 {port}")

    except subprocess.CalledProcessError:
        print(f"端口 {port} 没有被占用。")


# test_appium_installation()
# 示例：关闭占用 4723 端口的进程
free_port(4723)

def check_4723():
    port = 4723
    cmd = f'netstat -ano | findstr :{port}'
    result = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.stdout:
        lines = result.stdout.strip().splitlines()
        print("找到端口信息：", lines)
    else:
        print(f"未发现端口 {port} 的占用情况。")

check_4723()