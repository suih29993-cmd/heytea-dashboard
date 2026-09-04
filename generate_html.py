# -*- coding: utf-8 -*-
"""生成喜茶华南区数据看板 HTML (M5) - 数据内联, 双击即用."""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DB = json.load(open(os.path.join(BASE, 'data.json'), encoding='utf-8'))
PERIODS = DB['periods']
ORDER = DB['_order']
DEFAULT = DB['defaultPeriod']
def _js(o):
    return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
periods_json = _js(PERIODS)
order_json = _js(ORDER)
default_json = _js(DEFAULT)

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>喜茶华南区运营数据看板</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NCA2NCI+PHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiByeD0iMTQiIGZpbGw9IiM0NTY4NEEiLz48dGV4dCB4PSIzMiIgeT0iNDQiIGZvbnQtZmFtaWx5PSJOb3RvIFNhbnMgU0MsUGluZ0ZhbmcgU0MsTWljcm9zb2Z0IFlhSGVpLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzQiIGZvbnQtd2VpZ2h0PSI2MDAiIGZpbGw9IiNGRkZGRkYiIHRleHQtYW5jaG9yPSJtaWRkbGUiPuWWnDwvdGV4dD48L3N2Zz4=">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+SC:wght@400;500;600&family=Noto+Serif+SC:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  /* ============ Design Tokens ============ */
  :root{
    --bg:#F9F8F6;          /* 暖白页面背景 */
    --card:#FFFFFF;        /* 卡片/容器背景 */
    --ink:#1A1A1A;         /* 主要文字：墨黑 */
    --sub:#6E6B66;         /* 次要文字：暖灰 */
    --line:#E8E6E1;        /* 边框/分割线 */
    --accent:#45684A;      /* 品牌墨绿（强调） */
    --good:#5E7E5A;        /* 改善：鼠尾草绿 */
    --bad:#BE554B;         /* 恶化：砖红 */
    --neu:#A3A09A;         /* 无变化 */
    --warn-bg:#F9EFEC;     /* 异常背景 */
    --th-bg:#F1F0EC;       /* 表头背景 */
    --font-sans:"Noto Sans SC","PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;
    --font-num:"Inter","Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
  }
  *{box-sizing:border-box}
  html{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
  body{margin:0;font-family:var(--font-sans);background:var(--bg);color:var(--ink);font-size:14px;line-height:1.5}

  /* ============ Header（暖白 + 文字导航） ============ */
  header{background:var(--bg);padding:24px 32px 0;display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:18px;border-bottom:1px solid var(--line);position:relative}
  header .brand{display:flex;gap:12px;align-items:center}
  header .brand .logo{height:56px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
  header .brand .logo svg{height:56px;width:auto;display:block}
  header .brand .titles{flex:1}
  header .brand h1{margin:0;font-family:"Noto Serif SC","Songti SC","STSong",serif;font-size:22px;font-weight:600;letter-spacing:.5px;color:var(--ink)}
  header .brand .meta{margin-top:4px;font-size:12.5px;color:var(--sub);font-family:var(--font-num)}
  header .brand .meta .dot{margin:0 10px;color:#D4D1C9}
  .tabs{display:flex;gap:28px;align-self:flex-end}
  .tabs button{background:none;border:none;color:#4F4B45;padding:0 0 10px;cursor:pointer;font-size:15px;font-weight:500;letter-spacing:.3px;position:relative;font-family:var(--font-sans)}
  .tabs button::after{content:'';position:absolute;left:0;right:0;bottom:-1px;height:2px;background:transparent;border-radius:1px;transition:background .2s}
  .tabs button:hover{color:var(--ink)}
  .tabs button.active{color:var(--accent);font-weight:600}
  .tabs button.active::after{background:var(--accent)}
  .periodbar{position:absolute;top:16px;right:30px;display:flex;align-items:center;gap:6px;z-index:5}
  .periodbar label{font-size:12px;color:var(--sub);white-space:nowrap}
  .periodbar select{min-width:150px;padding:4px 24px 4px 10px;font-size:12px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--ink)}

  main{padding:26px 32px 36px;max-width:1320px;margin:0 auto}
  .sec{display:none}
  .sec.active{display:block}
  h2{font-size:18px;margin:2px 0 16px;color:var(--ink);font-weight:600;letter-spacing:.3px;font-family:var(--font-sans)}
  h3{font-size:16px;margin:20px 0 10px;color:var(--ink);font-weight:600;font-family:var(--font-sans)}
  h3:first-child{margin-top:4px}

  /* ============ 卡片 / 面板 ============ */
  .region-block{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 22px;margin-bottom:18px;box-shadow:0 1px 3px rgba(23,23,23,.05)}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:0 1px 3px rgba(23,23,23,.05)}
  .panel-tight{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px;box-shadow:0 1px 3px rgba(23,23,23,.05)}
  .panel-tight table.tbl th,.panel-tight table.tbl td{padding:8px 12px}

  /* ============ 区域 Tab ============ */
  .region-tabs{display:flex;gap:26px;border-bottom:1px solid var(--line);margin-bottom:22px;flex-wrap:wrap}
  .region-tabs button{background:none;border:none;color:var(--sub);padding:0 0 12px;cursor:pointer;font-size:15px;font-weight:500;position:relative;font-family:var(--font-sans)}
  .region-tabs button::after{content:'';position:absolute;left:0;right:0;bottom:-1px;height:1px;background:transparent}
  .region-tabs button:hover{color:var(--ink)}
  .region-tabs button.active{color:var(--accent);font-weight:600}
  .region-tabs button.active::after{background:var(--accent)}

  /* ============ KPI 卡片 ============ */
  .kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:0;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(23,23,23,.05)}
  .kpi{padding:18px 20px;border-right:1px solid var(--line)}
  .kpi:last-child{border-right:none}
  .kpi-label{font-size:12.5px;color:#45423D;margin-bottom:12px;font-family:var(--font-sans);font-weight:500;letter-spacing:.2px}
  .kpi-val{font-size:32px;font-weight:600;line-height:1;font-family:var(--font-num);letter-spacing:-.5px;color:var(--ink);font-variant-numeric:tabular-nums}
  .kpi-delta{font-size:12px;margin-top:9px;font-family:var(--font-num);font-weight:500;font-variant-numeric:tabular-nums}
  .kpi.warn .kpi-val{background:var(--warn-bg);padding:2px 6px;border-radius:6px;display:inline-block;line-height:1.2}
  .good{color:var(--good);font-weight:600}
  .bad{color:var(--bad);font-weight:600}
  .neu{color:var(--neu)}

  /* ============ 筛选栏 ============ */
  .filters{display:flex;gap:12px;flex-wrap:nowrap;align-items:center;background:none;border:none;border-radius:0;padding:0 0 14px;margin-bottom:6px;box-shadow:none}
  .fitem{display:flex;align-items:center;gap:6px;flex:0 0 auto}
  .fitem label{font-size:12.5px;color:var(--sub);white-space:nowrap}
  .fitem .search-wrap{position:relative;display:inline-flex;align-items:center}
  .fitem .search-wrap input{padding-right:32px}
  .fitem .search-wrap .ic{position:absolute;right:10px;color:var(--sub);font-size:14px;pointer-events:none}
  select{padding:7px 30px 7px 12px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:13px;color:var(--ink);min-width:150px;font-family:var(--font-sans);cursor:pointer;appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6" viewBox="0 0 10 6"><path fill="%23A3A09A" d="M0 0l5 6 5-6z"/></svg>");background-repeat:no-repeat;background-position:right 12px center}
  .filters select{height:36px}
  input[type=text]{padding:6px 11px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:13px;color:var(--ink);font-family:var(--font-sans)}
  select:focus{outline:none;border-color:var(--accent)}
  .help{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;border-radius:50%;border:1.5px solid #C7C4BE;color:#8A8781;font-size:11px;font-weight:600;line-height:1;cursor:pointer;margin-left:3px;vertical-align:middle;font-family:var(--font-sans);background:#fff}
  .help:hover{border-color:var(--accent);color:var(--accent)}
  .help-tip{position:fixed;z-index:60;display:none;max-width:320px;width:max-content;background:#fff;border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 24px rgba(23,23,23,.12);padding:10px 12px;font-size:12px;line-height:1.6;color:var(--ink);white-space:normal}

  /* ============ 表格 ============ */
  table.tbl{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:13px}
  table.tbl th{background:var(--th-bg);color:var(--ink);text-align:left;padding:10px 12px;font-weight:600;border-bottom:1px solid var(--line);font-family:var(--font-sans)}
  table.tbl td{padding:10px 12px;border-bottom:1px solid var(--line);background:var(--card);color:var(--ink);font-family:var(--font-sans)}
  table.tbl td.num,table.tbl td .num{font-family:var(--font-num);font-variant-numeric:tabular-nums}
  table.tbl td b.num{font-family:var(--font-num)}
  table.tbl tr:last-child td{border-bottom:none}
  table.tbl tbody tr:hover{background:#FAF9F6}
  table.tbl tbody tr:hover td{background:#FAF9F6}
  .metric-name{font-weight:600;color:var(--ink);font-family:var(--font-sans)}
  /* 分组表头（美团/闪购）：浅灰底 + 细分割 */
  table.tbl th.group-mt{background:var(--th-bg);color:var(--ink);text-align:center;border-right:1px solid var(--line)}
  table.tbl th.group-sg{background:var(--th-bg);color:var(--ink);text-align:center}
  #supStoreTable .tbl th{text-align:center}
  .tbl th.mt-col{background:var(--th-bg);color:var(--ink);border-right:1px solid var(--line)}
  .tbl th.sg-col{background:var(--th-bg);color:var(--ink)}
  /* 异常：仅预警单元格使用浅红底；其余默认白底 */
  .tbl td.warn{background:var(--warn-bg) !important}
  .dtext{font-size:12px;font-weight:600;white-space:nowrap;font-family:var(--font-num);font-variant-numeric:tabular-nums}
  .sort-acc{color:var(--accent);font-weight:700}
  .rank-no{color:var(--accent);font-family:var(--font-num);font-weight:600;letter-spacing:.5px;font-variant-numeric:tabular-nums}
  .legend{font-size:12.5px;color:var(--sub);margin:10px 0 14px;line-height:1.7}
  .legend b.good{color:var(--good);font-weight:600} .legend b.bad{color:var(--bad);font-weight:600}
  .legend .neu{color:var(--neu)}

  footer{text-align:center;color:var(--sub);font-size:12px;padding:22px 0 30px;border-top:1px solid var(--line);margin-top:8px}
  .tag{display:inline-block;font-size:11px;padding:3px 9px;border-radius:6px;background:#F1F0EC;color:#4F4B45;margin-left:10px;font-weight:500;line-height:1.4;vertical-align:.5px}
  .mini{padding:5px 12px;font-size:12px;border:1px solid var(--line);background:#fff;border-radius:8px;cursor:pointer;color:var(--ink)}
  .mini:hover{background:#F1F0EC}

  /* ============ 树形多选器 ============ */
  .tree-dropdown{position:relative;display:inline-block}
  .tree-trigger{display:inline-flex;align-items:center;gap:8px;min-width:150px;justify-content:space-between;padding:7px 30px 7px 12px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:13px;cursor:pointer;color:var(--ink);background-image:url("data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6" viewBox="0 0 10 6"><path fill="%23A3A09A" d="M0 0l5 6 5-6z"/></svg>");background-repeat:no-repeat;background-position:right 12px center;appearance:none;-webkit-appearance:none}
  .tree-trigger:hover,.tree-trigger:focus{border-color:var(--accent)}
  .tree-trigger:hover{border-color:var(--accent)}
  .tree-panel{position:absolute;z-index:20;top:calc(100% + 6px);left:0;width:440px;max-width:94vw;background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 32px rgba(23,23,23,.10);padding:14px 16px;display:none}
  .tree-panel.open{display:block}
  .tree-search{width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:8px;font-size:13px;margin-bottom:10px;font-family:var(--font-sans)}
  .tree-hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
  .tree-count{font-size:12px;color:var(--sub)}
  .tree-box{max-height:min(78vh,720px);overflow:auto;border:1px solid var(--line);border-radius:8px;padding:8px 0;background:#fff}
  #b3cityBox,#v2cityBox,#metricBox{max-height:none}
  .tree-node{font-size:13px}
  .tree-row{display:flex;align-items:center;gap:4px;padding:4px 12px;cursor:pointer;user-select:none}
  .tree-row:hover{background:#F7F6F2}
  .tree-arrow{width:16px;height:16px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:var(--sub);flex-shrink:0}
  .tree-arrow::after{content:'▶';font-size:10px}
  .tree-arrow.open::after{content:'▼'}
  .tree-spacer{width:16px;flex-shrink:0}
  .tree-cb{width:14px;height:14px;margin:0 4px 0 0;cursor:pointer;flex-shrink:0;accent-color:var(--accent)}
  .tree-label{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:var(--font-sans)}
  .tree-match{background:#F3EFE5;border-radius:4px;padding:0 4px}
  .tree-children{display:block}
  .tree-group{font-size:11px;color:var(--sub);font-weight:600;padding:6px 12px 2px;letter-spacing:.5px}
  .metric-row.tree-sel{background:#F3F1EC;font-weight:600;color:var(--accent)}
  .metric-row.tree-sel::after{content:'✓';margin-left:auto;color:var(--accent);font-weight:700;padding-right:4px}
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="logo" aria-label="HEYTEA 喜茶"><svg class="brand-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1050 759" role="img" aria-label="HEYTEA 喜茶"><path fill="#171717" fill-rule="evenodd" d="M593 141.5L569 147.5L555 154.5L543 162.5L524.5 181L505.5 211L496.5 222L486 230.5L469 240.5L462.5 248L463.5 259L474.5 270L469.5 276L469.5 283L471.5 287L494.5 305L472 308.5L466.5 313L466.5 323L469.5 334L475.5 345L490 359.5L501 365.5L512 368.5L523 373.5L527.5 379L527.5 387L524.5 393L498 425.5L431.5 354L464.5 315L468.5 309L467.5 304L460 297.5L403 261.5L398 261.5L392.5 268L387.5 279L336.5 370L336.5 375L338.5 379L348 389.5L364 400.5L375 405.5L379 406.5L388 405.5L402 388.5L464.5 472L466.5 475L464.5 480L464.5 485L469 488.5L472 488.5L475.5 486L485.5 467L499.5 445L535 399.5L602 399.5L603.5 402L603.5 411L607.5 432L613.5 456L614.5 484L617 487.5L620 488.5L624 487.5L627.5 480L626.5 460L615.5 407L615.5 384L618.5 373L624.5 362L633 353.5L660 339.5L681 323.5L698.5 303L709.5 282L713.5 268L715.5 253L714.5 230L710.5 213L706.5 203L693.5 182L684 171.5L673 162.5L650 149.5L632 143.5L620 141.5ZM522 208.5L511.5 224L500 235.5L478 249.5L474.5 253L479 257.5L485 260.5L490.5 267L488.5 273L482.5 280L501 293.5L507.5 301L509.5 307L507.5 313L500 317.5L480 320.5L480.5 328L486.5 339L495 347.5L507 354.5L521 358.5L534 366.5L539.5 375L540.5 379L539.5 386L541 387.5L601 387.5L603.5 386L604.5 376L610.5 361L614.5 355L625.5 344L620.5 336L616.5 324L613.5 307L638 296.5L644.5 288L644.5 278L640 272.5L634 269.5L627 269.5L617 277.5L593 265.5L563 244.5ZM512 227.5L509.5 231L510.5 234L513 237.5L522 243.5L536 244.5L542.5 240L541 235.5L531 235.5L530 236.5L525 235.5L516 227.5ZM403 276.5L394.5 292L401.5 298L404.5 303L405.5 311L403.5 316L394.5 323L392.5 330L386.5 336L385.5 347L379.5 353L376.5 362L369 367.5L361 367.5L354 364.5L349.5 371L349.5 373L358 381.5L368 388.5L379 393.5L382 393.5L384.5 391L452.5 309L443 301.5ZM388 301.5L384.5 309L390 314.5L392 314.5L395.5 312L396.5 309L392 302.5ZM380 315.5L374.5 325L379 328.5L383 327.5L385.5 325L383.5 318ZM371 332.5L366.5 339L365.5 343L368 345.5L375 345.5L377.5 343L377.5 338ZM361 350.5L358.5 354L360 356.5L367 358.5L369.5 356L369 353.5ZM423 363.5L410.5 379L473 463.5L490.5 436ZM665 457.5L660 460.5L656.5 465L655.5 475L657.5 479L664 484.5L667 485.5L676 484.5L681.5 480L683.5 476L683.5 467L678 459.5L674 457.5ZM665 459.5L658.5 466L657.5 474L664 482.5L673 483.5L679.5 479L681.5 475L681.5 468L680.5 465L676 460.5ZM666 463.5L664.5 465L664.5 477L666.5 478L666.5 467L672 466.5L673.5 469L668.5 472L674 478.5L674.5 476L672.5 473L675.5 470L675.5 467L673 464.5ZM438 519.5L436.5 521L436.5 553L438 554.5L443 554.5L444.5 553L445 543.5L458 543.5L458.5 553L460 554.5L465 554.5L465.5 520L460 519.5L458.5 521L458 537.5L445 537.5L444.5 520ZM479 519.5L478.5 554L502 554.5L502 547.5L485.5 547L485.5 544L487 542.5L499.5 542L499 536.5L485.5 536L485.5 527L487 525.5L501 525.5L501.5 520ZM512 519.5L512.5 523L523.5 542L523.5 545L518.5 554L525 554.5L543.5 520L537 519.5L535.5 521L528 536.5L519.5 520ZM553 519.5L553 525.5L561 525.5L562.5 527L562.5 552L561.5 553L563 554.5L569 554.5L569.5 526L579 525.5L579.5 521L578 519.5ZM591 519.5L589.5 521L589.5 553L591 554.5L613 554.5L613 547.5L597.5 547L598 542.5L610.5 542L610 536.5L597.5 536L597.5 526L612 525.5L612.5 520ZM638 519.5L623.5 554L629 554.5L632 550.5L645 550.5L648 554.5L653 554.5L654.5 553L648.5 542L639.5 520ZM638 533.5L634.5 544L642 544.5L642.5 542L639.5 537L639.5 534ZM519 585.5L518 587.5L507 587.5L507 590.5L517 590.5L518.5 592L509 592.5L508.5 595L534.5 595L534 592.5L524.5 592L526 590.5L536 590.5L536 587.5L525 587.5L524 585.5ZM549 585.5L547 588.5L542.5 589L542.5 592L548 592.5L549 595.5L553 595.5L554 592.5L561 592.5L562 595.5L567 595.5L568 592.5L572.5 592L572.5 589L571 587.5L568 587.5L567 585.5L562 585.5L561 588.5L555 588.5L553 585.5ZM557 595.5L543 602.5L541.5 604L542.5 607L545 607.5L557 600.5L571 607.5L574.5 605L571 601.5ZM510 597.5L509.5 604L512.5 606L511 607.5L507 607.5L507 610.5L537.5 610L537 607.5L531.5 607L533.5 605L533 597.5ZM516 600.5L516 602.5L527.5 602L527 600.5ZM555 603.5L554 607.5L546 607.5L545.5 611L554 611.5L554.5 621L561 621.5L561.5 612L570 611.5L570.5 609L569 607.5L562 607.5L560 603.5ZM519 605.5L519 607.5L524.5 607L524 605.5ZM510 612.5L510 621.5L534.5 621L534 612.5ZM547 613.5L544.5 620L549 621.5L550.5 615ZM566 614.5L564.5 616L566.5 620L568 621.5L571 620.5L570.5 615ZM516 615.5L516 617.5L528.5 617L527 615.5Z"/></svg></div>
    <div class="titles">
      <h1>喜茶 · 华南区运营数据看板</h1>
      <div class="meta" id="hdrMeta"></div>
    </div>
  </div>
  <div class="tabs">
    <button data-v="v1" class="active">区域周报总览</button>
    <button data-v="v2">门店全景排名</button>
    <button data-v="v3">督导视图</button>
  </div>
  <div class="periodbar">
    <label>数据周期</label>
    <select id="periodSel"></select>
  </div>
</header>
<main>
  <!-- 视图1 -->
  <section class="sec active" id="v1">
    <h2>区域周报总览 <span class="tag">数据源：汇总表</span></h2>
    <div class="region-tabs" id="regionTabs"></div>
    <div id="regionCards"></div>
    <h3>各区 Bottom 3 门店（按核心指标末位）<span class="tag">数据源：门店底表</span></h3>
    <div class="filters">
      <div class="fitem"><label>区域</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="b3regionTrigger">全部区域</div>
          <div class="tree-panel" id="b3regionPanel">
            <div class="tree-hd">
              <div><b>区域（可多选）</b> <span class="tree-count" id="b3regionCount"></span></div>
              <div>
                <button type="button" class="mini" id="b3regionCheckAll">全选</button>
                <button type="button" class="mini" id="b3regionClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="b3regionBox"></div>
          </div>
        </div>
      </div>
      <div class="fitem"><label>城市</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="b3cityTrigger">全部城市</div>
          <div class="tree-panel" id="b3cityPanel">
            <div class="tree-hd">
              <div><b>城市（可多选）</b> <span class="tree-count" id="b3cityCount"></span></div>
              <div>
                <button type="button" class="mini" id="b3cityCheckAll">全选</button>
                <button type="button" class="mini" id="b3cityClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="b3cityBox"></div>
          </div>
        </div>
      </div>
    </div>
    <div class="panel panel-tight"><div id="bottom3"></div></div>
  </section>

  <!-- 视图2 -->
  <section class="sec" id="v2">
    <h2>门店全景排名 <span class="tag">数据源：门店底表 + 美团底表</span></h2>
    <div class="filters">
      <div class="fitem"><label>区域</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="v2regionTrigger">全部区域</div>
          <div class="tree-panel" id="v2regionPanel">
            <div class="tree-hd">
              <div><b>区域（可多选）</b> <span class="tree-count" id="v2regionCount"></span></div>
              <div>
                <button type="button" class="mini" id="v2regionCheckAll">全选</button>
                <button type="button" class="mini" id="v2regionClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="v2regionBox"></div>
          </div>
        </div>
      </div>
      <div class="fitem"><label>城市</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="v2cityTrigger">全部城市</div>
          <div class="tree-panel" id="v2cityPanel">
            <div class="tree-hd">
              <div><b>城市（可多选）</b> <span class="tree-count" id="v2cityCount"></span></div>
              <div>
                <button type="button" class="mini" id="v2cityCheckAll">全选</button>
                <button type="button" class="mini" id="v2cityClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="v2cityBox"></div>
          </div>
        </div>
      </div>
      <div class="fitem"><label>督导</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="v2supTrigger">全部督导</div>
          <div class="tree-panel" id="v2supPanel">
            <div class="tree-hd">
              <div><b>督导（可多选）</b> <span class="tree-count" id="v2supCount"></span></div>
              <div>
                <button type="button" class="mini" id="v2supCheckAll">全选</button>
                <button type="button" class="mini" id="v2supClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="v2supBox"></div>
          </div>
        </div>
      </div>
      <div class="fitem"><label>门店</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="treeTrigger"><span id="treeTriggerTxt">⌕ 请输入门店名称</span></div>
          <div class="tree-panel" id="treePanel">
            <div class="tree-hd">
              <div><b>门店筛选</b> <span class="tree-count" id="treeCount"></span></div>
              <div>
                <button type="button" class="mini" id="treeExpand">全部展开</button>
                <button type="button" class="mini" id="treeCollapse">全部折叠</button>
                <button type="button" class="mini" id="treeCheckAll">全选</button>
                <button type="button" class="mini" id="treeClear">清空</button>
              </div>
            </div>
            <input type="text" class="tree-search" id="treeSearch" placeholder="请输入门店、城市，回车搜索">
            <div class="tree-box" id="treeBox"></div>
          </div>
        </div>
      </div>
      <div class="fitem"><label>平台</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="v2platformTrigger">全部平台</div>
          <div class="tree-panel" id="v2platformPanel">
            <div class="tree-hd">
              <div><b>平台（可多选）</b> <span class="tree-count" id="v2platformCount"></span></div>
              <div>
                <button type="button" class="mini" id="v2platformCheckAll">全选</button>
                <button type="button" class="mini" id="v2platformClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="v2platformBox"></div>
          </div>
        </div>
      </div>
      <div class="fitem"><label>指标</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="metricTrigger"><span id="metricTriggerTxt">请选择指标</span></div>
          <div class="tree-panel" id="metricPanel">
            <div class="tree-hd">
              <div><b>指标（可多选）</b> <span class="tree-count" id="metricCount"></span></div>
              <div>
                <button type="button" class="mini" id="metricAll">全选</button>
                <button type="button" class="mini" id="metricClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="metricBox"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="legend">说明：评分 / 回复率 / 满意度类指标 <b class="good">越高越好</b>；商责取消率 <b class="good">越低越好</b>。仅统计「营业中」门店。差值 <b class="good">改善</b> / <b class="bad">恶化</b> / <span class="neu">无变化</span>。</div>
    <h3>Top 10 门店</h3>
    <div class="panel" id="top3"></div>
    <h3 style="margin-top:22px">Bottom 10 门店</h3>
    <div class="panel" id="bottom10"></div>
    <div class="panel" id="storeDetail" style="margin-top:18px;display:none"></div>
  </section>

  <!-- 视图3 -->
  <section class="sec" id="v3">
    <h2>督导视图 <span class="tag">数据源：汇总表 + 门店底表</span></h2>
    <div class="filters">
      <div class="fitem"><label>区域</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="v3regionTrigger">全部区域</div>
          <div class="tree-panel" id="v3regionPanel">
            <div class="tree-hd">
              <div><b>区域（可多选）</b> <span class="tree-count" id="v3regionCount"></span></div>
              <div>
                <button type="button" class="mini" id="v3regionCheckAll">全选</button>
                <button type="button" class="mini" id="v3regionClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="v3regionBox"></div>
          </div>
        </div>
      </div>
      <div class="fitem"><label>督导</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="v3supTrigger">全部督导</div>
          <div class="tree-panel" id="v3supPanel">
            <div class="tree-hd">
              <div><b>督导（可多选）</b> <span class="tree-count" id="v3supCount"></span></div>
              <div>
                <button type="button" class="mini" id="v3supCheckAll">全选</button>
                <button type="button" class="mini" id="v3supClear">清空</button>
              </div>
            </div>
            <div class="tree-box" id="v3supBox"></div>
          </div>
        </div>
      </div>
      <div class="fitem"><label>门店</label>
        <div class="tree-dropdown">
          <div class="tree-trigger" id="v3treeTrigger"><span id="v3treeTriggerTxt">⌕ 请输入门店名称</span></div>
          <div class="tree-panel" id="v3treePanel">
            <div class="tree-hd">
              <div><b>门店筛选</b> <span class="tree-count" id="v3treeCount"></span></div>
              <div>
                <button type="button" class="mini" id="v3treeExpand">全部展开</button>
                <button type="button" class="mini" id="v3treeCollapse">全部折叠</button>
                <button type="button" class="mini" id="v3treeCheckAll">全选</button>
                <button type="button" class="mini" id="v3treeClear">清空</button>
              </div>
            </div>
            <input type="text" class="tree-search" id="v3treeSearch" placeholder="请输入门店、城市，回车搜索">
            <div class="tree-box" id="v3treeBox"></div>
          </div>
        </div>
      </div>
    </div>
    <div class="legend">说明：评分 / 回复率 / 满意度类指标 <b class="good">越高越好</b>；商责取消率 <b class="good">越低越好</b>。仅统计「营业中」门店。差值 <b class="good">改善</b> / <b class="bad">恶化</b> / <span class="neu">无变化</span>。单元格 <span style="padding:1px 6px;border-radius:4px;background:#FBF1EF">浅红=未达标预警</span>。选择督导后可进一步勾选其下属门店查看明细。</div>
    <h3>督导表现</h3>
    <div class="panel" id="supTable"></div>
    <div class="panel" id="supStoreTable" style="margin-top:18px;display:none"></div>
  </section>
</main>
<footer id="ftr"></footer>

<script>
const PERIODS = __PERIODS__;
const PERIOD_ORDER = __ORDER__;
const DEFAULT_PERIOD = __DEFAULT__;
let DATA = PERIODS[DEFAULT_PERIOD];
let CUR_PERIOD = DEFAULT_PERIOD;
const savedPeriod = localStorage.getItem('heatea_period');
if (savedPeriod && PERIODS[savedPeriod]) { CUR_PERIOD = savedPeriod; DATA = PERIODS[savedPeriod]; }
const METRICS = {
  mt_shop_score:{name:'美团店铺分',ch:'美团',unit:'score100',dir:'high'},
  mt_score:{name:'美团商家评分',ch:'美团',unit:'score',dir:'high'},
  mt_reply:{name:'美团回复率',ch:'美团',unit:'pct',dir:'high'},
  mt_exp:{name:'综合体验分',ch:'美团',unit:'score',dir:'high'},
  mt_quality:{name:'商品质量分',ch:'美团',unit:'score',dir:'high'},
  mt_service:{name:'服务体验分',ch:'美团',unit:'score',dir:'high'},
  mt_prod_sat:{name:'商品满意度',ch:'美团',unit:'score',dir:'high'},
  mt_pack_sat:{name:'包装满意度',ch:'美团',unit:'score',dir:'high'},
  sg_shop_score:{name:'闪购店铺分',ch:'闪购',unit:'score100',dir:'high'},
  sg_score:{name:'闪购商家评分',ch:'闪购',unit:'score',dir:'high'},
  sg_reply:{name:'闪购回复率',ch:'闪购',unit:'pct',dir:'high'},
  sg_bad_reply:{name:'闪购差评回复率',ch:'闪购',unit:'pct',dir:'high'},
  sg_cancel:{name:'商责取消率',ch:'闪购',unit:'pct',dir:'low'},
};
const METRIC_HELP={
  mt_score:'美团外卖商家综合评分，由平台综合各维度表现得出，分数越高越好。',
  mt_exp:'综合体验分 = 商品质量分×80% + 服务体验分×20%',
  mt_quality:'商品质量分 =（商品满意度得分×30% + 包装满意度得分×10% + 复购率得分×20% + 食品安全负反馈率得分×20%）÷ 80%',
  mt_service:'服务体验分 =（消息回复率×10% + 服务负反馈率×10%）÷ 20%',
  mt_prod_sat:'近60天内所有计分评价中商品评分和口味评分的平均值，反映顾客对商家所售商品的满意程度。商品满意度 =（1×一星评价数 + 2×二星评价数 + 3×三星评价数 + 4×四星评价数 + 5×五星评价数）÷ 总评价数',
  mt_pack_sat:'近60天内所有计分评价中包装评分的平均值，反映顾客对商品包装的满意程度。包装满意度 =（1×一星评价数 + 2×二星评价数 + 3×三星评价数 + 4×四星评价数 + 5×五星评价数）÷ 总评价数'
};
const REGION_METRICS=['mt_score','mt_reply','sg_score','sg_reply','sg_cancel'];
const CORE5=['mt_score','mt_reply','sg_score','sg_reply','sg_cancel'];
const ALL_M=Object.keys(METRICS);
const V3_MT_ORDER=['mt_score','mt_exp','mt_quality','mt_service','mt_prod_sat','mt_pack_sat','mt_reply'];
const V3_SG_ORDER=['sg_score','sg_reply','sg_bad_reply','sg_cancel'];
const V3_MT_HEADERS=['商家评分','综合体验分','商品质量分','服务体验分','商品满意度','包装满意度','消息回复率'];
const V3_SG_HEADERS=['商家评分','消息回复率','差评回复率','商责取消率'];

const CITY_TO_PROV={
  '福州市':'福建省','厦门市':'福建省','泉州市':'福建省','漳州市':'福建省','莆田市':'福建省','三明市':'福建省','南平市':'福建省','龙岩市':'福建省','宁德市':'福建省',
  '南宁市':'广西壮族自治区','柳州市':'广西壮族自治区','桂林市':'广西壮族自治区','梧州市':'广西壮族自治区','北海市':'广西壮族自治区','防城港市':'广西壮族自治区','钦州市':'广西壮族自治区','贵港市':'广西壮族自治区','玉林市':'广西壮族自治区','百色市':'广西壮族自治区','贺州市':'广西壮族自治区','河池市':'广西壮族自治区','崇左市':'广西壮族自治区',
  '海口市':'海南省','三亚市':'海南省','儋州市':'海南省','万宁市':'海南省','东方市':'海南省','五指山市':'海南省','琼海市':'海南省','文昌市':'海南省','定安县':'海南省','屯昌县':'海南省','澄迈县':'海南省','临高县':'海南省','白沙黎族自治县':'海南省','昌江黎族自治县':'海南省','乐东黎族自治县':'海南省','陵水黎族自治县':'海南省','保亭黎族苗族自治县':'海南省','琼中黎族苗族自治县':'海南省'
};
const PROVINCE_ORDER=['福建省','广西壮族自治区','海南省'];

function fmt(mk,v){
  if(v===null||v===undefined) return '—';
  const u=METRICS[mk].unit;
  if(u==='pct') return (v*100).toFixed(2)+'%';
  if(u==='score') return v.toFixed(2);
  return v.toFixed(1);
}
function dclass(mk,d){
  if(d===null||d===undefined) return 'neu';
  if(d===0) return 'neu';
  const dir=METRICS[mk].dir;
  const imp=(d>0&&dir==='high')||(d<0&&dir==='low');
  return imp?'good':'bad';
}
function dtext(mk,d){
  if(d===null||d===undefined) return '<span class="neu dtext">— 0.00</span>';
  const cls=dclass(mk,d);
  const ar=d>0?'▲':(d<0?'▼':'—');
  const u=METRICS[mk].unit;
  const dv=u==='pct'?(Math.abs(d)*100).toFixed(2)+'%':Math.abs(d).toFixed(u==='score'?2:1);
  return '<span class="'+cls+' dtext">'+ar+' '+dv+'</span>';
}
function opt(v,t){return '<option value="'+v+'">'+t+'</option>';}
function helpIcon(mk){
  const t=METRIC_HELP[mk];
  if(!t) return '';
  return ' <span class="help" data-mk="'+mk+'" tabindex="0">?</span>';
}
const _tip=document.createElement('div');_tip.id='helpTip';_tip.className='help-tip';document.body.appendChild(_tip);
function _showHelp(h){
  const mk=h.getAttribute('data-mk');
  const txt=METRIC_HELP[mk];
  if(!txt) return;
  _tip.textContent=txt;
  _tip.style.display='block';
  const r=h.getBoundingClientRect();
  const tw=_tip.offsetWidth||320, th=_tip.offsetHeight||20;
  let left=r.left+r.width/2-tw/2;
  left=Math.max(8,Math.min(left,window.innerWidth-tw-8));
  let top=r.bottom+6;
  if(top+th>window.innerHeight-8) top=r.top-th-6;
  _tip.style.left=Math.round(left)+'px';
  _tip.style.top=Math.round(top)+'px';
}
function _hideHelp(){ _tip.style.display='none'; }
document.addEventListener('mouseover',function(e){const h=e.target.closest('.help'); if(h)_showHelp(h);});
document.addEventListener('mouseout',function(e){const h=e.target.closest('.help'); if(h&&!h.contains(e.relatedTarget))_hideHelp();});
document.addEventListener('click',function(e){const h=e.target.closest('.help'); if(h)_showHelp(h); else _hideHelp();});
// ---- 视图1 ----
let v1RegionIdx=0; // 当前选中的区域 Tab 下标（默认第一个=战区总览）
function kpiState(mk,cur,delta){
  // 返回 KPI 卡片的预警状态：'warn' 未达标 → 当前值以 #FBF1EF 浅红高亮；'great' / '' 一律白底
  // 异常优先：未达标（评分<4.5 / 回复率<0.9 / 商责取消率>0.003）
  if(mk==='mt_score'||mk==='sg_score'){ if(cur!==null&&cur<4.5) return 'warn'; }
  else if(mk==='mt_reply'||mk==='sg_reply'){ if(cur!==null&&cur<0.9) return 'warn'; }
  else if(mk==='sg_cancel'){ if(cur!==null&&cur>0.003) return 'warn'; }
  // 优秀：评分>=4.8 / 回复率>=0.98
  if((mk==='mt_score'||mk==='sg_score')&&cur!==null&&cur>=4.8) return 'great';
  if((mk==='mt_reply'||mk==='sg_reply')&&cur!==null&&cur>=0.98) return 'great';
  return '';
}
function renderRegion(){
  const tabs=document.getElementById('regionTabs');
  const wrap=document.getElementById('regionCards');
  const regs=DATA.region_summary;
  // Tab 槽位（仅 3 个有数据的区域）
  const allNames=["华南战区","华南一区","华南二区"];
  const dataIdxFor=n=>regs.findIndex(r=>r.name===n);
  if(v1RegionIdx>=allNames.length) v1RegionIdx=0;
  // 渲染 Tab
  tabs.innerHTML='';
  allNames.forEach((n,i)=>{
    const b=document.createElement('button');
    b.textContent=n;
    if(i===v1RegionIdx) b.classList.add('active');
    const di=dataIdxFor(n);
    if(di<0){ b.disabled=true; b.style.opacity='.35'; b.style.cursor='default'; }
    else { b.onclick=()=>{ v1RegionIdx=i; renderRegion(); }; }
    tabs.appendChild(b);
  });
  // 渲染当前区域 KPI（无数据则提示）
  const curName=allNames[v1RegionIdx];
  const curDataIdx=dataIdxFor(curName);
  if(curDataIdx<0){
    wrap.innerHTML='<div class="region-block"><div style="color:var(--sub);font-size:13px;padding:24px 0;text-align:center">'+curName+' 暂无数据</div></div>';
    return;
  }
  const r=regs[curDataIdx];
  let cards='';
  REGION_METRICS.forEach(mk=>{
    const mm=r.metrics[mk];
    const st=kpiState(mk,mm.cur,mm.delta);
      cards+='<div class="kpi'+(st?' '+st:'')+'"><div class="kpi-label">'+METRICS[mk].name+'</div>'+
      '<div class="kpi-val">'+fmt(mk,mm.cur)+'</div>'+
      '<div class="kpi-delta">'+dtext(mk,mm.delta)+'</div></div>';
  });
  wrap.innerHTML='<div class="kpi-grid">'+cards+'</div>';
}
function renderBottom3(){
  const regs=b3RegTree.getChecked();
  const cities=b3CityTree.getChecked();
  let html='<table class="tbl"><thead><tr><th>指标 (渠道)</th><th>Bottom 1</th><th>Bottom 2</th><th>Bottom 3</th></tr></thead><tbody>';
  CORE5.forEach(mk=>{
    let list=DATA.stores.filter(s=>s.status==='营业中'&&s.metrics[mk].cur!==null&&(regs.length===0||regs.includes(s.region))&&(cities.length===0||cities.includes(s.city)));
    const dir=METRICS[mk].dir;
    list.sort((a,b)=>dir==='high'?a.metrics[mk].cur-b.metrics[mk].cur:b.metrics[mk].cur-a.metrics[mk].cur);
    const b3=list.slice(0,3);
    const cells=b3.map(s=>'<td>'+s.name+'<br><b class="num">'+fmt(mk,s.metrics[mk].cur)+'</b></td>').join('');
    html+='<tr><td class="metric-name">'+METRICS[mk].name+'<span class="tag">'+METRICS[mk].ch+'</span></td>'+cells+'</tr>';
  });
  html+='</tbody></table>';
  document.getElementById('bottom3').innerHTML=html;
}

// ---- 视图2 ----
const PLATFORMS={'美团':['mt_score','mt_reply','mt_exp','mt_quality','mt_service','mt_prod_sat','mt_pack_sat'],
                 '闪购':['sg_score','sg_reply','sg_bad_reply','sg_cancel']};
const SUB5=['mt_exp','mt_quality','mt_service','mt_prod_sat','mt_pack_sat'];
// ---- 通用门店树形多选组件（视图2/视图3 复用）----
function makeStoreTree(cfg){
  // cfg: {box, count, trigTxt, panel, getAvailable, onChange}
  let treeData=[];
  const $=id=>document.getElementById(id);
  function updateNodeFromChildren(node){
    if(!node.children||node.children.length===0)return;
    const all=node.children.every(c=>c.checked&&!c.indeterminate);
    const some=node.children.some(c=>c.checked||c.indeterminate);
    node.checked=all; node.indeterminate=!all&&some;
  }
  function setNodeChecked(node,checked){node.checked=checked;node.indeterminate=false;if(node.children)node.children.forEach(c=>setNodeChecked(c,checked));}
  function propagateUp(node){if(!node.parent)return;updateNodeFromChildren(node.parent);propagateUp(node.parent);}
  function getCheckedStoreNames(){const set=new Set();(function walk(ns){ns.forEach(n=>{if(n.type==='store'&&n.checked)set.add(n.id);if(n.children)walk(n.children);});})(treeData);return [...set];}
  function findNode(id,nodes){for(const n of (nodes||treeData)){if(n.id===id)return n;if(n.children){const f=findNode(id,n.children);if(f)return f;}}return null;}
  function toggleNode(id){const n=findNode(id);if(n){n.expanded=!n.expanded;renderTree();}}
  function onNodeCheck(id,checked){const n=findNode(id);if(!n)return;setNodeChecked(n,checked);propagateUp(n);renderTree();if(cfg.onChange)cfg.onChange();}
  function renderNode(node,depth){
    const el=document.createElement('div');el.className='tree-node';
    const hasChildren=node.children&&node.children.length>0;
    const row=document.createElement('div');row.className='tree-row';row.style.paddingLeft=(depth*18+8)+'px';
    const arrow=document.createElement('span');
    if(hasChildren){arrow.className='tree-arrow'+(node.expanded?' open':'');arrow.onclick=(e)=>{e.stopPropagation();toggleNode(node.id);};}
    else{arrow.className='tree-spacer';}
    const cb=document.createElement('input');cb.type='checkbox';cb.className='tree-cb';cb.checked=node.checked;cb.indeterminate=node.indeterminate;
    cb.onchange=(e)=>{e.stopPropagation();onNodeCheck(node.id,e.target.checked);};
    const label=document.createElement('span');label.className='tree-label'+(node.match?' tree-match':'');label.textContent=node.label;
    row.appendChild(arrow);row.appendChild(cb);row.appendChild(label);
    row.onclick=(e)=>{if(e.target.tagName!=='INPUT'&&e.target.className.indexOf('tree-arrow')===-1){cb.click();}};
    el.appendChild(row);
    if(hasChildren&&node.expanded){const wrap=document.createElement('div');wrap.className='tree-children';node.children.forEach(c=>wrap.appendChild(renderNode(c,depth+1)));el.appendChild(wrap);}
    return el;
  }
  function updateTreeCount(){
    const total=cfg.getAvailable().length;
    const checked=getCheckedStoreNames().length;
    const cnt=$(cfg.count); if(cnt) cnt.textContent='已选 '+checked+' / '+total+' 家门店';
    const trig=$(cfg.trigTxt); if(trig) trig.textContent=checked===total?'⌕ 请输入门店名称':'⌕ 已选 '+checked+' 家门店';
  }
  function renderTree(){const box=$(cfg.box);box.innerHTML='';treeData.forEach(n=>box.appendChild(renderNode(n,0)));updateTreeCount();}
  function build(){
    const stores=cfg.getAvailable();
    const prev=getCheckedStoreNames();
    const map={};
    stores.forEach(s=>{
      const prov=CITY_TO_PROV[s.city]||'其他';
      if(!map[prov])map[prov]={type:'province',id:prov,label:prov,expanded:true,children:{},parent:null};
      if(!map[prov].children[s.city])map[prov].children[s.city]={type:'city',id:s.city,label:s.city,expanded:true,children:{},parent:map[prov]};
      map[prov].children[s.city].children[s.name]={type:'store',id:s.name,label:s.name,expanded:false,store:s,parent:map[prov].children[s.city]};
    });
    treeData=PROVINCE_ORDER.filter(p=>map[p]).concat(Object.keys(map).filter(p=>!PROVINCE_ORDER.includes(p)).sort()).map(prov=>{
      const pnode=map[prov];
      pnode.children=Object.keys(pnode.children).sort().map(city=>{const cnode=pnode.children[city];cnode.children=Object.keys(cnode.children).sort().map(name=>cnode.children[name]);return cnode;});
      return pnode;
    });
    const checkedSet=new Set(prev.filter(n=>stores.some(s=>s.name===n)));
    if(checkedSet.size===0&&stores.length>0)stores.forEach(s=>checkedSet.add(s.name));
    treeData.forEach(p=>{p.children.forEach(c=>{c.children.forEach(st=>{st.checked=checkedSet.has(st.id);});updateNodeFromChildren(c);});updateNodeFromChildren(p);});
  }
  function onSearch(q){
    const lower=q.trim().toLowerCase();
    function mark(ns){ns.forEach(n=>{let cm=false;if(n.children)cm=mark(n.children);n.match=lower!==''&&n.label.toLowerCase().includes(lower);if(cm)n.expanded=true;});return lower===''?false:ns.some(n=>n.match||(n.children&&n.children.some(c=>c.match||(c.children&&c.children.some(st=>st.match)))));}
    mark(treeData);
    if(lower!=='')treeData.forEach(p=>p.expanded=true);
    renderTree();
  }
  function toggle(){const p=$(cfg.panel);if(p)p.classList.toggle('open');}
  function expandAll(){function exp(ns){ns.forEach(n=>{if(n.type!=='store')n.expanded=true;if(n.children)exp(n.children);});}exp(treeData);renderTree();}
  function collapseAll(){function col(ns){ns.forEach(n=>{if(n.type!=='store')n.expanded=false;if(n.children)col(n.children);});}col(treeData);renderTree();}
  function checkAll(){treeData.forEach(p=>setNodeChecked(p,true));renderTree();if(cfg.onChange)cfg.onChange();}
  function clearAll(){treeData.forEach(p=>setNodeChecked(p,false));renderTree();if(cfg.onChange)cfg.onChange();}
  return {build,render:renderTree,getChecked:getCheckedStoreNames,toggle,onSearch,expandAll,collapseAll,checkAll,clearAll};
}
function makeCityTree(cfg){
  const $=id=>document.getElementById(id);
  let treeData=[];
  function getCities(){return cfg.getCities();}
  function recomputeProv(p){
    const all=p.children.length>0&&p.children.every(c=>c.checked);
    const some=p.children.some(c=>c.checked);
    p.indeterminate=some&&!all;
    p.checked=all;
  }
  function onNodeCheck(node,checked){
    if(node.kind==='province'){node.children.forEach(c=>c.checked=checked);}
    else{node.checked=checked;}
    treeData.forEach(recomputeProv);
    renderTree();
    if(cfg.onChange)cfg.onChange();
  }
  function renderNode(node,depth){
    const el=document.createElement('div');el.className='tree-node';
    const row=document.createElement('div');row.className='tree-row';row.style.paddingLeft=(depth*18+8)+'px';
    const arrow=document.createElement('span');
    if(node.kind==='province'){arrow.className='tree-arrow'+(node.expanded?' open':'');arrow.onclick=(e)=>{e.stopPropagation();node.expanded=!node.expanded;renderTree();};}
    else{arrow.className='tree-spacer';}
    const cb=document.createElement('input');cb.type='checkbox';cb.className='tree-cb';cb.checked=node.checked;cb.indeterminate=node.indeterminate;
    cb.onchange=(e)=>{e.stopPropagation();onNodeCheck(node,e.target.checked);};
    const label=document.createElement('span');label.className='tree-label';label.textContent=node.label;
    row.appendChild(arrow);row.appendChild(cb);row.appendChild(label);
    row.onclick=(e)=>{if(e.target.tagName!=='INPUT'&&e.target.className.indexOf('tree-arrow')===-1){cb.click();}};
    el.appendChild(row);
    if(node.kind==='province'&&node.expanded){
      const wrap=document.createElement('div');wrap.className='tree-children';
      node.children.forEach(c=>wrap.appendChild(renderNode(c,depth+1)));
      el.appendChild(wrap);
    }
    return el;
  }
  function updateCount(){
    const total=getCities().length;
    const checked=getChecked().length;
    const cnt=$(cfg.count); if(cnt) cnt.textContent='共 '+total+' 个城市';
    const trig=$(cfg.trigger); if(trig) trig.textContent=checked===0?'全部城市':('已选 '+checked+' 城');
  }
  function renderTree(){const box=$(cfg.box);box.innerHTML='';treeData.forEach(n=>box.appendChild(renderNode(n,0)));updateCount();}
  function rebuild(){
    const cities=getCities();
    const prevSet=new Set(getChecked());
    const map={};
    cities.forEach(c=>{
      const p=CITY_TO_PROV[c]||'其他';
      if(!map[p])map[p]={kind:'province',id:p,label:p,expanded:true,checked:false,indeterminate:false,children:[]};
      map[p].children.push({kind:'city',id:c,label:c,checked:prevSet.has(c)});
    });
    treeData=Object.keys(map).sort((a,b)=>{
      const ia=PROVINCE_ORDER.indexOf(a), ib=PROVINCE_ORDER.indexOf(b);
      return (ia<0?99:ia)-(ib<0?99:ib);
    }).map(p=>{
      map[p].children.sort((a,b)=>a.label.localeCompare(b.label));
      return map[p];
    });
    treeData.forEach(recomputeProv);
    renderTree();
  }
  function getChecked(){const out=[];treeData.forEach(p=>p.children.forEach(c=>{if(c.checked)out.push(c.id);}));return out;}
  function checkAll(){treeData.forEach(p=>onNodeCheck(p,true));}
  function clear(){treeData.forEach(p=>onNodeCheck(p,false));}
  function toggle(){const p=$(cfg.panel);if(p)p.classList.toggle('open');}
  return {rebuild,getChecked,clear,checkAll,toggle};
}
// ---- 通用平面多选下拉（区域/督导/平台）----
function makeCheckTree(cfg){
  const $=id=>document.getElementById(id);
  let options=[];
  let checkedSet=new Set();
  function renderOptions(){
    const box=$(cfg.box);
    box.innerHTML='';
    if(options.length===0){box.innerHTML='<div class="tree-empty">暂无可选项</div>';updateTrigger();return;}
    options.forEach(op=>{
      const row=document.createElement('div');row.className='tree-row';
      const cb=document.createElement('input');cb.type='checkbox';cb.className='tree-cb';cb.checked=checkedSet.has(op.value);
      cb.onchange=()=>{if(cb.checked)checkedSet.add(op.value);else checkedSet.delete(op.value);renderOptions();if(cfg.onChange)cfg.onChange();};
      const label=document.createElement('span');label.className='tree-label';label.textContent=op.label;
      row.appendChild(cb);row.appendChild(label);
      row.onclick=(e)=>{if(e.target.tagName!=='INPUT')cb.click();};
      box.appendChild(row);
    });
    updateTrigger();
  }
  function updateTrigger(){
    const n=checkedSet.size;
    const trig=$(cfg.trigger); if(trig) trig.textContent = n===0 ? cfg.allText : '已选 '+n+' 项';
    const cnt=$(cfg.count); if(cnt) cnt.textContent='共 '+options.length+' 项';
  }
  function rebuild(arr,checked){
    options=arr.map(x=>typeof x==='string'?{value:x,label:x}:{value:x.value,label:x.label});
    const valid=new Set(options.map(o=>o.value));
    if(checked!==undefined) checkedSet=new Set(checked.filter(v=>valid.has(v)));
    else checkedSet=new Set([...checkedSet].filter(v=>valid.has(v)));
    renderOptions();
  }
  function getChecked(){return [...checkedSet];}
  function checkAll(){options.forEach(o=>checkedSet.add(o.value));renderOptions();if(cfg.onChange)cfg.onChange();}
  function clear(){checkedSet.clear();renderOptions();if(cfg.onChange)cfg.onChange();}
  function toggle(){const p=$(cfg.panel);if(p)p.classList.toggle('open');}
  return {rebuild,getChecked,clear,checkAll,toggle};
}
const REGION_OPTS=[{value:'华南一区',label:'华南一区'},{value:'华南二区',label:'华南二区'}];
const PLATFORM_OPTS=[{value:'美团',label:'美团'},{value:'闪购',label:'闪购'}];
const b3RegTree=makeCheckTree({box:'b3regionBox',count:'b3regionCount',trigger:'b3regionTrigger',panel:'b3regionPanel',allText:'全部区域',onChange:()=>{b3CityTree.rebuild();renderBottom3();}});
const v2RegTree=makeCheckTree({box:'v2regionBox',count:'v2regionCount',trigger:'v2regionTrigger',panel:'v2regionPanel',allText:'全部区域',onChange:()=>{fillSups();v2CityTree.rebuild();v2Tree.build();v2Tree.render();renderStore();}});
const v2SupTree=makeCheckTree({box:'v2supBox',count:'v2supCount',trigger:'v2supTrigger',panel:'v2supPanel',allText:'全部督导',onChange:()=>{v2CityTree.rebuild();v2Tree.build();v2Tree.render();renderStore();}});
const v2PlatTree=makeCheckTree({box:'v2platformBox',count:'v2platformCount',trigger:'v2platformTrigger',panel:'v2platformPanel',allText:'全部平台',onChange:()=>{fillMetrics();renderStore();}});
const v3RegTree=makeCheckTree({box:'v3regionBox',count:'v3regionCount',trigger:'v3regionTrigger',panel:'v3regionPanel',allText:'全部区域',onChange:()=>{fillV3Sups();v3Tree.build();v3Tree.render();renderSup();}});
const v3SupTree=makeCheckTree({box:'v3supBox',count:'v3supCount',trigger:'v3supTrigger',panel:'v3supPanel',allText:'全部督导',onChange:()=>{v3Tree.build();v3Tree.render();renderSup();}});
const b3CityTree=makeCityTree({
  box:'b3cityBox',count:'b3cityCount',trigger:'b3cityTrigger',panel:'b3cityPanel',
  getCities:()=>{
    const regs=b3RegTree.getChecked();
    return [...new Set(DATA.stores.filter(s=>s.status==='营业中'&&(regs.length===0||regs.includes(s.region))).map(s=>s.city))].sort();
  },
  onChange:renderBottom3
});
const v2CityTree=makeCityTree({
  box:'v2cityBox',count:'v2cityCount',trigger:'v2cityTrigger',panel:'v2cityPanel',
  getCities:()=>{
    const regs=v2RegTree.getChecked();
    const sups=v2SupTree.getChecked();
    return [...new Set(DATA.stores.filter(s=>s.status==='营业中' && (regs.length===0||regs.includes(s.region)) && (sups.length===0||sups.includes(s.supervisor))).map(s=>s.city))].sort();
  },
  onChange:()=>{v2Tree.build(); v2Tree.render(); renderStore();}
});
function getV2AvailableStores(){
  const regs=v2RegTree.getChecked();
  const sups=v2SupTree.getChecked();
  const cities=v2CityTree.getChecked();
  return DATA.stores.filter(s=>s.status==='营业中' && (regs.length===0||regs.includes(s.region)) && (sups.length===0||sups.includes(s.supervisor)) && (cities.length===0||cities.includes(s.city)));
}
function getV3AvailableStores(){
  const regs=v3RegTree.getChecked();
  const sups=v3SupTree.getChecked();
  return DATA.stores.filter(s=>s.status==='营业中' && (regs.length===0||regs.includes(s.region)) && (sups.length===0||sups.includes(s.supervisor)));
}
const v2Tree=makeStoreTree({box:'treeBox',count:'treeCount',trigTxt:'treeTriggerTxt',panel:'treePanel',getAvailable:getV2AvailableStores,onChange:renderStore});
const v3Tree=makeStoreTree({box:'v3treeBox',count:'v3treeCount',trigTxt:'v3treeTriggerTxt',panel:'v3treePanel',getAvailable:getV3AvailableStores,onChange:renderSup});

function closeTreeOutside(e){
  const panels=document.querySelectorAll('.tree-panel.open');
  panels.forEach(p=>{
    const t=p.previousElementSibling;
    if(!p.contains(e.target) && !(t&&t.contains(e.target))) p.classList.remove('open');
  });
}
function closeTreePanelsExcept(keep){
  document.querySelectorAll('.tree-panel.open').forEach(p=>{if(p!==keep)p.classList.remove('open');});
}
function fillSups(){
  const regs=v2RegTree.getChecked();
  const sups=[...new Set(DATA.supervisor_summary.filter(s=>regs.length===0||regs.includes(s.region)).map(s=>s.name))].sort();
  v2SupTree.rebuild(sups.map(x=>({value:x,label:x})));
}
function getMetricPool(){
  const plats=v2PlatTree.getChecked();
  let pool;
  if(plats.length===0) pool=ALL_M.slice();
  else pool=[...new Set(plats.flatMap(p=>PLATFORMS[p]||[]))];
  return pool.filter(m=>m!=='mt_shop_score'); // 视图2 不展示美团店铺分
}
function metricGroups(pool){
  const groups=[];
  const mt=['mt_score','mt_reply'].filter(m=>pool.includes(m));
  if(mt.length){
    groups.push({label:'美团',items:mt.map(m=>[m,METRICS[m].name])});
  }
  const sg=['sg_score','sg_reply','sg_bad_reply','sg_cancel'].filter(m=>pool.includes(m));
  if(sg.length){
    groups.push({label:'闪购',items:sg.map(m=>[m,METRICS[m].name])});
  }
  return groups;
}
let v2SelMets=[];
let v2ShowSub=false; // 美团商家评分（综合）表头点击展开/收起 5 项二级指标
function fillMetrics(){
  const pool=getMetricPool();
  v2ShowSub=false; // 切换平台时收起明细
  // 保留仍属于当前平台 pool 的已选指标；若清空则默认选第一个
  v2SelMets=v2SelMets.filter(m=>pool.includes(m));
  if(v2SelMets.length===0 && pool.length) v2SelMets=[pool[0]];
  renderMetricBox();
  updateMetricTrigger();
}
function renderMetricBox(){
  const pool=getMetricPool();
  const groups=metricGroups(pool);
  const box=document.getElementById('metricBox');
  box.innerHTML='';
  groups.forEach(g=>{
    const gh=document.createElement('div');
    gh.className='tree-group';
    gh.textContent=g.label;
    box.appendChild(gh);
    g.items.forEach(([mk,name])=>{
      const row=document.createElement('div');
      row.className='tree-row metric-row'+(v2SelMets.includes(mk)?' tree-sel':'');
      const cb=document.createElement('input');
      cb.type='checkbox'; cb.className='tree-cb'; cb.checked=v2SelMets.includes(mk);
      cb.onchange=(e)=>{
        e.stopPropagation();
        v2ShowSub=false; // 重新选择指标时收起明细
        if(e.target.checked){ if(!v2SelMets.includes(mk)) v2SelMets.push(mk); }
        else { v2SelMets=v2SelMets.filter(x=>x!==mk); }
        // 按 pool 顺序保持选中顺序（首个=主排序指标）
        v2SelMets=v2SelMets.slice().sort((a,b)=>pool.indexOf(a)-pool.indexOf(b));
        if(v2SelMets.length===0){ v2SelMets=[mk]; cb.checked=true; } // 至少保留一项
        renderMetricBox(); updateMetricTrigger(); renderStore();
      };
      const label=document.createElement('span');
      label.className='tree-label'; label.textContent=name;
      row.appendChild(cb); row.appendChild(label);
      row.onclick=(e)=>{ if(e.target.tagName!=='INPUT') cb.click(); };
      box.appendChild(row);
    });
  });
}
function updateMetricTrigger(){
  const cnt=document.getElementById('metricCount');
  const txt=document.getElementById('metricTriggerTxt');
  cnt.textContent='已选 '+v2SelMets.length+' 项';
  if(v2SelMets.length===0){ txt.textContent='请选择指标'; return; }
  if(v2SelMets.length<=2){ txt.textContent=v2SelMets.map(m=>METRICS[m].name).join('、'); }
  else { txt.textContent=v2SelMets.length+' 项指标'; }
}
function getFiltered(mets){
  const regs=v2RegTree.getChecked();
  const sups=v2SupTree.getChecked();
  const cities=v2CityTree.getChecked();
  const checked=v2Tree.getChecked();
  return DATA.stores.filter(s=>
    s.status==='营业中' &&
    (regs.length===0||regs.includes(s.region)) &&
    (sups.length===0||sups.includes(s.supervisor)) &&
    (cities.length===0||cities.includes(s.city)) &&
    checked.includes(s.name) &&
    mets.every(m=>s.metrics[m].cur!==null)
  );
}
function rankBg(idx,n,isBottom){
  return 'transparent';
}
function rankRows(arr,mets,showSub,isBottom){
  const n=arr.length;
  const primary=mets[0];
  const canExpand=(primary==='mt_score');
  const subCols=showSub?SUB5.slice():[];
  // 表头：固定列 + 主指标 + [展开的5项二级指标紧邻其后] + 其余已选指标
  let h='<table class="tbl"><thead><tr><th>#</th><th>门店</th><th>城市</th><th>督导</th>';
  mets.forEach((m,mi)=>{
    let thAttr=''; let arrow='';
    if(mi===0 && canExpand){
      thAttr=' style="cursor:pointer" title="点击展开/收起 5 项明细指标" data-v2sub="toggle"';
      arrow=' <span class="sort-acc">'+(showSub?'▾':'▸')+'</span>';
    } else if(mi===0){
      arrow=' <span class="sort-acc">↓</span>';
    }
    h+='<th'+thAttr+'>'+METRICS[m].name+helpIcon(m)+arrow+'</th>';
    if(mi===0 && subCols.length){
      subCols.forEach(s=>h+='<th>'+METRICS[s].name+helpIcon(s)+'</th>');
    }
  });
  h+='</tr></thead><tbody>';
  // 数据行：固定列 + 主指标 + [展开的5项二级指标紧邻其后] + 其余已选指标
  arr.forEach((s,idx)=>{
    const rank=isBottom?(n-idx):(idx+1);
    h+='<tr><td class="rank-no">'+String(rank).padStart(2,'0')+'</td><td class="txt">'+s.name+'</td><td class="txt">'+s.city+'</td><td class="txt">'+s.supervisor+'</td>';
    mets.forEach((m,mi)=>{
      const cur=s.metrics[m].cur;
      const warn=isWarn(m,cur)?' class="warn"':'';
      h+='<td'+warn+'><b class="num">'+fmt(m,cur)+'</b><br>'+dtext(m,s.metrics[m].delta)+'</td>';
      if(mi===0 && subCols.length){
        subCols.forEach(su=>{const w=isWarn(su,s.metrics[su].cur)?' class="warn"':'';h+='<td'+w+'><span class="num">'+fmt(su,s.metrics[su].cur)+'</span></td>';});
      }
    });
    h+='</tr>';
  });
  return h+'</tbody></table>';
}
function v2ToggleSub(){ v2ShowSub=!v2ShowSub; renderStore(); }
function renderStoreDetail(name){
  const s=DATA.stores.find(x=>x.name===name);
  if(!s) return;
  let html='<h3>门店详情：'+name+'</h3>';
  html+='<p style="color:var(--sub);font-size:13px">区域：'+s.region+'　|　城市：'+s.city+'　|　督导：'+s.supervisor+'　|　类型：'+s.type+'</p>';
  html+='<table class="tbl"><thead><tr><th>指标</th><th>本期</th><th>环比</th><th>区域排名</th></tr></thead><tbody>';
  ALL_M.forEach(m=>{
    const mv=s.metrics[m].cur;
    const peers=DATA.stores.filter(x=>x.region===s.region&&x.status==='营业中'&&x.metrics[m].cur!==null);
    const dir=METRICS[m].dir;
    peers.sort((a,b)=>dir==='high'?b.metrics[m].cur-a.metrics[m].cur:a.metrics[m].cur-b.metrics[m].cur);
    const rank=peers.findIndex(x=>x.name===name)+1;
    const pct=(rank/peers.length*100).toFixed(0);
    html+='<tr><td>'+METRICS[m].name+'<span class="tag">'+METRICS[m].ch+'</span></td>'+
      '<td><b class="num">'+fmt(m,mv)+'</b></td><td>'+dtext(m,s.metrics[m].delta)+'</td>'+
      '<td>第 '+rank+' / '+peers.length+'（前 '+pct+'%）</td></tr>';
  });
  html+='</tbody></table>';
  document.getElementById('storeDetail').innerHTML=html;
  document.getElementById('storeDetail').style.display='block';
  document.getElementById('top3').innerHTML=''; document.getElementById('bottom10').innerHTML='';
}
function renderStore(){
  if(v2SelMets.length===0){
    const tip='<div style="color:var(--sub);padding:10px 0">请在「指标」下拉中至少勾选一个指标。</div>';
    document.getElementById('top3').innerHTML=tip;
    document.getElementById('bottom10').innerHTML='';
    document.getElementById('storeDetail').style.display='none';
    return;
  }
  const mk=v2SelMets[0];
  if(mk!=='mt_score') v2ShowSub=false;
  const filtered=getFiltered(v2SelMets);
  if(filtered.length===0){
    const tip='<div style="color:var(--sub);padding:10px 0">当前筛选条件下无匹配门店，请在左侧「门店筛选」树中至少勾选一家门店。</div>';
    document.getElementById('top3').innerHTML=tip;
    document.getElementById('bottom10').innerHTML='';
    document.getElementById('storeDetail').style.display='none';
    return;
  }
  document.getElementById('storeDetail').style.display='none';
  const dir=METRICS[mk].dir;
  const st=filtered.slice().sort((a,b)=>dir==='high'?b.metrics[mk].cur-a.metrics[mk].cur:a.metrics[mk].cur-b.metrics[mk].cur);
  const top=st.slice(0,10);
  const bottom=st.slice(-10).reverse();
  const showSub=(mk==='mt_score' && v2ShowSub);
  const hint=(mk==='mt_score')?'<div style="color:var(--sub);font-size:12px;margin-bottom:8px">提示：点击 Top/Bottom 表中「美团商家评分」表头可展开/收起 综合体验分、商品质量分、服务体验分、商品满意度、包装满意度 5 项明细。</div>':'';
  document.getElementById('top3').innerHTML=hint+rankRows(top,v2SelMets,showSub,false);
  document.getElementById('bottom10').innerHTML=rankRows(bottom,v2SelMets,showSub,true);
}

// ---- 视图3 ----
function fillV3Sups(){
  const regs=v3RegTree.getChecked();
  const sups=[...new Set(DATA.supervisor_summary.filter(s=>regs.length===0||regs.includes(s.region)).map(s=>s.name))].sort();
  v3SupTree.rebuild(sups.map(x=>({value:x,label:x})));
}
// 视图3 预警判定：按指标返回是否标红
// 注意：pct 类指标底层存的是小数（0.92=92%），阈值需用小数：90%=0.9、100%=1.0、0.3%=0.003
function isWarn(mk,cur){
  if(cur===null || cur===undefined) return false;
  if(mk==='mt_score'||mk==='sg_score') return cur<4.5;
  if(mk==='mt_exp'||mk==='mt_quality'||mk==='mt_service'||mk==='mt_prod_sat'||mk==='mt_pack_sat') return cur<4.5;
  if(mk==='mt_reply'||mk==='sg_reply') return cur<0.9;
  if(mk==='sg_bad_reply') return cur<1.0;
  if(mk==='sg_cancel') return cur>0.003;
  return false;
}

function renderSup(){
  const regs=v3RegTree.getChecked();
  const supsSel=v3SupTree.getChecked();
  let sups=DATA.supervisor_summary.filter(s=>(regs.length===0||regs.includes(s.region)) && (supsSel.length===0||supsSel.includes(s.name)));
  let html='<table class="tbl"><thead><tr><th>督导</th><th>区域</th>';
  REGION_METRICS.forEach(mk=>{const c=METRICS[mk].ch==='美团'?'mt-col':'sg-col';html+='<th class="'+c+'">'+METRICS[mk].name+helpIcon(mk)+'</th>';});
  html+='</tr></thead><tbody>';
  sups.forEach(s=>{
    html+='<tr><td class="txt"><b>'+s.name+'</b></td><td class="txt">'+s.region+'</td>';
    REGION_METRICS.forEach(mk=>{const mm=s.metrics[mk];const w=isWarn(mk,mm.cur)?' warn':'';html+='<td'+(w?' class="'+w.trim()+'"':'')+'><span class="num">'+fmt(mk,mm.cur)+'</span><br>'+dtext(mk,mm.delta)+'</td>';});
    html+='</tr>';
  });
  html+='</tbody></table>';
  document.getElementById('supTable').innerHTML=html;
  // 门店明细表（选中督导后展示其下属门店，受门店树筛选控制）
  const stPanel=document.getElementById('supStoreTable');
  if(supsSel.length===0){ stPanel.style.display='none'; stPanel.innerHTML=''; return; }
  const checked=v3Tree.getChecked();
  let stores=DATA.stores.filter(s=>supsSel.includes(s.supervisor) && s.status==='营业中' && checked.includes(s.name));
  if(stores.length===0){ stPanel.style.display='block'; stPanel.innerHTML='<div style="color:var(--sub);padding:10px 0">所选督导下未勾选门店，请在「门店」下拉中勾选</div>'; return; }
  let sh='<h3>'+supsSel.join('、')+' · 门店明细（'+stores.length+' 家）</h3><div style="overflow-x:auto"><table class="tbl"><thead>'+
    '<tr><th rowspan="2">门店</th><th colspan="'+V3_MT_ORDER.length+'" class="group-mt">美团</th><th colspan="'+V3_SG_ORDER.length+'" class="group-sg">闪购</th></tr>'+
    '<tr>';
  V3_MT_ORDER.forEach((mk,i)=>sh+='<th class="mt-col">'+V3_MT_HEADERS[i]+helpIcon(mk)+'</th>');
  V3_SG_ORDER.forEach((mk,i)=>sh+='<th class="sg-col">'+V3_SG_HEADERS[i]+helpIcon(mk)+'</th>');
  sh+='</tr></thead><tbody>';
  stores.forEach(s=>{
    sh+='<tr><td class="txt"><b>'+s.name+'</b></td>';
    V3_MT_ORDER.forEach(mk=>{const mm=s.metrics[mk];const w=isWarn(mk,mm.cur)?' warn':'';sh+='<td'+(w?' class="'+w.trim()+'"':'')+'><span class="num">'+fmt(mk,mm.cur)+'</span><br>'+dtext(mk,mm.delta)+'</td>';});
    V3_SG_ORDER.forEach(mk=>{const mm=s.metrics[mk];const w=isWarn(mk,mm.cur)?' warn':'';sh+='<td'+(w?' class="'+w.trim()+'"':'')+'><span class="num">'+fmt(mk,mm.cur)+'</span><br>'+dtext(mk,mm.delta)+'</td>';});
    sh+='</tr>';
  });
  sh+='</tbody></table></div>';
  stPanel.style.display='block';
  stPanel.innerHTML=sh;
}

// ---- init ----
function applyPeriod(){
  const p=document.getElementById('periodSel').value;
  if(!PERIODS[p]||p===CUR_PERIOD) return;
  DATA=PERIODS[p];
  CUR_PERIOD=p;
  try{localStorage.setItem('heatea_period',p);}catch(e){}
  document.getElementById('hdrMeta').innerHTML='数据周期：'+DATA.meta.period+'<span class="dot">|</span>上一周期：'+DATA.meta.prevPeriod+'<span class="dot">|</span>营业中门店：'+DATA.meta.openTotal+' 家';
  document.getElementById('ftr').textContent='数据源：'+(DATA.meta.dataSource||'本周数据')+'（汇总表 / 门店底表 / 美团数据底表）　·　实时模式：更新数据文件后页面自动刷新';
  b3RegTree.rebuild(REGION_OPTS,['华南一区']); b3CityTree.rebuild();
  v2RegTree.rebuild(REGION_OPTS,[]); v2PlatTree.rebuild(PLATFORM_OPTS,[]); v2SupTree.rebuild([],[]); fillSups(); v2CityTree.rebuild();
  v3RegTree.rebuild(REGION_OPTS,[]); v3SupTree.rebuild([],[]); fillV3Sups();
  fillMetrics();
  v1RegionIdx=0;
  renderRegion(); renderBottom3();
  v2Tree.build(); v2Tree.render(); renderStore();
  v3Tree.build(); v3Tree.render(); renderSup();
}

function init(){
  document.getElementById('hdrMeta').innerHTML='数据周期：'+DATA.meta.period+'<span class="dot">|</span>上一周期：'+DATA.meta.prevPeriod+'<span class="dot">|</span>营业中门店：'+DATA.meta.openTotal+' 家';
  document.getElementById('ftr').textContent='数据源：'+(DATA.meta.dataSource||'本周数据')+'（汇总表 / 门店底表 / 美团数据底表）　·　实时模式：更新数据文件后页面自动刷新';
  // 数据周期切换
  const periodSel=document.getElementById('periodSel');
  periodSel.innerHTML=PERIOD_ORDER.map(function(p){
    return opt(p, PERIODS[p].meta.period);
  }).join('');
  periodSel.value=CUR_PERIOD;
  periodSel.onchange=applyPeriod;
  // tabs
  document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{
    document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.sec').forEach(x=>x.classList.remove('active'));
    b.classList.add('active'); document.getElementById(b.dataset.v).classList.add('active');
  });
  // 视图1 区域 / 城市 多选
  b3RegTree.rebuild(REGION_OPTS,['华南一区']);
  b3CityTree.rebuild();
  document.getElementById('b3regionTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('b3regionPanel'));b3RegTree.toggle();};
  document.getElementById('b3regionCheckAll').onclick=()=>b3RegTree.checkAll();
  document.getElementById('b3regionClear').onclick=()=>b3RegTree.clear();
  const b3rp=document.getElementById('b3regionPanel'); if(b3rp) b3rp.onclick=(e)=>e.stopPropagation();
  document.getElementById('b3cityTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('b3cityPanel'));b3CityTree.toggle();};
  document.getElementById('b3cityCheckAll').onclick=()=>b3CityTree.checkAll();
  document.getElementById('b3cityClear').onclick=()=>b3CityTree.clear();
  const b3cp=document.getElementById('b3cityPanel'); if(b3cp) b3cp.onclick=(e)=>e.stopPropagation();
  // 视图2 区域 / 督导 / 平台 / 城市 多选
  v2RegTree.rebuild(REGION_OPTS,[]);
  v2PlatTree.rebuild(PLATFORM_OPTS,[]);
  v2SupTree.rebuild([],[]);
  fillSups();
  v2CityTree.rebuild();
  document.getElementById('v2regionTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('v2regionPanel'));v2RegTree.toggle();};
  document.getElementById('v2regionCheckAll').onclick=()=>v2RegTree.checkAll();
  document.getElementById('v2regionClear').onclick=()=>v2RegTree.clear();
  const v2rp=document.getElementById('v2regionPanel'); if(v2rp) v2rp.onclick=(e)=>e.stopPropagation();
  document.getElementById('v2supTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('v2supPanel'));v2SupTree.toggle();};
  document.getElementById('v2supCheckAll').onclick=()=>v2SupTree.checkAll();
  document.getElementById('v2supClear').onclick=()=>v2SupTree.clear();
  const v2sp=document.getElementById('v2supPanel'); if(v2sp) v2sp.onclick=(e)=>e.stopPropagation();
  document.getElementById('v2platformTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('v2platformPanel'));v2PlatTree.toggle();};
  document.getElementById('v2platformCheckAll').onclick=()=>v2PlatTree.checkAll();
  document.getElementById('v2platformClear').onclick=()=>v2PlatTree.clear();
  const v2pp=document.getElementById('v2platformPanel'); if(v2pp) v2pp.onclick=(e)=>e.stopPropagation();
  document.getElementById('v2cityTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('v2cityPanel'));v2CityTree.toggle();};
  document.getElementById('v2cityCheckAll').onclick=()=>v2CityTree.checkAll();
  document.getElementById('v2cityClear').onclick=()=>v2CityTree.clear();
  const v2cp=document.getElementById('v2cityPanel'); if(v2cp) v2cp.onclick=(e)=>e.stopPropagation();
  // 视图2 指标多选面板
  document.getElementById('metricTrigger').onclick=(e)=>{e.stopPropagation();
    const mp=document.getElementById('metricPanel');
    closeTreePanelsExcept(mp);
    mp.classList.toggle('open');
  };
  const metricPanel=document.getElementById('metricPanel');
  if(metricPanel) metricPanel.onclick=(e)=>e.stopPropagation();
  document.getElementById('metricAll').onclick=()=>{
    const pool=getMetricPool();
    v2ShowSub=false;
    v2SelMets=pool.slice().sort((a,b)=>pool.indexOf(a)-pool.indexOf(b));
    renderMetricBox(); updateMetricTrigger(); renderStore();
  };
  document.getElementById('metricClear').onclick=()=>{
    v2ShowSub=false;
    v2SelMets=[];
    renderMetricBox(); updateMetricTrigger(); renderStore();
  };
  // 视图2 门店树
  document.getElementById('treeSearch').oninput=(e)=>v2Tree.onSearch(e.target.value);
  document.getElementById('treeExpand').onclick=()=>v2Tree.expandAll();
  document.getElementById('treeCollapse').onclick=()=>v2Tree.collapseAll();
  document.getElementById('treeCheckAll').onclick=()=>v2Tree.checkAll();
  document.getElementById('treeClear').onclick=()=>v2Tree.clearAll();
  document.getElementById('treeTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('treePanel'));v2Tree.toggle();};
  const tp=document.getElementById('treePanel'); if(tp) tp.onclick=(e)=>e.stopPropagation();
  if(document.addEventListener) document.addEventListener('click', closeTreeOutside);
  // 视图2 表头点击展开/收起二级指标（事件委托，兼容动态表格）
  document.addEventListener('click', function(e){
    const th=e.target.closest('th[data-v2sub="toggle"]');
    if(th) v2ToggleSub();
  });
  // 视图3
  v3RegTree.rebuild(REGION_OPTS,[]);
  v3SupTree.rebuild([],[]);
  fillV3Sups();
  document.getElementById('v3regionTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('v3regionPanel'));v3RegTree.toggle();};
  document.getElementById('v3regionCheckAll').onclick=()=>v3RegTree.checkAll();
  document.getElementById('v3regionClear').onclick=()=>v3RegTree.clear();
  const v3rp=document.getElementById('v3regionPanel'); if(v3rp) v3rp.onclick=(e)=>e.stopPropagation();
  document.getElementById('v3supTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('v3supPanel'));v3SupTree.toggle();};
  document.getElementById('v3supCheckAll').onclick=()=>v3SupTree.checkAll();
  document.getElementById('v3supClear').onclick=()=>v3SupTree.clear();
  const v3sp=document.getElementById('v3supPanel'); if(v3sp) v3sp.onclick=(e)=>e.stopPropagation();
  document.getElementById('v3treeSearch').oninput=(e)=>v3Tree.onSearch(e.target.value);
  document.getElementById('v3treeExpand').onclick=()=>v3Tree.expandAll();
  document.getElementById('v3treeCollapse').onclick=()=>v3Tree.collapseAll();
  document.getElementById('v3treeCheckAll').onclick=()=>v3Tree.checkAll();
  document.getElementById('v3treeClear').onclick=()=>v3Tree.clearAll();
  document.getElementById('v3treeTrigger').onclick=(e)=>{e.stopPropagation();closeTreePanelsExcept(document.getElementById('v3treePanel'));v3Tree.toggle();};
  const v3tp=document.getElementById('v3treePanel'); if(v3tp) v3tp.onclick=(e)=>e.stopPropagation();
  // first render
  renderRegion(); renderBottom3(); fillSups(); fillMetrics(); v2Tree.build(); v2Tree.render(); renderStore(); fillV3Sups(); v3Tree.build(); v3Tree.render(); renderSup();
}
init();
</script>
<script>
// ---- 本地实时自动刷新（仅 localhost 服务时生效）----
(function(){
  if(!(location.hostname==='localhost'||location.hostname==='127.0.0.1'))return;
  var lastV=null;
  function loop(){
    fetch('/__reload__?v='+(lastV==null?0:lastV),{cache:'no-store'}).then(function(r){
      return r.ok?r.json():null;
    }).then(function(d){
      if(d){
        if(lastV===null){lastV=d.v;}
        else if(d.v>lastV){location.reload();return;}
      }
      setTimeout(loop,1500);
    }).catch(function(){setTimeout(loop,1500);});
  }
  setTimeout(loop,1500);
})();
</script>
</body>
</html>'''

out = HTML.replace('__PERIODS__', periods_json).replace('__ORDER__', order_json).replace('__DEFAULT__', default_json)
with open(os.path.join(BASE, 'dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(out)
print('dashboard.html written, %d bytes' % len(out))
