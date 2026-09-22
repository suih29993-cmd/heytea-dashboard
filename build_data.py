# -*- coding: utf-8 -*-
r"""喜茶华南区数据看板 - 数据管道

自动扫描工作区里所有数据期文件夹，逐期构建缓存并合并输出 data.json。
新增一期数据只要把文件夹放进本目录即可，无需改代码。

数据期文件夹（任一种命名都会被识别）：
  双周基础数据MMDD-MMDD              周期由文件夹名决定
  N月评分数据 / YYYY年N月评分数据      周期优先取数据文件名里的「M.D-M.D」，否则按整月
  其它名字，只要目录里直接放着美团/闪购评分数据 xlsx，也当作一期

每期文件夹内（两种目录布局都兼容）：
  [评分数据\]全国评分数据*-美团.xlsx / *-闪购.xlsx  ← 门店级 / 督导级 / 区域·城市级 指标
  [评分数据\]有公式\*（有公式）.xlsx               ← 门店级明细：门店维度整列没有的指标、
                                                    二级指标的「上期」，并给出该期准确的日期区间
  基础数据\<期>.xlsx 或 <期>.xlsx                  ← 仅用于补 门店ID / 门店类型（可选）

整期只有「（有公式）」文件、且平铺在期文件夹根目录时（如 9.14-9.20评分数据\），
该文件身兼两职：既是评分数据（含 华南门店维度 / 华南汇总 / 督导 全表），也是门店级明细。

输出: data.json -> { defaultPeriod, _order, periods: {folder: 单期数据} }
"""
import openpyxl, json, os, re, datetime, sys, traceback

def _excepthook(t, v, tb):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_log.txt'), 'w', encoding='utf-8') as f:
            f.write(''.join(traceback.format_exception(t, v, tb)))
    except Exception:
        pass

sys.excepthook = _excepthook

BASE = os.path.dirname(os.path.abspath(__file__))
PERIOD_YEAR = 2026
OUT = os.path.join(BASE, 'data.json')
CACHE_DIR = os.path.join(BASE, '_data_cache')
_FOLDER_RE = re.compile(r'^双周基础数据(\d{2})(\d{2})-(\d{2})(\d{2})$')                     # 双周基础数据0824-0830
_RANGE_RE = re.compile(r'(\d{1,2})[.．](\d{1,2})\s*[-—–~～至]\s*(\d{1,2})[.．](\d{1,2})')    # 9.1-9.13
_MONTH_RE = re.compile(r'(?:(\d{4})年)?(\d{1,2})月')                                       # 9月 / 2026年9月
_SKIP_DIRS = ('_data_cache', '__pycache__')

# ---------------- 指标定义 ----------------
# 门店级：评分数据 -> 华南门店维度（门店名在第 5 列，从第 6 行开始）
STORE_COLS = {
    '美团': {'pair': {'mt_score': 6, 'mt_repeat': 15},
             'single': {'mt_goods_sat': 9, 'mt_pack_sat': 10, 'mt_repeat_score': 11,
                        'mt_food_safe': 12, 'mt_reply_score': 13, 'mt_service_fb': 14}},
    # 闪购门店维度另有「本期/上期消息回复率」百分比列（15/16）；美团门店维度没有该列
    # （只有「消息回复率得分（10%）」），美团的门店级消息回复率百分比改由
    # 评分数据\有公式\*（有公式）.xlsx 的「全国本期/全国上期」明细聚合，见 _read_mt_reply
    '闪购': {'pair': {'sg_score': 6, 'sg_reply': 15, 'sg_cancel': 17},
             'single': {'sg_taste_sat': 9, 'sg_pack_sat': 10, 'sg_repeat_score': 11,
                        'sg_food_safe': 12, 'sg_reply_score': 13, 'sg_service_fb': 14}},
}
# 区域/城市级：评分数据 -> 华南汇总（列整体后移 1，城市名在第 3 列，从第 5 行开始）
SUMMARY_COLS = {
    '美团': {'pair': {'mt_score': 5, 'mt_repeat': 14},
             'single': {'mt_goods_sat': 8, 'mt_pack_sat': 9, 'mt_repeat_score': 10,
                        'mt_food_safe': 11, 'mt_reply_score': 12, 'mt_service_fb': 13}},
    '闪购': {'pair': {'sg_score': 5, 'sg_reply': 14, 'sg_cancel': 16},
             'single': {'sg_taste_sat': 8, 'sg_pack_sat': 9, 'sg_repeat_score': 10,
                        'sg_food_safe': 11, 'sg_reply_score': 12, 'sg_service_fb': 13}},
}
# 督导级：评分数据 -> 督导维度 / 督导（本期·上期·变化 三元组，从第 3 行开始）
SUP_COLS = {
    '美团': {'mt_score': 2, 'mt_goods_sat': 5, 'mt_pack_sat': 8, 'mt_repeat_score': 11,
             'mt_food_safe': 14, 'mt_reply_score': 17, 'mt_service_fb': 20},
    # 闪购督导表最后一组（第 20-22 列）与门店级口径不一致（是比率、不是 0-5 分），
    # 因此不取该列，闪购「服务负反馈率」改由旗下门店聚合补齐
    '闪购': {'sg_score': 2, 'sg_taste_sat': 5, 'sg_pack_sat': 8, 'sg_repeat_score': 11,
             'sg_food_safe': 14, 'sg_reply_score': 17},
}
ALL_M = (list(STORE_COLS['美团']['pair']) + list(STORE_COLS['美团']['single'])
         + list(STORE_COLS['闪购']['pair']) + list(STORE_COLS['闪购']['single'])
         + ['mt_reply'])   # 美团消息回复率(%)：无固定列号，由（有公式）明细表聚合

