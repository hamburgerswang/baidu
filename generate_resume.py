# -*- coding: utf-8 -*-
"""根据原简历内容 + 百度工作总结，生成新版简历 docx。"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ACCENT = RGBColor(0x1F, 0x4E, 0x79)   # 深蓝，与原简历标题色接近
DARK = RGBColor(0x33, 0x33, 0x33)

doc = Document()

# ---------- 页面设置 ----------
sec = doc.sections[0]
sec.top_margin, sec.bottom_margin = Cm(1.6), Cm(1.6)
sec.left_margin, sec.right_margin = Cm(1.9), Cm(1.9)

# ---------- 全局默认字体 ----------
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
style.paragraph_format.space_after = Pt(2)


def set_east_asian(run, name="微软雅黑"):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def add_para(text="", size=10.5, bold=False, color=DARK, align=None,
             space_before=0, space_after=2, indent=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    set_east_asian(r)
    return p, r


def add_bottom_border(p):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), "1F4E79")
    pBdr.append(bottom)
    pPr.append(pBdr)


def section_title(text):
    p, r = add_para(text, size=13, bold=True, color=ACCENT, space_before=10, space_after=4)
    add_bottom_border(p)


def bullet(text, size=10.5):
    p, r = add_para("• " + text, size=size, indent=0.4)


def mixed_para(parts, size=10.5, space_before=0, space_after=2, indent=None):
    """parts: [(text, bold), ...] 同一段内混排"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    for text, bold in parts:
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = DARK
        set_east_asian(r)
    return p


