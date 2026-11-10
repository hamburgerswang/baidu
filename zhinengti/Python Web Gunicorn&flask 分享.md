> 原文：https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/KeF15lNOtH/-UXFkEkRyR/4eIOs9xLhLhaWO

Python Web Gunicorn&flask 分享

很多人刚开始使用 Flask 时，会直接运行：

```python
flask run
```
看到服务起来了就以为部署完成了。

但在**生产环境**中，这种方式是不安全也不高效的。

要理解原因，我们需要了解几个关键概念：**Python的并发**、**WSGI、Flask、Gunicorn**。

# 一、Python的并发
## 1.CPython是什么？
**CPython是Python的“官方”、最广泛使用的解释器实现。**

 CPython执行代码的过程有一个关键步骤：

* 它首先会把你的Python源代码（`.py`文件）编译成一种叫做 **字节码** 的中间格式。这个字节码会被保存在 `__pycache__` 目录下的 `.pyc` 文件中。
* 然后，CPython的 **虚拟机**（不是VMware那种，而是CPython内部的一个执行引擎）会读取这个字节码，并一条一条地执行它。

所以过程是：**Python源代码 (.py) -> 编译成字节码 (.pyc) -> CPython虚拟机执行字节码 -> 运行**

## 2.GIL 是什么？
**GIL**，全称 **Global Interpreter Lock**，**全局解释器锁**。

它并不是 Python 语言本身的特性，而是 **CPython 解释器**（Python 最主流、官方的解释器）为了实现内存管理（主要是垃圾回收）的线程安全而引入的一个机制。

GIL 是一个锁，或者**一把锁**，这把锁**加载了 Python 的解释器上（cPython）**，它要求任何 Python 代码在执行的时候需要先申请这把锁，否则就别想执行。

## 3.为什么 Python 要引入 GIL
### 3.1.Python的垃圾回收（引用计数）
Python 使用引用计数来进行内存管理（垃圾回收）。引用计数就是说 Python 里创建的所有对象，Python 都有一个变量（reference count）记录着当前有多少个引用指向了这个对象，当引用数变成 0 的时候，Python 就会回收这个对象所占用的内存。

```python
>>> import sys
>>> a = []
>>> b = a
>>> sys.getrefcount(a)
3
```
在上面这个简单的例子中，指向这个空 list 对象的引用计数是 3。a，b 和 传入sys.getrefcount 的参数（传参的时候会拷贝一次地址）这 3 个对象指向了空 list。

Python 的引用计数需要**避免资源竞争的问题**，我们需要在**有两个或多个线程**同时增加或减少引用计数的情况下，依然**保证引用计数的结果是正确的**。

但是，如果我们对每一个对象或者每一组对象都增加锁，这就意味在在你的 Python 程序中有很多个锁同时存在。**多个锁同时存在会有其他的风险--死锁。**

除此之外，性能下降也是多个锁存在的一大弊端。因为**申请锁和释放锁都是一笔不小的开销**。

# 二、Python WSGI
Python Web模式：Web Server（Gunicorn）+ 框架（Flask）+ 中间协议（WSGI）。

Python Web生态的并发解决方案是“多进程 + WSGI”，不是“线程/协程内置”

## 1.为什么需要 WSGI？
不同的服务器（如 Apache、Nginx、Gunicorn）和不同的 Python 框架（如 Flask、Django）之间，通信协议并不统一。

于是 Python 社区制定了一个标准接口，让二者能对接，这个标准就是 **WSGI**。

## 2.什么是 WSGI？
#### 2.1.1.定义
**WSGI (Web Server Gateway Interface)** 是 Python Web 应用与 Web 服务器之间的通信协议标准，或框架之间的一种简单而通用的接口

它定义了一个统一接口，让：

* Web 服务器（如 Nginx + Gunicorn、uWSGI）
* Web 应用框架（如 Flask、Django、FastAPI）

能够**解耦**并互相通信。

#### 2.1.2.诞生背景
在 WSGI 出现之前：

