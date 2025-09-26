import subprocess
import time
import socket
import signal
import os


def is_service_running(port=8090):
    """检查指定端口的服务是否在运行"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def strat_service(port=8090):
    """启动Daphne服务"""
    cmd = ['daphne', '-p', str(port), 'test_platform_2025_new.asgi:application']
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        return process
    except Exception as e:
        print(f"启动服务失败：{e}")
        return None


def stop_service(process=None, port=8090):
    """停止Daphne服务，可以通过进程对象或端口号来指定"""
    if process:
        # 如果提供了进程对象，直接终止它
        try:
            process.terminate()  # 发送SIGTERM信号
            process.wait(timeout=5)  # 等待进程终止
            print(f"服务已通过进程对象停止")
            return True
        except subprocess.TimeoutExpired:
            # 如果进程没有及时终止，强制杀死
            process.kill()
            print(f"服务未响应SIGTERM，已强制终止")
            return True
        except Exception as e:
            print(f"停止服务时发生错误：{e}")
            return False
    elif port:
        # 如果提供了端口号，找到使用该端口的进程并终止它
        try:
            # 对于Linux/Mac
            if os.name != 'nt':
                cmd = f"lsof -i :{port} | grep LISTEN | awk '{{print $2}}'"
                pid = subprocess.check_output(cmd, shell=True).decode().strip()
                if pid:
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(2)
                    print(f"端口{port}的服务已停止，PID: {pid}")
                    return True
            # 对于Windows
            else:
                cmd = f"netstat -ano | findstr :{port} | findstr LISTENING"
                output = subprocess.check_output(cmd, shell=True).decode()
                if output:
                    pid = output.strip().split()[-1]
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True)
                    time.sleep(2)
                    print(f"端口{port}的服务已停止，PID: {pid}")
                    return True
            return False
        except Exception as e:
            print(f"通过端口停止服务时发生错误：{e}")
            return False
    return False


def restart_service(process=None, port=8090):
    """重启Daphne服务"""
    # 先停止服务
    stopped = stop_service(process, port)
    if not stopped:
        print("无法停止当前服务")
        return None

    # 等待端口释放
    wait_count = 0
    while is_service_running(port) and wait_count < 10:
        time.sleep(1)
        wait_count += 1

    if is_service_running(port):
        print(f"端口 {port} 仍被占用，无法重启服务")
        return None

    # 重新启动服务
    return strat_service(port)


def connect_device(request, id):
    # 检查服务，没启动先启动
    service_proc = None
    if not is_service_running(port=8090):
        service_proc = strat_service(port=8090)
        # 再次确认服务是否启动成功
        if not is_service_running(port=8090):
            print("服务启动失败，请检查配置")


stop_service()