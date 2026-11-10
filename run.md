# run.sh 使用说明

`run.sh` 用来在浏览器中查看两个题库网页：

- **晋升考核题库**：`shuzhishengji/题目与答案.html`，共 635 道题目和参考答案。
- **述职题库**：`shuzhi_web.html`，题目来自 `shuzhi_questions.json`。

## 快速开始

```bash
cd /Users/v_wangpeng42/Desktop/work/go/self/baidu
./run.sh qa
```

浏览器会自动打开页面。查看期间不要关闭终端，看完按 `Ctrl+C` 停止。

## 命令

| 命令 | 作用 |
|:---|:---|
| `./run.sh` | 同时打开两个题库 |
| `./run.sh qa` | 只打开晋升考核题库 |
| `./run.sh shuzhi` | 只打开述职题库 |
| `PORT=9000 ./run.sh` | 指定端口（默认 8765），可以和上面的参数一起用 |

## 脚本做了什么

1. 运行 `shuzhishengji/build_qa_html.py`，根据 `shuzhishengji/题目与答案/` 下的 md 重新生成 `题目与答案.html`。改过 md 之后，重新运行脚本就能看到最新内容。
2. 在 `127.0.0.1` 上启动本地服务（`python3 -m http.server`），只有本机能访问。
3. 打印两个页面的地址，并用浏览器打开。
4. 按 `Ctrl+C` 或关闭终端时，停止本地服务。

默认地址：

- 晋升考核题库：`http://127.0.0.1:8765/shuzhishengji/题目与答案.html`
- 述职题库：`http://127.0.0.1:8765/shuzhi_web.html`

## 页面操作

| 操作 | 晋升考核题库 | 述职题库 |
|:---|:---|:---|
| 上一题 / 下一题 | 按钮，或键盘 ← → | 按钮，或键盘 ← → |
| 显示 / 隐藏答案 | 按钮，或空格 | 按钮，或空格 |
| 随机 | "随机抽题"按钮，或 R | "打乱顺序"按钮 |
| 筛选 | 按分类、按【高频】或【专家】、按关键词搜索 | 无 |
| 跳转 | 输入题号后点"跳转" | 无 |
| 记住位置 | 再次打开时回到上次看到的题 | 无 |

## 不启动服务也能看

晋升考核题库的题目已经打包进 html 文件，可以直接打开：

```bash
open shuzhishengji/题目与答案.html
```

述职题库需要读取 json 文件，浏览器不允许直接双击打开的页面读取本地文件，所以要用 `run.sh` 启动服务。直接双击打开时，页面会提示手动选择 `shuzhi_questions.json`。

## 常见问题

**页面显示"无法访问此网站""拒绝连接"**

本地服务没有在运行。原因通常是终端已经关闭、按过 `Ctrl+C`，或者访问的端口和启动时的端口不一致。重新执行 `./run.sh`，并保持终端打开。

**提示"端口已被占用"**

换一个端口：`PORT=9000 ./run.sh`。

**提示 Permission denied**

给脚本加上执行权限：`chmod +x run.sh`，或者用 `bash run.sh` 运行。

**浏览器没有自动打开**

复制终端里打印的地址，在浏览器中手动打开。

**改了 md，页面没有变化**

重新运行 `./run.sh`，然后刷新浏览器。如果只想重新生成页面、不启动服务，运行 `python3 shuzhishengji/build_qa_html.py`。

## 相关文件

| 文件 | 说明 |
|:---|:---|
| `run.sh` | 启动脚本 |
| `shuzhi_web.html`、`shuzhi_questions.json` | 述职题库的页面和题目 |
| `shuzhi_game.py` | 述职题库的命令行答题打分小游戏 |
| `shuzhishengji/题目与答案/*.md` | 晋升考核题库的题目和答案（修改这里） |
| `shuzhishengji/build_qa_html.py` | 根据 md 生成网页 |
| `shuzhishengji/qa_template.html` | 网页模板（样式和交互） |
| `shuzhishengji/题目与答案.html` | 生成出来的网页，不要直接修改 |

运行环境：macOS，需要 `python3`。
