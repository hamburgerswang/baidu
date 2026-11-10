> 原文：https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/KeF15lNOtH/-UXFkEkRyR/igyobhmrVCxd3l

Python包管理⼯具的演进史

# **1.** 第⼀阶段:前 **Pip** 时代
## **1.1 distutils**
Python 1.6 (2000年) 引⼊了标准库 distutils 。它是所有 Python 打包⼯具的鼻祖,但它严格来说 只是⼀个"构建系统",⽽⾮包管理器。在Python 3.10中被标记为废弃(deprecated)。在Python 3.12 标准库中已被彻底移除。

#### distutils 是什么？(历史背景)
在 pip 和 wheel 出现之前，distutils 是构建和安装 Python 模块的标准方法。它的主要作用是：

1. 构建 (Build): 将 Python 源码（以及可能的 C/C++ 扩展）编译成可分发的格式。
2. 分发 (Distribute): 创建源代码包（Source Distributions, sdist）。
3. 安装 (Install): 将包安装到用户的 Python site-packages 目录中。

#### 示例
假设你的项目目录结构如下：

```
my_project/
├── setup.py
├── README.txt
├── script_demo.py
├── my_module/
│   ├── __init__.py
│   └── core.py
└── src/
    └── my_extension.c
```
下面是对应的 setup.py：

```python
# 注意：导入的是 distutils.core 而不是 setuptools
from distutils.core import setup, Extension

# 1. 定义 C 扩展模块
# distutils 的优势在于它能处理简单的 C/C++ 编译
c_ext = Extension(
    'my_extension',           # 模块名
    sources=['src/my_extension.c'], # 源码
    include_dirs=['/usr/local/include'], # 头文件路径
    libraries=['m']           # 链接库 (例如数学库 libm)
)

setup(
    # --- 基础元数据 ---
    name='MyLegacyProject',
    version='1.0.0',
    description='这是一个纯 distutils 构建示例',
    author='Your Name',
    author_email='author@example.com',
    url='https://example.com',

    # --- 包含的 Python 包 ---
    # distutils 不支持 find_packages()，必须手动列出
    packages=['my_module'],

    # --- 包含独立的 py 模块 (不属于任何 package) ---
    py_modules=['extra_utils'],

    # --- 包含 C 扩展 ---
    ext_modules=[c_ext],

    # --- 安装可执行脚本 ---
    # 这些文件会被拷贝到系统的 bin 目录下（如 /usr/bin）
    scripts=['script_demo.py'],

    # --- 数据文件 ---
    # 将文件安装到系统特定位置 (目标路径, 源文件列表)
    # 注意：distutils 的 data_files 通常用于安装配置文件到 /etc 等位置
    data_files=[
        ('etc/my_project', ['README.txt']),
    ],
    
    # --- 分类器 ---
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
```
cli命令

```shell
# 构建项目（在 build/ 目录下生成文件）：
python setup.py build

# 构建分发文件
python setup.py sdist        # 源码分发, 生成 .tar.gz 文件
# 构建的二进制包不能通过python setup.py install安装，需要手动解压到site-packages目录。
python setup.py bdist        # 二进制分发Unix/Linux
python setup.py bdist_wininst  # 二进制分发Windows
python setup.py bdist_rpm    # 二进制分发RedHat

# 将模块安装到本地的 site-packages 目录中
python setup.py install
```
#### 技术局限
* ⽆法管理依赖: 它不知道你的包依赖什么。⽤⼾必须⼿动下载并安装所有前置依赖。
* ⽆卸载机制: 安装是单向的(复制⽂件到 site-packages),没有记录⽂件清单,⽆法⾃动移除。

### **1.2 Setuptools** 与 **easy_install**
由于 distutils 在依赖管理上的缺失，Phillip Eby 在 2004 年启动了 setuptools 项目。setuptools 是对 distutils 的一层封装和扩展，它引入了至关重要的 **install_requires** 参数，允许开发者在 setup.py 中声明项目依赖。配合其捆绑的 easy_install 命令行工具，Python 开发者第一次体验到了“自动下载并安装依赖”的便利 。

