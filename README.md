# Rana Lenormand：非官方40张雷诺曼技能

用于具备本地文件与Python执行能力的Codex技能环境：澄清占问、推荐牌阵、随机发牌、文字排阵、按来源组织模型解读，并在资料齐全时输出SVG/PNG。它不是独立网站，也不包含自己的语言模型。

**公开预览版本：0.6.0-rc.4-public.1，基于本机验收候选0.6.0-rc.4。** 公开的是程序、方法索引和原创说明，不包含电子书、课程原文、牌面、私人咨询或运行数据库。项目不隶属于Rana George，也不代表作者授权。维护账号：[sharonzeng776](https://github.com/sharonzeng776)。

## 能力与限制

- 固定40种符号，只保留一张男人和一张女人；沿用已核现代人物选择，无逆位。
- 支持已开放的小牌阵、8×5大桌、解释牌、年度分配、占星布局及固定Identifier；实际可执行清单由ready接口给出。
- 随机过程由程序执行并保留回放状态；模型负责语境解读。模型订阅或API费用取决于使用者所用平台，技能不另调付费语言API。
- 默认不带书籍或牌面，抽牌与文字布局可运行；完整Rana来源检索依赖外部资料，PNG还需要40张牌面、中文字体和Pillow。缺少来源时不应冒充已完成完整Rana解读。
- 原书读取严格绑定已核第二版EPUB的SHA和内部结构，并非任意第二版文件都能直接使用。课程原HTML也需使用者自行配置。未核文件须另行验证，不能简单改SHA绕过。
- 原版67组冻结回归为历史本机证据。本发布副本另做适配检查；未对所有系统、全部牌义语境或预测准确率作保证。
- 未核近边缘处理、数值评分、H分段洗牌、镜像、人物朝向及Identifier动态追加继续关闭。

## 安装与配置

本项目暂授予个人非商业安装使用许可，详见[LICENSE](LICENSE)；未授予一般开源修改和再发布权限。上游代码另依Apache-2.0授权。

在支持本地技能的环境中，将本目录作为一个完整技能目录安装，保留SKILL.md、scripts和references的相对关系。不要只复制SKILL.md。Python需3.10以上；已测试平台为Windows。PNG需要环境中已有Pillow及覆盖中文的字体；本项目不自动安装依赖。

将[config.example.json](config.example.json)复制到技能目录以外的私有目录，填入真实绝对路径，并设置环境变量RANA_CONFIG指向该JSON。Windows PowerShell示例：

```powershell
$env:RANA_CONFIG = 'D:/RanaPrivate/config.local.json'
python -X utf8 'D:/Skills/rana-lenormand/scripts/check_resources.py'
```

复制示例命令前修改路径。缺少书籍、课程、图片或字体会报告具体问题，不会替你下载资料或修改运行环境。保存报告还需要配置vault_root；真实报告只写入其03-案例研究，图片放附件。运行数据库、缓存及输出始终放在技能目录以外的个人运行目录。

完整的调用格式、牌阵选择、揭示顺序、图片清单配置与恢复规则见[首次使用](references/first-use.md)和[工作流](references/workflow.md)。仅查看可执行牌阵时，可在外部目录创建request.json，内容为：

```json
{"op":"ready"}
```

```powershell
python -X utf8 'D:/Skills/rana-lenormand/scripts/consult.py' 'D:/RanaRuntime/request.json' --db 'D:/RanaRuntime/session.sqlite'
```

## 资料与隐私

自行取得并在本地配置所需资料。默认的资料清单只保留已核版本指纹、牌号与定位，不能替代书籍或课程。请勿在Issue、仓库、提交或附件中发布电子书、课程、牌面、真实问题、人物身份、抽牌数据库或本地配置。SVG/PNG可能嵌入完整牌面，不应作为公开样例自动上传。

## 来源与授权

上游随机抽牌协议来自[dajiaohuang/divination-skills](https://github.com/dajiaohuang/divination-skills)，原文件及Apache-2.0许可已保留，见[第三方说明](THIRD_PARTY_NOTICES.md)。书籍、课程和牌面版权不由本项目授予。

本工具提供符号解读与思考辅助，不保证未来事件，不据牌面声称知道他人的真实心理。
