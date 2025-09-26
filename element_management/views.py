from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, ElementManage, AppPackage, TestCase, TestCaseExecution
from device_management.models import Devices
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from .appium_utils import AppiumDriverManager, ElementOperator, ElementLongPressOperator, ElementSwipeOperator, \
    ElementEnterTextOperator, JumpAdvertise, ElementClickAfterSwipingOperator, AppiumDriverPool
import json
import time
import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from django.core.paginator import Paginator
import logging
import ast

from .screenshot import ScreenshotManager

# Create your views here.
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@csrf_exempt
def product_page_management(request):
    product_name = request.GET.get("product_name")
    if product_name == "全部":
        products = Product.objects.all()

    elif product_name:
        products = Product.objects.filter(product_name=product_name).all()
    else:
        products = Product.objects.none()

    return render(request, "new_product_page_management.html", {"products": products})


def get_product_name(request):
    product_name = Product.objects.values("product_name").distinct()
    return JsonResponse({"functions": list(product_name)})


@csrf_exempt
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return JsonResponse({"status": "success", "message": "删除成功"})


@csrf_exempt
def add_product(request):
    """ 新增产品 """
    if request.method == "POST":
        data = json.loads(request.body)
        product_name = data.get("product_name")
        model = data.get("model")
        function = data.get("function")

        if product_name and model and function:
            product = Product.objects.create(product_name=product_name, model=model, function=function)
            return JsonResponse({"status": "success", "message": "产品添加成功", "product_id": product.id})

    return JsonResponse({"status": "error", "message": "参数缺失"}, status=400)


@csrf_exempt
def edit_product(request, product_id):
    """ 修改产品信息 """
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        data = json.loads(request.body)
        product.product_name = data.get("product_name", product.product_name)
        product.model = data.get("model", product.model)
        product.function = data.get("function", product.function)
        product.save()
        return JsonResponse({"status": "success", "message": "产品修改成功"})

    return JsonResponse({"status": "error", "message": "请求方法错误"}, status=400)


def get_products(request):
    """获取所有产品信息"""
    product_name = request.GET.get("product_name")

    model = request.GET.get("model")

    if product_name and model:
        # 返回匹配的function
        products = Product.objects.filter(product_name=product_name, model=model).values("function").distinct()
        return JsonResponse({"functions": list(products)})

    elif product_name:
        # 返回匹配的model
        products = Product.objects.filter(product_name=product_name).values("model").distinct()
        return JsonResponse({"models": list(products)})

    else:
        # 返回所有的product_name
        products = Product.objects.values("product_name").distinct()
        return JsonResponse({"products": list(products)})


@csrf_exempt
def add_element_info(request):
    """ 新增元素详情  """
    if request.method == "POST":
        data = json.loads(request.body)
        product_name = data.get("product_name")
        model = data.get("model")
        function = data.get("function")
        text = data.get("text", '无')
        content_desc = data.get("content_desc", '无')
        original_x_proportion = data.get("original_x_proportion", 0)
        original_y_proportion = data.get("original_y_proportion", 0)
        operate_type = data.get("operate_type")  # 操作方式
        start_x_start_y_end_x_end_y = data.get("start_x_start_y_end_x_end_y")
        duration = data.get("duration", 1000)
        enter_text = data.get("enter_text")
        remark = data.get("remark", '无')
        print(f'data:{data}')

        if product_name and model and function:
            element_info = ElementManage.objects.create(
                product_name=product_name, model=model, function=function, text=text,
                content_desc=content_desc, original_x_proportion=original_x_proportion,
                original_y_proportion=original_y_proportion, operate_type=operate_type,
                start_x_start_y_end_x_end_y=start_x_start_y_end_x_end_y, duration=duration,
                enter_text=enter_text, remark=remark
            )
            return JsonResponse({"status": "success", "message": "元素添加成功", "id": element_info.id})

    return JsonResponse({"status": "error", "message": "参数缺失1"}, status=400)


