# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Devices
import subprocess
import json
import socket
import time
from channels.generic.websocket import AsyncWebsocketConsumer
import cv2
import numpy as np


@csrf_exempt
def add_device(request):
    """ 新增设备 """
    if request.method == "POST":
        data = json.loads(request.body)
        name = data.get("name")
        device_type = data.get("device_type")
        ip_address = data.get("ip_address")
        port_num = data.get("port_num")
        status = data.get("status", "unknown")
        unique_id = data.get("unique_id", None)

        if name and device_type and ip_address and port_num:
            device = Devices.objects.create(
                name=name, device_type=device_type, ip_address=ip_address, port_num=port_num,
                status=status, unique_id=unique_id
            )
            return JsonResponse({"status": "success", "message": "设备添加成功", "device_id": device.id})

    return JsonResponse({"status": "error", "message": "参数缺失"}, status=400)


@csrf_exempt
def edit_device(request, id):
    """ 修改设备信息 """
    device = get_object_or_404(Devices, id=id)

    if request.method == "POST":
        data = json.loads(request.body)
        device.name = data.get("name", device.name)
        device.device_type = data.get("device_type", device.device_type)
        device.ip_address = data.get("ip_address", device.ip_address)
        device.port_num = data.get("port_num", device.port_num)
        device.status = data.get("status", device.status)
        device.unique_id = data.get("unique_id", device.unique_id)
        device.save()

        return JsonResponse({"status": "success", "message": "设备修改成功"})

    return JsonResponse({"status": "error", "message": "请求方法错误"}, status=400)


@csrf_exempt
def delete_device(request, id):
    """ 删除设备 """
    device = get_object_or_404(Devices, id=id)
    device.delete()
    return JsonResponse({"status": "success", "message": "设备删除成功"})


# 检查8090是否在运行
def is_service_running(port=8090):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)  # 1s超时
        s.connect(('127.0.0.1', port))
        return True
    except socket.error:
        return False
    finally:
        s.close()


# 启动daphne服务
def strat_service(port=8090):
    cmd = ['daphne', '-b', '0.0.0.0', '-p', str(port), 'test_platform_2025_new.asgi:application']
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        return process
    except Exception as e:
        print(f"启动服务失败：{e}")
        return None


def connect_device(request, id):
    # 检查服务，没启动先启动
    if not is_service_running(port=8090):
        service_proc = strat_service(port=8090)
        # 再次确认服务是否启动成功
        if not is_service_running(port=8090):
            return JsonResponse({"status": "error", "message": "服务启动失败，请检查配置"}, status=500)

    device = get_object_or_404(Devices, id=id)
    name = str(device.name)
    ip_address = device.ip_address
    port_num = str(device.port_num)
    unique_id = str(device.unique_id)

    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)

        if unique_id and unique_id in result.stdout:
            return JsonResponse(
                {"status": "success", "redirect_url": f"/device_management/video_stream/?unique_id={unique_id}"})


        elif ip_address and f"{ip_address}:{port_num}" in result.stdout:
            return JsonResponse(
                {"status": "success", "redirect_url": f"/device_management/video_stream/?unique_id={unique_id}"})


        else:
            return JsonResponse({"status": "error", "message": "未查询到该设备的连接状态"}, status=400)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def device_list(request):
    devices = Devices.objects.all()
    return render(request, 'new_device_management.html', {'devices': devices})


def video_stream(request):
    return render(request, 'video_stream.html')


def close_appium(request):
    port = 4723
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
            return JsonResponse({"status": "success", "message": f"已终止 PID: {pid} 占用的端口 {port}"})

    except subprocess.CalledProcessError:
        return JsonResponse({"status": "success", "message": f"端口 {port} 没有被占用。"})