* 每个 Python Web 框架都有自己的服务器接口
* Django、Flask、Pyramid 等框架无法共享服务器
* 开发者被限制在特定的服务器-框架组合中

#### 2.1.3.WSGI架构
|角色|描述|举例|
|-|-|-|
|**WSGI Server**|负责与操作系统和网络打交道，接收 HTTP 请求，调用应用并返回响应|Gunicorn、uWSGI、Waitress|
|**WSGI Application**|负责业务逻辑：路由、数据库操作、返回内容|Flask、Django、FastAPI|

```
   [客户端浏览器]
        │
        ▼
     [Nginx] (反向代理)
        │
        ▼
    [Gunicorn] (WSGI Server)
        │
        ▼
    [Flask App] (WSGI Application)

```
## 3.WSGI规范细节
一个 WSGI 应用程序本质上是一个**可调用对象**（callable），它必须：

* 接受 **两个参数**：

    1. `environ`：一个包含  WSGI 特定变量的字典
    2. `start_response`：一个可调用的函数

* 调用一次 `start_response` 函数，传入 HTTP 状态码和响应头
* 返回一个 **可迭代对象**，该对象产生字节字符串（bytestrings），即响应体

## 4.为什么其他语言（Go / Node.js / Java）不需要 WSGI？
因为这些语言 **内置了成熟的 Web 服务器模型。**

### 4.1.Go：语言层面带了原生 HTTP Server
Go 自带非常完善的 HTTP 服务器：

```
http.ListenAndServe(":8080", handler)
```
* 高并发
* 多线程（goroutine）
* 调度器由 Go runtime 提供
* 性能非常高

**Go 本身就能直接处理高并发 HTTP 请求，不需要额外的 “WSGI 规范”。**

### 4.2.为什么 Python 没有内置 HTTP Server？
因为 Python 在设计时：

* 是通用脚本语言
* 不是为 Web 定制的
* 没有统一的并发模型（线程、协程都是后来补的）
* 没有原生异步 I/O（asyncio 是 Python 3.4 之后才有）

所以需要 Web Server（Gunicorn）+ 框架（Flask）+ 中间协议（WSGI）。

# 三、Flask
#### 1.Flask简介
**Flask** 是一个轻量级的 Web 框架，采用 Python 编写，遵循 WSGI（Web Server Gateway Interface）规范。它为开发者提供了快速构建 Web 应用的基本功能，如路由、模板引擎和请求处理等，同时保持极高的灵活性和可扩展性。与 **Django** 等“全栈”框架不同，Flask 本身提供的功能较少，更多的是依赖于第三方扩展或开发者自行集成所需的功能。

#### 2.Flask 自带的开发服务器为什么不能直接用于生产？
Flask 自带了一个基于 **Werkzeug** 的简单服务器，用于**开发调试**。

但它 **不是** 一个真正的生产级 WSGI 服务器。

#### 原因如下：
|问题点|说明|
|-|-|
|单线程/单进程|只能处理一个请求，无法支撑并发|
|不支持多进程管理|无法充分利用多核 CPU|
|异常恢复能力差|程序崩溃后不会自动重启|
|安全性不足|没有针对 DDoS、超时、内存限制等机制|
|不适合负载均衡|无法与 Nginx 等服务器良好集成|

Flask 官方文档也明确指出：

> “The built-in server is not suitable for production. Use a production WSGI server instead.”


Flask 自带的服务器是基于 **Werkzeug** 的，它主要用于开发阶段，能够帮助开发者快速验证代码和进行调试。使用 `app.run()` 启动的服务器是单线程且非常简单，适合在开发过程中使用，但它存在一些重要的缺点，使得它无法胜任生产环境的任务

##### 2.1 性能问题
Flask 自带的服务器是单线程的，意味着它只能处理一个请求，无法同时处理多个请求。在高并发场景下，多个请求会被排队等待处理，这会导致性能瓶颈，无法满足大规模生产环境的需求。

