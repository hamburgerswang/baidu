> 原文：https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/pKzJfZczuc/noISsAmuLf/OnvKMIptkmJF0v

webui_qwen2.py代码解析

这是一个**完整的、基于 LoRA 微调的 Qwen2 模型的酒店对话机器人（Hotel Chatbot）应用脚本**。它将 LLM 的文本生成能力与外部的**数据库查询工具（HotelDB）**结合起来，实现了一个简单的 **Agent/Tool-Use（智能体/工具使用）**系统。

下面是对这个 Python 脚本的详细剖析和讲解：

---

## 💻 脚本核心功能：工具增强型对话系统
这个脚本的核心在于实现一个循环：**用户输入 $\rightarrow$ 模型生成回复/工具调用指令 $\rightarrow$ 调用数据库工具 $\rightarrow$ 模型根据工具结果生成最终回复 $\rightarrow$ 用户收到回复。**

### 1. 初始化与模型加载
|**代码段**|**作用**|**关键点**|
|-|-|-|
|`sys.path.append('../qwen2')`|将父目录下的 `qwen2` 文件夹添加到系统路径，以便导入自定义模块（如 `evaluate`）。|**模块导入**|
|`parser = argparse.ArgumentParser()`|定义命令行参数解析器，要求用户必须指定：`--model` (基础模型路径) 和 `--ckpt` (LoRA 检查点路径)。|**命令行配置**|
|`db = HotelDB()`|**实例化数据库客户端**。这是 LLM 将要调用的**外部工具**。|**工具初始化**|
|`tokenizer, model = load_model(args.model, args.ckpt)`|**加载微调后的 LoRA 模型**。这确保了模型能够理解和生成工具调用指令（如 `search({...})`）。|**LoRA 模型加载**|
|`get_completion(prompt)`|定义 LLM 推理函数，负责将 Prompt 编码、移动到 GPU (`.to("cuda")`)、执行生成并解码输出。|**模型推理**|

### 2. 核心函数：`chat` (对话逻辑)
`chat` 函数是整个应用的心脏，实现了 Agent 的决策和执行流程。

#### **A. 接收输入与构建上下文**
1. `context.append({'role':'user','content':user_input})`: 将最新的用户输入添加到**对话历史（context）**中。
2. `prompt = build_prompt(context)`: 调用自定义函数，将整个对话历史转换为 LLM 能理解的 **Prompt 格式**（例如：带有 System 角色、历史对话的 Prompt）。
3. `response = get_completion(prompt)`: **第一次调用 LLM**，获取模型的初步响应。

#### **B. 工具调用决策与执行 (Tool-Use)**
```python
 if "search" in response:
        # 取出最新一条 'search' 后面的json查询条件
        search_query = parse_json(response)
        if search_query is not None:
            search_field = json.dumps(search_query,indent=4,ensure_ascii=False)
            remove_search_history(context)
            context.append({'role':'search','arguments':search_query})
            # 调用酒店查询接口
            try:
                return_field = db.search(search_query, limit=3)
            finally:
                db.client.close()

            context.append({'role':'return','records':return_field})
            keys = []
            if return_field:
                keys = ['name', 'address', 'phone', 'price', 'rating', 'subway', 'type', 'facilities']
            data = {key: [item[key] for item in return_field] for key in keys}
            data = data or {"hotel": []}
            return_field = pd.DataFrame(data)
            # 将查询结果发给LLM，再次那么让LLM生成回复
            response = get_completion(build_prompt(context))

```
* **决策：** 如果 LLM 生成的响应中包含 `search` 关键词（即模型决定调用工具），则进入工具调用逻辑。
* **解析：**`search_query = parse_json(response)` 提取模型生成的查询条件（如 `{type: "豪华", price: "中等"}`）。
* **执行：**
    * 将解析的查询条件作为 `search` 角色添加到 Context。
    * 调用 `db.search(...)`**执行数据库查询**，获取结果（例如前 3 个酒店记录）。
    * 将查询结果作为 `return` 角色添加到 Context，**完成工具调用的闭环**。

* **二次生成：**`response = get_completion(build_prompt(context))`**第二次调用 LLM**。这次，Prompt 中包含了数据库的查询结果。模型不再是生成工具指令，而是根据这些**实际数据**生成友好、准确的**用户回复**。
* `remove_search_history(context)`: 这个步骤很关键，它清除了上一次搜索的 `search` 和 `return` 历史，以避免下次 Prompt 过长或重复执行搜索。

#### **C. 结束对话循环**
1. `reply = response.replace("assistant", "")`: 清理回复文本。
2. `chatbot.append((user_input, reply))`: 将用户输入和最终回复添加到 Gradio 的聊天界面历史。
3. `context.append({'role':'assistant','content':reply})`: 将最终回复添加到 Context，为下一轮对话做准备。

### 3. Gradio 用户界面 (UI)
* `with gr.Blocks() as demo:`: 使用 **Gradio** 框架快速搭建 Web 界面。
* 界面元素包括：`chatbot` (聊天历史)、`user_input` (输入框)、`search_field` (显示模型的搜索 JSON 指令)、`return_field` (以表格形式显示数据库的查询结果)。
* **事件绑定：**
    * `submitBtn.click(chat, ...)`: 提交按钮点击时，调用 `chat` 函数处理对话。
    * `emptyBtn.click(reset_state, ...)`: 清空按钮点击时，重置所有状态（聊天记录、Context）。


---

## 🌟 总结
这是一个将 **LLM 微调**、**工具使用（Tool-Use）**和 **Gradio 界面**集成的优秀实践案例。

**微调目标：** 模型的微调目标就是让它能够精确地在需要时生成结构化的 `search({...})` JSON 指令，并在收到数据库结果后，将结构化数据流畅地解释给用户听。