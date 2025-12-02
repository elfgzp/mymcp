# MCP：让 AI 助手更懂你的工作场景

最近在工作中用了一段时间的 MCP（Model Context Protocol），感觉挺有意思的，效率提升了不少。所以想写篇文章跟大家分享一下我的使用心得，也算是做个记录吧。

如果你也在用 Cursor 或者 Claude Desktop 这类 AI 工具，并且想让 AI 助手更"能干"一点，这篇文章可能会对你有帮助。我会从什么是 MCP 开始聊起，然后分享我在实际工作中是怎么用的，最后还会介绍一下我自己实现的 MCP 服务项目。

## 1. 什么是 MCP？先来聊聊这个"翻译器"

说到 MCP，可能很多人还不太熟悉。MCP 全称是 **Model Context Protocol**（模型上下文协议），这个名字听起来有点高大上，其实你可以把它理解成 AI 助手和外部工具之间的一个"翻译器"。

简单来说，传统的 AI 助手只能基于训练数据回答问题，就是那种"纸上谈兵"的感觉。但有了 MCP 之后，AI 助手就可以：
- 直接访问你本地或远程的工具和资源
- 执行各种自定义命令
- 获取实时的上下文信息
- 在你的工作环境中真正"动起来"

打个比方，MCP 就像是给 AI 助手装上了各种"外挂"，让它能够调用你系统中的各种能力。比如让 AI 去浏览器里找资料，或者执行你本地的脚本，再或者直接操作你的文件系统，这些都可以通过 MCP 来实现。

## 2. 我在工作中是怎么用 MCP 提升效率的

### 2.1 用 chrome-mcp 插件收集和整理文档，真的省事

我在工作中经常遇到这样的场景：比如开发蓝盾插件或者对接 TAPD SDK 插件的时候，相关文档可能分散在各个地方。有些在官方文档网站，有些在 GitHub，还有些可能我之前在 Chrome 浏览器上看过，但是忘了保存，再想找的时候就麻烦了。

以前我的做法就是手动复制粘贴，效率真的很低。后来我发现了 **chrome-mcp** 这个插件（项目地址：https://github.com/hangwin/mcp-chrome），它能让 AI 助手直接控制 Chrome 浏览器，真的让我的效率提升了不少。

#### chrome-mcp 到底是啥？

chrome-mcp 其实就是一个 MCP 服务，它可以让 AI 助手（比如 Cursor 或者 Claude Desktop）直接与 Chrome 浏览器交互。听起来是不是有点神奇？通过这个插件，AI 可以做这些事情：
- 打开网页（这个不用说）
- 读取网页内容（可以直接提取文字信息）
- 截图（想要保存页面的时候很方便）
- 填写表单、点击按钮（自动化操作）
- 获取网络请求信息（调试的时候很有用）
- 搜索标签页内容（找之前打开过的页面）
- 管理书签和历史记录（这个也很实用）

说实话，第一次用的时候真的觉得挺神奇的，AI 居然能直接控制浏览器。

#### 怎么安装和使用 chrome-mcp？

安装其实不算复杂，我来简单说一下步骤：

1. **下载 Chrome 扩展插件**
   - 访问 GitHub 仓库：https://github.com/hangwin/mcp-chrome/releases
   - 下载最新版本的 Chrome 扩展（`.crx` 文件）

2. **安装 Chrome 扩展**
   - 打开 Chrome 浏览器，进入 `chrome://extensions/` 页面
   - 记得启用"开发者模式"（在页面右上角有个开关）
   - 把下载的 `.crx` 文件直接拖放到扩展程序页面，点击"添加扩展"就完事了

3. **安装 mcp-chrome-bridge**
   - 打开终端，运行这个命令：
     ```bash
     npm install -g mcp-chrome-bridge
     ```
   - 前提是你得先有 Node.js（版本 18.19.0 或以上）和 npm，这个应该大多数开发者都有

4. **配置 MCP 服务**
   - 在你的 Cursor 或者其他支持 MCP 的 IDE 中，配置一下 MCP 服务器
   - 添加 chrome-mcp 服务的连接信息就行了

安装完成后，你就可以在 AI 助手里直接跟它说：
- "帮我在浏览器中打开蓝盾文档网站，并提取所有 API 接口说明"
- "打开我之前看过的 TAPD SDK 文档，把关键信息整理一下"
- "搜索我 Chrome 历史记录中关于某个项目的所有页面"

这样，AI 就能直接从浏览器中获取信息了，完全不用你手动复制粘贴。说实话，用了几次之后，真的就回不去了，太方便了。

---

**我如何使用 chrome-mcp 插件的实际场景**（这部分我会自己写，包括截图和使用场景，分享一些真实的工作场景）

---

### 2.2 自己动手实现一个 MCP 服务

虽然有很多现成的 MCP 服务可以用，但有时候我们可能想要一个完全符合自己需求的定制化服务。下面我就来聊聊我是怎么做的，其实没有想象中那么难。