# ================= 头部 =================
p, r = add_para("王 鹏", size=20, bold=True, color=ACCENT,
                align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
p, r = add_para("求职意向：高级研发工程师（Go 方向）        期望薪资：面谈",
                size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
add_para("籍贯：河北承德        出生年月：1994.03        民族：汉族        政治面貌：中共党员",
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
add_para("联系电话：15932412024        邮箱：15932412024@163.com",
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)

# ================= 教育背景 =================
section_title("教育背景")
mixed_para([("辽宁工业大学", True), ("    计算机科学与技术（本科）", False),
            ("                                        2020 - 2022", False)])

# ================= 专业技能 =================
section_title("专业技能")
skills = [
    [("熟练掌握 Go 及主流框架（gin、beego），具备大规模服务端系统的设计与开发经验；", False)],
    [("熟练掌握 PHP 及主流框架（tp、ci、yii、laravel）；", False)],
    [("熟练掌握 Python 及主流框架（flask、django、fastapi、langchain）；", False)],
    [("熟练使用 MySQL、MariaDB、Redis、MongoDB 等主流数据存储；", False)],
    [("熟练使用 Kafka、OTel、Elasticsearch、SSE 等其他技术；", False)],
    [("熟悉 AIGC 技术栈和大模型基本原理与使用方式，能够基于已有模型进行应用开发与功能实现；", False)],
    [("具备平台级系统架构能力与跨需求协调经验，主导过强耦合多需求的按期上线交付。", False)],
]
for s in skills:
    bullet(s[0][0])

# ================= 工作经历 =================
section_title("工作经历")


def job(company, title, period, lines):
    mixed_para([(company, True), ("    " + title, False),
                ("                                                            " + period, False)],
               space_before=6)
    for l in lines:
        bullet(l)


job("百度（Baidu）", "高级研发工程师", "2025年06月 – 2026年10月", [
    "负责智能体平台与互动数字人平台的后端研发，从单点需求开发成长为 PaaS/Pipeline 平台级能力的 server 侧 RD 负责人，累计代码提交约 324 次。",
    "主导数字人 PaaS/Pipeline 平台 server 侧建设：形象制作与素材能力、端到端评估平台线上化、资源池治理、生成式质检等核心能力；作为负责人协调两个强耦合需求（Pipeline 平台、端渲染方案接入）同步于 2026/08/31 如期上线。",
    "主导大规模数据治理：dbqa 7 亿存量内容治理、20B 衔接视频数据清理，并建设 PaaS 公共资源池，提升资源复用率。",
    "沉淀智能体平台基础能力：mount 服务链路多次迭代、模型链路 trace 完善、agent-tool 工具链建设，持续保障平台稳定性。",
    "深度参与商业化落地：B 端商业化工具、Q2C 高价值 Query 回复优化、线索表单提示词实验管控及上线后评估、会员售卖能力建设。",
])

job("幻世生成（北京）科技有限公司（腾讯员工创业孵化项目）", "高级开发工程师", "2023年10月 – 2025年06月", [
    "参与 AI 驱动型产品的后端架构设计与核心功能开发，主导基于 Go 语言的服务端系统实现。",
    "深度参与 AIGC 相关技术落地，包括大模型对话系统集成、多模态内容生成对接、实时交互逻辑优化等。",
    "与算法团队、前端团队高效协作，推动 AI 能力在业务场景中的融合与应用。",
])

job("博彦科技广州有限公司北京分公司（外包至腾讯）", "高级开发工程师", "2021年03月 – 2023年10月", [
    "负责腾讯内部多个中后台系统的开发与维护，涵盖微服务架构设计、数据流转、接口联调等关键环节。",
    "熟练使用 Go / Python / PHP 等语言构建高可用服务，提升系统性能与稳定性。",
    "积极参与项目迭代与代码评审，保障高质量交付。",
])

job("北京艺麟盛世科技发展有限公司", "后端开发工程师", "2018年02月 – 2021年02月", [
    "主导企业级后端系统的开发与维护，涉及电商平台、管理系统等多个项目。",
    "使用 PHP / Python 技术栈完成模块开发、数据库设计及接口调试等工作。",
    "注重系统可扩展性与安全性，具备从需求分析到部署上线的全流程开发经验。",
])

# ================= 项目经验 =================
section_title("项目经验")


def project(name, desc, tech, duties):
    mixed_para([(name, True)], space_before=6)
    add_para("项目描述：" + desc, indent=0.4)
    add_para("使用技术：" + tech, indent=0.4)
    add_para("主要职责：", indent=0.4)
    for d in duties:
        bullet(d)


project(
    "百度 - 互动数字人 PaaS / Pipeline 平台（核心项目）",
    "面向数字人内容生产的一站式 PaaS 平台，覆盖形象包制作、素材管理、端到端评估（Pipeline）、质检众测、公共资源池治理与生成式底板等能力，支撑可口可乐定制等大型项目交付。",
    "Go + 微服务 + MySQL + Redis + Pipeline 平台",
    [
        "作为平台 server 侧 RD 负责人，主导 PaaS 平台一期与端渲染方案接入 Pipeline 两个强耦合需求的设计、开发与跨团队协调，同步于 2026/08/31 如期上线。",
        "主导端到端评估平台线上化（Pipeline 二期）：评估集构建、评估模板更新、质检支持众测、评估重试信息记录、生产流程衔接与展示优化。",
        "建设形象制作与素材能力：自研 V1 版形象制作、形象包多表情多动作自定义配置、背景素材列表迭代，支撑可口可乐项目 V3 版本交付。",
        "设计生成式能力方案：PPL 支持生成式 / 生成式底板 / 长底板循环方案，建设机器自动化质检数据统计与质检模型接入。",
        "建设 PaaS 公共资源池与治理体系：公共库形象包、资源池梳理与治理、清理 20B 衔接视频数据；连续两期主导 O 端平台技术优化。",
        "推动国内 PaaS 平台声音升级（接入豆包）、for 大会形象定制支持，并参与实时互动数字人平台二期建设。",
    ],
)

project(
    "百度 - 智能体平台与商业化落地",
    "百度智能体（Agent）平台基础能力建设与商业化方向，覆盖平台稳定性、模型与数据链路、工具链建设及线索/会员商业化能力。",
    "Go + 微服务 + MySQL + Redis + Kafka + AB 实验",
    [
        "主导 mount 服务链路多次迭代：丢参数修复、新增 agent_template 来源、transdata 白名单、mount data 获取优化，保障核心链路稳定。",
        "完善模型与数据能力：deepseek 模型链路 trace、RFQ/session 获取能力升级、对话历史获取、平台数据捞取能力升级。",
        "建设 agent-tool 工具链：文件转换服务（修复 libreoffice 执行错误、新增 pptx 转图片）。",
        "参与互动数字人对话能力建设：多人对话调度数据需求与策略优化、对话历史导出、对话数据冷备、互动数字人 amis 改造、TTS 工具；主导 dbqa 7 亿存量内容治理。",
        "参与商业化项目：B 端商业化工具、Q2C 首轮高价值 Query 回复优化、线索表单提示词实验管控及上线后评估、线索工具会员售卖、B 端 v.10 商业化模板、挽留提问策略。",
    ],
)

project(
    "RPGGO.AI - RPGGO 游戏",
    "基于人工智能技术开发的个性化角色扮演游戏，通过大模型实现角色对话、剧情生成与互动体验，结合图像生成和语音处理能力，打造沉浸式 AI 驱动的游戏世界。",
    "Go + AI（LLM / 文生图 / 语音识别）+ Redis + MySQL + SSE",
    [
        "AI 对话系统集成：与算法工程师协作，基于 SSE 协议实现与 AI 大模型的长连接交互，保障实时、稳定的对话体验。",
        "多模态内容生成支持：对接图像生成模块，实现文本到图像的功能展示；协同语音工程团队，完成 TTS 与 STT 的数据交互与流程优化。",
        "核心业务逻辑设计与维护：负责游戏核心玩法与规则系统的开发与维护，确保 AI 与游戏逻辑的高效融合与稳定运行。",
        "前后端联调与协同开发：与 1D/2D 游戏客户端深度对接，打通游戏状态同步、用户行为反馈等关键链路，提升整体用户体验。",
    ],
)

project(
    "腾讯网 - 页面分发系统",
    "基于 Go + Nginx + SSI 的页面资源存储、分发、更新服务。",
    "Go + Redis + Dcache + Kafka + CBS + MySQL",
    [
        "进行版本的创新迭代与优化，保证产品的稳定运行。",
        "参与 dispatch auth 分发侧鉴权服务系统的开发和维护。",
        "参与 dispatch server 分发侧 server 的开发和维护。",
        "参与 ssi server 接入服务的开发和维护。",
    ],
)

project(
    "腾讯网 - 频道有限刷",
    "频道通过运营平台添加内容，腾讯网 kv_srv 程序拉取接口内容做离线缓存并且输出到接口。",
    "Go + Trpc + Protobuf + Redis + MySQL",
    [
        "参与项目的整体创新迭代与优化，保证产品的稳定运行。",
        "参与接口文档的编写与管理。",
        "参与接口服务的升级和优化。",
        "参与代码 coding，保证代码的可读性和高可用性。",
    ],
)

project(
    "腾讯新闻/微信插件 - 频道推荐",
    "频道获取个性化推荐内容，通过程序的 bpacker -> format -> apacker -> merger 打包成数据信息流。",
    "Go + Trpc + Protobuf + Redis + AB 实验",
    [
        "参与项目的整体创新迭代与优化，保证产品的稳定运行。",
        "参与接口文档的编写与管理。",
        "参与接口服务的升级和优化。",
        "参与代码 coding，保证代码的可读性和高可用性。",
    ],
)

out = "/Users/v_wangpeng42/Desktop/work/go/self/baidu/王鹏简历-新版.docx"
doc.save(out)
print("saved:", out)