# 督导视图派生指标：由二级指标按平台公式加权求和 (指标名, 权重)，6 项权重合计 100%
#   商品类 4 项合计 80%：满意度 30% + 包装满意度 10% + 复购率指标得分 20% + 食品安全负反馈率 20%
#   服务类 2 项合计 20%：消息回复率 10% + 服务负反馈率 10%
# 分类分要按「本维度总权重」归一化回 5 分制（商品除以 0.8、服务除以 0.2），不要再改回直接求和：
#   商品质量分 =（商品 4 项加权和）÷ 0.8（满分 5 分）
#   服务体验分 =（服务 2 项加权和）÷ 0.2（满分 5 分）
#   综合体验分 = 商品质量分×80% + 服务体验分×20%（满分 5 分）＝ 平台给出的评分 mt_score / sg_score
COMPOSITE = {
    'mt_quality': (('mt_goods_sat', 0.30), ('mt_pack_sat', 0.10),
                   ('mt_repeat_score', 0.20), ('mt_food_safe', 0.20)),
    'mt_service': (('mt_reply_score', 0.10), ('mt_service_fb', 0.10)),
    'sg_quality': (('sg_taste_sat', 0.30), ('sg_pack_sat', 0.10),
                   ('sg_repeat_score', 0.20), ('sg_food_safe', 0.20)),
    'sg_service': (('sg_reply_score', 0.10), ('sg_service_fb', 0.10)),
}
# 归一化除数 = 本维度子项权重合计
COMPOSITE_DENOM = {'mt_quality': 0.8, 'mt_service': 0.2, 'sg_quality': 0.8, 'sg_service': 0.2}
# 城市/战区层源表只给这些二级指标的「本期」一列，上期由旗下门店聚合补齐（见 build_period）
_CITY_PREV = ('mt_goods_sat', 'mt_pack_sat', 'mt_repeat_score', 'mt_food_safe',
              'mt_reply_score', 'mt_service_fb',
              'sg_taste_sat', 'sg_pack_sat', 'sg_repeat_score', 'sg_food_safe',
              'sg_reply_score', 'sg_service_fb')


def _month_end(year, month):
    nxt = datetime.date(year + 1, 1, 1) if month == 12 else datetime.date(year, month + 1, 1)
    return nxt - datetime.timedelta(days=1)


def _folder_year(folder):
    m = _MONTH_RE.search(folder)
    return int(m.group(1)) if (m and m.group(1)) else PERIOD_YEAR


def _has_rating_file(path):
    """目录下是否直接放着美团/闪购的评分数据 xlsx"""
    try:
        names = os.listdir(path)
    except OSError:
        return False
    return any(fn.lower().endswith('.xlsx') and not fn.startswith('~$') and ('美团' in fn or '闪购' in fn)
               for fn in names)


def _is_period_folder(name):
    """判断顶层目录是不是“一期数据”：双周基础数据MMDD-MMDD / *评分数据 / 目录里直接放着评分数据"""
    if name.startswith(('.', '_')) or name in _SKIP_DIRS:
        return False
    p = os.path.join(BASE, name)
    if not os.path.isdir(p):
        return False
    return bool(_FOLDER_RE.match(name) or '评分数据' in name or '基础数据' in name or _has_rating_file(p))


def _period_range(folder):
    """该期的 (起始日, 结束日)；判不出来返回 None

    优先级：文件夹名里的 MMDD-MMDD → 目录内数据文件名里的「M.D-M.D」→ 文件夹名里的「N月」按整月
    """
    m = _FOLDER_RE.match(folder)
    if m:
        sm, sd, em, ed = map(int, m.groups())
        y = _folder_year(folder)
        return datetime.date(y, sm, sd), datetime.date(y, em, ed)
    try:
        names = [folder] + sorted(os.listdir(os.path.join(BASE, folder)))
    except OSError:
        names = [folder]
    for n in names:
        m = _RANGE_RE.search(n)
        if m:
            sm, sd, em, ed = map(int, m.groups())
            y = _folder_year(folder)
            start, end = datetime.date(y, sm, sd), datetime.date(y, em, ed)
            if end < start:                      # 跨年，如 12.20-1.5
                end = datetime.date(y + 1, em, ed)
            return start, end
    m = _MONTH_RE.search(folder)
    if m:
        y = int(m.group(1)) if m.group(1) else PERIOD_YEAR
        mo = int(m.group(2))
        return datetime.date(y, mo, 1), _month_end(y, mo)
    return None


