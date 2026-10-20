# Loon4Streaming · 从 Surge 模板生成的 Loon 分流配置

[English](./README.md) | [Surge 源仓库](https://github.com/Sifortonzh/Config4Streaming)

## 导入新版

下载 [Loon4Streaming_rebuilt.conf](https://raw.githubusercontent.com/Sifortonzh/Loon4Streaming/main/Loon4Streaming_rebuilt.conf)，在 iPad 的 Loon 中作为**新配置**导入，便于随时切回旧配置。

1. 导入时保留已有节点/订阅（若当前版本提供该选项），或者在新配置的“订阅节点”页面添加机场的 **Loon 专用订阅**。不要把 Surge 整份配置当成 Loon 节点订阅。
2. 配置中的 MESL、SNTP 是禁用的 example.com 占位符；实际使用时换成自己的 Loon 订阅并启用，或保留原有的订阅。订阅只需在本地/iPad 填写，不要提交 GitHub。
3. 更新订阅，再看 Sub-ALL 和各地区筛选器的节点数量。若 Sub-ALL 为 0，先解决订阅格式/启用状态；若只有某地区为 0，检查机场是否提供该地区、名称是否匹配。
4. 将 Loon 的运行模式设为**规则模式**。初次检查时关闭其他插件/规则覆盖，然后重新连接 VPN。
5. 核对 Apple、WeChat 默认 DIRECT；PikPak 默认新加坡；Bilibili 同时覆盖国内和 Bstation 国际版。其他组的选项与图标随公共 Surge 模板生成。
6. 到请求日志核对实际命中策略与出口，再测试播放。节点测速成功不代表能解锁所有流媒体。部分地区不存在可用节点时，需要改选该服务允许的地区，不会为方便而混入其他地区的节点。

当前配置以本地规则快照提供，约 4 MB；首次导入/启动需要等待规则加载。它不包含真实机场订阅、证书、插件、脚本或 MITM。仓库其他历史 .conf/.lcf 文件保持原样，**新版入口是 rebuilt 文件**。

## 为什么旧 Loon 可能与 Surge 不同

此次确认的是配置层面的差异，尚未在用户 iPad 上复现具体失败请求，因此不将其描述为设备端最终诊断。

- 旧筛选器绑定 PAOPAO、Mitce 两个订阅别名，换成其他别名时筛选源可能为空。新版使用包含全部节点的 NameRegex，避免订阅名称绑定，并支持 HK01、SGP05、PH01、SK01、繁体地区名及常见旗帜；流量/到期提示条目被排除。台湾以台湾名称/旗帜识别，不单凭中国旗帜。
- Loon 原生顺序是域名优先于 IP，本地规则优先于插件、订阅规则。新版按 Surge 的条目顺序下载并展开规则，放进同一个本地 [Rule] 段，避免分成多个来源后被重新优先匹配。**Loon 域名优先于 IP 的引擎行为仍存在，不能宣称与 Surge 完全等价。**
- Surge smart 转为 Loon 原生 url-test；这是延迟择优，不是相同的智能算法，也不是解锁检测。地区通过远端筛选器确定。
- icon-url 转为 Loon 的 img-url，保留原图标和组顺序。新组继续在后面添加。
- iPad 不使用 macOS/Android 进程名规则，改由域名/IP 规则覆盖。转换不会悄悄忽略未知规则类型：遇到新类型会停止更新。
- Apple 的域名清单与其他规则分开提供。此次公共 Surge 模板已补上 DOMAIN-SET，Loon 也将其转换成原生 DOMAIN / DOMAIN-SUFFIX，避免 apple.com 等遗漏。
- 禁用 UDP 不支持时的直连回落；DNS 拦截使用 Loon 原生写法，开启加密 DNS。HTTPS 的 USER-AGENT 等依赖 HTTP 可见性的规则仍受客户端能力限制。

官方依据：[规则优先级](https://nsloon.app/en/docs/Rule/)、[节点筛选](https://nsloon.app/en/docs/Node/nodefilter/)、[订阅格式](https://nsloon.app/en/docs/Node/subscription/)、[策略组](https://nsloon.app/en/docs/Policy/policygroup/)。

## 一键更新与隐私

在 Mac 上双击 [tools/sync.command](./tools/sync.command)，先校验，再选择：

- 🔄 1：从 Surge 公共模板重新生成 Loon。
- 🚀 2：生成、校验并通过 SSH 发布 Loon 仓库 main。

默认读取相邻 Config4Streaming 仓库的 templates/Surge.shared.conf，复制的是公共策略逻辑，不是 iCloud 私有配置。原来 Surge 的“一键同步”继续管理 MESL/SNTP；修改后再运行 Loon 的“一键同步”，即可转换到 Loon。两个更新入口独立，避免意外连带发布。

更新会校验所有规则下载、图标内容、分组引用，并生成 [validation-report.json](./validation-report.json) 记录来源与哈希。按源清单中的顺序生成本地规则，规则源更新后需要重建并在 iPad 重新导入/更新配置；**不是 iPad 后台自动同步**。仅在 iPad 修改不会自动上传或反向改写 Surge。

- 默认只预览；python3 tools/sync_from_surge.py --apply 生成；添加 --publish 发布。
- --refresh 强制刷新公开资源；--offline 只用本地缓存验证，不能发布。
- --source /path/to/Surge.shared.conf 指定脱敏公共模板；带真实订阅或凭据的来源会拒绝。
- 如已有本地 Loon 配置，可加 --private-profile /path/to/old-loon.conf，仅提取它的 [Proxy] / [Remote Proxy] 到 .loon-sync/Loon4Streaming.private.conf，其他私有段不复制。该文件仅供自己导入，不会发布。不会访问任何第三方订阅转换服务。
- 本地缓存及备份保存在 Git 忽略的 .loon-sync/。更新前备份原输出；已生成文件若被手工修改，停止覆盖，请先将修改并回公共模板。
- 只提交脚本、说明、rebuilt 配置和公开校验报告；不会提交历史文件的无关本地删除。推送失败时本地生成和备份保留，可排除 SSH/网络问题后重试。

需要 Python 3 和 Git。安装 Loon 的设备上仍须验证实际订阅、筛选器数量、域名命中及播放。测试命令：python3 -m unittest discover -s tools -p 'test_*.py'。

## 来源与署名

公共策略来源：[Config4Streaming](https://github.com/Sifortonzh/Config4Streaming)。规则来源：BlackMatrix7 ios_rule_script、AWAvenue、Semporia 及 Sifortonzh 自定义规则；每个实际 URL、数量和哈希见校验报告。图标保持原作者链接（Qure、Orz-3/mini、Semporia 等），不宣称原创。规则快照引用和更新需尊重上游项目的许可与署名。