@csrf_exempt
def edit_element_info(request, element_info_id):
    """ 修改元素信息 """
    element_manage = get_object_or_404(ElementManage, id=element_info_id)

    if request.method == "POST":
        data = json.loads(request.body)
        element_manage.product_name = data.get("product_name", element_manage.product_name)
        element_manage.model = data.get("model", element_manage.model)
        element_manage.function = data.get("function", element_manage.function)
        element_manage.text = data.get("text", element_manage.text)
        element_manage.content_desc = data.get("content_desc", element_manage.content_desc)
        element_manage.original_x_proportion = data.get("original_x_proportion", element_manage.original_x_proportion)
        element_manage.original_y_proportion = data.get("original_y_proportion", element_manage.original_y_proportion)
        element_manage.operate_type = data.get("operate_type", element_manage.operate_type)
        element_manage.start_x_start_y_end_x_end_y = data.get("start_x_start_y_end_x_end_y",
                                                              element_manage.start_x_start_y_end_x_end_y)
        element_manage.duration = data.get("duration", element_manage.duration)
        element_manage.enter_text = data.get("enter_text", element_manage.enter_text)
        element_manage.remark = data.get("remark", element_manage.remark)
        element_manage.assertion = data.get("assertion", element_manage.assertion)
        element_manage.save()
        return JsonResponse({"status": "success", "message": "元素信息修改成功"})

    return JsonResponse({"status": "error", "message": "请求方法错误"}, status=400)


@csrf_exempt
def delete_element_info(request, element_info_id):
    related_cases = TestCase.objects.all()
    for case in related_cases:
        try:
            elements = ast.literal_eval(case.elements_list)
            if element_info_id in elements:
                return JsonResponse({"status": "success", "message": "该元素已经关联测试用例，无法直接删除"})
        except:
            continue
    element_manage = get_object_or_404(ElementManage, id=element_info_id)
    element_manage.delete()
    return JsonResponse({"status": "success", "message": "删除成功"})


@csrf_exempt
def element_info_list(request):
    page_number = request.GET.get("page_number", 1)
    product_name = request.GET.get("product_name")
    model = request.GET.get("model")
    function = request.GET.get("function")

    # 根据筛选条件过滤数据
    if product_name and model and function:
        if function == '全部':
            records = ElementManage.objects.filter(product_name=product_name, model=model).order_by('-id')
        else:
            records = ElementManage.objects.filter(product_name=product_name, model=model, function=function).order_by(
                '-id')
    elif product_name and model:
        records = ElementManage.objects.filter(product_name=product_name, model=model).order_by('-id')
    elif product_name:
        records = ElementManage.objects.filter(product_name=product_name).order_by('-id')
    else:
        records = ElementManage.objects.all().order_by('-id')

    # 使用Paginator 分页，每页10个数据
    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(page_number)

    devices = Devices.objects.all()
    print(f'传给前端的数据页码：{page_obj}')
    return render(request, 'element_info_list.html',
                  {'devices': devices, 'page_obj': page_obj})


@csrf_exempt
def get_element_info(request, element_id):
    """获取单个元素的详细信息"""
    try:
        element = ElementManage.objects.filter(id=element_id).values("id", "function", "text", "content_desc",
                                                                     "remark").first()

        return JsonResponse({
            "status": "success",
            "element": element
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })


@csrf_exempt
def check_element_list(request):
    """新增测试用例时，筛选元素列表"""
    product_name = request.GET.get("product_name")
    model = request.GET.get("model")
    function = request.GET.get("function")

    if product_name and model and function:
        products = ElementManage.objects.filter(product_name=product_name, model=model, function=function).values("id",
                                                                                                                  "function",
                                                                                                                  "text",
                                                                                                                  "content_desc",
                                                                                                                  "remark")
        print(f'{function}所有的功能：{products}')
        return JsonResponse({"products": list(products)})

    elif product_name and model:
        # products = ElementManage.objects.filter(product_name=product_name, model=model).values("id", "function", "text",
        #                                                                                        "content_desc", "remark")
        products = ElementManage.objects.filter(product_name=product_name, model=model).values("function").distinct()
        print(f'所有的功能：{products}')
        return JsonResponse({"products": list(products)})

    elif product_name:
        products = ElementManage.objects.filter(product_name=product_name).values("model").distinct()
        print(f'所有的页面：{products}')
        return JsonResponse({"models": list(products)})

    else:
        # 返回所有的product_name
        products = ElementManage.objects.values("product_name").distinct()
        print(f'所有的产品名称：{products}')
        return JsonResponse({"products": list(products)})


from tool.coze_ai import ImageJudgment
import tempfile
import os


