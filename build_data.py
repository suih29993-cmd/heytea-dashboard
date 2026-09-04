# -*- coding: utf-8 -*-
"""喜茶华南区数据看板 - 数据管道
自动扫描“双周基础数据MMDD-MMDD”文件夹，逐期构建并合并输出。
  主文件 双周基础数据<周期>.xlsx
    - 门店基础数据底表: 门店级 7 指标(本期/上周期/差值) + 区域/城市/督导维度
    - 汇总: 战区/区/督导 聚合的 7 指标
  有公式/1双周基础数据<周期>.xlsx
    - 美团数据底表(本期) / 美团数据底表上期: 门店日明细 -> 聚合出美团5新指标
输出: data.json  ->  { defaultPeriod, _order, periods: {folder: 单期数据} }
"""
import openpyxl, json, os, re, datetime, pandas as pd, sys, traceback
from collections import defaultdict

def _excepthook(t, v, tb):
    open(r'C:\Users\HEYTEA\Desktop\每周数据看板\_log.txt', 'w', encoding='utf-8').write(
        ''.join(traceback.format_exception(t, v, tb)))
sys.excepthook = _excepthook

BASE = os.path.dirname(os.path.abspath(__file__))
PERIOD_YEAR = 2026
OUT = os.path.join(BASE, 'data.json')
CACHE_DIR = os.path.join(BASE, '_data_cache')
_FOLDER_RE = re.compile(r'^双周基础数据(\d{2})(\d{2})-(\d{2})(\d{2})$')


def _period_key(folder):
    m = _FOLDER_RE.match(folder)
    sm, sd, em, ed = map(int, m.groups())
    return datetime.datetime(PERIOD_YEAR, sm, sd)


def _list_period_folders():
    cands = []
    for d in os.listdir(BASE):
        if _FOLDER_RE.match(d) and os.path.isdir(os.path.join(BASE, d)):
            cands.append(d)
    if not cands:
        raise SystemExit('未找到“双周基础数据MMDD-MMDD”格式的数据文件夹。')
    cands.sort(key=_period_key)
    return cands


def _period_str(folder):
    m = _FOLDER_RE.match(folder)
    sm, sd, em, ed = map(int, m.groups())
    start = datetime.datetime(PERIOD_YEAR, sm, sd)
    end   = datetime.datetime(PERIOD_YEAR, em, ed)
    ps = start - datetime.timedelta(days=7)
    pe = end   - datetime.timedelta(days=7)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), ps.strftime('%Y-%m-%d'), pe.strftime('%Y-%m-%d')


def num(x):
    if x is None:
        return None
    if isinstance(x, str) and x.strip() in ('', '#REF!', '#N/A', '-', '—'):
        return None
    try:
        return float(x)
    except Exception:
        return None


ALL_M = ['mt_shop_score', 'mt_score', 'mt_reply', 'sg_shop_score', 'sg_score',
         'sg_bad_reply', 'sg_reply', 'sg_cancel', 'mt_exp', 'mt_quality',
         'mt_service', 'mt_prod_sat', 'mt_pack_sat']
MT_KEYS = ['mt_exp', 'mt_quality', 'mt_service', 'mt_prod_sat', 'mt_pack_sat']