def _period_key(folder):
    r = _period_range(folder)
    if r:
        return datetime.datetime.combine(r[0], datetime.time())
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(BASE, folder)))
    except OSError:
        return datetime.datetime.min


def _period_str(folder):
    """(本期起, 本期止, 上期起, 上期止)

    上期优先取“上一期文件夹”的区间；没有上一期时，整月按上一自然月，非整月按同长度前移。
    """
    folders = list_period_folders()
    rng = _period_range(folder) or _period_range(folders[-1])
    if rng is None:
        return '', '', '', ''
    prev = None
    if folder in folders and folders.index(folder) > 0:
        prev = _period_range(folders[folders.index(folder) - 1])
    if prev is None:
        start, end = rng
        if start.day == 1 and end == _month_end(start.year, start.month):
            y, mo = (start.year - 1, 12) if start.month == 1 else (start.year, start.month - 1)
            prev = (datetime.date(y, mo, 1), _month_end(y, mo))
        else:
            span = datetime.timedelta(days=(end - start).days + 1)
            prev = (start - span, end - span)
    fmt = lambda d: d.strftime('%Y-%m-%d')
    return fmt(rng[0]), fmt(rng[1]), fmt(prev[0]), fmt(prev[1])


def list_period_folders():
    """当前工作区里所有数据期文件夹，按时间升序；server.py 也用它做自动识别"""
    cands = [d for d in os.listdir(BASE) if _is_period_folder(d)]
    if not cands:
        raise SystemExit('未找到数据文件夹（如“双周基础数据0824-0830”“8月评分数据”）。')
    cands.sort(key=_period_key)
    return cands


def _num(x):
    if x is None:
        return None
    if isinstance(x, str) and x.strip() in ('', '#REF!', '#N/A', '#DIV/0!', '#VALUE!', '-', '—', '/'):
        return None
    try:
        return float(x)
    except Exception:
        return None


def _txt(x):
    return str(x).strip() if x is not None else ''


def _pair(r, i):
    """本期 / 上期 两列，变化自动计算"""
    cur, prev = _num(r[i]), _num(r[i + 1])
    return {'cur': cur, 'prev': prev,
            'delta': round(cur - prev, 4) if (cur is not None and prev is not None) else None}


def _single(r, i):
    """只有本期一列"""
    return {'cur': _num(r[i]), 'prev': None, 'delta': None}


def _triple(r, i):
    """本期 / 上期 / 变化 三列"""
    cur, prev, d = _num(r[i]), _num(r[i + 1]), _num(r[i + 2])
    if d is None and cur is not None and prev is not None:
        d = round(cur - prev, 4)
    return {'cur': cur, 'prev': prev, 'delta': d}


def _metric_map(r, spec):
    out = {}
    for k, i in spec.get('pair', {}).items():
        out[k] = _pair(r, i)
    for k, i in spec.get('single', {}).items():
        out[k] = _single(r, i)
    return out


def _agg(rowset, mk):
    """由门店级聚合出 本期/上期/变化"""
    curs = [s['metrics'][mk]['cur'] for s in rowset if s['metrics'][mk]['cur'] is not None]
    prevs = [s['metrics'][mk]['prev'] for s in rowset if s['metrics'][mk]['prev'] is not None]
    cur = round(sum(curs) / len(curs), 4) if curs else None
    prev = round(sum(prevs) / len(prevs), 4) if prevs else None
    return {'cur': cur, 'prev': prev,
            'delta': round(cur - prev, 4) if (cur is not None and prev is not None) else None}


def _wavg(rows, mk, which):
    """按门店数加权平均"""
    num = den = 0.0
    for r in rows:
        v = r['metrics'].get(mk, {}).get(which)
        w = r.get('storeCount') or 0
        if v is None or not w:
            continue
        num += v * w
        den += w
    return round(num / den, 4) if den else None


def _composite(metrics, parts, denom=1.0):
    """按权重加权求和后除以本维度总权重（归一化到 5 分制）；任一分项缺失则记 None"""

    def calc(which):
        total = 0.0
        for k, w in parts:
            v = (metrics.get(k) or {}).get(which)
            if v is None:
                return None
            total += v * w
        return round(total / denom, 4) if denom else None

    cur, prev = calc('cur'), calc('prev')
    return {'cur': cur, 'prev': prev,
            'delta': round(cur - prev, 4) if (cur is not None and prev is not None) else None}


def _row_channel(row):
    """行属于哪个渠道：由「有本期值的指标前缀」判断

    城市层每个渠道各出一行（城市名会重复），主键必须带上渠道才不会串行；
    区域行则是两个渠道合并在同一行。
    """
    metrics = row.get('metrics') or {}
    for prefix, ch in (('mt_', '美团'), ('sg_', '闪购')):
        for mk, mv in metrics.items():
            if mk.startswith(prefix) and isinstance(mv, dict) and mv.get('cur') is not None:
                return ch
    return ''