setuptools 还引入了 **.egg** 格式，这是一种早期的二进制分发格式（类似于 Java 的 JAR 文件）。Egg 文件实际上是一个 ZIP 压缩包，包含了编译好的字节码和元数据，Python 可以直接导入其中的模块而无需解压。这种格式极大地简化了分发过程，特别是对于包含非 Python 资源文件的库。

#### 代码考古
这是⼀个典型的旧时代打包脚本,你可以看到它不仅定义元数据,还试图动态修改环境:

```shell
# setup.py (setuptools 早期⻛格)
from setuptools import setup, find_packages
setup(
 name="LegacyApp",
 version="0.1.0",
 packages=find_packages(),

 # 依赖声明:⾮常宽松,极易导致未来版本不兼容
 install_requires=[
    "requests",
    "BeautifulSoup",
 ],

 # .egg 特有的 entry_points,当时⾮常先进的概念
 # entry_point 是一个特殊的分组，专门用于注册命令行可执行脚本
 # 当用户安装该包时，setuptools 会自动生成一个名为 legacy-cli 的可执行文件
 # legacy.main是模块路径，即legacy/main.py,调用函数时run
 entry_points={
    'console_scripts': [
        'legacy-cli = legacy.main:run',
    ],
 },

 # 允许直接从 zip ⽂件运⾏,虽然⽅便但导致调试极为困难
 zip_safe=True,
)
```
#### egg包构建
```toml
# 构建二进制包
python setup.py bdist_egg
```
#### egg包安装:
```bash
# 从PyPI下载并安装包
easy_install LegacyApp
# 输出:
# Searching for LegacyApp
# Reading http://pypi.python.org/simple/LegacyApp/
# Best match: LegacyApp 0.1.0
# Processing LegacyApp-0.1.0-py2.7.egg
# ...
# Installed /usr/lib/python2.7/site-packages/LegacyApp-0.1.0-py2.7.egg
```
#### 核⼼痛点与实战问题
`setuptools`和`easy_install`的野心过大，试图解决从构建、分发到安装、管理的整个生命周期问题。但其有两个问题：

1. 其内部架构极其复杂且难以维护
2.  easy_install 没有卸载命令! ⼀旦安装了⼀个错误的包,或者想升级⼀个包,你往往需要⼿动进⼊系统⽬录删除⽂件,这经常导致残留的 .pth ⽂件破坏 Python 环境。

# **2.** 第⼆阶段:标准化时代——Pip 与 Virtualenv 的组合
时间跨度:*2008*年 *- 2016*年左右

随着 Python 社区的壮⼤,Ian Bicking 创建了 pip (Pip Installs Packages) 和 virtualenv ,这标志 着 Python 包管理进⼊了现代⽂明。

