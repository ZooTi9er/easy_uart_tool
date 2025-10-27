# Easy UART Tool - 基于 PyQt5 的专业串口调试工具

一个基于 PyQt5 的专业 UART 串口调试工具，展示了多线程架构的最佳实践。该项目采用 "Worker + moveToThread" 模式，特别适合学习 GUI 应用程序的多线程编程。

## 🌟 核心特性

- ✅ **多线程架构**: UI线程与串口处理线程完全分离
- ✅ **响应式UI**: 串口通信不会阻塞界面操作
- ✅ **实时数据处理**: 串口数据的实时接收和显示
- ✅ **线程安全通信**: 通过 PyQt5 信号槽机制实现跨线程安全通信

## 🏗️ 架构设计

### 多线程架构模式

项目采用 PyQt5 推荐的 "Worker + moveToThread" 多线程设计模式：

🧵 **主线程 (UI Thread)**:
- 负责用户界面渲染和事件处理
- 处理用户交互（按钮点击、菜单选择等）
- 更新数据显示区域（线程安全操作）
- 管理应用程序生命周期

🧵 **工作线程 (Serial Thread)**:
- 专门处理串口通信任务（阻塞操作）
- 监听串口数据到达事件
- 管理串口连接状态
- 执行数据收发操作

### 跨线程通信机制

线程间通过 PyQt5 的信号槽机制安全通信：

📡 **主线程 → 工作线程**（操作请求信号）:
- `signal_Serialstart_function` → 串口初始化请求
- `signal_push_open_serial_button` → 串口操作请求

📤 **工作线程 → 主线程**（状态和数据信号）:
- `signal_serial_button_pushed` → 状态更新通知
- `signal_update_textbrowser` → 数据更新通知

## 🚀 快速开始

### 环境配置

```bash
# 使用 conda 创建环境
conda create -n easy_uart_env python=3.11
conda activate easy_uart_env

# 安装依赖 (推荐使用 conda)
conda install pyqt5 pyserial
pip install PyQt5-tools  # 用于 Qt Designer 等开发工具

# 或者使用 pip
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```

### UI 开发工作流

```bash
# 1. 使用 Qt Designer 编辑界面
designer form.ui

# 2. 重新生成 UI 代码 (每次修改 form.ui 后必须执行)
pyuic5 form.ui -o form.py

# 3. 运行应用测试
python main.py
```

## 📁 项目结构

```
easy_uart_tool/
├── main.py              # 主程序，包含 InitForm 类和多线程初始化
├── serial_thread.py     # 串口工作线程模块，包含 Serial_Qthread_function 类
├── form.py             # 自动生成的 UI 代码（不要直接编辑）
├── form.ui             # Qt Designer 界面定义文件
├── requirements.txt    # 项目依赖列表
├── README.md           # 项目说明文档
└── CLAUDE.md           # Claude Code 项目指导文档
```

## 🔧 串口配置

### 当前固定参数
- 波特率: 256000 bps
- 数据位: 8
- 停止位: 1
- 校验位: 无校验
- 流控制: 无

### 参数扩展
如需添加可配置的串口参数，可以修改 `main.py` 的 `open_serial()` 方法。

## 📖 技术深度解析

### 多线程初始化流程

项目中的4个关键线程创建步骤（main.py:77-95）：

```python
# 1. 创建工作线程对象
self.Serial_QThread = QtCore.QThread()

# 2. 创建工作对象
self.Serial_Qthread_function = Serial_Qthread_function()

# 3. 将工作对象移动到工作线程（核心步骤！）
self.Serial_Qthread_function.moveToThread(self.Serial_QThread)

# 4. 启动工作线程的事件循环
self.Serial_QThread.start()
```

### 跨线程信号槽连接

建立了4个重要的通信桥梁（main.py:97-120）：

```python
# 1. 线程内部初始化连接
self.Serial_Qthread_function.signal_Serialstart_function.connect(
    self.Serial_Qthread_function.Serial_Init_function
)

# 2. 发送串口操作请求连接
self.Serial_Qthread_function.signal_push_open_serial_button.connect(
    self.Serial_Qthread_function.slot_push_open_serial_button
)

# 3. 接收工作线程状态更新
self.Serial_Qthread_function.signal_serial_button_pushed.connect(
    self.slot_signal_serial_button_pushed
)

# 4. 接收工作线程数据更新
self.Serial_Qthread_function.signal_update_textbrowser.connect(
    self.slot_update_textbrowser
)
```

### 线程安全原则

❗ **重要约束**：
- 禁止在工作线程中直接操作 UI 组件
- 所有界面更新必须在主线程中执行
- 使用信号槽机制确保线程间安全通信

## 🛠️ 开发指南

### UI 开发
1. **架构原则**: 采用 **单继承 + UI实例** 模式，所有UI组件通过 `self.ui` 访问
2. **不要直接编辑 `form.py`**，此文件由 `pyuic5` 从 `form.ui` 自动生成
3. 修改界面应该编辑 `form.ui` 文件，然后执行 `pyuic5 form.ui -o form.py`
4. UI 组件只能在主线程中访问和修改（线程安全原则）

### 多线程开发
1. **线程职责分离**:
   - 主线程负责 UI 渲染和用户交互
   - 工作线程负责串口 I/O 操作
2. **线程安全**:
   - 确保串口操作在工作线程中执行
   - 所有 UI 更新必须在主线程中执行
3. **信号槽通信**:
   - 跨线程通信只能通过 PyQt5 信号槽机制

## 🎯 学习要点

### 多线程学习路径
1. 理解餐厅类比（前台服务员 vs 后厨厨师）
2. 学习4个关键线程创建步骤
3. 掌握4个跨线程通信桥梁
4. 实践信号槽机制的使用
5. 体验线程安全的UI更新

### 最佳实践
- 遵循单一职责原则
- 使用类型提示和文档字符串
- 添加适当的错误处理
- 保持代码注释的一致性

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👨‍💻 作者

**zootiger** - [GitHub](https://github.com/ZooTi9er)

## 🙏 致谢

- PyQt5 官方文档
- pyserial 库开发者
- 开源社区的支持