# 各级行的主键：门店/督导/区域用名字，城市用 (区域, 城市, 渠道)
_LEVEL_KEYS = (('stores', lambda r: r['name']),
               ('supervisor_summary', lambda r: r['name']),
               ('city_summary', lambda r: (r['region'], r['city'], _row_channel(r))),
               ('region_summary', lambda r: r['name']))


def _fill_prev_from_previous(period, prev_period):
    """用上一期的「本期值」补齐本期缺失的「上期值」

    为什么需要：源表在门店/城市/区域层只给二级指标的「本期」一列（没给上期），
    而这些二级指标算出来的商品质量分/服务体验分又要求 6 项齐全才算得出环比，
    于是这些层级一直显示「—」。平台在督导层给的是「本期/上期/变化」三元组，不受影响。

    只在两期窗口首尾相接时才补（本期 meta.prevPeriod == 上一期 meta.period），
    否则（例如半月期、缺上一期）原样返回。只补 prev 为空的指标，
    平台自带的上期列不覆盖；上一期没有的实体或指标仍为 None（前端显示「—」）。
    """
    a_meta, b_meta = period.get('meta') or {}, prev_period.get('meta') or {}
    if not a_meta.get('prevPeriod') or a_meta.get('prevPeriod') != b_meta.get('period'):
        return 0
    filled = 0
    for key, keyf in _LEVEL_KEYS:
        srcs = {}
        for row in prev_period.get(key) or []:
            try:
                srcs[keyf(row)] = row
            except (KeyError, TypeError):
                continue
        for row in period.get(key) or []:
            try:
                src = srcs.get(keyf(row))
            except (KeyError, TypeError):
                continue
            if not src:
                continue
            src_metrics = src.get('metrics') or {}
            for mk, mv in (row.get('metrics') or {}).items():
                if not isinstance(mv, dict) or mv.get('prev') is not None:
                    continue
                bv = src_metrics.get(mk)
                bv = bv.get('cur') if isinstance(bv, dict) else None
                if bv is None:
                    continue
                mv['prev'] = bv
                mv['delta'] = round(mv['cur'] - bv, 4) if mv.get('cur') is not None else None
                filled += 1
    return filled


def _apply_composites(period):
    """给某期各级（门店/督导/城市/区域）metrics 补齐派生指标

    顺序有讲究：先用 COMPOSITE 算出两个分类分（各自除以维度总权重归一化），
    商品质量分/服务体验分才会出现在 metrics 里，供后面的加权平均使用。
    """
    for s in period.get('stores', []):
        for mk, parts in COMPOSITE.items():
            s['metrics'][mk] = _composite(s['metrics'], parts, COMPOSITE_DENOM.get(mk, 1.0))
    for key in ('supervisor_summary', 'city_summary', 'region_summary'):
        for row in period.get(key, []):
            for mk, parts in COMPOSITE.items():
                row['metrics'][mk] = _composite(row['metrics'], parts, COMPOSITE_DENOM.get(mk, 1.0))
    return period


# ---------------- 文件定位 ----------------
def _first_dir(folder, *rels):
    """按顺序返回第一个存在的目录；rels 里用 () 表示期文件夹本身"""
    for rel in rels:
        p = os.path.join(BASE, folder, *rel) if rel else os.path.join(BASE, folder)
        if os.path.isdir(p):
            return p
    return None


def _rating_files(folder):
    """返回 {'美团': 路径, '闪购': 路径}

    兼容 期文件夹\\评分数据\\*.xlsx 与 期文件夹\\*.xlsx 两种布局。
    第一轮只认不含「有公式」的文件名（有公式文件由 _formula_file() 单独定位）；平铺布局下
    再补一轮认「（有公式）」文件——那种期整期只有一份有公式导出，它本身就含全套 sheet。
    """
    d = _first_dir(folder, ('评分数据',), ())
    if not d:
        return {}
    flat = os.path.normcase(d) == os.path.normcase(os.path.join(BASE, folder))
    found = {}
    for want_formula in (False, True):
        if want_formula and not flat:                   # 折叠布局：有公式文件不是评分数据
            break
        for fn in sorted(os.listdir(d)):
            if ('有公式' in fn) != want_formula:
                continue
            if not fn.lower().endswith('.xlsx'):
                continue
            if fn.startswith('~$') or fn.startswith('.'):   # 跳过 Excel 临时锁文件
                continue
            p = os.path.join(d, fn)
            if not os.path.isfile(p):
                continue
            if '美团' in fn:
                found.setdefault('美团', p)
            elif '闪购' in fn:
                found.setdefault('闪购', p)
    return found


