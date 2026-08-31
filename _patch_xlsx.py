# -*- coding: utf-8 -*-
"""Patch specific inlineStr cells in the GBFR xlsx (stdlib only).
Rewrites the zip with modified sheet XMLs. Verifies each replacement."""
import zipfile, shutil, sys

SRC = 'GBFR伤害公式_v4_代码解包版.xlsx'
DST = 'GBFR伤害公式_v4_代码解包版.new.xlsx'

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def replace_cell(xml, ref, new_text):
    """Replace the whole <c r=ref ...>...</c> (or self-closing) with inlineStr cell."""
    start = xml.find('<c r="%s"' % ref)
    assert start >= 0, 'cell %s not found' % ref
    gt = xml.find('>', start)
    # self-closing?
    if xml[gt-1] == '/':
        old = xml[start:gt+1]
        attrs = xml[start:gt-1]
    else:
        end = xml.find('</c>', gt)
        old = xml[start:end+4]
        attrs = xml[start:gt]
    # normalize attrs: keep r= and s=, drop any t=
    import re
    m_s = re.search(r'\ss="(\d+)"', attrs)
    s_attr = ' s="%s"' % m_s.group(1) if m_s else ''
    new = '<c r="%s"%s t="inlineStr"><is><t>%s</t></is></c>' % (ref, s_attr, esc(new_text))
    return xml.replace(old, new, 1), old

def insert_row(xml, ref, cells, dim_old, dim_new):
    """Insert a new row before </sheetData>. cells = list of (ref, style_or_None, text)."""
    parts = []
    for cr, st, tx in cells:
        s_attr = ' s="%s"' % st if st else ''
        parts.append('<c r="%s"%s t="inlineStr"><is><t>%s</t></is></c>' % (cr, s_attr, esc(tx)))
    row = '<row r="%s">%s</row>' % (ref, ''.join(parts))
    assert '</sheetData>' in xml
    xml = xml.replace('</sheetData>', row + '</sheetData>', 1)
    assert dim_old in xml
    xml = xml.replace(dim_old, dim_new, 1)
    return xml

patches = {}  # sheetfile -> function(xml)->xml

# ---------------- sheet6: 问题四·上限与额外伤害 ----------------
S6 = {
 'B5': "天星之雪 = SKILL_324_00 / 因子 GEEN_324(Key 2828591747, Celestial Aqua), 满级15: 官方文本'对破防状态的敌人造成的伤害量提升; 连锁时域和奥义连锁中造成的伤害量提升'(EN原文: Boosts the damage dealt to foes in Break, including link time attacks and chain bursts), Explain模板'DMG Dealt +{0:.1f}%'(=造成的伤害+15%, L15)。skill_status每级仅LevelValue1非零(1→15): 单倍率条件型'造成的伤害UP'因子, 破防/连锁时域/奥义连锁三个触发条件共用同一倍率——数据层不存在'时域单独走另一乘区'的第二参数。",
 'B6': "上限外增伤(额外伤害)乘区的(1+Σ造成伤害up)因子——乘在min(可造成伤害, 上限)之后, 不被伤害上限截断(v4.1修正, 此前标'上限内非面板乘算区'系仅凭文本字面推断)。证据链: ①Explain模板与OD刺客(SKILL_030)/破防刺客(SKILL_031)/天星之止息(SKILL_326)完全相同('DMG Dealt +{0:.1f}%'), skill.tbl中324/326同为Unk11=7, 均为单参数结构; ②同模板的天星之止息已实测为上限外增伤(DLC配装攻略); ③决定性结构证据: 奥义连锁走独立管线(ChainBurstATKRate_FullChain/3Chain/2Chain, chainBurstDamageLimit_=9999999), 无视防御、不暴击、不吃常规伤害上升/上限UP——若天星之雪是上限内乘区修饰器, 对连锁必然无效, 但官方文本明确'奥义连锁中造成的伤害量提升', 故其倍率只能挂在min()截断之后; ④SKILL_009(Linked Together)有专用Chain Burst DMG参数槽, 证明'连锁伤害率'是独立通道, 而324无此参数, 其单倍率只能经通用DMG-Dealt通道(即上限外1+Σ造成伤害up)同时作用于破防/时域/连锁三种场景。",
 'B7': "不直接相乘, 但会间接跟随: 追击段(addDamage)是独立伤害段=最终主伤害×Σ追击伤害%, 触发率与伤害%有自己的参数体系(addDamage1stParam_/2ndParam_等), 天星之雪不加追击率、不加追击伤害%; 但追击段按'最终主伤害'的固定百分比计算, 主伤害被天星之雪在上限外×1.15后, 追击段同步×1.15(跟随主伤害, 非公式内相乘)。",
 'B8': "天星之雪本身不被伤害上限截断(上限外因子, 无上限检测); 同一Σ造成伤害up内与其他DMG-Dealt源加算(如同时带天星之止息: 1+0.15+0.10=1.25); 对OD缩放<1的Boss依然全额有效(对比buff增伤: 受上限检测约束, OD期间恒为0); 追击段独立于主伤害上限(见问题二)。",
 'B11': "上限外'(1+Σ造成伤害up)/(1+属性弱点加成)'的代码实现: DamageCalcParam.msg 官方参数 weakElementAddDamageRate_=0.2(弱点属性追加伤害率, 即属性转换/天星之止息类'上限外伤害'的系数), addDamageLimitBonusStatusRate_=0.5(追加伤害上限状态率, 即buff增伤0.5折算系数), playerStatusAttackerRateUpperLimit_=2(玩家攻击buff率上限200%, 对应 buff增伤 min[...,2])。上限内'造成的伤害+'因子(连击加成/能力伤害等)是否同样走上限外, 官方文本未区分, 需逐项实测。v4.1修正: 天星之雪由'上限内(字面推断)'修正为'上限外(1+Σ造成伤害up)'——依据同Explain模板家族(030/031/326)+326实测+奥义连锁独立管线结构论证(见'走哪个乘区')。残存不确定: 030 OD刺客/031破防刺客同模板, 按同规则推定同样走上限外, 尚未逐项实测(已在乘区明细表标注)。",
}
S6_newrow = ('13', [('A13', None, '连锁时域与天星之雪(专项)'),
    ('B13', '4', "问: 连锁时域期间天星之雪是否作用于额外伤害乘区? 答: 是。①连锁时域本身不改变伤害公式结构——代码层与时域相关的仅有linktime曲线(时域条累积速率, 与伤害无关)和魔晶石词条link_time_disable/link_time_no_drain, 没有任何'时域改上限/加乘区'的参数; 时域的作用只是让天星之雪的触发条件成立。②条件成立时+15%作为DMG-Dealt项进入上限外增伤=(1+属性弱点)×(1+Σ造成伤害up)+0.5×buff增伤的Σ内, 乘在min()之后: 已达上限的攻击在时域内仍×1.15, 未达上限的攻击同样×1.15(上限外因子无上限检测)。③与攻击up/防御down对比: 后者在上限外只能经0.5×buff增伤折算(整体封顶+50%)且需通过上限检测, OD期间失效; 天星之雪无折算、无检测、OD期间有效——这是上限外因子的核心价值。④置信度: 结构证据强(单倍率同模板家族+连锁独立管线论证), 最终判定建议实机A/B: 打木桩使普攻稳定贴上限, 进时域后数字×1.15即证实(若仍贴上限不动则为上限内, 证伪)。")])

