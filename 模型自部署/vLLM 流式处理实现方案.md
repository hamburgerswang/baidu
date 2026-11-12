vLLM 流式处理实现方案

# vLLM 流式处理实现方案
## Context（背景）
当前 vLLM 服务所有 API 端点都是**非流式响应**，需要等待模型生成完整结果后一次性返回。这导致：

* **用户体验差**：长文本生成时等待时间长，无法实时看到生成过程
* **无法适配流式场景**：无法对接需要实时响应的前端应用（如打字机效果）
* **资源浪费**：即使客户端中途取消，服务端仍继续生成完整结果

虽然请求结构中已定义 `Stream` 字段（[library/types/request.go:8](library/types/request.go#L8)），但从未实现流式逻辑。所有控制器都使用 `ghttp.NewJSONResponse()` 一次性返回完整 JSON。

**本方案目标**：在现有接口基础上添加流式支持，通过 `stream=true` 参数控制，遵循开闭原则，最小化代码改动。

---

## 设计原则
### 1. 开闭原则（Open-Closed Principle）
* ✅ **对扩展开放**：新增流式处理方法和逻辑
* ✅ **对修改关闭**：不修改原有非流式方法的核心逻辑
* ✅ **策略模式**：通过 `stream` 参数在入口处分发到不同处理器

### 2. 路径不变原则
* ✅ 现有路径保持不变：`/api/chat/text`、`/api/chat/image`、`/v1/chat/completions`
* ✅ 通过请求体中的 `stream` 字段判断流式/非流式
* ✅ 向后兼容：非流式请求行为完全不变

### 3. 技术约束
* ✅ 使用 GDP `ghttp.EventWriter` 实现 SSE（Server-Sent Events）
* ✅ 流式请求自动设置 `no_cache=1`（流式无法缓存完整结果）
* ✅ 保留限流逻辑（`resource.VCLimit`）
* ✅ 保留熔断逻辑（`resource.CircuitBreaker`）
* ✅ 添加 Context 取消检测（客户端断开时及时停止）
* ✅ 流式超时时间放宽（从 15s 增加到 120s）
* ✅ vLLM 返回什么就立即转发什么（不做分批缓冲）

---

## 架构设计
### 分层架构图
```
┌─────────────────────────────────────────────────────────────┐
│  Controller Layer (控制器层)                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  智能分发器 (Request Dispatcher)                        │ │
│  │  - 解析请求体检测 stream 参数                           │ │
│  │  - 路由到对应处理器                                     │ │
│  └────────┬─────────────────────────┬─────────────────────┘ │
│           │                         │                        │
│     [stream=false]            [stream=true]                  │
│           │                         │                        │
│           ▼                         ▼                        │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Non-Stream      │      │  Stream          │            │
│  │  Handler         │      │  Handler         │            │
│  │  (原有逻辑复用)   │      │  (新增方法)       │            │
│  │  - VllmFetch     │      │  - VllmFetchStream│           │
│  │  - 返回完整JSON   │      │  - 返回SSE流      │            │
│  └──────────────────┘      └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Stream Handler Layer (流式处理层 - 新增)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  StreamHandler (library/stream/stream_handler.go)      │ │
│  │  - 封装 GDP ghttp.EventWriter                          │ │
│  │  - 实时转发 vLLM 的 SSE 响应                            │ │
│  │  - Context 取消检测                                    │ │
│  │  - 错误处理和日志记录                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Proxy Layer (代理层)                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  VllmFetcher Interface (统一接口)                      │ │
│  └────────┬─────────────────────────┬─────────────────────┘ │
│           │                         │                        │
│           ▼                         ▼                        │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  VllmFetch       │      │  VllmFetchStream │            │
│  │  (原有实现)       │      │  (新增方法)       │            │
│  │  - 缓存检查       │      │  - 自动no_cache=1 │            │
│  │  - 限流器         │      │  - 限流器(共用)    │            │
│  │  - 熔断器         │      │  - 熔断器(共用)    │            │
│  │  - 完整响应       │      │  - 流式响应        │            │
│  └──────────────────┘      └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  vLLM Layer (vLLM 引擎)                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  vLLM gRPC Endpoint (本地服务)                          │ │
│  │  - 接收 /v1/chat/completions 请求                       │ │
│  │  - 根据 stream 参数返回 JSON 或 SSE                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```
---

## 详细实现方案
### 1. 新增流式处理库（新建）
**文件**：`library/stream/stream_handler.go`（新建）

**职责**：

* 封装 GDP `ghttp.EventWriter` 的 SSE 流式写入
* 从 vLLM 读取流式响应并实时转发
* Context 取消检测
* 错误处理和日志记录

**核心接口**：

```go
type StreamHandler struct {
    writer  ghttp.EventWriter  // GDP 提供的 SSE Writer
    ctx     context.Context    // 用于取消检测
}

// NewStreamHandler 创建流式处理器
func NewStreamHandler(ctx context.Context, req ghttp.Request) (*StreamHandler, error)

// StreamFromReader 从 vLLM 响应流中读取并实时转发
// 要求1: 不做分批缓冲，vLLM 返回什么就立即写入
// 要求4: 添加 Context 取消检测
func (h *StreamHandler) StreamFromReader(reader io.Reader) error

// WriteError 写入错误事件
func (h *StreamHandler) WriteError(err error) error

// Close 关闭流式连接
func (h *StreamHandler) Close() error
```
**关键实现逻辑**：

```go
func (h *StreamHandler) StreamFromReader(reader io.Reader) error {
    scanner := bufio.NewScanner(reader)
    chunkCount := 0

    for scanner.Scan() {
        // ✅ 要求4: Context 取消检测
        select {
        case <-h.ctx.Done():
            // 客户端断开，立即停止
            logit.AddNotice(h.ctx, logit.String("stream_cancelled", "true"))
            return h.ctx.Err()
        default:
        }

        line := scanner.Text()

        if strings.HasPrefix(line, "data: ") {
            // ✅ 要求1: 立即写入，不缓冲
            h.writer.Write([]byte(line + "\n\n"))
            h.flush() // 立即刷新
            chunkCount++
        }
    }

    return scanner.Err()
}
```
---

### 2. 扩展代理层（遵循开闭原则）
**文件**：`model/service/proxy/vllm.go`（修改）

**原则**：

* ✅ **不修改** 原有 `VllmFetch`、`CallVllmModel` 等方法
* ✅ **新增** 带 `Stream` 后缀的独立方法
* ✅ 流式方法自动禁用缓存、调整超时

#### 2.1 新增流式入口方法
```go
// VllmFetchStream 流式请求处理（新增方法，不修改原有 VllmFetch）
func VllmFetchStream(ctx context.Context, params types.VllmRequestParams, streamHandler *stream.StreamHandler) error {
    // ✅ 要求3: 流式自动禁用缓存
    params.NoCache = "1"
    params.Stream = true

    logit.AddNotice(ctx, logit.String("hit_cache", "0"))
    logit.AddNotice(ctx, logit.String("stream_mode", "true"))
    umetrics.RecordAdd(1, umetrics.MetricsLabels{HitCache: "false", StreamMode: "true"})

    // ✅ 要求2: 保留限流逻辑
    _, err := resource.VCLimit.Execute(ctx, func() (interface{}, error) {
        return nil, CallVllmModelStream(ctx, params, streamHandler)
    })

    return err
}
```
#### 2.2 新增流式模型调用方法
```go
// CallVllmModelStream 流式调用 vLLM（新增方法）
func CallVllmModelStream(ctx context.Context, params types.VllmRequestParams, streamHandler *stream.StreamHandler) error {
    // ✅ 要求2: 保留熔断逻辑
    return resource.CircuitBreaker.Execute(func() error {
        startTime := time.Now()
        defer ModelCostMetrics(ctx, startTime)

        // ✅ 要求5: 流式超时放宽到 120 秒
        timeout := 120000 // 120 秒
        if to, errAtoi := strconv.Atoi(resource.ServiceEnv.ModelPredStreamTimeout); errAtoi == nil && to > 0 {
            timeout = to
        }

        return vllmPostRalStream(ctx, params, timeout, streamHandler)
    })
}
```
#### 2.3 新增流式 RAL 调用方法
```go
// vllmPostRalStream 流式 RAL 请求（新增方法）
func vllmPostRalStream(ctx context.Context, params types.VllmRequestParams, timeout int, streamHandler *stream.StreamHandler) error {
    localIP := env.LocalIP()
    grpcPort, _ := os.LookupEnv("LRS_RESOURCE_PORT_NAMING_GRPC")
    Host := localIP + ":" + grpcPort

    api := "/v1/chat/completions"
    if params.VllmAPI != "" {
        api = params.VllmAPI
    }

    // 确保启用流式
    params.Stream = true

    // 构建 RAL 请求
    ralReq := &ghttp.RalRequest{
        Method:  http.MethodPost,
        APIName: api,
        Path:    api,
        Host:    Host,
        Header: map[string][]string{
            "content-type": {"application/json"},
            "accept":       {"text/event-stream"}, // 告诉 vLLM 返回 SSE
        },
    }

    ralReq.WithBody(params, codec.JSONEncoder)

    ralResp := &ghttp.RalResponse{}
    addr := ral.ROptAddrDummy(gaddr.New("tcp", Host))
    timeoutConfig := ral.ROptTimeOut(500, 5000, timeout)

    if err := ral.RAL(ctx, "vllm_site", ralReq, ralResp, addr, timeoutConfig); err != nil {
        return errors.Wrap(err, "ral vllm stream error")
    }

    rawResp := ralResp.Response()
    if rawResp.StatusCode != http.StatusOK {
        return fmt.Errorf("vllm request failed with status: %d", rawResp.StatusCode)
    }

    // ✅ 显式关闭 Body（方案一：更清晰、无歧义）
    // ✅ 要求1: 实时转发，不缓冲
    // ✅ 要求4: Context 取消检测在 StreamFromReader 中实现
    err := streamHandler.StreamFromReader(rawResp.Body)
    closeErr := rawResp.Body.Close()

    // 优先返回读取错误，其次返回关闭错误
    if err != nil {
        return err
    }
    return closeErr
}
```
#### 2.4 新增原样转发流式方法
```go
// CallVllmModelWithBodyStream 原样转发流式请求（新增方法，用于 /v1/chat/completions）
func CallVllmModelWithBodyStream(ctx context.Context, rawBody io.Reader, api string, streamHandler *stream.StreamHandler) error {
    return resource.CircuitBreaker.Execute(func() error {
        startTime := time.Now()
        defer ModelCostMetrics(ctx, startTime)

        timeout := 120000 // 流式超时 120 秒
        if to, errAtoi := strconv.Atoi(resource.ServiceEnv.ModelPredStreamTimeout); errAtoi == nil && to > 0 {
            timeout = to
        }

        return vllmPostRalWithBodyStream(ctx, rawBody, timeout, api, streamHandler)
    })
}

// vllmPostRalWithBodyStream 流式原样转发（新增方法）
func vllmPostRalWithBodyStream(ctx context.Context, rawBody io.Reader, timeout int, api string, streamHandler *stream.StreamHandler) error {
    localIP := env.LocalIP()
    grpcPort, _ := os.LookupEnv("LRS_RESOURCE_PORT_NAMING_GRPC")
    Host := localIP + ":" + grpcPort

    ralReq := &ghttp.RalRequest{
        Method:  http.MethodPost,
        APIName: api,
        Path:    api,
        Host:    Host,
        Header: map[string][]string{
            "content-type": {"application/json"},
            "accept":       {"text/event-stream"},
        },
        Body: rawBody,
    }

    ralResp := &ghttp.RalResponse{}
    addr := ral.ROptAddrDummy(gaddr.New("tcp", Host))
    timeoutConfig := ral.ROptTimeOut(500, 5000, timeout)

    if err := ral.RAL(ctx, "vllm_site", ralReq, ralResp, addr, timeoutConfig); err != nil {
        return errors.Wrap(err, "ral vllm stream error")
    }

    rawResp := ralResp.Response()
    if rawResp.StatusCode != http.StatusOK {
        return fmt.Errorf("vllm request failed with status: %d", rawResp.StatusCode)
    }

    // ✅ 显式关闭 Body（方案一：更清晰、无歧义）
    err := streamHandler.StreamFromReader(rawResp.Body)
    closeErr := rawResp.Body.Close()

    // 优先返回读取错误，其次返回关闭错误
    if err != nil {
        return err
    }
    return closeErr
}
```
**代码改动统计**：

* ✅ **0 行修改**原有方法
* ✅ **新增 4 个方法**（约 150 行代码）

---

### 3. 控制器层智能分发（最小化改动）
#### 3.1 修改 `ChatText` 方法
**文件**：`servers/httpserver/controller/chat.go`

**改动原则**：

* ✅ 在方法入口处添加 `stream` 参数检测（约 10 行代码）
* ✅ 流式逻辑封装到独立私有方法（不污染原有逻辑）
* ✅ 非流式逻辑完全不变

```go
func ChatText(ctx context.Context, req ghttp.Request) ghttp.Response {
    // ✅ 新增：解析请求体检测流式参数（约 5 行）
    bodyBytes, _ := io.ReadAll(req.Body())
    var params types.VllmRequestParams
    json.Unmarshal(bodyBytes, &params)

    // ✅ 新增：流式分支（约 3 行）
    if params.Stream {
        return chatTextStreamHandler(ctx, req, bodyBytes)
    }

    // ========== 以下为原有逻辑，完全不变 ==========
    req.SetBody(io.NopCloser(bytes.NewReader(bodyBytes)))

    nowTime := time.Now()
    response := types.Response{
        ErrNo:        0,
        ModelType:    resource.ModelConf.AppName,
        ModelVersion: resource.ModelConf.ModelVersion,
    }

    res, err := proxy.VllmFetch(ctx, req, &response, "Text")
    if err != nil {
        resource.LoggerService.Warning(ctx, "vllm fetch err:"+err.Error())
        response.ErrNo = 1
        response.Msg = "VllmFetch failed"
        return ghttp.NewJSONResponse(http.StatusInternalServerError, response)
    }

    response.Data = res
    return ghttp.NewJSONResponse(http.StatusOK, response)
}

// ✅ 新增：流式处理逻辑（私有方法，约 30 行）
func chatTextStreamHandler(ctx context.Context, req ghttp.Request, bodyBytes []byte) ghttp.Response {
    // 创建流式处理器
    streamHandler, err := stream.NewStreamHandler(ctx, req)
    if err != nil {
        return ghttp.NewJSONResponse(http.StatusInternalServerError, map[string]string{
            "error": "Failed to create stream handler: " + err.Error(),
        })
    }
    defer streamHandler.Close()

    // 解析请求参数
    var params types.VllmRequestParams
    if err := json.Unmarshal(bodyBytes, &params); err != nil {
        streamHandler.WriteError(err)
        return nil
    }

    // 调用流式代理
    if err := proxy.VllmFetchStream(ctx, params, streamHandler); err != nil {
        resource.LoggerService.Warning(ctx, "vllm stream fetch err:"+err.Error())
        streamHandler.WriteError(err)
    }

    return nil // 已通过 EventWriter 直接写入响应
}
```
**代码改动统计**：

* ✅ `ChatText` 方法：新增 8 行（流式检测和分发）
* ✅ 原有逻辑：0 行修改
* ✅ 新增私有方法 `chatTextStreamHandler`：约 30 行

#### 3.2 修改 `ChatImage` 方法
**文件**：`servers/httpserver/controller/chat.go`

**改动逻辑**：与 `ChatText` 完全一致

```go
func ChatImage(ctx context.Context, req ghttp.Request) ghttp.Response {
    // ✅ 新增：流式检测和分发（约 8 行）
    bodyBytes, _ := io.ReadAll(req.Body())
    var params types.VllmRequestParams
    json.Unmarshal(bodyBytes, &params)

    if params.Stream {
        return chatImageStreamHandler(ctx, req, bodyBytes)
    }

    // ========== 原有逻辑完全不变 ==========
    req.SetBody(io.NopCloser(bytes.NewReader(bodyBytes)))

    response := types.Response{
        ErrNo:        0,
        ModelType:    resource.ModelConf.AppName,
        ModelVersion: resource.ModelConf.ModelVersion,
    }

    res, err := proxy.VllmFetch(ctx, req, &response, "Image")
    // ... 原有错误处理逻辑 ...

    response.Data = res
    return ghttp.NewJSONResponse(http.StatusOK, response)
}

// ✅ 新增：流式处理逻辑（私有方法，约 30 行）
func chatImageStreamHandler(ctx context.Context, req ghttp.Request, bodyBytes []byte) ghttp.Response {
    streamHandler, err := stream.NewStreamHandler(ctx, req)
    if err != nil {
        return ghttp.NewJSONResponse(http.StatusInternalServerError, map[string]string{
            "error": "Failed to create stream handler: " + err.Error(),
        })
    }
    defer streamHandler.Close()

    var params types.VllmRequestParams
    if err := json.Unmarshal(bodyBytes, &params); err != nil {
        streamHandler.WriteError(err)
        return nil
    }

    if err := proxy.VllmFetchStream(ctx, params, streamHandler); err != nil {
        resource.LoggerService.Warning(ctx, "vllm stream fetch err:"+err.Error())
        streamHandler.WriteError(err)
    }

    return nil
}
```
#### 3.3 修改 `CallVllmWithBody` 方法
**文件**：`servers/httpserver/controller/proxy.go`

```go
func CallVllmWithBody(ctx context.Context, req ghttp.Request) ghttp.Response {
    api := req.QueryDefault("api", "/v1/chat/completions")

    bodyBytes, err := io.ReadAll(req.Body())
    if err != nil {
        return ghttp.NewJSONResponse(http.StatusInternalServerError, err.Error())
    }

    // ✅ 新增：检测流式请求（约 8 行）
    var bodyMap map[string]interface{}
    json.Unmarshal(bodyBytes, &bodyMap)
    if stream, ok := bodyMap["stream"].(bool); ok && stream {
        return callVllmWithBodyStreamHandler(ctx, req, bodyBytes, api)
    }

    // ========== 以下为原有逻辑，完全不变 ==========
    promppt := string(bodyBytes)
    rawBody := io.NopCloser(bytes.NewReader(bodyBytes))

    readCache := req.QueryDefault("readCache", "0")
    writeCache := req.QueryDefault("writeCache", "0")

    if readCache == "1" {
        // ... 原有缓存逻辑 ...
    }

    logit.AddNotice(ctx, logit.String("hit_cache", "0"))

    result, err := resource.VCLimit.Execute(ctx, func() (interface{}, error) {
        return proxy.CallVllmModelWithBody(ctx, rawBody, api)
    })

    if err != nil {
        return ghttp.NewJSONResponse(http.StatusInternalServerError, err.Error())
    }

    // ... 原有响应处理逻辑 ...

    return ghttp.NewJSONResponse(http.StatusOK, jsonObject)
}

// ✅ 新增：流式原样转发（私有方法，约 35 行）
func callVllmWithBodyStreamHandler(ctx context.Context, req ghttp.Request, bodyBytes []byte, api string) ghttp.Response {
    streamHandler, err := stream.NewStreamHandler(ctx, req)
    if err != nil {
        return ghttp.NewJSONResponse(http.StatusInternalServerError, map[string]string{
            "error": "Failed to create stream handler: " + err.Error(),
        })
    }
    defer streamHandler.Close()

    logit.AddNotice(ctx, logit.String("hit_cache", "0"))
    logit.AddNotice(ctx, logit.String("stream_mode", "true"))
    umetrics.RecordAdd(1, umetrics.MetricsLabels{HitCache: "false", StreamMode: "true"})

    rawBody := bytes.NewReader(bodyBytes)

    _, err = resource.VCLimit.Execute(ctx, func() (interface{}, error) {
        return nil, proxy.CallVllmModelWithBodyStream(ctx, rawBody, api, streamHandler)
    })

    if err != nil {
        resource.LoggerService.Warning(ctx, "vllm stream fetch err:"+err.Error())
        streamHandler.WriteError(err)
    }

    return nil
}
```
**控制器层总改动统计**：

* ✅ `chat.go`：新增约 70 行（8 + 30 + 8 + 30）
* ✅ `proxy.go`：新增约 45 行（8 + 35）
* ✅ 原有逻辑：0 行修改
* ✅ 总计新增约 115 行代码

---

### 4. 路由层（完全不需要修改）
**文件**：`servers/httpserver/router.go`

✅ **无需任何改动**！现有路由自动支持流式：

```go
// 这些路由保持不变，自动支持 stream 参数
router.HandleFunc("any", "/api/chat/text", controller.ChatText)
router.HandleFunc("any", "/api/chat/image", controller.ChatImage)
router.HandleFunc("any", "/v1/chat/completions", controller.CallVllmWithBody)
router.HandleFunc("any", "/vllm", controller.CallVllmWithBody)
```
---

### 5. 配置扩展（可选）
#### 5.1 环境变量配置
**文件**：`bootstrap/bootstrap.go`

```go
type ServiceEnvStruct struct {
    // ... 原有配置 ...
    ModelPredTimeout       string `env:"MODEL_PRED_TIMEOUT" default:"15000"`

    // ✅ 新增：流式超时配置
    ModelPredStreamTimeout string `env:"MODEL_PRED_STREAM_TIMEOUT" default:"120000"` // 120 秒
}
```
#### 5.2 配置文件（可选）
**文件**：`conf/model.toml`

```toml
# ✅ 新增流式超时配置段
[stream]
timeout_ms = 120000  # 流式请求总超时 120 秒
```
---

## 熔断器和限流器复用说明
### 1. 限流器（Concurrent Limiter）
**当前实现**：`library/resource/concurent_limiter.go`

* 使用 GDP `limit.ConcurrentLimiter` 控制最大并发数
* 支持通过 uniconf 动态调整

**流式处理策略**：
✅ **共用限流器**（推荐）

* 流式和非流式共用 `resource.VCLimit`
* 流式请求占用时间更长，但并发控制逻辑相同
* 简单有效，无需额外配置

```go
// 流式和非流式都使用同一个限流器
_, err := resource.VCLimit.Execute(ctx, func() (interface{}, error) {
    if params.Stream {
        return nil, CallVllmModelStream(ctx, params, streamHandler)
    } else {
        return CallVllmModel(ctx, params)
    }
})
```
### 2. 熔断器（Circuit Breaker）
**当前实现**：`library/resource/circuit_breaker.go`

* 使用 `sony/gobreaker` 实现
* 三种状态：Closed → Open → Half-Open

**工作机制**：

```
Closed (正常)
  ├─ 60s 内请求数 ≥ 20
  ├─ 失败率 ≥ 20%
  └─ 连续失败 ≥ 1 次
      └─> 触发熔断，转 Open

Open (熔断中)
  ├─ 所有请求立即失败
  ├─ 持续 5 秒
  └─> 转 Half-Open

Half-Open (试探)
  ├─ 允许 10 个试探请求
  ├─ 成功 → Closed
  └─ 失败 → Open
```
**流式处理策略**：
✅ **共用熔断器**，但需区分中断原因

```go
func CallVllmModelStream(ctx context.Context, params types.VllmRequestParams, streamHandler *stream.StreamHandler) error {
    return resource.CircuitBreaker.Execute(func() error {
        // 尝试建立连接
        err := vllmPostRalStream(ctx, params, timeout, streamHandler)

        // 区分中断原因
        if err != nil && ctx.Err() != nil {
            // Context 取消（客户端断开），不触发熔断
            return nil
        }

        // 其他错误，触发熔断
        return err
    })
}
```
**关键点**：

* ✅ 连接失败、vLLM 不可用 → 触发熔断
* ✅ 客户端主动断开（Context 取消）→ 不触发熔断

---

## SSE 响应格式
### OpenAI 兼容格式（用于 `/v1/chat/completions`）
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"qwen","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"qwen","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"qwen","choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"qwen","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```
### 自定义格式（用于 `/api/chat/text`、`/api/chat/image`）
vLLM 引擎返回的 SSE 格式会被直接转发，无需额外处理。

---

## 文件清单
### 新建文件
1. `library/stream/stream_handler.go`（约 150 行）

    * SSE 流式处理器
    * Context 取消检测
    * 实时转发逻辑

### 修改文件
2. `model/service/proxy/vllm.go`（新增约 150 行）

    * 新增 `VllmFetchStream`
    * 新增 `CallVllmModelStream`
    * 新增 `vllmPostRalStream`
    * 新增 `CallVllmModelWithBodyStream`
    * 新增 `vllmPostRalWithBodyStream`
    * ✅ 原有方法 0 行修改

3. `servers/httpserver/controller/chat.go`（新增约 70 行）

    * 修改 `ChatText`：新增 8 行流式检测
    * 新增 `chatTextStreamHandler`：约 30 行
    * 修改 `ChatImage`：新增 8 行流式检测
    * 新增 `chatImageStreamHandler`：约 30 行
    * ✅ 原有逻辑 0 行修改

4. `servers/httpserver/controller/proxy.go`（新增约 45 行）

    * 修改 `CallVllmWithBody`：新增 8 行流式检测
    * 新增 `callVllmWithBodyStreamHandler`：约 35 行
    * ✅ 原有逻辑 0 行修改

5. `bootstrap/bootstrap.go`（新增 1 行）

    * 新增环境变量 `MODEL_PRED_STREAM_TIMEOUT`

### 无需修改文件
* ✅ `servers/httpserver/router.go`：路由完全不变
* ✅ `library/resource/circuit_breaker.go`：熔断器复用
* ✅ `library/resource/concurent_limiter.go`：限流器复用
* ✅ `library/types/request.go`：`Stream` 字段已存在

---

## 代码量统计
|类型|行数|说明|
|-|-|-|
|**新建文件**|~150|`stream_handler.go`|
|**代理层新增**|~150|5 个新方法|
|**控制器层新增**|~115|3 个私有方法 + 流式检测|
|**配置新增**|~2|环境变量配置|
|**原有代码修改**|**0**|✅ 完全遵循开闭原则|
|**总计**|~417|所有新增代码|

---

## 测试方案
### 1. 单元测试
**文件**：`library/stream/stream_handler_test.go`

```go
func TestStreamHandler_StreamFromReader(t *testing.T) {
    // 模拟 SSE 流
    sseData := `data: {"content":"Hello"}
data: {"content":" world"}
data: [DONE]
`
    reader := strings.NewReader(sseData)

    // 创建 mock EventWriter
    // 测试实时转发逻辑
}

func TestStreamHandler_ContextCancel(t *testing.T) {
    // 测试 Context 取消时的行为
}
```
### 2. 集成测试
#### 测试 1：非流式请求（向后兼容）
```bash
curl -X POST http://localhost:8080/api/chat/text \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "qwen",
    "stream": false
  }'

