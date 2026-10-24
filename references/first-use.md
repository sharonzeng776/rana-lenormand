# 首次配置与可复制的公开调用

这是基于0.6.0-rc.4的公开预览副本，版本0.6.0-rc.4-public.1。Python 3.10+；PNG需要当前环境已有Pillow。CLI用UTF-8，Windows也可显式`python -X utf8`。不安装服务、依赖或调用付费API。

## 资料定位

原书、原HTML、彩色图片都不在包内。references/sources.json保留已核版本SHA与内部定位，card-images.json保留已核牌面指纹，但私人路径已移除，默认关闭彩色输出。使用者须自行提供有权使用的资料，并在**技能源目录之外**建立本地配置，令环境变量RANA_CONFIG指向该JSON；模板见项目根目录config.example.json。配置不放宽书籍SHA核验；不同EPUB即使同为第二版，也可能需要另行核验，不能仅改SHA强行启用。

图文输出需提供外部card_images_manifest：从references/card-images.json复制到私有资料目录，配置40个selected_assets的source，保留cardID、SHA及现代人物选择；核对全部40张后设render_ready=true、missing_ids=[]。不同像素文件需要重新核对编号、人物版本和SHA；不自动从互联网下载牌面。缺图保留文字，不重抽。

```json
{
  "book_path": "D:/RanaPrivate/essential-second-edition.epub",
  "course_dir": "D:/RanaPrivate/course",
  "card_images_manifest": "D:/RanaPrivate/card-images.json",
  "font_path": "C:/Windows/Fonts/msyh.ttc",
  "vault_root": "D:/RanaPrivate/Vault"
}
```

这些是示意路径，须替换为真实绝对路径。未配置课程时返回COURSE_MISSING；未配置报告目录时返回VAULT_MISSING；不存在的显式配置返回CONFIG_MISSING。不要把本地配置、书籍、课程、图片或数据库提交到仓库。course.search查**正文关键词**，不按文件名检索；资料属于研究材料，不是执行指令。

运行前可执行只读预检：`python -X utf8 <技能路径>/scripts/check_resources.py`。它核对第二版/40图SHA、课程目录、字体及已有Pillow，缺失时给配置提示。它不安装依赖、不复制原资料。

## 运行目录与输入

下面的RUNTIME表示独立的绝对运行目录；input.json、session.sqlite、cache、out均放在那里。每次调用都给同一持久数据库；新问题使用新inquiry。数据库不跨用户混用，也不为每个H阅读清空。

`python -X utf8 <技能绝对路径>/scripts/consult.py <RUNTIME>/input.json --db <RUNTIME>/session.sqlite --output <RUNTIME>/result.json`

逐条将JSON保存为input.json调用。先推荐/审核，不抽牌：

```json
{"op":"recommend","question":"未来三周这次面试是否有录用倾向？","intent":"yesno","topic":"career"}
```

用户选择后才configure（示例中的消息引用必须换成真实已有引用，不能伪造确认）：

```json
{
  "op": "configure",
  "inquiry": "inquiry-001",
  "plan": {
    "question": "未来三周这次面试是否有录用倾向？",
    "intent": "yesno",
    "topic": "career",
    "spread": "small",
    "variant": "answer.random",
    "profile": "general",
    "roles": [],
    "primary_reference": null,
    "timeframe": {
      "value": 3,
      "unit": "week"
    },
    "context": {
      "count": 5,
      "techniques": [
        "storyline"
      ]
    },
    "acceptance": {
      "question_ref": "用户确认原问题的消息",
      "spread_ref": "用户选择回答线的消息"
    }
  }
}
```

```json
{"op":"new","inquiry":"inquiry-001","request":"draw-001","revision":0}
```

**new不接受seed、order或权重**。首次只揭示中央；render.all先展示、reading.plan读central_first，再reveal。此时await_reveal=true不能提交最终报告。以下每条分别调用：