def _formula_file(folder, plat):
    """「有公式」文件：兼容 评分数据\\有公式\\、有公式\\ 与平铺在期文件夹根目录三种布局"""
    for d in (_first_dir(folder, ('评分数据', '有公式'), ('有公式',)), _first_dir(folder, ())):
        if not d:
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith('.xlsx') and not fn.startswith('~$') and '有公式' in fn and plat in fn:
                return os.path.join(d, fn)
    return None


def _base_file(folder):
    """基础数据底表：兼容 基础数据\\<期>.xlsx 与平铺 <期>.xlsx 两种布局"""
    for rel in ((folder, '基础数据', folder + '.xlsx'), (folder, folder + '.xlsx')):
        p = os.path.join(BASE, *rel)
        if os.path.exists(p):
            return p
    return None


def _store_info(folder):
    """按门店名取 门店ID / 门店类型（可选，取不到就不补）"""
    p = _base_file(folder)
    out = {}
    if not p:
        return out
    try:
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        ws = wb['门店基础数据底表']
        for r in ws.iter_rows(min_row=4, values_only=True):
            name = r[5]
            if not name:
                continue
            mid = r[6]
            out[str(name).strip()] = {
                'id': str(int(mid)) if isinstance(mid, (int, float)) else str(mid or ''),
                'type': r[4] or '未知',
            }
        wb.close()
    except Exception as e:
        print('   （门店底表读取失败，忽略：%s）' % e, flush=True)
    return out


_WRAP_RE = re.compile(r'^[^\(（]*[\(（](.+?)[\)）]$')


def _norm_store(s):
    """去掉明细表门店名的「喜茶(...)」外壳，统一全角/半角括号与空白，便于与门店名对齐"""
    t = re.sub(r'\s+', '', str(s or '')).replace('（', '(').replace('）', ')')
    m = _WRAP_RE.match(t)
    return (m.group(1) if m else t).strip()


# 「有公式」文件里的门店明细表（0 基列号）
#   美团：门店×日期明细（表名 全国本期/全国上期，另有「日期」列可反推该期区间）
#   闪购：一店一行（表名 本期/上期，没有日期列）；华南最新一期平铺导出时表名也是 本期/上期
# cols 里既有门店维度整列没有的指标，也有「只给本期一列」的二级指标——后者的上期全靠「上期」表
_DETAIL = {
    '美团': {'cur': ('全国本期', '本期'), 'prev': ('全国上期', '上期'),
             'name': 5, 'sid': 6, 'date': 4, 'frame': True,
             'cols': {'mt_score': 10, 'mt_goods_sat': 13, 'mt_pack_sat': 14,
                      'mt_repeat_score': 15, 'mt_repeat': 16, 'mt_reply_score': 17,
                      'mt_reply': 18, 'mt_service_fb': 19, 'mt_food_safe': 20}},
    '闪购': {'cur': ('本期',), 'prev': ('上期',),
             'name': 4, 'sid': 5, 'date': None, 'frame': False,
             'cols': {'sg_score': 8, 'sg_taste_sat': 9, 'sg_pack_sat': 10,
                      'sg_repeat_score': 11, 'sg_food_safe': 12, 'sg_reply_score': 13,
                      'sg_service_fb': 14, 'sg_reply': 15, 'sg_cancel': 16}},
}
# 「战区框架表」列号（0 基）：美团外卖ID 9、门店名称 15
_MT_FRAME_NAME, _MT_FRAME_ID = 15, 9