1. pip 解决`easy_install`无法卸载依赖的问题
2. .whl包格式替代.egg格式，解决 `.egg` 格式的[不足](https://chat.deepseek.com/share/hpqielvp400qiqzr4n)以及源码分发时需要现场编译的问题--可能因环境不同导致安装失败（如 C 扩展需本地编译）
3. venv 解决**版本冲突** 和 **依赖地狱**



### 从案例说起
#### pip引入
```python
from flask import Flask

# 创建 Flask 应用实例
app = Flask(__name__)

# 定义路由和视图函数
@app.route('/')
def hello_world():
    return 'Hello, World!'

# 启动应用
if __name__ == '__main__':
    app.run()
```
运行

```python
python main.py

# 没有依赖，报错
Traceback (most recent call last):
 File "/Users/guochang05/selflearn/python/pyenv/main.py", line 1, in <module>
    from flask import Flask
ModuleNotFoundError: No module named 'flask'
```
安装依赖

```bash
pip3 install flask
```
查看flask安装目录

```bash
pip3 show  flask
# output
Location: /opt/miniconda3/lib/python3.9/site-packages
```
包被安装在了全局目录，这样有两个问题:

1. 版本冲突：A项目需要1.1.x，B项目需要2.0.x，由于B项目升级了flask库，会导致A项目无法运行。
2. 依赖地狱：

    * 你的项目 MyApp 需要 PackageA==1.2 和 PackageB==2.0
    * PackageA==1.2 依赖 CommonLib>=1.0,<2.0
    * PackageB==2.0 依赖 CommonLib>=1.5,<2.5
    * 但是 CommonLib 的 1.5 版本引入了一个破坏性变更

#### venv引入
为了解决**版本冲突** 和 **依赖地狱** ，Python 3.3+ 内置了 venv 模块，用于创建隔离环境。其原理简单粗暴：在环境根目录下新建一个 **bin** 目录,然后把系统 Python 的 **python** 和 **pip** 文件复制进去。这样新环境获得的就是隔离的 **独立 Python 解释器** 和 **pip** 。

创建虚拟环境

```bash
# 推荐使用.venv 作为虚拟环境目录名,因为ide会自动识别并配置环境
python3 -m venv .venv

# 激活虚拟环境, 实现的本质是设置python文件的path为$VIRTUAL_ENV/bin/python, 后 包的引入路径变为了$VIRTUAL_ENV/lib/pythonX.X/site-packages,替换了原始的全局目录, 使得每个项⽬拥有独⽴的 site-packages。
source myenv/bin/activate

# Windows
myenv\Scripts\activate

# 显示venv目录结构
tree -L3 .venv/
.venv/
├── bin
│   ├── Activate.ps1
│   ├── activate
│   ├── activate.csh
│   ├── activate.fish
│   ├── pip
│   ├── pip3
│   ├── pip3.9
│   ├── python -> python3
│   ├── python3 -> /opt/miniconda3/bin/python3
│   └── python3.9 -> python3
├── include
├── lib
│   └── python3.9
│       └── site-packages
└── pyvenv.cfg
```
#### 管理依赖 (requirements.txt)
pip解决了包依赖安装的问题，venv解决了依赖隔离的问题，那么还有个对项目的依赖管理问题。

早期的解决方案是使用`requirements.txt`文件，在里面添加对应的依赖包，由于没有自动化的方式，对该文件的维护有两种：

1. 手动维护，每次安装依赖包后，手动更新`requirements.txt`文件。
2. 使用`pip freeze > requirements.txt`，每次安装依赖包后，使用`pip freeze`命令生成`requirements.txt`文件。

后续其他人只要使用`pip install -r requirements.txt`就可以把所有依赖包安装出来。

###### 存在的问题
1. 如果是手动维护方式，无法保证每次新增包都写入requirements.txt，这样就会导致依赖不一致。
2. 如果是使用pip freeze的方式，如果删掉某个依赖包后，该包依赖的其他包通过pip freeze不会删除，出现孤儿依赖的问题。

# **3.** 第三阶段：一体化工具：Pipenv ， Poetry，UV
到目前为止，python有了现代化的依赖管理，虚拟环境，基于这些，让我们回顾一下，对于一个新项目，我们引入一个包，如何处理：

1. 创建虚拟环境：`python -m venv venv`
2. 激活虚拟环境：`source .venv/bin/activate`
3. 新建`pyproject.toml`文件，在其中定义所需要的依赖
4. 执行依赖安装：`pip install -e .`

还是有下面的问题：

1. 流程操作有点复杂
2. 引入依赖无法自动更新`requirements.txt`文件

这些问题催生了一系列的的包管理工具。`Pipenv`（由 Kenneth Reitz 在 2017 年发起）和 `Poetry`（由 Sébastien Eustace 在 2018 年创建）是其中的佼佼者，`uv` 是由 Astral（Ruff、Black 等工具的开发者）推出的 超快 Python 包安装器和解析器，旨在替代 pip 和 pip-tools，提供极速的依赖解析和安装体验。

它们的核心思想是 **“一体化”**：将**虚拟环境管理、依赖声明和版本锁定**整合进一个工作流中。

### Pipenv 与 Pipfile
Pipenv 引入了 `Pipfile` 和 `Pipfile.lock`。

* `Pipfile`: 取代了 `requirements.txt`，使用 TOML 格式。它区分了 `[packages]`（生产依赖）和 `[dev-packages]`（开发依赖），解决了环境依赖分离的问题。
* `Pipfile.lock`: 自动生成的锁文件，记录了每个包的确切版本和哈希值，保证了在任何环境下都能安装完全相同的依赖，实现了可复现的构建。

**工作流示例:**

```bash
# 安装一个包，Pipenv 会自动创建虚拟环境、更新 Pipfile、生成 Pipfile.lock
$ pipenv install requests

# 安装开发依赖
$ pipenv install pytest --dev

# 从锁文件安装所有依赖
$ pipenv sync
```
### Poetry 与 pyproject.toml
Poetry 则更进一步，它从一开始就拥抱了 `PEP 518` 定义的 `pyproject.toml` 文件。Poetry 使用 `pyproject.toml` 的 `[tool.poetry]` 部分来管理项目元数据、依赖、脚本等所有信息。

* `pyproject.toml`: 作为唯一的项目配置文件，统一了原本散落在 `setup.py`, `requirements.txt` 等文件中的信息。
* `poetry.lock`: 与 `Pipfile.lock` 类似，提供了确定性的依赖锁定。
* **内置构建系统**: Poetry 还自带了打包和发布功能，可以轻松将项目构建为 Wheel 和 sdist，并发布到 PyPI。

**工作流示例:**

```bash
# 交互式创建 pyproject.toml
$ poetry init

# 添加依赖，Poetry 会更新 pyproject.toml 并锁定版本
$ poetry add requests

# 安装所有依赖
$ poetry install
```
尽管这两个工具极大地改善了开发体验，但它们也并非完美，例如早期版本存在性能问题、依赖解析速度慢等。然而，它们提出的理念——**声明式依赖、自动环境管理、版本锁定**——为后续的标准化和工具发展铺平了道路。



### uv
uv 是由 Astral（Ruff、Black 等工具的开发者）推出的 超快 Python 包安装器和解析器，旨在替代 pip 和 pip-tools，提供极速的依赖解析和安装体验。

#### why uv
✅ 极速安装：比 pip 快 10-100 倍（基于 Rust 实现）。

✅ 兼容 pip 和 pip-tools：支持 requirements.txt 和 pyproject.toml。

✅ 支持虚拟环境管理：替代 venv 和 virtualenv。

✅ 跨平台：支持 Windows、macOS 和 Linux。

✅ 生产级稳定：由 Astral 团队维护，用于 Ruff 等大型项目。

#### 安装UV
`pip install uv`

#### 基本使用
```bash
# 安装flask包
# 这一条命令会做
# 1. 更新pyproject.toml文件，添加dependencies字段
# 2. 检查并自动创建.venv虚拟环境,并激活该环境
# 3. 安装flask包到当前环境中
uv add flask

# 如果是老项目，没有pyproject.toml文件，只想安装flask，则可以使用下面的命令.
# uv 几乎支持所有的pip命令语法，只需要在最开始加上uv即可
uv pip install flask

# 卸载flask
uv remove flask

# 安装项目依赖
# 这一条命令会做
1. 检查pyproject.toml文件，获取所有的依赖
2. 如果没有虚拟环境则创建虚拟环境
3. 将需要的依赖安装到虚拟环境中
uv sync


# 运行脚本
uv run maim.py

# uvx = uv tool run 用于在隔离的环境中运行工具
uvx ruff check .

# 创建虚拟环境 替代 python -m venv .venv
uv venv .venv
```
# **4.** 第四阶段:依赖与构建标准化
## 依赖文件
由于项目的名称、版本、依赖等元数据散落在 setup.py、requirements.txt 等各处。`requirements.txt`依赖无法区分开发和生产环境依赖等问题，PEP 621（2020年）规定了在 pyproject.toml 中使用标准的 [project] 表来存储这些静态元数据。这一标准的落地使得工具之间可以共享配置，降低了迁移成本 。

安装`pyproject.toml`定义的依赖
`pip install -e .`

```sql
# 1. 构建系统配置（必须）
[build-system]
# 构建依赖（setuptools 是默认后端，也可换成 poetry/flit/hatch）
requires = ["setuptools>=42.0", "wheel"]
# 构建后端（PEP 517 标准）
build-backend = "setuptools.build_meta"


# 2. 项目元数据（PEP 621 标准）
[project]
name = "my_awesome_package"  # 包名（PyPI 上唯一标识）
version = "1.0.0"            # 版本（也可用动态版本，见下方注释）
description = "A Python package for doing awesome things"
readme = "README.md"         # 项目说明文件
authors = [
    {name = "Alice Developer", email = "alice@example.com"},
    {name = "Bob Contributor", email = "bob@example.com"}
]
license = {text = "MIT"}      # 许可证（也可用 file = "LICENSE"）
keywords = ["awesome", "tool", "productivity"]
classifiers = [              # PyPI 分类（https://pypi.org/classifiers/）
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
requires-python = ">=3.10"    # Python 版本要求
dependencies = [             # 生产环境依赖
    "requests>=2.25.0",
    "numpy>=1.20.0; python_version >= '3.7'",  # 条件依赖
    "pandas>=1.3.0; extra == 'analysis'",      # 可选依赖标记
]

# 可选依赖组（通过 `pip install package[extra1,extra2]` 安装）
[project.optional-dependencies]
test = ["pytest>=6.0", "pytest-cov"]
dev = ["black>=23.0", "mypy>=1.0", "flake8"]
docs = ["sphinx>=5.0", "furo"]
analysis = ["scipy>=1.8.0"]  # 触发上方 pandas 的条件依赖

# 项目入口（CLI 或 GUI 脚本）
[project.scripts]
my-cli = "my_package.cli:main"  # 命令行：`my-cli` 会调用 `my_package.cli.main()`

# 图形界面入口（可选）
[project.gui-scripts]
my-gui = "my_package.gui:launch"

# 包内数据文件（如静态资源）
[project.include-packages]
include = ["my_package.data"]  # 包含非 Python 文件（需配合 MANIFEST.in）


# 3. 动态版本控制（从代码中读取版本，替代硬编码）
[tool.setuptools.dynamic]
version = {attr = "my_package.__version__"}  # 从 my_package/__init__.py 读取


# 4. 开发工具配置（可选）
# 4.1 pytest 配置
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "--verbose --color=yes"
testpaths = ["tests"]

# 4.2 Black 代码格式化
[tool.black]
line-length = 88
target-version = ["py310"]

# 4.3 mypy 类型检查
[tool.mypy]
strict = true
ignore_missing_imports = true

# 4.4 Coverage 测试覆盖率
[tool.coverage.run]
source = ["my_package"]
omit = ["*/__init__.py"]

# 4.5 其他工具（如 ruff, isort 等）
[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I"]  # 启用的检查规则


# 5. 自定义构建选项（如 C 扩展）
[tool.setuptools]
# 包含子包
packages = ["my_package", "my_package.submodule"]

# 包含数据文件
package-data = {"my_package" = ["data/*.json", "templates/*.html"]}

# C/C++ 扩展（需配合 setup.py 或 pybind11）
[tool.setuptools.cmdclass]
build_ext = "setuptools.command.build_ext:build_ext"
```


## Lock File
锁定文件（Lockfile）是保证应用可复现性的关键。然而，各家工具（Pipenv, Poetry, PDM）都有自己的锁文件格式，互不兼容。关于统一锁文件格式的讨论在社区持续了数年，历经 PEP 665 的失败，最终在 2025 年，PEP 751 终于被接受。
PEP 751 定义了一个名为 pylock.toml 的标准锁文件格式。它支持：

* 包级锁定（Package Locking）：锁定包的版本和哈希。
* 文件级锁定（File Locking）：锁定具体安装的文件。
* 环境标记：允许一个锁文件覆盖多个平台和 Python 版本。

PEP 751 的通过意味着未来 pip、uv、Poetry 等工具将能够读写通用的锁文件，彻底消除工具锁定的壁垒

# **5.** Conda
在 Python 包管理的历史中, Conda 是⼀个必须单独讨论的存在。它不只是⼀个 Python 包管理器, 它是⼀个全语⾔、跨平台的⼆进制包与环境管理器。

## **5.1** 为什么有了 **Pip** 还需要 **Conda**?
Pip 是 Python 官⽅的包管理器,它只能管理 Python 包。但是数据科学领域极其依赖底层数值计算库(如 NumPy 依赖 BLAS/LAPACK,TensorFlow 依赖 CUDA/cuDNN,GDAL 依赖复杂的 C++ 地理 库)。

**Conda** 的核⼼优势: Conda 将 Python 解释器本⾝也视为⼀个"包"。它可以安装⾮ Python 的依赖项 (如 C++ 库、R 语⾔包、系统级⼯具)。

## **5.2** Conda vs Pip 对⽐分析
|特性|Pip|Conda|
|-|-|-|
|管理对象|Python 包|任何⼆进制⽂件 (Python, R, C++, CUDA等)|
|环境来源|系统 Python 或 venv|独⽴管理的 Conda 环境 (含不同版本 Python)|
|包来源|PyPI (Python Package Index)|Anaconda Repository, Conda-forge|
|⼆进制兼容性|依赖 Wheel,可能需⾃⾏编译|严格预编译,保证⼆进制兼容|
|主要缺点|处理⾮ Python 依赖困难|体积庞⼤,解析速度慢,且有商业授权限制(Anaconda主频道对大型商业组织)|

## **5.3** Conda
> 建议: 现在推荐使⽤ Miniconda 或 Mambaforge 代替庞⼤的 Anaconda 发⾏版。Mamba 是 Conda 的 C++ 重写版,解决了 Conda 极慢的解析速度问题。
```shell
# 1. 创建环境 (指定 Python 版本) 
conda create --name datascience python=3.9

# 2. 激活环境 
conda activate datascience

# 3. 安装复杂的科学计算栈 # Conda 会⾃动处理 MKL、BLAS 等底层库的链接 
conda install numpy pandas scipy scikit-learn

# 4. 导出环境配置 (environment.yml) 
conda env export > environment.yml

# 5. 从配置重建环境 c
onda env create -f environment.yml
```
混合使⽤警告: 尽量避免在⼀个环境中混⽤ pip install 和 conda install ,这极易导致库 ⽂件被覆盖或路径混乱。

# 6.演进总结
* **easy_install** 解决了"去哪下载包"的问题,但留下了卸载难题。
* **pip** 解决了"卸载与管理"问题,但没有解决环境隔离。
* **virtualenv** 解决了"环境隔离"问题,但⽆法保证构建的⼀致性(版本漂移)。
* **Poetry/Pipenv** 引⼊ **Lockfile** 解决了"⼀致性"问题,但带来了性能瓶颈。
* **uv** 引⼊ **Rust** 解决了"性能"问题,并开始统⼀碎⽚化的⼯具链。