#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
作者：zootiger
github：https://github.com/ZooTi9er

这个项目是一个基于 PyQt5 的 UART 串口调试工具，展示了多线程架构的最佳实践。
特别适合学习 PyQt5 的多线程编程，采用 "Worker + moveToThread" 模式。

核心特性：
- 多线程架构：UI线程与串口处理线程完全分离
- 响应式UI：串口通信不会阻塞界面操作
- 实时数据处理：串口数据的实时接收和显示
- 线程安全通信：通过 PyQt5 信号槽机制实现跨线程安全通信

架构设计：
- 主线程 (InitForm)：负责UI渲染和用户交互
- 工作线程 (Serial_Qthread_function)：负责串口I/O操作
- 跨线程通信：通过信号槽机制确保线程安全
"""

from PyQt5 import QtWidgets as qw
import sys
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import serial_thread
import time
import threading
import os

# 导入UI模块
import form

class InitForm(qw.QMainWindow):
    """
    主窗口类 - 单继承 QMainWindow，采用 UI实例 模式
    
    职责：
    - 负责用户界面渲染和事件处理
    - 处理用户交互（按钮点击、菜单选择等）
    - 更新数据显示区域（线程安全操作）
    - 管理应用程序生命周期
    """
    
    def __init__(self):
        super(InitForm, self).__init__()
        
        # 🔑【UI实例创建】创建UI实例并设置界面
        self.ui = form.Ui_MainWindow()  # 创建UI实例
        self.ui.setupUi(self)           # 设置UI界面
        
        # 串口参数
        self.set_parameter = {}
        
        # 🔑【关键步骤1】创建工作线程对象
        self.Serial_QThread = QtCore.QThread()
        
        # 🔑【关键步骤2】创建工作对象
        self.Serial_Qthread_function = Serial_Qthread_function()
        
        # 🔑【关键步骤3】将工作对象移动到工作线程（核心步骤！）
        self.Serial_Qthread_function.moveToThread(self.Serial_QThread)
        
        # 🔑【关键步骤4】启动工作线程的事件循环
        self.Serial_QThread.start()
        
        # 📡【跨线程信号槽连接1】线程内部初始化连接
        self.Serial_Qthread_function.signal_Serialstart_function.connect(
            self.Serial_Qthread_function.Serial_Init_function
        )
        
        # 📡【跨线程信号槽连接2】发送串口操作请求连接
        self.Serial_Qthread_function.signal_push_open_serial_button.connect(
            self.Serial_Qthread_function.slot_push_open_serial_button
        )
        
        # 📤【跨线程信号槽连接3】接收工作线程状态更新
        self.Serial_Qthread_function.signal_serial_button_pushed.connect(
            self.slot_signal_serial_button_pushed
        )
        
        # 📤【跨线程信号槽连接4】接收工作线程数据更新
        self.Serial_Qthread_function.signal_update_textbrowser.connect(
            self.slot_update_textbrowser
        )
        
        # 初始化串口参数
        self.set_parameter['comboBox_databit'] = 8
        self.set_parameter['comboBox_stopbit'] = 1
        self.set_parameter['comboBox_checkbit'] = 0
        self.set_parameter['comboBox_flowctrl'] = 0
        
        # 扫描串口
        self.serial_scan()
        
        # 连接按钮信号
        self.ui.open_serial_button.clicked.connect(self.open_serial)
        self.ui.comboBox_Com.currentTextChanged.connect(self.combobox_com_changed)
        
        # 设置窗口标题
        self.setWindowTitle("UART串口调试工具")
        
        # 🔑【触发初始化】发送串口初始化信号
        self.Serial_Qthread_function.signal_Serialstart_function.emit()
        
        # 打印线程信息用于验证
        print(f"主线程ID: {threading.get_ident()}")
    
    def serial_scan(self):
        """扫描可用串口"""
        port_list = list(serial.tools.list_ports.comports())
        portname_list = []
        for port in port_list:
            portname_list.append(port.device)
        self.ui.comboBox_Com.addItems(portname_list)
        
        if len(portname_list) == 0:
            self.ui.comboBox_Com.addItem("无可用串口")
    
    def combobox_com_changed(self):
        """串口选择改变事件"""
        if self.ui.comboBox_Com.currentText() == "无可用串口":
            self.serial_scan()
    
    def open_serial(self):
        """
        📡 跨线程信号发送 - 将用户操作传递到工作线程
        
        【线程安全原则】
        ⚠️  注意：串口操作不能在主线程中执行！
        串口操作是阻塞性的 I/O 操作，会阻塞 UI 响应
        必须通过信号槽机制将操作请求发送到工作线程
        """
        # 准备串口参数
        self.set_parameter['comboBox_port'] = self.ui.comboBox_Com.currentText()  # 🔄 通过self.ui访问
        self.set_parameter['comboBox_baudrate'] = 256000  # 当前固定为256000
        # 其他参数已经在初始化中设置
        
        # 📤【跨线程信号发送】发送串口操作请求到工作线程
        self.Serial_Qthread_function.signal_push_open_serial_button.emit(self.set_parameter)
    
    def slot_signal_serial_button_pushed(self, state):
        """
        📤 接收工作线程状态更新 - UI 状态同步槽函数
        
        【线程安全机制】
        ✅ 这个函数在主线程中执行（由 Qt 的信号槽机制保证）
        ✅ 可以安全地操作 UI 组件（按钮文本更新）
        """
        if state == 1:
            self.ui.open_serial_button.setText("关闭串口")  # 🔄 通过self.ui访问
        else:
            self.ui.open_serial_button.setText("打开串口")   # 🔄 通过self.ui访问
    
    def slot_update_textbrowser(self, data):
        """
        📤 接收工作线程数据 - UI 数据显示槽函数
        
        【线程安全机制】
        ✅ 这个函数在主线程中执行（由 Qt 的信号槽机制保证）
        ✅ 可以安全地操作 UI 组件（文本显示更新）
        """
        # 数据格式化为十六进制显示
        Byte_data = bytes(data)
        view_data = ''
        for i in range(0, len(Byte_data)):
            view_data = view_data + '{:02x}'.format(Byte_data[i]) + ' '
        
        # 更新文本显示区域
        self.ui.textBrowser.insertPlainText(view_data)     # 🔄 通过self.ui访问
        self.ui.textBrowser.insertPlainText('\n')         # 🔄 通过self.ui访问
        
        # 自动滚动到底部
        self.ui.textBrowser.ensureCursorVisible()
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        print("正在关闭应用程序...")
        
        # 停止工作线程
        if hasattr(self, 'Serial_QThread'):
            self.Serial_QThread.quit()
            self.Serial_QThread.wait(3000)  # 等待3秒
            
        # 关闭串口
        if hasattr(self, 'Serial_Qthread_function'):
            if hasattr(self.Serial_Qthread_function, 'Serial') and self.Serial_Qthread_function.Serial.isOpen():
                self.Serial_Qthread_function.Serial.close()
                
        event.accept()
        print("应用程序已关闭")

if __name__ == '__main__':
    app = qw.QApplication(sys.argv)
    
    # 创建主窗口
    main_form = InitForm()
    
    # 显示主窗口
    main_form.show()
    
    # 运行应用程序
    sys.exit(app.exec_())