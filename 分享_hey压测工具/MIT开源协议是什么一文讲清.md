# MIT 开源协议是什么？一文讲清

hey 这款压测工具遵循的就是 MIT 开源协议。很多主流开源项目（React、Vue、jQuery、Rails、.NET Core 等）也都用它。这篇就把 MIT 协议讲清楚：它允许什么、要求什么、和其他协议有什么区别。

## 一、一句话理解

MIT 协议是目前最宽松、最流行的开源协议之一。核心就一句话：

> 你几乎可以随便用（商用、修改、闭源都行），但必须在副本里保留原作者的版权声明和这份许可证，而且作者不对软件承担任何责任。

## 二、协议全文与逐句翻译

MIT 协议全文很短，只有一段，这也是它受欢迎的原因之一。

```text
MIT License

Copyright (c) <year> <copyright holders>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

逐段翻译：

- **授权段**：特此免费授予任何获得本软件副本的人，不受限制地使用本软件的权利，包括使用、复制、修改、合并、发布、分发、再许可、以及销售软件副本，也可以允许拿到软件的人这样做，但要满足下面的条件。
- **条件段**：在软件的所有副本或重要部分中，都必须包含上面的版权声明和这份许可声明。
- **免责段**：本软件按"原样"提供，不提供任何形式的担保。作者或版权持有人不对任何索赔、损害或其他责任负责。

## 三、它给了你什么权利，又要求你做什么

|类别|内容|
|:---|:---|
|允许（权利）|商用、修改、分发、私用、再许可、闭源（可以把它用进你的闭源商业产品）|
|要求（义务）|在你分发的副本中保留版权声明和这份许可证原文|
|不提供（限制）|不提供任何担保；作者不承担任何责任；没有授予商标权|

一句话：**义务只有一条——保留版权和许可声明。**

## 四、为什么这么多项目选 MIT

- **简单**：全文一段话，非法律专业的人也能读懂。
- **宽松**：几乎没有限制，商用和闭源都没问题，企业用得放心。
- **兼容性好**：可以和绝大多数其他协议（包括 GPL）组合使用。
- **传播快**：限制越少，越多人愿意用、愿意基于它做二次开发，有利于项目扩散。

## 五、和其他常见开源协议的对比

|协议|宽松程度|是否要求衍生作品开源|是否含专利授权|典型项目|
|:---|:---|:---|:---|:---|
|MIT|最宽松|否|否（仅版权，不含专利条款）|React、Vue、jQuery、hey|
|BSD（2/3-Clause）|很宽松，和 MIT 接近|否|否|Nginx、FreeBSD|
|Apache 2.0|宽松，但更严谨|否|是（明确授予专利权，并有专利反制条款）|Kubernetes、Android|
|MPL 2.0|中等（文件级 Copyleft）|改动的文件要开源，新增文件可闭源|是|Firefox|
|LGPL|较强（库级 Copyleft）|动态链接可闭源，修改库本身要开源|是|部分 C/C++ 库|
|GPL v3|最严格（强 Copyleft）|是，衍生作品必须用同样协议开源|是|Linux 内核(v2)、Git|

**选型简记：**

- 想让别人（包括商业公司）尽可能自由地用你的代码 → MIT / BSD / Apache 2.0。
- 在意专利保护、面向企业 → Apache 2.0。
- 希望衍生作品也必须开源、保持开放 → GPL 系列。

## 六、使用 MIT 软件时的注意事项

- **必须保留 LICENSE 文件和版权声明**：把别人 MIT 的代码用进你的项目时，要把它的许可证原文和版权行一起带上（通常放在项目的 LICENSE、NOTICE 或第三方声明里）。这是唯一的硬性义务，漏掉就构成侵权。
- **可以闭源**：你基于 MIT 代码做的产品可以不开源、可以收费，没问题。
- **不改原作者署名**：保留的是原作者的版权声明，不是把它换成自己的。
- **自担风险**：因为有免责条款，用出问题作者不负责，关键场景要自己做测试和评估。
- **注意商标**：MIT 只授予版权相关权利，不授予商标权，用别人的项目名做宣传要另外注意。

## 七、给自己的项目加上 MIT 协议

1. 在项目根目录新建 `LICENSE` 文件，粘贴上面的协议全文。
2. 把 `<year>` 换成年份，`<copyright holders>` 换成你的名字或组织，例如 `Copyright (c) 2026 Wang Peng`。
3. 在 README 里注明 `License: MIT`。
4. 如果用了别人 MIT 的代码，把对方的版权声明也一并保留。

## 八、小结

MIT 协议的精髓就是"**给你最大自由，只要你保留我的署名，并且我不担责**"。它简单、宽松、兼容性好，所以成了开源世界里最流行的协议之一。hey 选择 MIT，也是希望任何人都能自由地使用、修改、集成这款压测工具，包括用在商业项目里。
