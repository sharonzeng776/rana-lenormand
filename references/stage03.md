# 阶段3接口增量

仍用consult.py input.json --db absolute.sqlite。GT请求兼容原接口。小阵plan保留同一组顶层字段，spread=small、variant见ready、roles可空、primary_reference=null；question/intent/topic/acceptance必须明确。acceptance含question_ref、spread_ref，实质改写另标rewritten及rewrite_confirmed。

context仅接受本阶段选项：回答线count=5或7；techniques默认[storyline]，五张时可声明storyline/pairs/lotus/135-24/group；指定焦点还需focus_card及boundary=first4-last_retry1-near_hold。预置九宫focus_card；选择options至少2、原书恰好2（描述版默认每组3）；金字塔topics恰好3及timeframe；H entities两人的稳定ID，后续还需period_ref。H在同一数据库内识别，跨数据库不保证。

new参数inquiry/request/revision不变。小阵返回visible_facts，不是完整内部DrawFacts；事实hash始终是完整不可变事实承诺。回答线random初次仅中央，reveal参数request/revision=0展示余牌，重复调用不多抽。steps参数request、可选technique仅可选择计划已声明读法；返回实际位置、卡号、来源。render参数request/output，输出同一ViewModel的文字/SVG及manifest。trace返回机械操作和回答线边界尝试，不含seed；不要在解释牌或年度中复用此接口。

BoundaryHold不产生虚构可见牌序，完整尝试在事件中保留；末张最多自动重发一次，近边缘不明自动停止。小阵同一inquiry的第二个new请求被拒绝，用户明确要求新抽时建立新inquiry并在咨询记录注明原request（新inquiry的new可传reason={kind:explicit_user,message_ref:...}及parent，原位重抽仍关闭）。

策略版本：sample-pop-v1为通用无放回有序抽样；remaining-shuffle-pick-v1每次用拒绝采样pop重建剩余牌序、取首牌；shuffle-locate-window-v1完整洗40后定位取邻，必要时沿同一随机流再洗一次；preset-center-pop-v1从39抽8然后插入指定E。不同策略不能共用版本名。章末Muree覆盖沿用source。

来源详见small.SPECS、原架构覆盖表及coverage.json；布局、读法与门控均由small.py执行。H一次七张顺序与九宫39选8是已披露产品数字化约定。正常推荐只返回ready，历史catalog不是推荐清单。完整可复制plan与调用见first-use.md；测试材料不随安装包分发。

指定焦点首张形成四牌时，仅已核线性storyline开放：焦点位置1、后三张位置2/3/4、全线。pairs/lotus/135-24/group在该四牌边界暂停，不把五牌技法临时改造成四牌版本；保留原阵，不自动重抽。抽前应披露这一边界约束。