#### 实现 MCP 服务需要准备什么？

说实话，实现一个基础的 MCP 服务并不复杂，你基本上需要了解这些：

1. **编程语言基础**
   - Python 或 JavaScript/TypeScript 都可以，看你的喜好
   - 我个人建议用 Python，因为官方 SDK 支持比较好，用起来也简单

2. **MCP 协议的理解**
   - 了解 MCP 的基本通信协议（其实就是 JSON-RPC 2.0，不是什么新东西）
   - 理解 tools/list 和 tools/call 这些核心接口，说白了就是"我能提供哪些工具"和"调用这个工具"

3. **网络通信的基础知识**
   - 如果你要做远程服务，那需要了解 HTTP、WebSocket 或者 SSE
   - 如果做本地服务，主要就是标准输入输出的通信（stdio），这个应该都会

4. **MCP SDK**
   - 直接用官方的 MCP SDK 就行，这样可以大大简化开发
   - Python 有 `mcp` 包，JavaScript 有 `@modelcontextprotocol/sdk`，都挺好用的

5. **工具设计的思路**
   - 想清楚你的服务要提供哪些工具（tools）
   - 每个工具需要什么参数，返回什么结果，这个在写代码之前想清楚就行

总的来说，如果你会用 Python 写个简单的脚本，基本就能实现一个基础的 MCP 服务了。真的没那么复杂，至少比我想象的要简单。

#### 我做的 mymcp 服务

基于这些理解，我自己动手实现了一个 MCP 服务项目：**mymcp**（项目地址：https://github.com/elfgzp/mymcp）

这个项目的核心想法其实很简单：**能不能做一个 MCP 服务的"聚合器"？**

说白了，我想让 mymcp 成为一个顶层服务，它不仅可以提供我自己定义的命令，还能把其他多个 MCP 服务整合在一起，统一对外提供服务。这样我就不用在 Cursor 里配置一大堆 MCP 服务了，一个 mymcp 就能搞定。

**mymcp 的核心特性：**

我设计的时候主要考虑了这几个点：

1. **自定义命令**
   - 支持 HTTP 接口调用：可以把任何 HTTP API 包装成 MCP 工具，这样调用公司内部 API 就很方便了
   - 支持脚本执行：可以把本地脚本包装成 MCP 工具，做一些自动化的事情

2. **MCP 服务聚合**
   - 作为顶层服务，可以集成多个其他 MCP 服务
   - 统一管理，统一调用，不用每个服务都单独配置
   - 通过前缀避免工具名冲突，比如文件系统的工具可以加个 `fs_` 前缀

3. **热更新**
   - 这个是我觉得比较实用的功能，添加或移除 MCP 服务时无需重启
   - 配置变更立即生效，不需要每次都重启服务

4. **灵活鉴权**
   - 支持 API Key、Bearer Token、Basic Auth 等多种鉴权方式
   - 敏感信息用环境变量管理，这样比较安全

5. **Web 管理界面**
   - 提供友好的 Web 界面来管理配置
   - 可以实时查看服务状态和工具列表，不用去改配置文件

6. **轻量级**
   - 无数据库依赖，单文件配置就够了
   - 通过 `uvx` 可以直接运行，无需安装，部署起来很方便

**为什么做这个项目？**

这个项目其实是从实际需求中来的。我在工作中发现很多时候需要：
- 调用公司内部的 API（比如查个数据、调个接口）
- 执行一些自动化脚本（比如打包、部署什么的）
- 同时使用多个 MCP 服务（比如文件系统、GitHub、数据库等）

如果没有 mymcp，我就得：
1. 为每个 API 单独写一个 MCP 服务（太麻烦了）
2. 在 Cursor 中配置多个 MCP 服务（配置一堆东西）
3. 管理多个服务的配置和连接（维护成本高）

有了 mymcp 之后，我只需要：
1. 在配置文件中定义要调用的 API（写个 YAML 就行）
2. 配置要聚合的其他 MCP 服务（也是写配置）
3. 启动 mymcp，所有工具都统一在一个服务中（一个服务搞定所有事情）

这样效率就高多了，而且维护起来也简单。

**使用场景示例：**

举个例子，我是这么配置的：

```yaml
# 配置一个 HTTP API 命令，调用公司内部的接口
commands:
  - name: "get_team_status"
    description: "获取团队工作状态"
    type: "http"
    http:
      method: "GET"
      url: "https://internal-api.company.com/team/status"
      auth:
        ref: "internal_api_auth"
    parameters:
      - name: "team_id"
        type: "string"
        required: true

# 聚合其他 MCP 服务，把文件系统和 GitHub 的都整合进来
mcp_servers:
  - name: "filesystem"
    connection:
      type: "stdio"
      command: "uvx"
      args:
        - "mcp-server-filesystem"
        - "/path/to/workspace"
    prefix: "fs"  # 加个前缀，避免工具名冲突
  
  - name: "github"
    connection:
      type: "stdio"
      command: "uvx"
      args:
        - "github:modelcontextprotocol/servers"
        - "github-mcp"
    prefix: "gh"  # GitHub 的工具也加个前缀
```

