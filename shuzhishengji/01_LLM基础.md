# 01 LLM 基础（40 题）

标记：【高频】常被问到；【专家】考察深度，专家职级重点准备。

1. 【高频】Transformer 的整体结构是什么？Encoder、Decoder 分别做什么？
2. 【高频】Self-Attention 的计算过程是什么？为什么要除以 √d_k？
3. Multi-Head Attention 的作用是什么？头数怎么影响效果和计算量？
4. 【专家】MHA、MQA、GQA 的区别是什么？对推理显存和速度有什么影响？
5. 位置编码有哪些方案？绝对位置编码、RoPE、ALiBi 各有什么特点？
6. 【专家】RoPE 为什么能做长度外推？NTK-aware、YaRN 等外推方法的思路是什么？
7. Decoder-only 架构为什么成为大模型主流？
8. 【高频】什么是 KV Cache？为什么能加速推理？它的显存占用怎么估算？
9. 【专家】PagedAttention（vLLM）解决了什么问题？原理是什么？
10. 【专家】Prefill 和 Decode 两个阶段的计算特点有什么不同？为什么要分开优化？
11. 【高频】首 token 延迟（TTFT）和每 token 延迟（TPOT）分别受什么因素影响？怎么优化？
12. Continuous Batching 和静态 Batching 的区别是什么？
13. 【专家】投机解码（Speculative Decoding）的原理是什么？什么场景收益大？
14. 【高频】Temperature、Top-k、Top-p 分别是什么？怎么影响输出？
15. Greedy、Beam Search、采样解码各适合什么场景？
16. 重复惩罚（repetition penalty）、频率惩罚、存在惩罚有什么区别？
17. 【高频】Tokenizer 有哪些方案（BPE、WordPiece、SentencePiece）？中文 token 计费为什么更贵？
18. 上下文窗口长度受什么限制？长上下文模型就不需要 RAG 了吗？
19. 【专家】Lost in the Middle 现象是什么？对 Prompt 和 RAG 设计有什么启发？
20. 【高频】预训练、SFT、RLHF 三个阶段分别做什么？
21. RLHF 中奖励模型怎么训练？PPO 的大致流程是什么？
22. 【专家】DPO 和 PPO 的区别是什么？GRPO 有什么特点？
23. 【高频】LoRA 的原理是什么？rank 怎么选？QLoRA 又做了什么？
24. 全参微调、LoRA、Prompt Tuning、P-Tuning 怎么选型？
25. 【高频】什么时候应该微调，什么时候用 RAG 或 Prompt 就够了？
26. 微调数据怎么构造？数据量、质量、多样性哪个更重要？
27. 灾难性遗忘是什么？微调时怎么缓解？
28. 【高频】模型量化（INT8、INT4、GPTQ、AWQ）的原理和精度损失怎么权衡？
29. 模型蒸馏的原理是什么？在 Agent 场景怎么用小模型替代大模型？
30. MoE 架构的原理是什么？推理时有什么挑战？
31. 【高频】大模型幻觉产生的原因有哪些？工程上怎么缓解？
32. 推理模型（如 o1、DeepSeek-R1）和普通指令模型在使用上有什么区别？
33. 【专家】思维链（CoT）为什么能提升推理能力？对延迟和成本有什么影响？
34. 结构化输出（JSON Mode、约束解码）是怎么实现的？
35. 【专家】Grammar-constrained decoding 的原理是什么？和后置校验重试相比有什么优劣？
36. Embedding 模型和生成模型的训练目标有什么不同？
37. 多模态大模型（图文）一般怎么把图像接入语言模型？
38. 【高频】如何评估一个大模型在你业务上的效果？
39. 私有化部署大模型需要考虑哪些问题（显存、吞吐、并发、成本）？
40. 【专家】给定 QPS 和平均输入输出长度，怎么估算需要多少张 GPU？