def build_period(folder):
    period, period_end, prev, prev_end = _period_str(folder)
    main = os.path.join(BASE, folder, folder + '.xlsx')
    meit = os.path.join(BASE, folder, '有公式', '1' + folder + '.xlsx')

    # ---------- 1. 门店底表 ----------
    wb = openpyxl.load_workbook(main, read_only=True, data_only=True)
    ws = wb['门店基础数据底表']
    rows = list(ws.iter_rows(min_row=4, values_only=True))
    wb.close()

    stores = []
    for r in rows:
        status, region, sup, city, mtype, name, mid = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
        if not region or not name:
            continue
        metrics = {
            'mt_shop_score': {'cur': num(r[8]),  'prev': num(r[9]),  'delta': num(r[10])},
            'mt_score':      {'cur': num(r[11]), 'prev': num(r[12]), 'delta': num(r[13])},
            'mt_reply':      {'cur': num(r[14]), 'prev': num(r[15]), 'delta': num(r[16])},
            'sg_shop_score': {'cur': num(r[17]), 'prev': num(r[18]), 'delta': num(r[19])},
            'sg_score':      {'cur': num(r[20]), 'prev': num(r[21]), 'delta': num(r[22])},
            'sg_bad_reply':  {'cur': num(r[23]), 'prev': num(r[24]), 'delta': num(r[25])},
            'sg_reply':      {'cur': num(r[26]), 'prev': num(r[27]), 'delta': num(r[28])},
            'sg_cancel':     {'cur': num(r[29]), 'prev': num(r[30]), 'delta': num(r[31])},
            'mt_exp':      {'cur': None, 'prev': None, 'delta': None},
            'mt_quality':  {'cur': None, 'prev': None, 'delta': None},
            'mt_service':  {'cur': None, 'prev': None, 'delta': None},
            'mt_prod_sat': {'cur': None, 'prev': None, 'delta': None},
            'mt_pack_sat': {'cur': None, 'prev': None, 'delta': None},
        }
        stores.append({
            'id': str(int(mid)) if isinstance(mid, (int, float)) else str(mid),
            'name': name, 'region': region, 'city': city,
            'supervisor': sup, 'type': mtype, 'status': status,
            'metrics': metrics
        })

    # ---------- 2. 美团日明细聚合 ----------
    matched = 0
    if os.path.exists(meit):
        def agg_meituan(sheet):
            # 0-based 列: D=3 日期, E=4 门店名称, F=5 门店ID, BV..BZ=73..77
            cols = [3, 4, 5, 73, 74, 75, 76, 77]
            df = pd.read_excel(meit, sheet_name=sheet, usecols=cols, header=None,
                               skiprows=1, engine='openpyxl')
            df.columns = ['date', 'store_name', 'store_id', 'mt_exp', 'mt_quality',
                          'mt_service', 'mt_prod_sat', 'mt_pack_sat']
            for c in MT_KEYS:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            df['store_id'] = pd.to_numeric(df['store_id'], errors='coerce')
            df = df.dropna(subset=['store_id'])
            df['store_id'] = df['store_id'].astype('int64').astype(str)
            return df.groupby('store_id')[MT_KEYS].mean()
        cur_agg = agg_meituan('美团数据底表')
        prev_agg = agg_meituan('美团数据底表上期')
        for s in stores:
            mid = s['id']
            if mid in cur_agg.index:
                matched += 1
                c = cur_agg.loc[mid]
                p = prev_agg.loc[mid] if mid in prev_agg.index else None
                for key in MT_KEYS:
                    cv = None if pd.isna(c[key]) else float(c[key])
                    pv = None
                    if p is not None and not pd.isna(p[key]):
                        pv = float(p[key])
                    s['metrics'][key] = {
                        'cur': cv,
                        'prev': pv,
                        'delta': round(cv - pv, 4) if (cv is not None and pv is not None) else None
                    }

    # ---------- 3. 汇总表: 战区/区/督导 ----------
    wb2 = openpyxl.load_workbook(main, read_only=True, data_only=True)
    ws2 = wb2['汇总']
    hrows = list(ws2.iter_rows(min_row=4, values_only=True))
    wb2.close()

    region_summary, supervisor_summary = [], []
    for r in hrows:
        a, b = r[0], r[1]
        if a is None and b is None:
            continue
        m = {
            'mt_shop_score': {'cur': num(r[2]),  'prev': num(r[3]),  'delta': num(r[4])},
            'mt_score':      {'cur': num(r[5]),  'prev': num(r[6]),  'delta': num(r[7])},
            'mt_reply':      {'cur': num(r[8]),  'prev': num(r[9]),  'delta': num(r[10])},
            'sg_shop_score': {'cur': num(r[14]), 'prev': num(r[15]), 'delta': num(r[16])},
            'sg_score':      {'cur': num(r[17]), 'prev': num(r[18]), 'delta': num(r[19])},
            'sg_reply':      {'cur': num(r[20]), 'prev': num(r[21]), 'delta': num(r[22])},
            'sg_cancel':     {'cur': num(r[26]), 'prev': num(r[27]), 'delta': num(r[28])},
        }
        if b is None and a in ('华南战区', '华南一区', '华南二区'):
            region_summary.append({'name': a, 'metrics': m})
        elif b is not None:
            supervisor_summary.append({'name': b, 'region': a, 'metrics': m})

    # ---------- 4. 城市级聚合 (仅营业中) ----------
    city_map = defaultdict(list)
    for s in stores:
        if s['status'] == '营业中':
            city_map[(s['region'], s['city'])].append(s)

    city_summary = []
    for (reg, city), lst in city_map.items():
        agg = {'cur': {}, 'prev': {}, 'delta': {}}
        for mk in ALL_M:
            curs = [x['metrics'][mk]['cur'] for x in lst if x['metrics'][mk]['cur'] is not None]
            prevs = [x['metrics'][mk]['prev'] for x in lst if x['metrics'][mk]['prev'] is not None]
            agg['cur'][mk]   = round(sum(curs) / len(curs), 4) if curs else None
            agg['prev'][mk]  = round(sum(prevs) / len(prevs), 4) if prevs else None
            agg['delta'][mk] = round(agg['cur'][mk] - agg['prev'][mk], 4) \
                if (agg['cur'][mk] is not None and agg['prev'][mk] is not None) else None
        city_summary.append({'region': reg, 'city': city, 'storeCount': len(lst), 'metrics': agg})

    return {
        'meta': {
            'period': '%s ~ %s' % (period, period_end),
            'prevPeriod': '%s ~ %s' % (prev, prev_end),
            'dataSource': folder,
            'storeTotal': len(stores),
            'openTotal': sum(1 for s in stores if s['status'] == '营业中'),
            'mtMatched': matched
        },
        'region_summary': region_summary,
        'supervisor_summary': supervisor_summary,
        'city_summary': city_summary,
        'stores': stores
    }


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
            cache[folder] = json.load(open(os.path.join(CACHE_DIR, d), encoding='utf-8'))
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
    # 全量构建：逐期写缓存，再合并
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