##### 2.2 缺乏并发支持
Flask 的开发服务器没有内置并发处理能力，无法有效利用多核 CPU。尽管可以通过一些配置修改让它支持多线程，但 Flask 开发服务器本质上并不是为了高并发设计的，性能和稳定性无法与专门的生产级 Web 服务器（如 Gunicorn 或 uWSGI）相提并论。

##### 2.3 缺少容错性
Flask 的开发服务器也没有提供类似于生产环境中所需的错误处理、重启策略和日志管理功能。如果在生产环境中发生了崩溃或死锁，Flask 的开发服务器不能自动恢复，也无法有效地管理多个进程，造成服务的不可用。

# 四、Flask是如何实现WSGI的
## 1.Python的__call__方法
如果一个类实现了 `__call__(self, ...)` 方法，那么它的实例就可以像下面这样使用：

```python
obj = MyClass()
obj() 
```
也就是说：**类的实例变成了“可调用对象”（callable object）**。

`__call__` 让实例可以像函数一样被调用，它是 Python 实现可调用对象（callable object）的机制

## 2.Flask的__call__
在 Flask 中，WSGI 接口的定义主要体现在 Flask 应用对象本身就是一个 WSGI 可调用对象。

具体来说，Flask 类实现了 `__call__` 方法，该方法接受两个参数：`environ` 和 `start_response`。当 Flask 应用对象被调用时，它会调用 `wsgi_app` 方法，该方法处理请求并返回响应。

```python
class Flask:
    def __call__(self, environ, start_response):
        """WSGI 服务器调用入口点"""
        return self.wsgi_app(environ, start_response)
    
    def wsgi_app(self, environ, start_response):
        # 1. 创建请求上下文
        ctx = self.request_context(environ)
        ctx.push()
        
        try:
            try:
                # 2. 请求预处理
                response = self.full_dispatch_request()
            except Exception as e:
                # 3. 错误处理
                response = self.make_response(self.handle_exception(e))
            
            # 4. 返回响应
            return response(environ, start_response)
        finally:
            # 5. 清理工作
            ctx.pop()
```


# 五、Gunicorn 是什么？
**Gunicorn (Green Unicorn)** 是一个高性能的 **WSGI HTTP Server**，专门用于运行 Python Web 应用（Flask、Django、FastAPI 等）。

Gunicorn 以其**高性能、易于配置、跨平台**的特点，在生产环境中被广泛使用。