这样配置后，我就可以在一个 MCP 服务中使用所有的工具了：
- 我自己定义的工具：`get_team_status`（调用公司 API）
- 文件系统工具：`fs_list_files`、`fs_read_file` 等（操作文件）
- GitHub 工具：`gh_search_repos`、`gh_create_issue` 等（GitHub 操作）

是不是很方便？一个服务就把所有需要的功能都整合到一起了。

---

**我实际是怎么用 mymcp 的**（这部分我会自己写，包括详细的配置示例和真实的使用场景，可能会放一些实际工作中的例子）

---

## 3. 总结一下，MCP 到底给我带来了什么

### 3.1 MCP 给我带来的好处

用了 MCP 一段时间后，说实话，我觉得它给我带来的改变还是挺明显的。总结一下，主要有这么几点：

**1. 效率真的提升了很多**
   - 以前需要手动操作的事情，现在可以直接让 AI 助手完成
   - 比如收集文档、整理信息、执行自动化任务等等，这些重复性的工作现在基本不用我操心了

**2. 标准化集成，省心**
   - MCP 提供了一个标准化的接口，让我能轻松集成各种工具和服务
   - 不需要为每个工具都写一套复杂的集成代码，基本上配置一下就能用

**3. 可扩展性很强**
   - 需要新功能时，可以快速添加新的 MCP 服务
   - 不需要修改现有的代码和配置，添加就行了，很方便

**4. 统一管理，维护简单**
   - 通过 mymcp 这样的聚合服务，可以把多个工具统一管理
   - 配置集中在一个地方，维护起来简单多了，不用到处找配置文件

**5. 开发友好，定制化容易**
   - 实现自己的 MCP 服务并不复杂，门槛不高
   - 可以根据实际需求定制化，想加什么功能就加什么功能

总的来说，MCP 让我感觉 AI 助手真正成为了我的工作伙伴，而不是只能聊天的工具。现在很多时候，我会直接让 AI 去帮我做一些事情，而不是我自己手动去做，这种体验真的挺棒的。

### 3.2 推荐一些资源和链接

如果你想深入了解 MCP 或者开始使用，我整理了一些我觉得比较有用的资源，分享给大家：

**官方资源（这些是必看的）：**
- [MCP 官方文档](https://modelcontextprotocol.io/) - 最权威的文档，想深入了解的话这个一定要看
- [MCP GitHub 组织](https://github.com/modelcontextprotocol) - 官方 SDK 和示例都在这里
- [MCP 规范文档](https://spec.modelcontextprotocol.io/) - 如果你想自己实现服务，这个协议规范要了解

**实用的 MCP 服务（这些是我用过觉得不错的）：**
- [chrome-mcp](https://github.com/hangwin/mcp-chrome) - Chrome 浏览器控制，前面已经介绍过了
- [mcp-server-filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) - 文件系统操作，这个很常用
- [mcp-server-github](https://github.com/modelcontextprotocol/servers/tree/main/src/github) - GitHub 操作，对开发者很有用
- [mcp-server-postgres](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres) - PostgreSQL 数据库操作，如果项目用 PostgreSQL 的话可以用这个

**我的项目（打个广告，哈哈）：**
- [mymcp](https://github.com/elfgzp/mymcp) - MCP 服务聚合器，支持自定义命令和热更新，就是我刚才介绍的那个

**学习资源（想深入学习的话）：**
- [MCP 社区讨论](https://github.com/modelcontextprotocol/servers/discussions) - 官方社区的讨论和问答，有问题可以在这里问
- [MCP 示例集合](https://github.com/modelcontextprotocol/servers) - 各种官方示例服务，可以参考别人的实现

**集成指南（开始使用的话看这些）：**
- [Cursor MCP 配置指南](https://docs.cursor.com/context/model-context-protocol) - 如果你用 Cursor，这个指南很有用
- [Claude Desktop MCP 配置](https://claude.ai/docs/mcp) - 如果用 Claude Desktop，看这个

希望这些资源能帮助大家更好地使用 MCP，提升工作效率！如果你有什么好的 MCP 服务或者使用心得，也欢迎在评论区分享，大家一起交流学习。

最后想说一句，MCP 虽然现在可能还不是特别普及，但我觉得它的潜力还是挺大的。随着 AI 工具越来越普及，这种标准化的接口协议应该会有更大的发展空间。如果你还没开始用，不妨试试看，说不定也能帮你提升不少效率。

好了，这篇文章就先写到这里。如果有什么问题或者想法，欢迎交流！

---

*文档最后更新时间：2025年1月*

