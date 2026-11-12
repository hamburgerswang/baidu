vLLM 模型自部署：原理与部署指南



## 1. 端口架构与请求原理
### 1.1 一个 Pod 内跑了几个进程？
同一个容器（Pod）内并存 3 类进程，对外/对内共暴露 **4 个端口**：

* **Go 服务进程**（GDP 框架）：占用 `Main` + `Admin` 两个端口
* **vLLM 推理进程**：占用 `GRPC` 端口（名字叫 GRPC，实际是 vLLM 的 HTTP 端口）
* **图片处理 Python 进程**（`img_process.py`）：占用 `PYSERVER` 端口

### 1.2 四个端口分别是什么
|端口名|环境变量|进程|作用|
|-|-|-|-|
|**Main**|`LRS_RESOURCE_PORT_NAMING_MAIN`|Go 服务|对外主入口，接收业务请求（`/v1/chat/completions`、`/api/chat/image` 等）|
|**Admin**|`LRS_RESOURCE_PORT_NAMING_ADMIN`|Go 服务|管理/监控端口（`/metrics`、`/debug/pprof/`、探活面板）|
|**GRPC**|`LRS_RESOURCE_PORT_NAMING_GRPC`|vLLM|vLLM 推理 HTTP 端口，Go 服务把请求转发到这里；健康检查 `/health`|
|**PYSERVER**|`LRS_RESOURCE_PORT_NAMING_PYSERVER`|Python|图片预处理服务，健康检查 `/health`|

> 端口名来自 `conf/app.toml` 的 `[[Meta.Ports]]` 定义；监听地址在 `conf/server.toml`（`HTTPServer.Listen = tcp@0.0.0.0:{port.Main}`、`AdminServer.Listen = ...{port.Admin}`）。
### 1.3 国内 vs 国外：端口从哪来（核心区别）
四个端口的"名字和职责"国内外**完全一致**，区别只在于**端口号怎么拿到**：

* **国内（端口段动态注入）**：CNAP「命名端口」模式会在容器启动时自动注入 `LRS_RESOURCE_PORT_NAMING_*` 环境变量，端口号由平台动态分配（开发默认值：Main=8083、Admin=8084）。Go 服务和 `start.sh` 直接读环境变量即可。

![](image/22b2a23012864f75bc42888fb68ed6e4.png)
* **国外（静态兜底）**：海外 CNAP「命名端口-静态」模式**不注入** `LRS_RESOURCE_PORT_NAMING_*`。所以 `bin/abroad/*/start.sh` 里对四个变量做了写死兜底：

![](image/b971a3cfddba42df80465e815264c72e.png)
```bash
# bin/abroad/dh_4b_base/start.sh
export LRS_RESOURCE_PORT_NAMING_MAIN=${LRS_RESOURCE_PORT_NAMING_MAIN:-8000}
export LRS_RESOURCE_PORT_NAMING_ADMIN=${LRS_RESOURCE_PORT_NAMING_ADMIN:-8001}
export LRS_RESOURCE_PORT_NAMING_GRPC=${LRS_RESOURCE_PORT_NAMING_GRPC:-8002}
export LRS_RESOURCE_PORT_NAMING_PYSERVER=${LRS_RESOURCE_PORT_NAMING_PYSERVER:-8003}
```
含义：`${VAR:-默认值}` = 平台若已注入就用平台的，没注入就用静态默认（8000~8003）。这样海外静态端口场景下服务也能正常起。



### 1.4 别人访问 Main 端口，怎么请求到模型上？（请求链路图）
外部调用方**只访问 Main 端口**，Go 服务在同一 Pod 内把请求转发给 vLLM 的 GRPC 端口，拿到推理结果再返回。全链路如下：

```mermaid
flowchart TD
    Client["外部调用方"]

    subgraph Pod["同一个 CNAP Pod（一台机器）"]
        direction TB
        Go["Go 服务进程<br/>Main 端口 / Admin 端口"]
        Vllm["vLLM 推理进程<br/>GRPC 端口 /v1/chat/completions"]
        Py["图片处理进程<br/>PYSERVER 端口"]
    end

    Client -->|"HTTP 请求 Main 端口<br/>/v1/chat/completions"| Go
    Go -->|"本机转发 localhost:GRPC 端口<br/>RAL HTTP 调用"| Vllm
    Go -.->|"图片场景先调用"| Py
    Vllm -->|"推理结果"| Go
    Go -->|"响应（可读写缓存）"| Client
```
代码路径（对应上图）：

* 路由注册：`servers/httpserver/router.go` → `/v1/chat/completions` 绑定 `controller.CallVllmWithBody`
* 控制层：`servers/httpserver/controller/proxy.go` → 读 body、查缓存、经**并发限流器** `resource.VCLimit.Execute` 调用模型、写缓存
* 服务层：`model/service/proxy/vllm.go` → `vllmPostRal()` 读取 `LRS_RESOURCE_PORT_NAMING_GRPC`，拼出 `本机IP:GRPC端口`，用 RAL 发 HTTP 到本地 vLLM

