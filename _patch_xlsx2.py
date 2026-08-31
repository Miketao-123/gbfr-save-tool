# -*- coding: utf-8 -*-
"""Add explanatory rows to sheet9 (攻击up·防御down·OD详解)."""
import zipfile

SRC = 'GBFR伤害公式_v4_代码解包版.xlsx'
DST = 'GBFR伤害公式_v4_代码解包版.new.xlsx'

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def insert_rows(xml, rows, dim_old, dim_new):
    parts = []
    for ref, cells in rows:
        cs = []
        for cr, st, tx in cells:
            s_attr = ' s="%s"' % st if st else ''
            cs.append('<c r="%s"%s t="inlineStr"><is><t>%s</t></is></c>' % (cr, s_attr, esc(tx)))
        parts.append('<row r="%s">%s</row>' % (ref, ''.join(cs)))
    assert '</sheetData>' in xml and dim_old in xml
    xml = xml.replace('</sheetData>', ''.join(parts) + '</sheetData>', 1)
    return xml.replace(dim_old, dim_new, 1)

new_rows = [
 ('10', [('A10', None, 'OD失效的深层原因(通俗)'),
   ('B10', '4', "buff增伤的本质是'被上限浪费部分的补偿': 贴满上限时buff的上限内效果被min()白吃, 系统把被吃部分的一半返还(0.5折算, 封顶+50%)。而'是否被上限挡住'的判定在OD缩放之后、且只看结果数字不看原因: min(raw,上限)≤上限是min的定义, ×(<1的OD缩放)后必然严格小于上限→判定永远为'没顶到'→补偿恒不发。换言之检测器是'瞎'的: 你没顶到上限是因为伤害低、还是因为OD缩放砍了一刀, 它分不清, 一律按'没顶到'处理。好比撞墙反弹奖励: OD缩放是墙前的泥沼, 你撞不到墙不是力气不够, 但裁判只看碰没碰到墙。注意: 失效的只是上限外补偿通道; 上限内通道(1+攻up)(1+防down)OD期间仍全额有效——只是毕业环境本来就贴满上限, 这部分被min()吃掉看不见。")]),
 ('11', [('A11', None, 'OD期间buff的实际作用与替代手段'),
   ('B11', '4', "OD期间 atk/def buff 唯一还有用的场景: 无buff时 raw<上限(弱招式/低面板)——此时它在上限内全额生效把你往上限抬(如raw 0.7C→+30%攻→0.91C, ×od后仍×1.30); 无限难度毕业环境人人常驻贴满, 故体感'OD时buff全废'。OD期间真正有效的增伤: ①伤害上限up(天星之炼/煌/界/焰, 把min()的墙加高, ×od后仍更高); ②属性转换×1.2(上限外, 无检测); ③天星之雪/止息等DMG-Dealt因子(上限外1+Σ造成伤害up, 无检测); ④追击(独立addDamage段)。排序证据状态: 检测在OD缩放之后的结构来自voltskyghost社区实测, 是唯一能同时解释'非OD时buff有上限外收益'与'OD时恒0'两个观测的模型; exe符号佐证各组件(PlayerDamageLimitParameter/SetEnemyDamageRate=OD缩放/powerDamageUpBuffRate_), 排序本身未经反编译直接确认。")]),
]

zin = zipfile.ZipFile(SRC)
zout = zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename == 'xl/worksheets/sheet9.xml':
        xml = data.decode('utf-8')
        xml = insert_rows(xml, new_rows, 'A1:B9', 'A1:B11')
        data = xml.encode('utf-8')
        print('patched sheet9: +2 rows')
    zout.writestr(item, data)
zout.close()
print('written', DST)
