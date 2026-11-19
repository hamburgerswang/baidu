# BuilderAgent 需求 SOP — 总结

> 来源：[BuilderAgent需求SOP](https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/sKDyMRFxWe/6XrP29TGw_/vyoLQJb1plN3bj)（创建：赵虓鲁，发布：黄泽滨）
> 交流反馈如流群：13166269

## 一句话概括

一套基于 Comate AI 智能体的"人机协同"敏捷开发全流程，覆盖从需求准备到上线的 **7 个阶段**。人工负责决策、评审、上线把关，机器负责代码生成、测试、部署；阶段 2~4 为可迭代 loop，阶段 5~7 线性推进。适用于具备完整沙箱环境的数字人视频等业务线。

## 七个阶段速览

- **阶段1 需求准备【人】**：编写 PRD、在「AI 提效空间」提交 Feature 卡片（类型必须 Feature、状态流转到"详评完成"、开发环境选"沙箱"）、通过 eClaw 机器人拉项目群、按手册创建并配置沙箱、完成 Comate 授权。初始化完成标志：`CLADU.md`（AI 环境就绪）、`WIZSTAR_READY.txt`（模块部署完成，约 10 分钟）。
- **阶段2 需求澄清【loop】**：Skill `requirements-clarification`。在 Comate 切 Spec Mode，提交澄清指令（附 iCafe 卡片 + PRD），产出澄清 doc → 人工 review → 产出 `spec.md`、`tasks.md`。
- **阶段3 开发编排【loop】**：Skill `enhanced-superpowers-flow`。按 task 列表逐任务写增量代码并补单测。PM 重点检查：方案是否全覆盖需求、异常态/跨服务链路是否遗漏、是否在开发分支而非 master、单测/E2E 是否真实执行。涉及 MySQL/Redis/MQ/数据格式变更需生成数据变更技术文档并与研发确认。
- **阶段4 测试编排【loop】**：AICR 静态审查（`cecom-ep-aireview`）→ E2E 测试（`frontend-e2e`）→ 人工环境自测 → 质量检查；未通过回到开发。该流程通常已自动包含在开发步骤里。
- **阶段5 沙箱准出【自】**：Skill `submit-code`。完善 spec 沉淀业务知识、扫描变更自动拆 story 子卡片、检查/创建分支、逐仓库生成 commit 并推送 CR。质量门未通过不得提交。
- **阶段6 test 环境验证**：生成迭代摘要推送群 → 有 DB 变更需人工上线 → 自动部署 qa01-02（轮询耗 token 较多，最多同时 2 个需求在海外环境验证）→ 生成测试用例（lazymind）→ 人工 review 用例 → 验证 test 环境 → 流转卡片到"测试完成"。
- **阶段7 项目上线【人】**：值班 RD 完成 CR 合入、解决冲突、预发上线（builder 协同验证）、prod 上线（builder 验证最终效果）、case 自动收集。前端 vibe coding 需走 iCode 检查通过后一键通知 CR 人、登记上线单、经前端值周发布。

## 关键约束与注意点

- iCafe 卡片必须在「AI 提效空间」创建，否则自动化流程识别不到卡片字段。
- 单测/E2E 结果须如实标注：`failed` 必须修复，`skipped`/`not_covered`/环境阻断须说明原因，不能写成通过。
- 代码改动走开发分支，禁止直接改 master。
- 自动部署轮询消耗 token 较多，需关注成本。
- 权限相关联系人：zhaoxiaolu01、huangzebin01、zhangyongzhe01；代码库权限需加入 `dh_agent_builder@baidu.com` 邮件组。

## 阶段 ↔ Skill 对照

- 阶段1：`sandbox-manager`
- 阶段2：`requirements-clarification`
- 阶段3：`enhanced-superpowers-flow`
- 阶段4：`cecom-ep-aireview`、`frontend-e2e`、`playwright-cli-smoke`
- 阶段5：`submit-code`、`icafe-subcard-splitter`、`create-branch`、`smart-commit`

## 后续优化方向（文档 todo）

- 判断自动化等级，与 PMO 建立此类需求的发布机制
- 业务知识库建设，提升 AICR 准确率至可自动合并
- 海外环境并发能力对齐、token 成本优化
- 对齐研发开发规范、直播模板复用 or 新建
