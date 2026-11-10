# 03 Agent 架构与规划（50 题）

1. 【高频】什么是 Agent？和普通的 LLM 应用、Workflow 有什么区别？
2. 【高频】Agent 的核心组成部分有哪些（规划、记忆、工具、行动）？
3. 【高频】ReAct 的原理是什么？有什么缺点？
4. Plan-and-Execute 和 ReAct 有什么区别？各适合什么任务？
5. 【专家】Reflexion、Self-Refine 这类自我反思机制怎么实现？怎么避免无限反思？
6. 【高频】Workflow（固定编排）和自主 Agent 怎么选？什么时候该用哪种？
7. 【专家】如何设计一个"可控的自主性"：哪些步骤让模型决定，哪些步骤写死？
8. Agent 的任务分解（Task Decomposition）有哪些方法？
9. 【高频】Agent 陷入死循环或反复调用同一工具怎么处理？
10. 【高频】Agent 最大步数怎么设置？超过后怎么收尾？
11. Agent 执行到一半失败，如何做断点恢复？
12. 【专家】Agent 状态机怎么设计？run、step、tool_call 等状态如何流转？
13. OpenAI Assistants API 中 Assistant、Thread、Run、Step 分别是什么？
14. 【高频】LangChain 的核心抽象有哪些？你怎么评价它？
15. 【高频】LangGraph 和 LangChain 的区别是什么？StateGraph、节点、边、条件边怎么用？
16. 【专家】LangGraph 的 checkpoint 机制是什么？怎么实现人机协同（human-in-the-loop）中断和恢复？
17. AutoGPT、BabyAGI 这类早期 Agent 为什么在生产中很难用？
18. 【高频】你会自研 Agent 框架还是用开源框架？依据是什么？
19. 【专家】如何设计一个算子化（DAG/flow）的 Agent 执行引擎？算子之间怎么传递上下文？
20. Agent 的执行图用配置驱动还是代码驱动？各有什么优劣？
21. 【高频】Coding Agent（如 Claude Code、Cursor）的核心设计是什么？
22. 【专家】Claude Code 这类 Agent 的工具设计、上下文管理、子 Agent 机制有什么值得借鉴的地方？
23. Agent 中"路由（Router）"模式是什么？怎么实现意图路由？
24. 【高频】意图识别用大模型还是分类模型？怎么做混合方案？
25. Agent 如何处理用户中途改变需求或打断？
26. 【专家】实时语音/数字人 Agent 的对话打断（barge-in）怎么实现？
27. Agent 回复中如何插入结构化组件（卡片、表单、按钮）？
28. 【高频】Agent 如何在对话中挂载商业化组件（线索表单、商品卡）？召回时机怎么控制？
29. 多轮对话中，Agent 怎么判断任务是否已完成？
30. Agent 的"追问澄清"策略怎么设计？
31. 【专家】如何让 Agent 的行为可预测、可解释？
32. 什么是 Agentic RAG？和传统 RAG 有什么区别？
33. Agent 中的"思考"内容要不要展示给用户？流式展示怎么做？
34. Deep Research 类 Agent 的架构是什么样的？
35. 【专家】Deep Research 类 Agent 如何控制搜索轮次、去重和结果汇总？
36. Browser/Computer Use Agent 的实现思路是什么？难点在哪？
37. Code Interpreter 的实现原理是什么？沙箱怎么做？
38. 【高频】Agent 中的代码执行沙箱有哪些隔离方案（容器、gVisor、Firecracker、WASM）？
39. Agent 如何处理文件上传、文件解析（pdf、docx、pptx）？
40. 【专家】Agent 的多模型策略怎么设计：哪些步骤用大模型，哪些用小模型？
41. 模型调用失败时怎么做降级（换模型、换策略、返回兜底文案）？
42. 【高频】GPTs / 智能体平台（如文心智能体、Coze）的整体架构是什么样的？
43. 低代码智能体平台中，用户配置（人设、知识库、插件）如何转成运行时的 Agent？
44. 【专家】智能体平台如何同时支持上万个不同配置的 Agent？配置怎么加载和缓存？
45. Agent 的"人设"一致性怎么保证？
46. 【高频】Agent 和传统规则对话系统（任务型对话、槽位填充）怎么结合？
47. Agent 如何根据用户画像做个性化回复？
48. 【专家】Agent 的定时任务、主动触达（proactive agent）怎么设计？
49. 你认为当前 Agent 落地最大的瓶颈是什么？
50. 【专家】如果让你从零设计公司级的 Agent 平台，你会怎么分层？核心模块有哪些？