[https://github.com/benoitc/gunicorn](https://github.com/benoitc/gunicorn)

### 1.Gunicorn 的工作原理
Gunicorn 是一个基于 **多进程** 模型的 WSGI 服务器。

它主要做的事情是：

* 监听端口，接收来自客户端（浏览器）的 HTTP 请求。
* 创建多个 worker 进程来处理并发请求。
* 每个 worker 进程负责处理一个 HTTP 请求，并返回响应。
* 进程之间的通信与任务分配由 Gunicorn 内部管理，确保负载均衡。

### 2.Gunicorn 工作流程
1. **Gunicorn 启动 **Gunicorn 启动时，会根据配置启动若干个 **worker 进程**，每个 worker 都是一个独立的 Python 进程。
2. **接收请求 **Web 服务器（如 Nginx）将 HTTP 请求转发给 Gunicorn，Gunicorn 分配给空闲的 worker 进程进行处理。
3. **处理请求 **Worker 进程通过 WSGI 协议调用 Flask（或其他框架）应用程序，处理业务逻辑，生成响应数据。
4. **返回响应 **处理完请求后，worker 进程将响应返回给 Web 服务器，最终由 Web 服务器发送到客户端。
5. **管理进程 **Gunicorn 会根据配置自动管理 worker 进程的生命周期，处理如进程崩溃后的重启、进程数的自动调整等。

### 3.启动示例
```
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
其中：

* `-w 4` 表示启用 4 个 worker 进程
* `-b` 指定绑定地址和端口
* `app:app` 表示 `app.py` 文件中的 Flask 实例对象名

### 4.Gunicorn 核心组件
|组件模块|核心职责|关键实现机制或特点|
|-|-|-|
|**Master进程**|作为管理进程，负责worker进程的生命周期管理（启动、维护数量、关闭）、信号处理和应用热更新。|使用**信号机制**与外部交互，通过**管道（Pipe）和select**实现事件循环与唤醒机制。|
|**Worker进程**|由Master进程通过**pre-fork**方式创建，**独立处理**实际的HTTP请求。|不同类型的Worker（如Sync, Gevent）处理并发的方式不同；Worker进程会**加载WSGI应用**。|
|**通信与同步**|Master进程需要知道Worker进程的健康状态。|早期通过**临时文件时间戳**实现心跳机制；Worker进程定期"触碰"文件来表明存活。|
|**Socket监听**|处理来自客户端的网络连接。|Master进程创建监听Socket；Worker进程**继承**这些Socket，在各自的循环中**竞争接受**新连接。|

```python
          ┌────────────┐
          │   Nginx    │
          └────┬───────┘
               │
         ┌─────▼─────┐
         │  Gunicorn │
         │   Master  │
         └─────┬─────┘
       ┌────────┴────────┐
       │                 │
┌──────▼───────┐   ┌─────▼──────┐
│ Worker #1    │   │ Worker #2  │
│  (WSGI App)  │   │ (WSGI App) │
└──────────────┘   └────────────┘

```
### 5.Gunicorn 的进程模型
Gunicorn 采用 **Pre-fork 模型**，即：

Master 进程预先 fork 多个 Worker 进程，共享同一个监听 socket。

```python
 # gunicorn/arbiter.py
def spawn_worker(self):
    self.worker_age += 1
    worker = self.worker_class(self.worker_age, self.pid, self.LISTENERS, self.app, self.timeout, self.cfg, self.log)

    pid = os.fork()   # 关键点！！！
    if pid != 0:
        # master 进程继续执行
        self.WORKERS[pid] = worker
        return pid

    # 子进程（worker）执行这里
    worker.init_process()

```
##### 5.1.优点
* 充分利用多核 CPU；
* 各 worker 相互隔离，单个崩溃不会影响整体；
* Master 可平滑重启 workers 实现无中断升级。

##### 5.2. 启动流程
1. Master 创建监听 socket；
2. 根据配置 fork 出 N 个 Worker；
3. 每个 Worker：

    * 接收 Master 传入的 socket；
    * 调用 `accept()` 接收连接；
    * 解析 HTTP 请求并调用 WSGI 应用；

4. Worker 返回响应；
5. Master 监控 Worker 状态，必要时重启。

### 6.Gunicorn 的worker类型
Gunicorn 提供多种 Worker 模型以适应不同场景：

|worker|类型|并发来源|特点|
|-|-|-|-|
|**sync**|进程|1 worker = 1 请求|最可靠但并发低|
|**gthread**|进程 + 多线程|线程|WSGI 下 I/O 并发最稳定|
|**gevent**|协程 + 单线程|greenlet|高并发但有 monkey patch 风险|
|**eventlet**|协程|greenlet|不常用|

`worker-class` 选项允许你指定要使用的 Worker 类型。不同的 Worker 类型有不同的并发模型和适用场景。

* **同步（sync）**：默认类型。
* **Gevent**：基于协程的并发模型，适用于 IO 密集型任务（如网络请求、数据库查询等）。
* **Eventlet**：与 Gevent 类似，也是基于协程的并发模型。
* **TornadoWorker**：基于 Tornado 框架的 Worker 类型，适用于高并发的异步场景。

### 7.Gunicorn 的优点
|优点|说明|
|-|-|
|**多进程模型**|支持多 worker，有效利用多核 CPU，提升并发性能|
|**自动重启与进程管理**|进程崩溃自动恢复，保证服务可用性|
|**高可扩展性**|可与 Nginx、systemd、Supervisor 等无缝配合|
|**安全可靠**|支持超时、连接数限制、守护进程运行等机制|
|**性能优秀**|纯 Python 实现，启动快、资源占用少|
|**广泛兼容**|兼容各种 WSGI 框架（Flask、Django、FastAPI 等）|