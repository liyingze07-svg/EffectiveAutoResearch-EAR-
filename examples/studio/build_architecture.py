"""Author editable, bilingual architecture figures from the released module contracts."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)

class Figure:
    def __init__(self, width, height, title):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" class="ear-architecture" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>', '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10Z" fill="#574176"/></marker><marker id="teal" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10Z" fill="#20786c"/></marker></defs>', '<style>.ear-architecture text{font-family:Arial,"PingFang SC",sans-serif;fill:#292438}.ear-architecture .small{font-size:17px;fill:#777080}.ear-architecture .label{font-size:19px;font-weight:600}.ear-architecture .heading{font-size:22px;font-weight:600}.ear-architecture .note{font-size:18px;fill:#20786c}</style>']
    def box(self,x,y,w,h,title,sub='',fill='#fff',stroke='#b1a5bf'):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        self.label(x+w/2,y+(h/2+7 if not sub else h/2-5),title,'label')
        if sub:self.label(x+w/2,y+h/2+24,sub,'small')
    def label(self,x,y,text,cls='small',anchor='middle'):
        self.parts.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{escape(text)}</text>')
    def path(self,d,feedback=False,dashed=False):
        color = '#20786c' if feedback else '#574176'
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" marker-end="url(#{"teal" if feedback else "arrow"})"'+(' stroke-dasharray="7 5"' if dashed else '')+'/>')
    def group(self,x,y,w,h,title,fill='#faf8fc'):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="#cfc6d9" stroke-width="1.5"/>')
        self.label(x+20,y+32,title,'heading','start')
    def save(self,name):
        (OUT/name).write_text(''.join(self.parts)+'</svg>')

for lang in ['en','zh']:
    def t(en,zh):return zh if lang=='zh' else en
    f=Figure(1180,520,t('AutonomousMath: research revision and strategy evolution','AutonomousMath：研究修订与策略演化'))
    f.group(20,25,1140,345,t('INNER LOOP · A complete research episode','内层循环 · 一次完整研究尝试'))
    f.box(43,140,160,84,t('Research target','研究目标'),t('Direction / proposal','方向 / 提案'),fill='#f0e9fa')
    f.group(232,92,535,144,t('Research worker','研究执行 Agent'),fill='#fff')
    f.box(255,151,141,70,t('Seek','检索与选题'))
    f.box(422,151,141,70,t('Prove ↔ check','证明 ↔ 质疑'))
    f.box(589,151,155,70,t('Harden & write','强化与写作'),t('Proof + paper','证明 + 稿件'))
    f.path('M203 182H255');f.path('M396 185H422');f.path('M563 185H589')
    f.box(255,261,489,47,t('Supervisor · checkpoints and versioned state','监督器 · 检查点与版本化研究状态'),fill='#f1edf6')
    f.path('M667 221V261')
    f.box(817,142,178,84,t('Fixed referee','固定终审'),t('2 fresh sessions','两个新会话'),fill='#e8f4ef',stroke='#6aa091')
    f.box(1030,142,110,84,t('Deliver','交付'),t('Artifacts','成果包'),fill='#e8f4ef',stroke='#6aa091')
    f.path('M744 284H784V183H817');f.path('M995 183H1030')
    f.label(787,124,t('Snapshot','版本快照'),'small')
    f.path('M904 226V334H497V308',True,True)
    f.path('M255 284H244V246H408V185H422',True,True)
    f.label(709,357,t('Feedback → revise → submit a new snapshot','评审反馈 → 修订 → 提交新版本'),'note')
    f.group(20,400,1140,100,t('OUTER · Evolution','外层 · 策略演化'),fill='#f7f1e8')
    f.box(341,420,223,59,t('Episode outcomes','完整尝试的结果'),t('Same task set','相同任务集'),fill='#fff',stroke='#b9a58b')
    f.box(603,420,214,59,t('Select + retain baseline','选择并保留初始策略'),fill='#fff',stroke='#b9a58b')
    f.box(856,420,283,59,t('Mutate / cross over / explore','变异 / 交叉 / 探索'),fill='#fff',stroke='#b9a58b')
    f.path('M960 226V383H452V420',True,True);f.path('M564 449H603');f.path('M817 449H856');f.path('M1139 449H1171V76H496V92',True,True)
    f.save(f'math-architecture.{lang}.svg')

    f=Figure(1180,380,t('AutoVibeIdea: evidence updates the candidate search','AutoVibeIdea：证据驱动候选搜索'))
    f.group(20,20,1140,340,t('AutoVibeIdea · UCT-guided best-first expansion','AutoVibeIdea · UCT 引导的优先扩展'))
    f.box(45,121,179,85,t('Direction + limits','方向与资源约束'),t('Research brief','研究输入'),fill='#f0e9fa')
    f.box(266,121,188,85,t('Retrieve + critique','检索与批判'),t('Literature / gaps','文献 / 研究缺口'))
    f.box(499,121,184,85,t('Expand candidates','扩展候选'),t('Questions / methods','问题 / 方法'))
    f.box(728,121,181,85,t('Evaluate + prune','评价与剪枝'),t('Evidence / feasibility','证据 / 可行性'),fill='#e8f4ef',stroke='#6aa091')
    f.box(954,121,180,85,t('Refine proposal','精修研究提案'),t('Validation plan','最小验证计划'),fill='#e8f4ef',stroke='#6aa091')
    for a,b in [(224,266),(454,499),(683,728),(909,954)]:f.path(f'M{a} 163H{b}')
    f.path('M819 206V265H359V206',True,True)
    f.label(590,294,t('Update node values → select the next expansion','更新节点价值 → 选择下一次扩展'),'note')
    f.label(590,333,t('Keep literature, candidate lineage and reasons for stopping','保留文献、候选谱系与停止理由'),'small')
    f.save(f'idea-architecture.{lang}.svg')

    f=Figure(1180,425,t('AutoRebuttal: concern diagnosis, evidence work and verified responses','AutoRebuttal：诊断关切、补齐证据与核查回复'))
    f.group(20,20,1140,385,t('AutoRebuttal · Evidence before the response','AutoRebuttal · 先解决证据，再组织回应'))
    f.box(44,105,180,80,t('Paper + reviews','论文与评审'),t('Existing evidence','已有证据'),fill='#f0e9fa')
    f.box(266,105,200,80,t('Map + diagnose','映射与诊断'),t('B1 · Concern coverage','B1 · 关切覆盖'))
    f.box(505,105,206,80,t('Fill technical gaps','补齐技术缺口'),t('Proof / experiments','证明 / 实验'),fill='#f7f1e8',stroke='#b9a58b')
    f.box(750,105,189,80,t('Draft + consensus','草稿与共识'),t('r7 · Content gate','r7 · 内容门控'))
    f.box(978,105,160,80,t('Author package','作者材料包'),t('Replies + ledger','回应 + 证据账本'),fill='#e8f4ef',stroke='#6aa091')
    for a,b in [(224,266),(466,505),(711,750)]:f.path(f'M{a} 145H{b}')
    f.path('M365 105V80H845V105');f.label(605,71,t('Sufficient evidence: draft directly','证据充分：直接起草'),'small')
    f.path('M608 185V218H517V185',True,True);f.label(607,244,t('S-ante / S-exp: design + result checks','S-ante / S-exp：设计与结果检查'),'small')
    f.box(680,285,293,60,t('B2 · Fidelity / B3 · Loopholes','B2 · 忠实性 / B3 · 漏洞检查'),fill='#e8f4ef',stroke='#6aa091')
    f.path('M845 185V285');f.path('M973 315H1058V185');f.path('M680 315H361V185',True,True)
    f.label(518,341,t('Revise or retain unresolved issues','返回修订或保留未解决事项'),'note')
    f.label(590,386,t('Final technical claims and responses go to the author for review','最终技术结论与回复交由作者核查'),'small')
    f.save(f'rebuttal-architecture.{lang}.svg')
print('Saved six editable architecture figures.')