# 期望：返回完整 JSON 响应（与之前行为一致）
```
#### 测试 2：流式请求
```bash
curl -X POST http://localhost:8080/api/chat/text \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "写一首诗"}],
    "model": "qwen",
    "stream": true
  }'

# 期望：返回 SSE 流式响应，逐字打印
# data: {"choices":[{"delta":{"content":"春"}}]}
# data: {"choices":[{"delta":{"content":"眠"}}]}
# ...
# data: [DONE]
```
#### 测试 3：OpenAI 兼容流式
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "qwen",
    "stream": true
  }'

# 期望：返回 OpenAI 兼容的 SSE 格式
```
#### 测试 4：客户端中途断开
```bash
# 启动请求后 2 秒 Ctrl+C 中断
timeout 2s curl -X POST http://localhost:8080/api/chat/text \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "写一篇长文章"}],
    "model": "qwen",
    "stream": true
  }'

# 期望：服务端日志显示 stream_cancelled=true
# 期望：熔断器不触发（Context 取消不算失败）
```
#### 测试 5：vLLM 不可用
```bash
# 停止 vLLM 引擎，然后请求
curl -X POST http://localhost:8080/api/chat/text \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'

# 期望：立即返回错误事件
# data: {"error":{"message":"ral vllm stream error: ...","type":"server_error"}}
# 期望：熔断器触发（连接失败算失败）
```
### 3. 性能测试
```bash
# 使用 wrk 进行压测
wrk -t10 -c100 -d30s --timeout 60s \
  -s stream_test.lua \
  http://localhost:8080/api/chat/text

# 监控指标：
# 1. 并发限流器使用情况（limiter_get）
# 2. 熔断器状态（circuit_breaker）
# 3. 流式请求耗时（stream_duration_ms）
# 4. Context 取消次数（stream_cancelled）
```
---