def _read_detail(folder, plat, info):
    """「有公式」文件里的门店明细 → 门店级指标 + 该期准确的日期区间

    返回 (per_store, ranges)：
      per_store[门店名][指标] = {'cur':…, 'prev':…, 'delta':…}，指标见 _DETAIL[plat]['cols']，
        口径与文件自身公式一致：对门店的全部日期取平均（已核对：门店维度的本期值 = 明细本期均值）。
      ranges = (本期(起,止), 上期(起,止))，取自美团明细的「日期」列，比文件夹名更准，用于页面上的
        「数据周期 / 上一周期」文案；闪购明细没有日期列，返回 (None, None)。

    明细表门店名带「喜茶(...)」外壳，先按规范化名称匹配；对不上时用「战区框架表」的
    门店名称 → 美团外卖ID 反查 ID，再按 ID 匹配。
    """
    cfg = _DETAIL[plat]
    path = _formula_file(folder, plat)
    if not path:
        return {}, (None, None)
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

        def pick(names):
            for n in names:
                if n in wb.sheetnames:
                    return n
            return None

        def collect(sheet):
            by_name, by_id, days = {}, {}, []
            if not sheet:
                return by_name, by_id, days
            for r in wb[sheet].iter_rows(min_row=2, values_only=True):
                if len(r) > cfg['name'] and r[cfg['name']]:
                    nk, sid = _norm_store(r[cfg['name']]), str(r[cfg['sid']]).strip()
                    for mk, i in cfg['cols'].items():
                        v = _num(r[i]) if len(r) > i else None
                        if v is None:
                            continue
                        by_name.setdefault((nk, mk), []).append(v)
                        by_id.setdefault((sid, mk), []).append(v)
                if cfg['date'] is not None and len(r) > cfg['date']:
                    d = _txt(r[cfg['date']])
                    if len(d) == 8 and d.isdigit():
                        days.append(d)
            days.sort()
            return by_name, by_id, days

        cur, prev = collect(pick(cfg['cur'])), collect(pick(cfg['prev']))
        frame = {}
        if cfg['frame'] and '战区框架表' in wb.sheetnames:
            for r in wb['战区框架表'].iter_rows(min_row=2, values_only=True):
                if len(r) > _MT_FRAME_NAME and r[1] and r[_MT_FRAME_NAME] and r[_MT_FRAME_ID]:
                    frame[_norm_store(r[_MT_FRAME_NAME])] = str(r[_MT_FRAME_ID]).strip()
        wb.close()
    except Exception as e:
        print('   （%s（有公式）读取失败，忽略明细补数：%s）' % (plat, e), flush=True)
        return {}, (None, None)

    def mean(src, name, sid, mk):
        seq = src[0].get((name, mk)) or (src[1].get((sid, mk)) if sid else None)
        return round(sum(seq) / len(seq), 4) if seq else None

    out = {}
    for name in info:
        nk = _norm_store(name)
        ik = str((info.get(name) or {}).get('id') or '').strip() or frame.get(nk, '')
        rec = {}
        for mk in cfg['cols']:
            c, pv = mean(cur, nk, ik, mk), mean(prev, nk, ik, mk)
            if c is None and pv is None:
                continue
            rec[mk] = {'cur': c, 'prev': pv,
                       'delta': round(c - pv, 4) if (c is not None and pv is not None) else None}
        if rec:
            out[name] = rec

    def span(days):
        if not days:
            return None
        fmt = lambda d: '%s-%s-%s' % (d[:4], d[4:6], d[6:])
        return (fmt(days[0]), fmt(days[-1]))

    return out, (span(cur[2]), span(prev[2]))


# ---------------- 评分数据各层级 ----------------
def _store_spec(plat, header):
    """门店维度取数列号；第 15/16 列的含义各期不同，按表头判断

    美团：8 月是「本期/上期复购率」，9 月起改成「本期/上期消息回复率」；
    闪购：一直是「本期/上期消息回复率」+ 第 17/18 列「本期/上期商责取消率」。
    """
    spec = dict(STORE_COLS[plat])
    spec['pair'] = dict(spec['pair'])
    spec['single'] = dict(spec['single'])
    if plat == '美团':
        spec['pair'].pop('mt_repeat', None)
        h15 = _txt(header[15]) if len(header) > 15 else ''
        if '复购率' in h15:
            spec['pair']['mt_repeat'] = 15
        elif '消息回复率' in h15:
            spec['pair']['mt_reply'] = 15
    return spec


def _read_rating_stores(path, plat):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['华南门店维度']
    header = list(ws.iter_rows(min_row=4, max_row=4, values_only=True))[0]
    spec = _store_spec(plat, header)
    out = {}
    for r in ws.iter_rows(min_row=6, values_only=True):
        name = r[5]
        if not name:
            continue
        name = str(name).strip()
        out[name] = {
            'region': _txt(r[1]), 'province': _txt(r[2]),
            'city': _txt(r[3]), 'supervisor': _txt(r[4]),
            'metrics': _metric_map(r, spec),
        }
    wb.close()
    return out


def _read_rating_sups(path, plat):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sheet in ('督导维度', '华南督导', '督导'):     # 美团 8 月=督导维度、9 月=华南督导；闪购 9 月=华南督导
        if sheet in wb.sheetnames:
            break
    else:
        wb.close()
        return {}
    ws = wb[sheet]
    out = {}
    for r in ws.iter_rows(min_row=3, values_only=True):
        name = r[1]
        if not name:
            continue
        out[str(name).strip()] = {
            'region': _txt(r[0]),
            'metrics': {k: _triple(r, i) for k, i in SUP_COLS[plat].items()},
        }
    wb.close()
    return out


def _read_rating_summary(path, plat):
    """返回 (战区行指标, 城市行列表)"""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['华南汇总']
    top, cities = None, []
    for r in ws.iter_rows(min_row=5, values_only=True):
        city = r[3]
        if not isinstance(city, str):
            continue
        city = city.strip()
        if city in ('', '影响分数'):
            continue
        m = _metric_map(r, SUMMARY_COLS[plat])
        if city == '战区':
            if top is None:
                top = m
            else:
                top.update(m)
            continue
        cities.append({'region': _txt(r[1]), 'city': city,
                       'storeCount': int(_num(r[4]) or 0), 'metrics': m})
    wb.close()
    return top, cities


