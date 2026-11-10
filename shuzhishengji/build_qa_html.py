"""把 题目与答案/*.md 打包成可离线打开的翻页网页 题目与答案.html。

用法（在任意目录执行）：python3 shuzhishengji/build_qa_html.py
修改 md 后重新运行即可刷新网页；页面样式和交互在 qa_template.html 中。
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, '题目与答案')
TEMPLATE = os.path.join(BASE, 'qa_template.html')
OUT = os.path.join(BASE, '题目与答案.html')

files = []
for name in sorted(os.listdir(SRC)):
    if not re.match(r'^\d+_.*\.md$', name):
        continue
    text = open(os.path.join(SRC, name), encoding='utf-8').read()
    title = re.match(r'^# (.+?)（\d+ 题）', text, re.M).group(1).strip()
    section, qs, cur = '', [], None
    for line in text.split('\n'):
        m_sec = re.match(r'^## (.+)$', line)
        m_q = re.match(r'^### (\d+)\. (.+)$', line)
        if m_q:
            cur = {'no': int(m_q.group(1)), 'title': m_q.group(2).strip(), 'section': section, 'lines': []}
            qs.append(cur)
        elif m_sec:
            section, cur = m_sec.group(1).strip(), None
        elif cur is not None and not line.startswith('**答案：**'):
            cur['lines'].append(line)
    for q in qs:
        q['answer'] = '\n'.join(q.pop('lines')).strip()
    files.append({'title': title, 'questions': qs})

data = json.dumps(files, ensure_ascii=False).replace('</', '<\\/')
html = open(TEMPLATE, encoding='utf-8').read().replace('/*__DATA__*/null', data)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(OUT, sum(len(f['questions']) for f in files), 'questions', len(html) // 1024, 'KB')
