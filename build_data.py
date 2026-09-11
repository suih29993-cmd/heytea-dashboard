# -*- coding: utf-8 -*-
r"""喜茶华南区数据看板 - 数据管道

扫描“双周基础数据MMDD-MMDD”文件夹，逐期构建缓存并合并输出 data.json。

每期文件夹内（两种目录布局都兼容）：
  评分数据\全国评分数据*-美团.xlsx / *-闪购.xlsx   ← 门店级 / 督导级 / 区域·城市级 指标
  基础数据\<期>.xlsx  或  <期>.xlsx                ← 仅用于补 门店ID / 门店类型（可选）

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
_FOLDER_RE = re.compile(r'^双周基础数据(\d{2})(\d{2})-(\d{2})(\d{2})$')

# ---------------- 指标定义 ----------------
# 门店级：评分数据 -> 华南门店维度（门店名在第 5 列，从第 6 行开始）
STORE_COLS = {
    '美团': {'pair': {'mt_score': 6, 'mt_repeat': 15},
             'single': {'mt_goods_sat': 9, 'mt_pack_sat': 10, 'mt_repeat_score': 11,
                        'mt_food_safe': 12, 'mt_reply_score': 13, 'mt_service_fb': 14}},
    '闪购': {'pair': {'sg_score': 6, 'sg_cancel': 17},
             'single': {'sg_taste_sat': 9, 'sg_pack_sat': 10, 'sg_repeat_score': 11,
                        'sg_food_safe': 12, 'sg_reply_score': 13, 'sg_service_fb': 14}},
}
# 区域/城市级：评分数据 -> 华南汇总（列整体后移 1，城市名在第 3 列，从第 5 行开始）
SUMMARY_COLS = {
    '美团': {'pair': {'mt_score': 5, 'mt_repeat': 14},
             'single': {'mt_goods_sat': 8, 'mt_pack_sat': 9, 'mt_repeat_score': 10,
                        'mt_food_safe': 11, 'mt_reply_score': 12, 'mt_service_fb': 13}},
    '闪购': {'pair': {'sg_score': 5, 'sg_cancel': 16},
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
         + list(STORE_COLS['闪购']['pair']) + list(STORE_COLS['闪购']['single']))

# 督导视图派生指标：由二级指标按平台公式加权求和 (指标名, 权重)
# 商品质量分 = 满意度×30% + 包装满意度×10% + 复购率指标得分×20% + 食品安全负反馈率×20%（满分 4 分）
# 服务体验分 = 消息回复率×10% + 服务负反馈率×10%（满分 1 分）
# 评分 = 商品质量分 + 服务体验分（满分 5 分），即各分项按权重直接相加，不做归一化。
COMPOSITE = {
    'mt_quality': (('mt_goods_sat', 0.30), ('mt_pack_sat', 0.10),
                   ('mt_repeat_score', 0.20), ('mt_food_safe', 0.20)),
    'mt_service': (('mt_reply_score', 0.10), ('mt_service_fb', 0.10)),
    'sg_quality': (('sg_taste_sat', 0.30), ('sg_pack_sat', 0.10),
                   ('sg_repeat_score', 0.20), ('sg_food_safe', 0.20)),
    'sg_service': (('sg_reply_score', 0.10), ('sg_service_fb', 0.10)),
}


def _period_key(folder):
    m = _FOLDER_RE.match(folder)
    sm, sd, em, ed = map(int, m.groups())
    return datetime.datetime(PERIOD_YEAR, sm, sd)


def _period_str(folder):
    m = _FOLDER_RE.match(folder)
    sm, sd, em, ed = map(int, m.groups())
    start = datetime.datetime(PERIOD_YEAR, sm, sd)
    end   = datetime.datetime(PERIOD_YEAR, em, ed)
    ps = start - datetime.timedelta(days=7)
    pe = end   - datetime.timedelta(days=7)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), ps.strftime('%Y-%m-%d'), pe.strftime('%Y-%m-%d')


def _list_period_folders():
    cands = []
    for d in os.listdir(BASE):
        if _FOLDER_RE.match(d) and os.path.isdir(os.path.join(BASE, d)):
            cands.append(d)
    if not cands:
        raise SystemExit('未找到“双周基础数据MMDD-MMDD”格式的数据文件夹。')
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


def _composite(metrics, parts):
    """按权重直接求和（商品质量分满分 4 分、服务体验分满分 1 分）；任一分项缺失则记 None"""

    def calc(which):
        total = 0.0
        for k, w in parts:
            v = (metrics.get(k) or {}).get(which)
            if v is None:
                return None
            total += v * w
        return round(total, 4)

    cur, prev = calc('cur'), calc('prev')
    return {'cur': cur, 'prev': prev,
            'delta': round(cur - prev, 4) if (cur is not None and prev is not None) else None}


def _apply_composites(period):
    """给某期各级（门店/督导/城市/区域）metrics 补齐派生指标"""
    for s in period.get('stores', []):
        for mk, parts in COMPOSITE.items():
            s['metrics'][mk] = _composite(s['metrics'], parts)
    for key in ('supervisor_summary', 'city_summary', 'region_summary'):
        for row in period.get(key, []):
            for mk, parts in COMPOSITE.items():
                row['metrics'][mk] = _composite(row['metrics'], parts)
    return period


# ---------------- 文件定位 ----------------
def _rating_files(folder):
    """返回 {'美团': 路径, '闪购': 路径}；跳过“有公式”子目录"""
    d = os.path.join(BASE, folder, '评分数据')
    found = {}
    if not os.path.isdir(d):
        return found
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if not os.path.isfile(p) or not fn.lower().endswith('.xlsx'):
            continue
        if fn.startswith('~$') or fn.startswith('.'):   # 跳过 Excel 临时锁文件
            continue
        if '美团' in fn:
            found.setdefault('美团', p)
        elif '闪购' in fn:
            found.setdefault('闪购', p)
    return found


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


# ---------------- 评分数据各层级 ----------------
def _read_rating_stores(path, plat):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['华南门店维度']
    out = {}
    for r in ws.iter_rows(min_row=6, values_only=True):
        name = r[5]
        if not name:
            continue
        name = str(name).strip()
        out[name] = {
            'region': _txt(r[1]), 'province': _txt(r[2]),
            'city': _txt(r[3]), 'supervisor': _txt(r[4]),
            'metrics': _metric_map(r, STORE_COLS[plat]),
        }
    wb.close()
    return out


def _read_rating_sups(path, plat):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = '督导维度' if '督导维度' in wb.sheetnames else '督导'
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
        raise RuntimeError('未找到「评分数据」文件夹或评分数据文件')

    # ---------- 1. 门店级 ----------
    store_rec = {}
    for plat, path in rating.items():
        for name, rec in _read_rating_stores(path, plat).items():
            tgt = store_rec.setdefault(name, {
                'region': rec['region'], 'province': rec['province'],
                'city': rec['city'], 'supervisor': rec['supervisor'], 'metrics': {}})
            tgt['metrics'].update(rec['metrics'])
    if not store_rec:
        raise RuntimeError('评分数据「华南门店维度」未读到任何门店')

    info = _store_info(folder)
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
        city_rows.extend(cities)

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
    valid = set(_list_period_folders())
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
    out = {'defaultPeriod': order[-1], '_order': order, 'periods': cache}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('merged periods=%d default=%s' % (len(order), order[-1]), flush=True)


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
    folders = _list_period_folders()
    for f in folders:
        try:
            print('构建 %s ...' % f, flush=True)
            _write_cache(f, build_period(f))
        except Exception as e:
            print('跳过 %s：%s' % (f, e), flush=True)
    merge()


if __name__ == '__main__':
    main()