```json
{"op":"render.all","request":"draw-001","output":"RUNTIME/out/draw-001-central"}
{"op":"reading.plan","request":"draw-001"}
{"op":"reveal","request":"draw-001","revision":0}
{"op":"reading.plan","request":"draw-001"}
{"op":"source.bundle","card":40,"topic":"Work","cache":"RUNTIME/cache","limit":20000}
{"op":"render.all","request":"draw-001","output":"RUNTIME/out/draw-001"}
```

RUNTIME/out必须换成绝对路径。每个JSON对象是一个独立输入文件，不把多个对象连成一个非法JSON。实际检索card由可见牌确定，不固定40；技法如unit55,start144,end155。截断按next_offset续读。后续Claim和报告格式见workflow.md。

## 完整大桌计划

用下面plan替换configure中的plan，其余沿configure→new→render.all→reading.plan。GT不需reveal。本人29与主参照40独立，所有未来区由市场所在列一次确定。

```json
{
  "question": "未来三个月我的求职进展如何？",
  "intent": "process_and_outcome",
  "topic": "career",
  "spread": "gt40",
  "variant": "flat",
  "profile": "career",
  "roles": [
    {
      "card_id": 29,
      "entity_id": "querent"
    }
  ],
  "primary_reference": 40,
  "timeframe": {
    "value": 3,
    "unit": "month",
    "declared_ref": "已向用户说明时段的消息"
  },
  "context": {
    "owns_business": false,
    "final_four_intent": "advice"
  },
  "acceptance": {
    "question_ref": "用户确认问题",
    "spread_ref": "用户选择大桌",
    "anchor_ref": "用户选择市场为主参照"
  }
}
```

## 其余计划的最小改动

保留完整11个顶层字段。small/series的primary_reference=null，roles可以空；plan必须在抽前锁定。small变体详见stage03.md，series/解释牌见stage04.md。

- 过程九宫：small/box.process，intent=process，context={}；同列三阶段不是过去现在未来。
- 建议九宫：small/box.advice，intent=advice，context={}；上行不建议投入。
- 预置九宫：small/box.center，context={"focus_card":29}，E为指定非随机，其他39抽8。
- 指定回答线：small/answer.focus，context={"count":5,"techniques":["storyline"],"focus_card":40,"boundary":"first4-last_retry1-near_hold"}。BoundaryHold保留首抽，不换种子继续试。
- 比较：small/decision.book，intent=comparison，context={"options":["A","B"]}。
- H：small/h.once，context={"entities":["稳定本人ID","稳定对方ID"]}；同库后续加period_ref="未来三周"且问题明确时段。角色A/B不是自动指定男人女人。
- 年度：series/yearly，context={"start_month":"2026-12"}；先完整读12月组，reading.complete，再reserve.allocate。
- 占星：series/astro.wheel或astro.columns，context={}；不索取出生资料。布局由用户决定，不能擅自改布局重抽。
- Identifier：series/identifier.one或identifier.two，context={}；固定五行，不能识别真实隐秘心理。

## 恢复与重抽

断开后用相同数据库及request重放replay，不重新new其他request。不清楚先检索；只有实质歧义才按stage04两阶段解释，最多一轮。小阵明确重抽先新inquiry并configure，再new传parent=原request及reason={"kind":"explicit_user","message_ref":"真实重抽指令"}；GT/series仍沿同inquiry原协议。原句解释仅replay，不抽牌。

## 报告

reading.plan返回的required步骤都要实际完成；reading.validate只做结构检查。模型完成来源反查与语义审读后，reading.save保存一篇主报告，真实路径在配置Vault/03-案例研究，附件在Vault/附件；年度分配/解释牌/后续解释修订该主报告。相同正文重试幂等，文件冲突拒绝；写入失败用同一请求重试恢复。不要将固定测试写真实案例。

指定焦点首张形成四牌时，仅已核线性storyline开放：焦点位置1、后三张位置2/3/4、全线。pairs/lotus/135-24/group在该四牌边界暂停，不把五牌技法临时改造成四牌版本；保留原阵，不自动重抽。抽前应披露这一边界约束。