@csrf_exempt
def debug_element(request):
    """Appium 调试元素 使用驱动池"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # 提取参数
            device_id = data.get("device_id")
            device_type = data.get("device_type")
            device_version = data.get("device_version")
            text = data.get("text")
            content_desc = data.get("content_desc")
            x_proportion = data.get("x_proportion")
            y_proportion = data.get("y_proportion")
            operate_type = data.get("operate_type")
            start_end_x_y = data.get("startEndXy")
            duration = data.get("duration")
            enter = data.get("enter")
            product_name = data.get("product_name")
            remark = data.get("remark")
            assertion = data.get("assertion")

            # 获取应用包信息
            app_info = AppPackage.objects.filter(product_name=product_name).first()
            if not app_info:
                return JsonResponse({"status": "error", "message": "未找到app包信息"}, status=400)

            app_package = app_info.app_package
            app_activity = app_info.app_activity

            # 从驱动池获取驱动
            driver_pool = AppiumDriverPool()
            driver = None
            try:
                driver = driver_pool.get_driver(
                    device_id=device_id,
                    device_type=device_type,
                    device_version=device_version,
                    app_package=app_package,
                    app_activity=app_activity
                )
            except Exception as e:
                logger.error(f"获取驱动失败: {str(e)}")
                return JsonResponse({"status": "error", "message": f"获取驱动失败: {str(e)}"}, status=500)

            # 判断处理类型
            try:
                if operate_type == 'click':
                    operator = ElementOperator(driver, device_id=device_id)

                    try:
                        operator.click_element(
                            text=text,
                            content_desc=content_desc,
                            x_proportion=x_proportion,
                            y_proportion=y_proportion
                        )

                    except Exception as e:
                        return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

                    # finally:
                    #     driver.quit()

                elif operate_type == 'long_press':
                    operator = ElementLongPressOperator(driver, device_id=device_id)
                    try:
                        operator.long_press_element(
                            text=text,
                            content_desc=content_desc,
                            x_proportion=x_proportion,
                            y_proportion=y_proportion,
                            duration=duration
                        )

                    except Exception as e:
                        return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

                    finally:
                        pass
                        # driver.quit()

                elif operate_type == 'swipe' or operate_type == 'from_bottom_to_top_swipe':
                    operator = ElementSwipeOperator(driver, device_id=device_id)
                    try:
                        operator.swipe_element(start_end_x_y, duration)


                    except Exception as e:
                        return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

                    finally:
                        print("33333333333333333")

                elif operate_type == 'enter_text':
                    operator = ElementEnterTextOperator(driver, device_id=device_id)
                    try:
                        operator.enter_text(
                            position_text=text,
                            enter=enter
                        )
                    except Exception as e:
                        return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)
                    # finally:
                    #     driver.quit()

                elif operate_type == 'click_after_swiping':
                    operator = ElementClickAfterSwipingOperator(driver, device_id=device_id)
                    try:
                        operator.click_after_swipe_element(
                            text=text,
                            content_desc=content_desc,
                            x_proportion=x_proportion,
                            y_proportion=y_proportion,
                            start_x_start_y_end_x_end_y=start_end_x_y,
                            duration=duration
                        )
                    except Exception as e:
                        return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

                # 开始进行断言
                try:
                    if assertion and assertion != 'None':
                        # 创建临时文件
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            temp_path = tmp.name

                        # 截图保存到临时文件
                        driver.get_screenshot_as_file(temp_path)

                        result = ImageJudgment().send_local_image_with_text(product_name, remark, temp_path, assertion)
                        logger.info(f'打印coze的输出结果:{result}')

                        if 'True' in result:
                            logger.info(f'内容：{content_desc}，断言成功')
                        else:
                            return JsonResponse({"status": "error", "message": f"内容：{content_desc}，断言失败！！！"},
                                                status=200)

                        # 清理临时文件
                        os.unlink(temp_path)

                except Exception as e:
                    return JsonResponse({"status": "error", "message": f"断言失败: {str(e)}"}, status=500)
                # 将驱动释放回池中
                driver_pool.release_driver(device_id, app_package)
                return JsonResponse({"status": "success", "message": "调试成功"})

            except Exception as e:
                # 确保在错误情况下也释放驱动
                if driver:
                    driver_pool.release_driver(device_id, app_package)

                logger.error(f"调试失败: {str(e)}")

                return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"请求处理异常: {str(e)}"}, status=500)


@csrf_exempt
def test_case_list(request):
    # test_cases = TestCase.objects.all()
    return render(request, 'new_test_case_list.html')


@csrf_exempt
def delete_case_list(request, test_case_id):
    case = get_object_or_404(TestCase, id=test_case_id)
    case.delete()
    return JsonResponse({"status": "success", "message": "删除成功"})


@csrf_exempt
def add_test_case(request):
    """ 新增测试用例 """
    if request.method == "POST":
        data = json.loads(request.body)
        case_name = data.get("case_name")
        product_name = data.get("product_name")
        model = data.get("model")
        function = data.get("function")
        element_id = data.get("element_id")  # 元素id列表

        if not case_name or not element_id:
            return JsonResponse({"status": "error", "message": "用例名称或元素ID不能为空"}, status=400)

        # 保存测试用例
        test_case = TestCase.objects.create(case_name=case_name, product_name=product_name, model=model,
                                            function=function, elements_list=json.dumps(element_id))
        return JsonResponse({"status": "success", "message": "测试用例添加成功", "test_case_id": test_case.id})

    return JsonResponse({"status": "error", "message": "参数缺失"}, status=400)


@csrf_exempt
def edit_test_case(request, test_case_id):
    """ 修改测试用例信息 """
    test_case = get_object_or_404(TestCase, id=test_case_id)

    if request.method == "POST":
        data = json.loads(request.body)
        case_name = data.get("case_name")
        product_name = data.get("product_name")
        model = data.get("model")
        function = data.get("function")
        element_id = data.get("element_id")  # 元素id列表
        if not case_name or not element_id:
            return JsonResponse({"status": "error", "message": "用例名称或元素ID不能为空"}, status=400)

        # 更新测试用例
        test_case.case_name = case_name
        test_case.product_name = product_name
        test_case.model = model
        test_case.function = function

        test_case.elements_list = json.dumps(element_id)

        test_case.save()
        return JsonResponse({"status": "success", "message": "测试用例修改成功"})

    return JsonResponse({"status": "error", "message": "请求方法错误"}, status=400)


@csrf_exempt
def get_elements_details(request):
    """根据id列表获取详细信息"""
    try:
        element_ids = json.loads(request.GET.get('ids', []))
        elements_details = []

        for element_id in element_ids:
            element_details = TestCase.objects.filter(id=element_id).values('text', 'content_desc', 'remark').first()
            details_str = ''.join(
                [element_details['text'], element_details['content_desc'], element_details['remark']])
            elements_details.append(details_str)
        content = '|'.join(elements_details)

        return JsonResponse({
            'status': 'success',
            'elements': content
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
def check_case_list(request):
    product_name = request.GET.get("product_name")
    model = request.GET.get("model")
    page_number = request.GET.get("page_number", 1)

    if product_name and model:
        if model == "全部":
            products = TestCase.objects.filter(product_name=product_name).values(
                "id", "case_name", "product_name", "model", "function", "elements_list"
            ).order_by('-id')

            # 使用Paginator 分页，每页5个数据
            paginator = Paginator(products, 5)
            page_obj = paginator.get_page(page_number)

            result = []

            for product in page_obj:
                element_details = []
                elements = product['elements_list']

                for element_id in json.loads(elements):
                    element_details_item = ElementManage.objects.filter(id=element_id).values('remark').first()

                    element_details.append(element_details_item['remark'])

                    product['element_details'] = '|'.join(element_details)
                result.append(product)
            print(f'check_case_list传给前端的数据：{result}')
            return JsonResponse({
                "products": result,
                "total_pages": paginator.num_pages
            })
        else:
            products = TestCase.objects.filter(product_name=product_name, model=model).values(
                "id", "case_name", "product_name", "model", "function", "elements_list"
            ).order_by('-id')

            # 使用Paginator 分页，每页5个数据
            paginator = Paginator(products, 5)
            page_obj = paginator.get_page(page_number)

            result = []

            for product in page_obj:
                element_details = []
                elements = product['elements_list']

                for element_id in json.loads(elements):
                    element_details_item = ElementManage.objects.filter(id=element_id).values('remark').first()

                    details_str = ''.join(
                        element_details_item['remark']
                    )
                    element_details.append(details_str)

                    product['element_details'] = '|'.join(element_details)
                result.append(product)
            print(f'check_case_list传给前端的数据：{result}')
            return JsonResponse({
                "products": result,
                "total_pages": paginator.num_pages
            })

    elif product_name:
        # 返回匹配的model
        products = TestCase.objects.filter(product_name=product_name).values("model").distinct()
        return JsonResponse({"models": list(products)})

    else:
        # 返回所有的product_name
        products = TestCase.objects.values("product_name").distinct()
        return JsonResponse({"products": list(products)})


@csrf_exempt
def search_case(request):
    """搜索用例"""
    try:
        search_keyword = request.GET.get("search_keyword", "").strip()
        page_number = request.GET.get("page_number", "").strip()
        products = TestCase.objects.filter(case_name__icontains=search_keyword).values(
            "id", "case_name", "product_name", "model", "function", "elements_list"
        )

        # 使用Paginator 分页，每页5个数据
        paginator = Paginator(products, 5)
        page_obj = paginator.get_page(page_number)

        result = []

        for product in page_obj:
            element_details = []
            elements = product['elements_list']

            for element_id in json.loads(elements):
                element_details_item = ElementManage.objects.filter(id=element_id).values('text', 'content_desc',
                                                                                          'remark').first()

                details_str = ''.join(
                    [element_details_item['text'], element_details_item['content_desc'],
                     element_details_item['remark']]
                )
                element_details.append(details_str)

                product['element_details'] = '|'.join(element_details)
            result.append(product)
        # print(f'传给前端的数据：{result}')
        return JsonResponse({"products": result, "total_pages": paginator.num_pages})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
def case_debug_implement(request):
    devices = Devices.objects.all().values('unique_id', 'device_type', 'version', 'name')
    # print(f"设备详情是：{devices}")
    return render(request, 'new_case_debug_implement.html', {'devices': list(devices)})


@csrf_exempt
def debug_case(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(f"data：{data}")
            # 提取参数
            elements_list = data.get("elements_list")
            unique_id = data.get("unique_id")
            device_type = data.get("device_type")
            device_version = data.get("device_version")
            product_name = data.get("product_name")

            # 获取应用包信息
            app_info = AppPackage.objects.filter(product_name=product_name).first()

            if not app_info:
                return JsonResponse({"status": "error", "message": "未找到app包信息"}, status=400)

            app_package = app_info.app_package
            app_activity = app_info.app_activity

            # 初始化 driver
            # driver_manager = AppiumDriverManager(
            #     device_id=unique_id,
            #     device_type=device_type,
            #     device_version=device_version,
            #     app_package=app_info.app_package,
            #     app_activity=app_info.app_activity
            # )
            #
            # driver = driver_manager.create_driver()

            device_id = unique_id
            # 从驱动池获取驱动
            driver_pool = AppiumDriverPool()
            driver = None

            try:
                driver = driver_pool.get_driver(
                    device_id=device_id,
                    device_type=device_type,
                    device_version=device_version,
                    app_package=app_package,
                    app_activity=app_activity
                )
            except Exception as e:
                logger.error(f"获取驱动失败: {str(e)}")
                return JsonResponse({"status": "error", "message": f"获取驱动失败: {str(e)}"}, status=500)

            for elements_id in elements_list:

                # 获取ElementManage数据
                elements_info = ElementManage.objects.filter(id=elements_id).first()
                text = elements_info.text
                content_desc = elements_info.content_desc
                x_proportion = elements_info.original_x_proportion
                y_proportion = elements_info.original_y_proportion
                operate_type = elements_info.operate_type
                duration = elements_info.duration
                start_end_x_y = elements_info.start_x_start_y_end_x_end_y
                enter = elements_info.enter_text
                remark = elements_info.remark
                assertion = elements_info.assertion

                try:
                    if operate_type == 'click':
                        operator = ElementOperator(driver, device_id=device_id)

                        try:
                            operator.click_element(
                                text=text,
                                content_desc=content_desc,
                                x_proportion=x_proportion,
                                y_proportion=y_proportion
                            )
                        except Exception as e:
                            return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

                    elif operate_type == 'long_press':
                        operator = ElementLongPressOperator(driver, device_id=device_id)
                        try:
                            operator.long_press_element(
                                text=text,
                                content_desc=content_desc,
                                x_proportion=x_proportion,
                                y_proportion=y_proportion,
                                duration=duration
                            )

                        except Exception as e:
                            return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

                    elif operate_type == 'swipe' or operate_type == 'from_bottom_to_top_swipe':
                        operator = ElementSwipeOperator(driver, device_id=device_id)
                        try:
                            operator.swipe_element(start_end_x_y, duration)

                        except Exception as e:
                            return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

                    elif operate_type == 'enter_text':
                        operator = ElementEnterTextOperator(driver, device_id=device_id)
                        try:
                            operator.enter_text(
                                position_text=text,
                                enter=enter
                            )
                        except Exception as e:
                            return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)
                        # finally:
                        #     driver.quit()

                    elif operate_type == 'click_after_swiping':
                        operator = ElementClickAfterSwipingOperator(driver, device_id=device_id)
                        try:
                            operator.click_after_swipe_element(
                                text=text,
                                content_desc=content_desc,
                                x_proportion=x_proportion,
                                y_proportion=y_proportion,
                                start_x_start_y_end_x_end_y=start_end_x_y,
                                duration=duration
                            )
                        except Exception as e:
                            return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)

                    # 开始进行断言
                    try:
                        if assertion and assertion != 'None':
                            print(f'assertion的值: {repr(assertion)}')  # 用repr显示真实值

                            # 创建临时文件
                            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                                temp_path = tmp.name

                            # 截图保存到临时文件
                            driver.get_screenshot_as_file(temp_path)

                            result = ImageJudgment().send_local_image_with_text(product_name, remark, temp_path,
                                                                                assertion)
                            logger.info(f'打印coze的输出结果:{result}')

                            if 'True' in result:
                                logger.info(f'内容：{content_desc}，断言成功')
                            else:
                                return JsonResponse({"status": "error", "message": f"内容：{content_desc}，断言失败！！！"},
                                                    status=200)

                            # 清理临时文件
                            os.unlink(temp_path)

                    except Exception as e:
                        return JsonResponse({"status": "error", "message": f"断言失败: {str(e)}"}, status=500)

                except Exception as e:
                    if driver:
                        driver_pool.release_driver(device_id, app_package)
                    return JsonResponse({"status": "error", "message": f"单个元素调用失败: {str(e)}"}, status=500)

            return JsonResponse({"status": "success", "message": "调试成功"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"调试失败: {str(e)}"}, status=500)


@csrf_exempt
def execution_case(request):
    """执行多条测试用例"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(f"执行data1：{data}")
            # 提取参数
            test_case_id = data.get("case_ids")
            unique_id = data.get("unique_id")
            device_type = data.get("device_type")
            device_version = data.get("device_version")
            product_name = data.get("product_name")

            # 获取应用包信息
            app_info = AppPackage.objects.filter(product_name=product_name).first()

            if not app_info:
                return JsonResponse({"status": "error", "message": "未找到app包信息"}, status=400)

            app_package = app_info.app_package
            app_activity = app_info.app_activity

            # 创建截图文件夹
            screenshot_manager = ScreenshotManager()
            case_folder_path = screenshot_manager.create_screenshot_folder()

            # 初始化驱动池
            driver_pool = AppiumDriverPool()

            def save_execution_result(case_id, start_time, end_time, result, log=""):
                """保存测试用例执行结果"""
                execution_time = end_time - start_time
                screenshot_path = ""

                if driver:
                    try:
                        screenshot_manager.driver = driver
                        screenshot_path = screenshot_manager.capture_and_save(case_folder_path)
                        print(f'保存路径是{screenshot_path}')
                    except Exception as e:
                        print(f"截图失败: {e}")

                TestCaseExecution.objects.create(
                    unique_id=unique_id,
                    product_name=product_name,
                    test_case_id=case_id,
                    start_time=datetime.datetime.fromtimestamp(start_time),
                    end_time=datetime.datetime.fromtimestamp(end_time),
                    execution_time=execution_time,
                    result=result,
                    log=log,
                    screenshot_path=screenshot_path
                )
                print(f'测试用例 {case_id} 执行{result}，结果已保存')

            for case_id in test_case_id:
                driver = None
                retry_count = 0
                max_retries = 2  # 最大重试次数

                while retry_count <= max_retries:
                    try:
                        print(f"开始执行测试用例 {case_id} (尝试 {retry_count + 1}/{max_retries + 1})")

                        # 从驱动池获取驱动
                        try:
                            driver = driver_pool.get_driver(
                                device_id=unique_id,
                                device_type=device_type,
                                device_version=device_version,
                                app_package=app_package,
                                app_activity=app_activity
                            )

                            # 根据设备类型采用不同的应用重启策略
                            print("确保应用处于全新状态")

                            try:
                                # 首先尝试终止应用
                                if hasattr(driver, 'terminate_app'):
                                    print(f"终止应用: {app_package}")
                                    driver.terminate_app(app_package)
                                else:
                                    print("驱动不支持terminate_app方法，尝试替代方法")
                                    # 尝试使用close_app()
                                    if hasattr(driver, 'close_app'):
                                        print("使用close_app()关闭应用")
                                        driver.close_app()

                                time.sleep(2)  # 等待应用完全关闭

                                # 启动应用
                                print(f"启动应用: {app_package}")
                                if device_type.lower() == 'android':
                                    # Android特有的启动方法
                                    if hasattr(driver, 'start_activity'):
                                        print(f"使用start_activity启动: {app_package}/{app_activity}")
                                        driver.start_activity(app_package, app_activity)
                                    else:
                                        # 回退到通用方法
                                        print("使用activate_app启动应用")
                                        if hasattr(driver, 'activate_app'):
                                            driver.activate_app(app_package)
                                        else:
                                            print("使用launch_app启动应用")
                                            driver.launch_app()
                                else:
                                    # iOS或其他设备类型
                                    print("使用launch_app启动应用")
                                    driver.launch_app()

                            except Exception as app_control_error:
                                print(f"应用控制异常，尝试通用方法: {str(app_control_error)}")
                                try:
                                    # 最后的回退方案
                                    driver.launch_app()
                                except Exception as launch_error:
                                    print(f"无法启动应用: {str(launch_error)}")
                                    # 继续执行，可能应用已在运行
                                # 等待应用启动
                                time.sleep(5)


                        except Exception as e:
                            logger.error(f"获取驱动或控制应用失败: {str(e)}")
                            retry_count += 1
                            if retry_count > max_retries:
                                return JsonResponse({"status": "error", "message": f"获取驱动失败: {str(e)}"},
                                                    status=500)
                            continue  # 重试

                        operator = ElementOperator(driver, device_id=unique_id)

                        elements_list = TestCase.objects.filter(id=case_id).values("elements_list").first()
                        print(f"elements_list是:{elements_list}")

                        start_time = time.time()

                        # 等待应用加载和初始化
                        print("等待应用加载...")
                        time.sleep(8)

                        # 获取第一个要操作的元素信息
                        first_element_id = json.loads(elements_list['elements_list'])[0]
                        first_element = ElementManage.objects.filter(id=first_element_id).first()
                        print(
                            f"等待第一个元素: id={first_element.id}, text={first_element.text}, content_desc={first_element.content_desc}")

                        # 等待第一个元素出现
                        max_wait_time = 15
                        wait = WebDriverWait(driver, max_wait_time)

                        # 使用多个定位策略，但添加更多调试信息
                        element_found = False
                        try:
                            if first_element.text and first_element.text.strip():
                                print(f"尝试通过text定位: {first_element.text}")
                                wait.until(
                                    EC.presence_of_element_located((By.XPATH, f"//*[@text='{first_element.text}']")))
                                element_found = True
                                print("通过text定位成功")
                        except Exception as e:
                            print(f"通过text定位失败")

                        if not element_found and first_element.content_desc and first_element.content_desc.strip():
                            try:
                                print(f"尝试通过content-desc定位: {repr(first_element.content_desc)}")
                                # 处理包含换行符的content-desc，使用contains方式
                                clean_desc = first_element.content_desc.replace('\n', ' ').strip()
                                if len(clean_desc) > 10:  # 如果太长，只取前面部分
                                    clean_desc = clean_desc.split()[0]  # 取第一个单词
                                wait.until(EC.presence_of_element_located(
                                    (By.XPATH, f"//*[contains(@content-desc, '{clean_desc}')]")))
                                element_found = True
                                print("通过content-desc定位成功")
                            except Exception as e:
                                print(f"通过content-desc定位失败")

                        # 如果都找不到，说明页面可能还在加载或元素定位有问题，但不影响后续执行
                        if not element_found:
                            print("元素定位未成功，但继续执行（依赖坐标点击）...")
                            # 不再抛出异常，而是继续执行

                        # 执行测试步骤
                        print("开始执行测试步骤")
                        test_completed = True  # 标记测试是否正常完成
                        failure_reason = ""

                        for elements_id in json.loads(elements_list['elements_list']):
                            elements_info = ElementManage.objects.filter(id=elements_id).first()
                            text = elements_info.text
                            content_desc = elements_info.content_desc
                            x_proportion = elements_info.original_x_proportion
                            y_proportion = elements_info.original_y_proportion
                            operate_type = elements_info.operate_type
                            duration = elements_info.duration
                            start_end_x_y = elements_info.start_x_start_y_end_x_end_y
                            enter = elements_info.enter_text
                            remark = elements_info.remark
                            assertion = elements_info.assertion

                            try:
                                if operate_type == 'click':
                                    operator = ElementOperator(driver, device_id=unique_id)

                                    operator.click_element(
                                        text=text,
                                        content_desc=content_desc,
                                        x_proportion=x_proportion,
                                        y_proportion=y_proportion
                                    )

                                elif operate_type == 'long_press':
                                    operator = ElementLongPressOperator(driver, device_id=unique_id)
                                    operator.long_press_element(
                                        text=text,
                                        content_desc=content_desc,
                                        x_proportion=x_proportion,
                                        y_proportion=y_proportion,
                                        duration=duration
                                    )

                                elif operate_type == 'swipe' or operate_type == 'from_bottom_to_top_swipe':
                                    operator = ElementSwipeOperator(driver, device_id=unique_id)
                                    operator.swipe_element(start_end_x_y, duration)

                                elif operate_type == 'enter_text':
                                    operator = ElementEnterTextOperator(driver, device_id=unique_id)
                                    operator.enter_text(
                                        position_text=text,
                                        enter=enter
                                    )

                                elif operate_type == 'click_after_swiping':
                                    operator = ElementClickAfterSwipingOperator(driver, device_id=unique_id)
                                    operator.click_after_swipe_element(
                                        text=text,
                                        content_desc=content_desc,
                                        x_proportion=x_proportion,
                                        y_proportion=y_proportion,
                                        start_x_start_y_end_x_end_y=start_end_x_y,
                                        duration=duration
                                    )

                                time.sleep(1)  # 每个操作后短暂等待

                                # 开始进行断言
                                try:
                                    if assertion and assertion != 'None':
                                        # 创建临时文件
                                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                                            temp_path = tmp.name

                                        # 截图保存到临时文件
                                        driver.get_screenshot_as_file(temp_path)

                                        result = ImageJudgment().send_local_image_with_text(product_name, remark,
                                                                                            temp_path,
                                                                                            assertion)
                                        logger.info(f'打印coze的输出结果:{result}')

                                        if 'True' in result:
                                            logger.info(f'内容：{content_desc}，断言成功')
                                        else:
                                            logger.info(f'内容：{content_desc}，断言失败')
                                            test_completed = False
                                            failure_reason = f"断言失败: {assertion},remark:{remark}"
                                            # 清理临时文件
                                            os.unlink(temp_path)
                                            break

                                        # 清理临时文件
                                        os.unlink(temp_path)

                                except Exception as e:
                                    pass

                            except Exception as e:
                                test_completed = False
                                failure_reason = str(e)
                                break

                        end_time = time.time()

                        # 统一保存执行结果
                        if test_completed:
                            save_execution_result(case_id, start_time, end_time, "success")
                        else:
                            save_execution_result(case_id, start_time, end_time, "fail", failure_reason)

                        break  # 成功执行，跳出重试循环

                    except Exception as e:
                        print(f"测试用例 {case_id} 执行出错: {e}")
                        end_time = time.time()

                        # 保存失败执行记录
                        save_execution_result(case_id, start_time, end_time, "fail", str(e))

                        retry_count += 1
                        if retry_count <= max_retries:
                            print(f"准备第 {retry_count + 1} 次重试...")
                            time.sleep(3)  # 重试前等待
                        else:
                            print(f"测试用例 {case_id} 已达到最大重试次数")

                    finally:
                        # 确保在完成后释放驱动
                        if driver:
                            try:
                                driver_pool.release_driver(unique_id, app_package)
                                print(f"已释放驱动回池")
                            except Exception as release_error:
                                print(f"释放驱动时出错: {str(release_error)}")

            return JsonResponse({"status": "success", "message": "所有测试用例执行完成"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"执行失败: {str(e)}"}, status=500)


@csrf_exempt
def execution_case_record(request):
    page_number = request.GET.get("page_number", 1)

    records = TestCaseExecution.objects.values("id", "unique_id", "product_name", "test_case_id", "start_time",
                                               "end_time", "execution_time", "result", "log",
                                               "screenshot_path").order_by('-start_time')

    # 使用Paginator 分页，每页10个数据
    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(page_number)

    result = []

    for record in page_obj:
        unique_id = record['unique_id']
        device = Devices.objects.filter(unique_id=unique_id).values('name').first()

        test_case_id = record['test_case_id']
        case_name = TestCase.objects.filter(id=test_case_id).values('case_name').first()

        if device:
            record['unique_id'] = device['name']

        if case_name:
            record['test_case_id'] = case_name['case_name'] + '|' + str(test_case_id)
        result.append(record)

    print(f'传给前端的数据：{result}')
    return render(request, 'new_execution_case_record.html', {
        'result': result,
        'page_obj': page_obj,
    })
