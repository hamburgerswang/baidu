> 原文：https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/KeF15lNOtH/-UXFkEkRyR/9ieBXRNM21KaDx

KV cache 数据结构

KV-Cache 在显存里到底长什么样？可以一句话总结：**“按层存放、按 token 增长、四维张量，外加一张地址映射表把不连续的物理块拼成逻辑序列。”**

下面分层拆开说明。

---

## 1. 存了什么？
对 Transformer 的 **每一层、每个注意力头、每个 token** 都缓存两组向量：

* Key 向量——用于与后续 Query 做点积算注意力权重
* Value 向量——用于加权求和得到注意力输出

因此 KV-Cache 的内容就是 **Key 张量 + Value 张量** 的集合，除此之外没有别的。

---

## 2. 逻辑数据结构（开发者视角）
最自然的表示是 **List[Tuple[Tensor, Tensor]]**，长度 = 模型层数 `num_layers`：

```
kv_cache = [
    (key_cache_l0, value_cache_l0),   # 第0层
    (key_cache_l1, value_cache_l1),   # 第1层
    ...
]
```
每个张量的形状：

```
key_cache_li   : (batch_size, num_heads, seq_len, head_dim)
value_cache_li : (batch_size, num_heads, seq_len, head_dim)
```
* batch_size：并发处理的序列数
* seq_len：当前已缓存的 token 数（随生成步骤 +=1）
* head_dim = hidden_size / num_heads

---

## 3. 物理数据结构（系统视角）
由于 seq_len 动态增长且显存有限，**不可能为每个序列预留一大段连续显存**。现代推理框架（vLLM、nano-vllm、SGLang 等）采用 **分页式 KV-Cache**：

### 3.1 固定大小的 Block（页）
* 每块可容纳 `block_size` 个 token 的 KV（如 16 或 256 个 token）
* 显存真正分配的是 `(block_size, num_heads, head_dim)` 大小的 Key/Value Tensor 对

### 3.2 Block Table —— 物理→逻辑的地址翻译
* **Sequence → Block 映射表**：记录一个序列的 “第 i 个逻辑 token” 现在落在哪个 block、哪个 slot
* **Slot Mapping**：一维整数数组，长度 = 当前序列长度，元素值 = 全局显存池中的物理 slot 编号

示意：

```
逻辑 token 0~15  → 物理 block 3，slot 0~15
逻辑 token 16~31 → 物理 block 7，slot 0~15
...
```
GPU 计算 attention 时通过这张表把分散的物理块拼成逻辑上连续的 K/V 矩阵——这就是 PagedAttention 的核心思想。

---

## 4. 小结：一张图看清 KV-Cache 的“两层结构”
|层级|数据结构|作用|典型尺寸（单序列，一层）|
|-|-|-|-|
|**逻辑视图**|`List[(K,V)]`<br/> 每层一对张量|方便模型代码读写|`(1, num_heads, seq_len, head_dim)`|
|**物理视图**|分页式 Block 池 + Block Table|节省显存、支持变长、多并发|每块 <br/>`(block_size, num_heads, head_dim)`|

---

这样，开发者可以按“四维张量”直观理解 KV-Cache；系统实现则靠“分页 + 地址映射”把显存利用率、并发度做到极致。