def build_period(folder):
    period, period_end, prev, prev_end = _period_str(folder)
    rating = _rating_files(folder)
    if not rating:
        raise RuntimeError('未找到评分数据文件（美团 / 闪购）')

    # ---------- 1. 门店级 ----------
    store_rec = {}
    plat_names = {}           # 各渠道「华南门店维度」里的门店（明细只给这些门店补数）
    for plat, path in rating.items():
        recs = _read_rating_stores(path, plat)
        plat_names[plat] = set(recs)
        for name, rec in recs.items():
            tgt = store_rec.setdefault(name, {
                'region': rec['region'], 'province': rec['province'],
                'city': rec['city'], 'supervisor': rec['supervisor'], 'metrics': {}})
            tgt['metrics'].update(rec['metrics'])
    if not store_rec:
        raise RuntimeError('评分数据「华南门店维度」未读到任何门店')

    info = _store_info(folder)
    # 门店名以美团「华南门店维度」为准，底表只用来提供门店 ID（可能缺）
    #（有公式）明细补两件事：门店维度整列没有的指标（美团 8 月缺消息回复率、9 月起缺复购率），
    # 以及门店维度只给「本期」一列的二级指标的上期（明细自带「上期」表）。
    detail, ranges = {}, (None, None)
    for plat in rating:
        det, rng = _read_detail(folder, plat,
                                {n: info.get(n, {}) for n in plat_names.get(plat, ())})
        for name, dv in (det or {}).items():
            detail.setdefault(name, {}).update(dv)
        if rng and rng[0]:
            ranges = rng
    cur_r, prev_r = ranges or (None, None)
    # 明细的「上期」是紧邻的上一小段（平铺那期是 9/07–9/13），和「上一期文件夹」的区间
    # （_period_str 推出来的 prev/prev_end）对不上时，门店/城市层就没有别的上期来源，只能靠明细补；
    # 对得上（8 月、9 月这两期）就保持原样，留给 merge() 的 _fill_prev_from_previous 补。
    use_detail_prev = bool(prev_r) and prev_r != (prev, prev_end)
    # 「有公式」明细的日期列是这一期最准的区间，用它覆盖文件夹名推出来的文案
    if cur_r:
        period, period_end = cur_r
    if prev_r:
        prev, prev_end = prev_r
    for name, rec in store_rec.items():
        for mk, mv in (detail.get(name) or {}).items():
            tgt = rec['metrics'].get(mk)
            if tgt is None:                 # 门店维度整列没有该指标 → 整条照搬明细
                rec['metrics'][mk] = dict(mv)
                continue
            if not use_detail_prev:
                continue                    # 门店维度自带的本期/上期优先，不覆盖
            if tgt.get('cur') is None:
                tgt['cur'] = mv.get('cur')
            if tgt.get('prev') is None:
                tgt['prev'] = mv.get('prev')
            if tgt.get('cur') is not None and tgt.get('prev') is not None:
                tgt['delta'] = round(tgt['cur'] - tgt['prev'], 4)
    blanks = {mk: {'cur': None, 'prev': None, 'delta': None} for mk in ALL_M}
    stores = []
    for name, rec in store_rec.items():
        meta = info.get(name, {})
        stores.append({
            'id': meta.get('id') or name,
            'name': name, 'region': rec['region'], 'province': rec['province'],
            'city': rec['city'], 'supervisor': rec['supervisor'],
            'type': meta.get('type') or '未知', 'status': '营业中',
            'metrics': {mk: dict(rec['metrics'].get(mk) or blanks[mk]) for mk in ALL_M},
        })

    # ---------- 2. 督导级 ----------
    sup_rec = {}
    for plat, path in rating.items():
        for name, rec in _read_rating_sups(path, plat).items():
            tgt = sup_rec.setdefault(name, {'region': rec['region'], 'metrics': {}})
            if not tgt['region']:
                tgt['region'] = rec['region']
            tgt['metrics'].update(rec['metrics'])
    supervisor_summary = []
    for name, rec in sup_rec.items():
        mine = [s for s in stores if s['supervisor'] == name]
        supervisor_summary.append({
            'name': name, 'region': rec['region'],
            # 督导表里没有的指标（美团复购率、闪购商责取消率）由旗下门店聚合补齐
            'metrics': {mk: rec['metrics'].get(mk) or _agg(mine, mk) for mk in ALL_M},
        })

    # ---------- 3. 区域 / 城市级 ----------
    top_metrics, city_rows = {}, []
    for plat, path in rating.items():
        top, cities = _read_rating_summary(path, plat)
        if top:
            top_metrics.update(top)
        for c in cities:
            c['plat'] = plat
        city_rows.extend(cities)

    # 美团消息回复率：美团「华南汇总」「督导」表都没有百分比列 → 由旗下门店聚合补齐
    by_city = {}
    for s in stores:
        by_city.setdefault(s['city'], []).append(s)
    for r in city_rows:
        if r['plat'] == '美团' and r['metrics'].get('mt_reply', {}).get('cur') is None:
            r['metrics']['mt_reply'] = _agg(by_city.get(r['city'], []), 'mt_reply')
        if not use_detail_prev:
            continue
        # 城市层只给这些二级指标的「本期」→ 上期由旗下门店聚合补齐；城市级本来就是旗下门店的
        # 简单平均（已与「华南汇总」逐城市核对一致），所以两级的本期/上期是同一套口径。
        for mk in _CITY_PREV:
            mv = r['metrics'].get(mk)
            if mv is None or mv.get('prev') is not None:
                continue
            mv['prev'] = _agg(by_city.get(r['city'], []), mk).get('prev')
            if mv.get('prev') is not None and mv.get('cur') is not None:
                mv['delta'] = round(mv['cur'] - mv['prev'], 4)

    city_summary = [{
        'region': r['region'], 'city': r['city'], 'storeCount': r['storeCount'],
        'metrics': {mk: dict(r['metrics'].get(mk) or blanks[mk]) for mk in ALL_M},
    } for r in city_rows]

    region_summary = []
    if top_metrics:
        tm = {}
        for mk in ALL_M:
            m = top_metrics.get(mk)
            if m and m.get('cur') is not None:
                tm[mk] = m
                if use_detail_prev and m.get('prev') is None:
                    # 战区行只给「本期」的二级指标 → 上期按城市行简单平均补齐
                    #（源表 战区行就是「=AVERAGE(各城市)」，两期必须同一口径才可比）
                    pv = [c['metrics'][mk]['prev'] for c in city_rows
                          if c['metrics'].get(mk, {}).get('prev') is not None]
                    if pv:
                        m['prev'] = round(sum(pv) / len(pv), 4)
                        m['delta'] = round(m['cur'] - m['prev'], 4)
            else:   # 战区行缺该指标（如闪购商责取消率）→ 按城市门店数加权补齐
                cur, pv = _wavg(city_rows, mk, 'cur'), _wavg(city_rows, mk, 'prev')
                tm[mk] = {'cur': cur, 'prev': pv,
                          'delta': round(cur - pv, 4) if (cur is not None and pv is not None) else None}
        region_summary.append({'name': '华南战区', 'metrics': tm})
    for rname in ('华南一区', '华南二区'):
        rows = [r for r in city_rows if r['region'] == rname]
        if not rows:
            continue
        metrics = {}
        for mk in ALL_M:
            cur, pv = _wavg(rows, mk, 'cur'), _wavg(rows, mk, 'prev')
            metrics[mk] = {'cur': cur, 'prev': pv,
                           'delta': round(cur - pv, 4) if (cur is not None and pv is not None) else None}
        region_summary.append({'name': rname, 'metrics': metrics})

    out = {
        'meta': {
            'period': '%s ~ %s' % (period, period_end),
            'prevPeriod': '%s ~ %s' % (prev, prev_end),
            'dataSource': folder,
            'storeTotal': len(stores),
            'openTotal': sum(1 for s in stores if s['status'] == '营业中'),
            'mtMatched': sum(1 for s in stores if s['metrics']['mt_score']['cur'] is not None),
        },
        'region_summary': region_summary,
        'supervisor_summary': supervisor_summary,
        'city_summary': city_summary,
        'stores': stores,
    }
    return _apply_composites(out)