## 监控指标
### 新增指标
```go
// library/umetrics/metrics.go

// 流式模式标识
umetrics.RecordAdd(1, umetrics.MetricsLabels{StreamMode: "true"})

// 流式 chunk 数量
umetrics.RecordSet(float64(chunkCount), umetrics.MetricsLabels{StreamChunks: "true"})

// 流式取消次数
umetrics.RecordAdd(1, umetrics.MetricsLabels{StreamCancelled: "true"})
```
### 日志增强
```go
// 流式请求标识
logit.AddNotice(ctx, logit.String("stream_mode", "true"))

// 流式 chunk 数量
logit.AddNotice(ctx, logit.Int("stream_chunks", chunkCount))

// 流式耗时
logit.AddNotice(ctx, logit.Int64("stream_duration_ms", durationMs))

// Context 取消原因
logit.AddNotice(ctx, logit.String("stream_cancelled", "true"))
logit.AddNotice(ctx, logit.String("cancel_reason", ctx.Err().Error()))
```
---

## 部署流程
### Phase 1: 本地开发（1-2 天）
1. ✅ 实现 `stream_handler.go`
2. ✅ 扩展 `proxy/vllm.go`
3. ✅ 修改控制器
4. ✅ 本地单元测试

### Phase 2: Sandbox 测试（1 天）
1. ✅ 部署到 Sandbox 环境
2. ✅ 集成测试（非流式、流式、断开、故障）
3. ✅ 性能测试（并发、超时、熔断）
4. ✅ 监控指标验证

