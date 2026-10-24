# 运行接口

Python 3.10以上；文字/SVG/检索用标准库，PNG需要已有Pillow，不自动安装或修改环境。首次配置及完整示例见[first-use.md](first-use.md)，正常阅读见[workflow.md](workflow.md)。

CLI以UTF-8 JSON输入输出。`python scripts/consult.py request.json --db 绝对运行目录/session.sqlite --output 绝对运行目录/result.json`。技能源目录不保存数据库、缓存或产物。不要直接调用legacy_*，这些仅是内部依赖。

configure锁定后不能修改。new重复request返回原结果，revision沿configure或当前状态。H需要同一持久数据库与双方稳定ID；新占问新inquiry，不能为新占问清空数据库导致关系首次识别重置。交换左右不变关系。跨数据库身份识别不支持。

GT/series明确重抽沿原inquiry，reason={kind:explicit_user,message_ref:消息标识}，parent=原request。小阵明确重抽新inquiry，也传reason/parent，公开结果redraw显示关联；普通新问不传parent。仅不清楚/不满意不能当授权。

import仅兼容旧GT/nine/line非随机导入；small/series不支持该入口，不用它绕过其发牌方法。ready为运行能力，catalog是知识目录。
