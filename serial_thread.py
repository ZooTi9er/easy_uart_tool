#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
作者：zootiger
github：https://github.com/ZooTi9er

串口工作线程模块 - 专门负责串口通信的多线程处理

这个模块实现了 PyQt5 的 "Worker + moveToThread" 多线程模式：
- 工作线程专门处理串口 I/O 操作
- 通过信号槽机制与主线程安全通信
- 确保串口操作不会阻塞 UI 界面

核心功能：
- 串口连接管理
- 数据接收和发送
- 跨线程状态通知
- 错误处理和恢复
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QIODevice, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import time
import threading

class Serial_Qthread_function(QtCore.QObject):
    """
    串口工作线程类 - 在工作线程中执行所有串口操作
    
    职责：
    - 专门处理串口通信任务（阻塞操作）
    - 监听串口数据到达事件
    - 管理串口连接状态
    - 执行数据收发操作
    
    执行环境：
    - 此类中的所有槽函数都在工作线程中执行
    - 可以安全地执行阻塞性的 I/O 操作
    - 不会阻塞主线程的 UI 响应
    """
    
    # 📤【信号定义】向主线程发送状态和数据
    signal_serial_button_pushed = pyqtSignal(int)    # 状态更新信号（state: 0=关闭, 1=打开, 2=错误）
    signal_update_textbrowser = pyqtSignal(list)    # 数据更新信号（data: 接收到的数据列表）
    
    # 📡【信号定义】接收主线程的操作请求
    signal_Serialstart_function = pyqtSignal()       # 串口初始化信号
    signal_push_open_serial_button = pyqtSignal(dict)  # 串口操作信号（parameter: 串口参数字典）
    
    def __init__(self):
        super().__init__()
        
        # 串口对象 - 在工作线程中使用
        self.Serial = QSerialPort()
        
        # 状态管理：0=关闭, 1=打开, 2=错误
        self.state = 0
        
        # 串口参数缓存
        self.serial_params = {}
        
        # 打印线程信息用于验证
        print(f"工作线程初始化 - 线程ID: {threading.get_ident()}")
    
    def Serial_Init_function(self):
        """
        🔧 工作线程初始化函数 - 在工作线程中执行
        
        【执行环境】
        ✅ 此函数在工作线程中执行（由 moveToThread() 保证）
        ✅ 可以安全地创建和配置串口对象
        """
        print("工作线程初始化完成")
        print(f"串口工作线程ID: {threading.get_ident()}")
        
        # 配置串口数据接收
        self.Serial.readyRead.connect(self.Serial_receive_data)
    
    def slot_push_open_serial_button(self, parameter):
        """
        🧵 工作线程中执行 - 串口操作槽函数
        
        【执行环境】
        ✅ 此函数在工作线程中执行（由 moveToThread() 保证）
        ✅ 可以安全地执行阻塞性的串口 I/O 操作
        ✅ 不会阻塞主线程的 UI 响应
        
        Args:
            parameter (dict): 串口配置参数
                - comboBox_port: 串口名称
                - comboBox_baudrate: 波特率
                - comboBox_databit: 数据位
                - comboBox_stopbit: 停止位
                - comboBox_checkbit: 校验位
                - comboBox_flowctrl: 流控制
        """
        print(f"工作线程执行串口操作 - 线程ID: {threading.get_ident()}")
        
        # 缓存串口参数
        self.serial_params = parameter.copy()
        
        if self.state == 0:
            # 🔧【串口打开流程】配置并尝试打开串口
            try:
                # 设置串口参数
                self.Serial.setPortName(parameter['comboBox_port'])
                self.Serial.setBaudRate(parameter['comboBox_baudrate'])
                
                # 设置数据位
                data_bits_map = {5: QSerialPort.Data5, 6: QSerialPort.Data6, 
                               7: QSerialPort.Data7, 8: QSerialPort.Data8}
                self.Serial.setDataBits(data_bits_map.get(parameter['comboBox_databit'], QSerialPort.Data8))
                
                # 设置停止位
                stop_bits_map = {1: QSerialPort.OneStop, 1.5: QSerialPort.OneAndHalfStop, 
                               2: QSerialPort.TwoStop}
                self.Serial.setStopBits(stop_bits_map.get(parameter['comboBox_stopbit'], QSerialPort.OneStop))
                
                # 设置校验位
                parity_map = {0: QSerialPort.NoParity, 1: QSerialPort.EvenParity, 
                            2: QSerialPort.OddParity, 3: QSerialPort.MarkParity, 
                            4: QSerialPort.SpaceParity}
                self.Serial.setParity(parity_map.get(parameter['comboBox_checkbit'], QSerialPort.NoParity))
                
                # 设置流控制
                flow_control_map = {0: QSerialPort.NoFlowControl, 1: QSerialPort.HardwareControl, 
                                   2: QSerialPort.SoftwareControl}
                self.Serial.setFlowControl(flow_control_map.get(parameter['comboBox_flowctrl'], QSerialPort.NoFlowControl))
                
                # 尝试打开串口
                if self.Serial.open(QSerialPort.ReadWrite):
                    self.state = 1
                    print(f"串口已打开: {parameter['comboBox_port']}")
                    
                    # 📤【跨线程信号通知】向主线程报告状态变化
                    self.signal_serial_button_pushed.emit(self.state)
                else:
                    print(f"串口打开失败: {parameter['comboBox_port']}")
                    self.state = 2
                    
                    # 📤【跨线程信号通知】向主线程报告错误状态
                    self.signal_serial_button_pushed.emit(self.state)
                    
            except Exception as e:
                print(f"串口操作异常: {str(e)}")
                self.state = 2
                
                # 📤【跨线程信号通知】向主线程报告异常状态
                self.signal_serial_button_pushed.emit(self.state)
                
        else:
            # 🔧【串口关闭流程】关闭串口连接
            try:
                if self.Serial.isOpen():
                    self.Serial.close()
                    print(f"串口已关闭: {parameter['comboBox_port']}")
                    
                self.state = 0
                
                # 📤【跨线程信号通知】向主线程报告状态变化
                self.signal_serial_button_pushed.emit(self.state)
                
            except Exception as e:
                print(f"串口关闭异常: {str(e)}")
                self.state = 2
                
                # 📤【跨线程信号通知】向主线程报告异常状态
                self.signal_serial_button_pushed.emit(self.state)
    
    def Serial_receive_data(self):
        """
        📤 串口数据接收函数 - 在工作线程中执行
        
        【执行环境】
        ✅ 此函数在工作线程中执行（由 readyRead 信号触发）
        ✅ 可以安全地读取串口数据（阻塞操作）
        ✅ 不会阻塞主线程的 UI 响应
        
        【数据流向】
        1. 串口设备 → QSerialPort (工作线程)
        2. 数据到达 → readyRead 信号
        3. 数据读取 → Serial_receive_data() 方法 (在工作线程中)
        4. 数据封装 → signal_update_textbrowser 信号
        5. 线程间传递 → 主线程接收到信号 (Qt 自动处理)
        6. UI 更新 → 在主线程中更新显示区域 (线程安全)
        """
        try:
            # 读取可用数据
            if self.Serial.bytesAvailable() > 0:
                # 读取串口数据
                data = self.Serial.readAll()
                
                # 将 QByteArray 转换为字节列表
                data_list = []
                for byte in data:
                    data_list.append(byte)
                
                print(f"接收到数据: {len(data_list)} 字节")
                
                # 📤【跨线程信号发送】将数据发送到主线程进行显示
                self.signal_update_textbrowser.emit(data_list)
                
        except Exception as e:
            print(f"数据接收异常: {str(e)}")
    
    def close_serial(self):
        """
        🔧 安全关闭串口 - 在工作线程中执行
        
        【执行环境】
        ✅ 此函数在工作线程中执行
        ✅ 可以安全地关闭串口连接
        """
        try:
            if hasattr(self, 'Serial') and self.Serial.isOpen():
                self.Serial.close()
                self.state = 0
                print("串口已安全关闭")
                
        except Exception as e:
            print(f"串口关闭异常: {str(e)}")
    
    def __del__(self):
        """
        🔧 析构函数 - 确保资源正确释放
        """
        self.close_serial()