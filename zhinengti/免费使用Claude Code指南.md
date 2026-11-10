> 原文：https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/KeF15lNOtH/-UXFkEkRyR/YQxxeM66iXjCNx

免费使用Claude Code指南

# 1.免费模型资源申请
注册登录[modelScope](https://modelscope.cn/my/overview)，并绑定阿里云账号后，该账号下就有每天2000次的模型调用额度。在[访问令牌](https://modelscope.cn/my/myaccesstoken)页面获取Api-Key

对于个人日常使用足够。重点是免费。不需要翻墙。

里面有常见的开源大模型可用，例如最新的开源sota模型：Qwen3-Coder-480B-A35B-Instruct，GLM-4.5，Kimi-K2等。DeepSeek-R1,DeepSeek-V3等模型也都有。

# 2.安装Claude-Code和Claude-Code-Router
安装[claude-code](https://docs.anthropic.com/en/docs/claude-code/quickstart)

```bash
npm install -g @anthropic-ai/claude-code
```
安装[claude-code-router](https://github.com/musistudio/claude-code-router)

> claude-code-router的原理是启动一个代理服务，本质是通过设置claude-code原生支持的ANTHROPIC_AUTH_TOKEN，ANTHROPIC_BASE_URL变量，将代理转发到claude-code-router启动的这个代理服务上。
```bash
npm install -g @musistudio/claude-code-router
```
# 3.开箱即用的配置
在`~/.claude-code-router/config.json`填写下面的配置,修改api-key

```go
{
    "Providers": [
        {
            "name": "modelscope",
            "api_base_url": "https://api-inference.modelscope.cn/v1/chat/completions",
            "api_key": "your api key",
            "models": [
                "Qwen/Qwen3-Coder-480B-A35B-Instruct",
                "ZhipuAI/GLM-4.5"
            ],
            "transformer": {
                "use": [
                    [
                        "maxtoken",
                        {
                            "max_tokens": 65536
                        }
                    ],
                    "reasoning"
                ]
            }
        }
    ],
 
    "Router": {
        "default": "modelscope,Qwen/Qwen3-Coder-480B-A35B-Instruct"
  }
    
}
```
# 4.启动`ccr code`
# 5.更复杂的配置
## 配置Transformer
Transformer的本质是在请求或响应时对请求参数或响应参数做改写，具体的transformer的实现见[该仓库](https://github.com/musistudio/llms/tree/main/src/transformer)

常见的Transformer

* `maxtoken`: 设置特定的 `max_tokens` 值。
* `reasoning`: 用于处理 `reasoning_content` 字段。将`reasoning_content`转为claude协议的`thinking`字段



## 配置Router
通过对请求参数分析，按场景进行请求不同的模型。详细实现方式参考[该文件](https://github.com/musistudio/claude-code-router/blob/main/src/utils/router.ts)

`Router` 对象定义了在不同场景下使用哪个模型：

* `default`: 用于常规任务的默认模型。
* `background`: 用于后台任务的模型。如果请求的模型是claude-3-5-haiku，则走这条通路。
* `think`: 用于推理密集型任务（如计划模式）的模型。如果body.thinking则认为需要思考模型，走该通路
* `longContext`: 用于处理长上下文（例如，> 60K 令牌）的模型。判断上下文长度如果大于`longContextThreshold`，则走该通路
* `longContextThreshold` (可选): 触发长上下文模型的令牌数阈值。如果未指定，默认为 60000。
* `webSearch`: 用于处理网络搜索任务，需要模型本身支持。如果工具中有`web_search`则，走该通路。



```go
{
  "Providers": [
    {
      "name": "modelscope",
      "api_base_url": "https://api-inference.modelscope.cn/v1/chat/completions",
      "api_key": "dc607bd6-c073-4ea1-97dc-204cb1b4ff05",
      "models": [
        "Qwen/Qwen3-Coder-480B-A35B-Instruct","ZhipuAI/GLM-4.5"
      ],
      "transformer": {
        "use": [
          [
            "maxtoken",
            {
              "max_tokens": 65536
            }
          ]
        ]
      }
    },
    {
      "name": "daye",
      "api_base_url": "https://newapi.aliyahzombie.top/v1/chat/completions",
      "api_key": "api key",
      "models": [
        "gemini-2.5-pro"
      ],
      "transformer": {
       "use": [
          [
            "maxtoken",
            {
              "max_tokens": 117000
            }
          ]
        ]
      }
    }
  ],
    "Router": {
    "default": "modelscope,ZhipuAI/GLM-4.5",
    "background": "modelscope,ZhipuAI/GLM-4.5",
    "think": "daye,gemini-2.5-pro",
    "longContext": "daye,gemini-2.5-pro",
    "longContextThreshold": 60000,
    "webSearch": "gemini,gemini-2.5-flash"
  }
}
```