def _write_cache(folder, out):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, folder + '.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


def merge():
    valid = set(list_period_folders())
    cache, order = {}, []
    for d in sorted(os.listdir(CACHE_DIR)):
        if not d.endswith('.json'):
            continue
        folder = d[:-5]
        if folder not in valid:
            try:
                os.remove(os.path.join(CACHE_DIR, d))
            except OSError:
                pass
            continue
        try:
            cache[folder] = _apply_composites(
                json.load(open(os.path.join(CACHE_DIR, d), encoding='utf-8')))
            order.append(folder)
        except Exception:
            pass
    if not cache:
        raise SystemExit('没有可用的期缓存，请先全量构建。')
    order.sort(key=_period_key)
    # 上期补数：源表在门店/城市/区域层没有二级指标的上期列，用上一期的本期值补上，
    # 补完再重算派生指标，商品质量分/服务体验分 才能带上环比。
    filled = 0
    for i in range(1, len(order)):
        filled += _fill_prev_from_previous(cache[order[i]], cache[order[i - 1]])
    if filled:
        for f in order:
            _apply_composites(cache[f])
    out = {'defaultPeriod': order[-1], '_order': order, 'periods': cache}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('merged periods=%d default=%s filled_prev=%d' % (len(order), order[-1], filled), flush=True)


def main():
    if '--folder' in sys.argv:
        folder = sys.argv[sys.argv.index('--folder') + 1]
        print('构建 %s ...' % folder, flush=True)
        _write_cache(folder, build_period(folder))
        print('已更新缓存 [%s]' % folder, flush=True)
        return
    if '--merge' in sys.argv:
        merge()
        return
    folders = list_period_folders()
    for f in folders:
        try:
            print('构建 %s ...' % f, flush=True)
            _write_cache(f, build_period(f))
        except Exception as e:
            print('跳过 %s：%s' % (f, e), flush=True)
    merge()


if __name__ == '__main__':
    main()