一句话原理：**Main 是门面，GRPC 是真正的模型**。Go 服务只在同一 Pod 内做转发、缓存、限流、协议适配，从不跨机器调模型。



### 1.5 外部调用方是怎么"找到"Main 端口的（入口差异）
> 说明：Pod 内的转发链路（1.4）已由代码确认；**下面的对外入口方式属于平台侧接入**，请以 CNAP 控制台配置为准，本节结论待你用截图核对。
* **国内**：走 CNAP 服务发现 / BNS / 域名，调用方通过服务名寻址，平台把流量路由到 Main 端口（动态端口对调用方透明）。

![](image/9d020485a8af4678b9461b5b2cbef578.png)
* **国外**：走静态 IP / 网关，Main 端口固定（默认 8000），调用方按约定的静态地址访问。

![](image/4172901c54124581ad9612a4bfd4a61e.png)
```mermaid
flowchart LR
    subgraph 国内
        C1["调用方"] -->|"服务名/BNS/域名"| SD["CNAP 服务发现"] -->|"路由到动态 Main 端口"| M1["Main"]
    end
    subgraph 国外
        C2["调用方"] -->|"静态 IP / 网关"| M2["Main = 8000（静态）"]
    end
```
> 【需你确认/提供截图 A】CNAP「服务发现 / 访问入口」配置页，国内外各一张，用来最终敲定本节写法。
---

## 2. 部署步骤（重点讲 CNAP 平台配置与国内外差异）


### 2.1 前置动作
* 模型策略已上传 BOS：
    * `代码写到./upload_model.sh <本地模型路径> <模型名> <版本号>`，

* 确认能部署成功镜像
    * 可以提前做好


![](image/6e57428f1e1b4d06b1a553272483fd83.png)
    * 也可以提前写好放到`docekrfile、build.sh` 。

### 2.2 整体部署流程
```mermaid
flowchart TD
    A["选择/编写对应模型的 start.sh<br/>国内: 根目录 start.sh；国外: bin/abroad/&lt;模型&gt;/start.sh"] --> B["确认镜像已编译产出"]
    B --> C["CNAP 创建应用/服务"]
    C --> D{"国内 or 国外？"}
    D -->|国内| E["端口：命名端口（动态）<br/>不用配端口号，平台注入 LRS_RESOURCE_PORT_NAMING_*"]
    D -->|国外| F["端口：命名端口-静态<br/>Main/Admin/GRPC/PYSERVER = 8000/8001/8002/8003"]
    E --> G["配置探活（Main + GRPC + PYSERVER）"]
    F --> G
    G --> H["配置资源：GPU 卡数、显存、镜像地址"]
    H --> I["部署上线 → Pod 拉起"]
    I --> J["容器内 start.sh：下载模型 → 起 vLLM → 起图片服务 → 探活/预热"]
    J --> K["探活通过 → 服务进入可用状态"]
```
### 2.3 国内 vs 国外：部署差异对照
|差异点|国内|国外（abroad）|
|-|-|-|
|端口模式|CNAP 命名端口（动态注入）|CNAP 命名端口-静态（不注入）|
|端口号|平台分配，无需手填|静态写死 8000/8001/8002/8003（`start.sh` 兜底）|
|start.sh 位置|仓库根目录 `start.sh`|`bin/abroad/<模型>/start.sh`|
|vLLM 启动方式|前台 `&` 后台运行|`nohup ... > vllm.log 2>&1 &`，日志落文件|
|探活|`start.sh` 内联轮询 GRPC `/health`|独立 `bin/abroad/probe.sh`，同时探 Main/GRPC/PYSERVER|
|预热 Warmup|无|有（发短/长两条 prompt 消除首包 triton autotune 延迟 >55s）|
|探活地址|`http://APPSPACE_POD_IP:GRPC/health`|Main `/alive/ping`、GRPC `/health`、PYSERVER `/health`|



---

## 3. 依赖清单
* **BOS 对象存储**：模型权重存储与拉取（`upload_model.sh` / `download_model.sh`，凭证在 `~/.go-bcecli/credentials`）。

![](image/0ddf21f1db774c4d90f9582615d9b1c3.png)
* **CNAP 平台**：容器调度、端口映射、探活、扩缩容。

![](image/b2fb385153a64ab281c56633f81a7e52.png)
![](image/4ff5f4d49a144ab6ac5f01798a317e5c.png)
![](image/2acb11460016488c8aac9791ec241495.png)
![](image/b509b756b94e464b9042e683adebcfe6.png)
![](image/f214e961b3524a0fb7668181eccf7e14.png)


* **GPU + CUDA**：`start.sh` 用 `nvidia-smi --list-gpus` 统计卡数作为 `--tensor-parallel-size`；基础镜像 CUDA 12.6。

![](image/159213f512a9419198f43550226d922c.png)
* **vLLM**：推理引擎，具体版本需要测试。
* **图片处理服务**：`img_process.py`（Flask），仅图片类模型需要。
* **环境变量**：`LRS_RESOURCE_PORT_NAMING_{MAIN,ADMIN,GRPC,PYSERVER}`、`APPSPACE_POD_IP`。

---

## 4.混布模型
* 太复杂先不展开