### Phase 3: 生产灰度（1 天）
1. ✅ 生产环境灰度发布（10% 流量）
2. ✅ 监控流式指标
3. ✅ 逐步扩大到 100%

### Phase 4: 文档更新（1 天）
1. ✅ 更新 API 文档（流式使用说明）
2. ✅ 更新 CLAUDE.md（流式配置和监控）
3. ✅ 编写故障排查手册

---

## 风险评估
### 低风险 ✅
* **向后兼容**：非流式请求完全不受影响
* **原有代码修改量**：0 行（完全遵循开闭原则）
* **GDP 框架支持**：已确认支持 `ghttp.EventWriter`

### 中风险 ⚠️
* **流式超时配置**：需要根据实际业务调整（建议初始 120s）
* **并发限流器压力**：流式请求占用时间更长，可能需要调整上限
* **监控告警**：需要配置流式相关告警规则

### 缓解措施
1. ✅ Sandbox 充分测试
2. ✅ 生产灰度发布
3. ✅ 实时监控指标
4. ✅ 快速回滚机制（保留原有逻辑，可随时关闭流式）

---

## 总结
### 核心优势
1. ✅ **开闭原则**：新增方法，0 行修改原有代码
2. ✅ **路径不变**：现有 API 自动支持流式
3. ✅ **自动优化**：流式自动禁用缓存
4. ✅ **实时转发**：不做分批缓冲，vLLM 返回什么就立即转发
5. ✅ **Context 取消**：客户端断开时及时停止
6. ✅ **限流复用**：共用并发限流器
7. ✅ **熔断复用**：共用熔断器，智能区分故障原因
8. ✅ **超时放宽**：流式超时 120s（可配置）
9. ✅ **向后兼容**：非流式请求完全不受影响

### 代码量
* **新增**：约 417 行
* **修改**：0 行
* **删除**：0 行
