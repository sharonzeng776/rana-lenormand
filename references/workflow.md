# 当前工作流与接口

使用现有Python运行`python scripts/consult.py input.json --db 绝对会话数据库 --output result.json`。不另接语言API；自然阅读由当前模型完成。

## 检索与证据

source.index(cache)返回40卡章标题定位；source.bundle(cache,card,topic)支持Work/Love/Money/Advice or Action/Time or Timing/Objects and Areas等，career/relationship等别名也可。返回一般语境、主题、Muree覆盖，missing明确缺节，长段truncated和next_offset续读传offset。技法可用unit/start/end取精确段。可选course_query补课程；course.search(cache,query)返回有SHA/节点/层级/邻近上下文的课程检索，并注册C:证据ID。用户补充见user-supplements.json，不当成作者原文。

缓存按SHA/extract-v2分章，源size/mtime变化后重新完整核SHA，拒绝未知版本；缓存命中不重扫83MB原书。不是抵御恶意伪造mtime的安全机制。E:来源ID绑定书籍SHA/单元/范围，续读窗口累计完整才可用于验证。

## 阅读计划与Claim

reading.plan(request)返回已确认问题/角色、全局axis（仅GT）、可见事实、commitment、reveal_revision及步骤。模型逐项完成required；conditional说明适用与否，optional按疑点使用。小阵是其实际读法，不套GT宫位；年度仅可见36牌进入计划。

reading.validate(request,document)：document字段限revision、claims、completed_steps、answer、review。completed_steps为步骤ID→实质分析文本；claims含id/statement/facts/sources/counterevidence，可选alternatives/kind/step_ids。facts含position/card_id，GT可选house/role/zone；sources必须已取得完整上下文的E:/C: ID。检查必读遗漏、错牌/隐藏牌、错宫/角色/轴线、失效来源及过期揭示版本。没有重要反向信息也应说明理由。程序只检查结构，返回requires_model_review；文字是否充分、解释是否合理由模型审读。

不接受facts_hash或候选完整hash，不提供年度尾序枚举验证通道；公开只用request/commitment/reveal_revision。分配后重新取计划与版本，不改原事实。原句解释用原阵；新占问恢复完整40。解释牌两阶段及年度分配沿既有协议，不靠读不顺无限追加。

## 图文与报告

render.all(request,output,font_path可选)返回text/svg/png/errors/view_model。默认C:/Windows/Fonts/msyh.ttc，检查cmap覆盖；字体/缺字/PNG故障保留文字和SVG，缺图保留文字，不换黑白、不重抽。按原图等比缩放、保留水印；manifest只含可见VM、源SHA、字体及承诺。带点变体名前缀不会互相覆盖。

reading.save(request,document,path,markdown,index_path可选,test_fixture=false)：真实报告限Vault/03-案例研究；模型先将图片生成在Vault/附件并在正文引用。新报告不覆盖未知文件，同request后续保持同一路径，旧修订正文留数据库。测试test_fixture=true只能写samples，不更新真实案例索引。程序不生成结论，只保存模型已经完成且审读的正文。

正文先问题和范围、图文牌阵、详细分析、直接答案、条件/近似时间/建议及必要来源提示，避免技术JSON和每句免责声明。年度补月、解释批次及后续解释在一篇主报告修订，并标重要改动。reader界面不展示seed。

## 参数参考与当前边界

小阵参数见stage03.md，多阶段参数见stage04.md；这两份只提供参数细节，当前功能状态以SKILL和ready为准。所有旧关闭状态已统一：PNG、解释牌、年度、占星及固定Identifier已可用；未核边缘、数值评分、H分段、镜像、朝向及Identifier动态追加关闭。旧render/source接口仅兼容；正常阅读使用render.all/source.bundle。catalog为知识目录，不当成ready。

完整调用示例见first-use.md；测试咨询和审查记录只留运行层，不随候选包分发。候选已准备，尚未安装或公开发布，不宣称所有组合和语境都已验证。

回答线仅中央揭示时reading.plan返回await_reveal=true和central_first步骤；先解释中央可见牌，明确reveal后重新取完整计划。await_reveal时不能验证/保存最终阅读。旧揭示版本不能用于新报告。

报告同request、同内容重试返回同revision，可恢复已提交但未落文件的修订；不同正文增加revision，旧正文保留。索引在写正文前验证。解释牌分析关联原request，在原报告修订；不要用解释request覆盖父报告。

能力由capabilities.json的已审查清单与实际策略同时匹配，deal/layout/read/render/tests任一缺失便不进ready/推荐/配置；清单是本轮验收记录，不是自动证明未来任意代码的质量。

恢复咨询先reading.plan：locked_plan返回已确认问题、意图、牌阵、角色、时段与抽前语义；timing（仅GT）列出近似尺度及原校准候选。步骤meaning保留实际月份/领域/组合语义，不需从数据库或开发者记忆恢复。校准冲突由模型说明并询问，不能静默合并为精确日期。locked_plan只含用户已知计划，不含seed、余牌顺序或完整facts_hash。