# ---------------- sheet8: 天星系列因子乘区 ----------------
S8 = {
 'F6': "上限外增伤区(额外伤害乘区1+Σ造成伤害up); 不被上限截断; 经同一上限外通道对奥义连锁生效",
 'G6': "官方文本'DMG Dealt+'(与030/031/326同Explain模板, 单倍率[15]); 同家族326实测上限外; 结构证据: 奥义连锁走独立管线(ChainBurstATKRate/chainBurstDamageLimit_)不吃上限内乘区, 文本明确对连锁生效→倍率必在min()之后; 时域侧无任何专属参数(linktime曲线=时域条累积) | 高(结构证据), 待A/B实测复核",
 'B11': "① 官方文本 'ATK +X%' → 攻击力区(面板(1+Σ攻击力%), 上限内, 达上限后被截断); ② 'DMG Cap +X%' → 上限区(提高 atkTypeDamageLimit_Normal=9999/Ability=14999/SpArts=19999 的(1+上限up), 等于变相突破上限); ③ 'DMG Dealt +X%' → 上限外增伤区(1+Σ造成伤害up, 乘在min()之后): 天星之止息实测上限外, 天星之雪经结构论证同区(v4.1修正); 其余同模板因子(030 OD刺客/031 破防刺客)按同规则推定上限外, 待逐项实测; ④ 天星家族无专属曲线/参数类(exe 无 Celestial 符号, DamageCalcParam 无其曲线引用), 机制由通用技能数值驱动。",
}

# ---------------- sheet11: 乘区明细 ----------------
S11 = {
 'E7': "官方文本; ⚠v4.1: 破防刺客(031)/OD刺客(030)Explain同为'DMG Dealt +X%'模板, 按2.0规则推定走上限外(1+Σ造成伤害up)而非本区, 待逐项实测(见问题四)",
}

# ---------------- sheet1: 说明(关键结论速览) ----------------
S1 = {
 'B18': "①DLC2.0公式: 实际伤害=min(可造成伤害, 上限×(1+上限up))×OD缩放×上限外增伤; 上限外增伤=(1+属性弱点)×(1+Σ造成伤害up)+0.5×buff增伤",
 'B19': "②攻击力%(ATK+)全加算进同一面板区(上限内); 攻击up/防御down达上限后仍可经0.5×buff增伤生效(封顶+50%, 需过上限检测, OD期间失效)",
 'B20': "③追击=独立addDamage段(主伤害×Σ追击%), 触发率各自判定, 追击伤害%加算, 独立于上限",
 'B21': "④DMG Dealt+X%类因子(天星之雪/天星之止息等)走上限外(1+Σ造成伤害up), 不被上限截断, OD有效; 天星之雪在连锁时域/破防/奥义连锁均经此区生效(v4.1)",
}

def apply_cells(pairs):
    def fn(xml):
        for ref, txt in pairs.items():
            xml, old = replace_cell(xml, ref, txt)
            print('  patched', ref, '(old len %d)' % len(old))
        return xml
    return fn

def apply_s6(xml):
    xml = apply_cells(S6)(xml)
    xml = insert_row(xml, S6_newrow[0], S6_newrow[1], 'A1:B12', 'A1:B13')
    print('  inserted row 13')
    return xml

patch_map = {
    'xl/worksheets/sheet1.xml': apply_cells(S1),
    'xl/worksheets/sheet6.xml': apply_s6,
    'xl/worksheets/sheet8.xml': apply_cells(S8),
    'xl/worksheets/sheet11.xml': apply_cells(S11),
}

zin = zipfile.ZipFile(SRC)
zout = zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename in patch_map:
        print('patching', item.filename)
        xml = data.decode('utf-8')
        xml = patch_map[item.filename](xml)
        data = xml.encode('utf-8')
    zout.writestr(item, data)
zout.close()
print('written', DST)
