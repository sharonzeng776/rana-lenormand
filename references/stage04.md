# 阶段4增量接口

固定Identifier：series/identifier.one每行1张、identifier.two每行2张，五行依次意图/外显/隐藏性质/情绪核心/行为结果。只作象征语境，不声称事实读取心理。原版adaptive及product-clarifier叠加均不启用。

年度：series/yearly，context={start_month:"2026-11"}；占星series/astro.wheel或astro.columns，context={}。顶层plan字段与原版相同，acceptance含question_ref与spread_ref；schema、锁定计划哈希边界不变。轮盘从九点边界起第一宫居该扇区中点195°，数学角递增、屏幕Y取负，原图image/141.jpg已核对。三牌在各宫作为同一组，列版同一套序列按组展示，无需出生资料。

configure/new/replay/render/steps继续使用原入口。年度new只给36张与reserve_count，不给facts_hash/seed/余牌顺序；commitment用私有32字节seed作高熵nonce，避免已知36张后枚举24个余牌次序验证裸hash。内部facts_hash从未改变。已知牌池可推出余牌集合，不承诺集合保密。

先完成月份阅读，reading.complete参数request、reading_ref。reserve.allocate参数request、months_in_order（连续12月标签中恰好4个有序月份，可重复）、revision（初始0）、message_ref。先提交AllocationEvent再揭示；重复相同分配幂等，改月份拒绝。分配不调用随机源，不改DrawFacts；展示位置由原事实和独立分配记录派生。占星末4张是全局提醒，不接受补月。

解释牌clarifier.prepare参数ticket、parent（GT/小阵统一原request）、target（整数原位置）、ambiguity、evidence（相关原文/主题检索依据）、announcement（已输出的预告引用或文字）、count1～3。返回prepared。相同ticket重试不重复占额度，更换任何内容拒绝；同一parent+target唯一，目标须已揭示主位置、不能为解释牌。prepare和draw完成状态分别可由tickets/jobs/draws持久记录恢复。

clarifier.draw只接受ticket/request，不接受抽后改count；全40独立洗牌抽前1～3，本批不重复，允许跨批及与原阵重复。seed提交后恢复原批；每个目标最多一次，不递归。render返回单独解释小行，标签含原request/位置/疑点；不能填原阵空位。解释原句通常replay+source，无实质歧义不prepare。

series和解释批次的trace/reveal/geometry均不开放；audit.export只在该批全部揭示后、带confirmed_ref显式确认才返回完整事实及回放seed。不要将它作为日常日志使用。旧小阵trace依原边界审计协议保留，不会路由年度数据。公开manifest只包含当前可见ViewModel和承诺。

series新抽支持原reason={kind:explicit_user,message_ref:...}与parent请求，保留原阵和原因；无消息证据不重抽。原小阵重抽仍按独立新inquiry规则。缺图返回文字和ASSET_UNAVAILABLE，不回退黑白、不改牌序。render.all由同一ViewModel生成文字/SVG/PNG，模型解读及阅读检查见workflow.md；发布未执行。

本地数据库并非对拥有本机文件读取权的恶意模型的安全沙箱，不能绕过接口读取隐藏顺序。阅读完成与预告的消息真实性由咨询模型负责；程序校验必要证据字段、额度及事务条件，不伪称自动验证自然语言质量。
