from django.urls import path
from . import views
from django.urls import re_path
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.product_page_management, name='element_management'),  # 功能首页
    path("product/get_product_name/", views.get_product_name, name="get_product_name"),
    path("product/add/", views.add_product, name="add_product"),
    path("product/edit/<int:product_id>/", views.edit_product, name="edit_product"),
    path("product/delete/<int:product_id>/", views.delete_product, name="delete_product"),
    path("get_products/", views.get_products, name="get_products"),

    path("add_element_info/", views.add_element_info, name="add_element_info"),
    path("edit_element_info/<int:element_info_id>/", views.edit_element_info, name="edit_element_info"),
    path("delete_element_info/<int:element_info_id>/", views.delete_element_info, name="delete_element_info"),
    path("element_info_list", views.element_info_list, name="element_info_list"),
    path("check_element_list/", views.check_element_list, name="check_element_list"),
    path("get_element_info/<int:element_id>/", views.get_element_info, name="get_element_info"),


    path("debug_element/", views.debug_element, name="debug_element"),

    path("test_case_list/", views.test_case_list, name="test_case_list"),
    path("delete_case_list/<int:test_case_id>/", views.delete_case_list, name="delete_case_list"),
    path("add_test_case/", views.add_test_case, name="add_test_case"),
    path("edit_product/<int:test_case_id>/", views.edit_test_case, name="edit_test_case"),

    path("check_case_list/", views.check_case_list, name="check_case_list"),
    path("get_elements_details/", views.get_elements_details, name="get_elements_details"),
    path("search_case/", views.search_case, name="search_case"),

    # 用例调试与执行
    path("case_debug_implement/", views.case_debug_implement, name="case_debug_implement"),
    path("debug_case/", views.debug_case, name="debug_case"),
    path("execution_case/", views.execution_case, name="execution_case"),
    path("execution_case_record/", views.execution_case_record, name="execution_case_record"),



]
