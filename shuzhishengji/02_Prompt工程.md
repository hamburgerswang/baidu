# 02 Prompt 工程（30 题）

1. 【高频】一个好的 System Prompt 一般包含哪些部分？
2. 【高频】Zero-shot、Few-shot、CoT 分别适用什么场景？
3. Few-shot 示例怎么选？示例顺序会影响效果吗？
4. 【高频】如何让模型稳定输出 JSON？输出不合法时怎么兜底？
5. ReAct Prompt 的格式是什么？Thought、Action、Observation 各起什么作用？
6. Self-Consistency 的原理是什么？成本怎么控制？
7. Tree of Thoughts、Graph of Thoughts 和 CoT 的区别是什么？
8. 【高频】怎么减少模型"编造"内容？Prompt 层面有哪些手段？
9. 用"禁止做 X"和"应该做 Y"两种写法，哪种更有效？为什么？
10. 【专家】Prompt 迭代优化的流程是什么？怎么证明新版本比旧版本好？
11. 【高频】Prompt 如何做版本管理和灰度发布？
12. 角色设定（persona）对输出效果有多大影响？
13. 长 Prompt 中关键指令放在哪里效果最好？
14. 【专家】Prompt 缓存（Prompt Caching）的原理是什么？Prompt 结构怎么设计才能命中缓存？
15. 怎么用 Prompt 控制回复长度和风格？
16. 【高频】什么是 Prompt 注入？直接注入和间接注入有什么区别？
17. 【专家】如何防御 Prompt 注入？有没有根本解决办法？
18. 越狱（Jailbreak）攻击有哪些常见手法？怎么检测？
19. 多轮对话中，历史消息怎么组织到 Prompt 里？
20. 如何让模型在信息不足时主动追问而不是猜测？
21. 【高频】换模型后 Prompt 效果变差，怎么排查和迁移？
22. 自动 Prompt 优化（如 DSPy、APE）的思路是什么？
23. 中英文 Prompt 对中文任务效果有区别吗？
24. 【专家】如何设计一个 Prompt 模板系统，支持变量注入、多版本和 AB 实验？
25. 结构化 Prompt（XML 标签、Markdown 分区）有什么好处？
26. 输出格式要求和推理质量之间有冲突吗？怎么平衡？
27. 【高频】追问生成（Suggestion）的 Prompt 怎么设计？怎么评估追问质量？
28. 如何用 Prompt 让模型做分类、意图识别？和训练小模型相比怎么选？
29. Prompt 里放大量规则时，模型遵循率下降怎么办？
30. 【专家】在不换模型、不增加成本的约束下，如何系统性地把某类 badcase 率降下来？
