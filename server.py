# -*- coding: utf-8 -*-
"""喜茶华南区数据看板 - 本地实时服务（增量重建）

用法:
    python server.py                 # 默认 http://127.0.0.1:8000，自动打开浏览器
    python server.py --port 8080     # 换个端口
    python server.py --no-open       # 不自动打开浏览器

数据源:
    把新的“双周基础数据MMDD-MMDD”文件夹放进“每周数据看板”目录即可。
    服务会跟踪每期数据的变化，只重建“变动的那几期”，再合并页面并自动刷新。
"""
import os, re, sys, json, time, threading, subprocess, webbrowser, hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = {'v': 0, 'lock': threading.Lock()}
WATCH_INTERVAL = 2.0
BUILD_LOCK = threading.Lock()
_FOLDER_RE = re.compile(r'^双周基础数据(\d{2})(\d{2})-(\d{2})(\d{2})$')


def _run(script, *args):
    py = sys.executable
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    subprocess.run([py, os.path.join(BASE, script)] + list(args), cwd=BASE, env=env, check=True)


def _code_sig():
    """build_data.py / generate_html.py 的修改指纹，脚本本身变了就全量重构建。"""
    items = []
    for f in ('build_data.py', 'generate_html.py'):
        p = os.path.join(BASE, f)
        if os.path.exists(p):
            st = os.stat(p)
            items.append('%s:%d:%d' % (f, st.st_mtime_ns, st.st_size))
    return hashlib.sha1(','.join(items).encode('utf-8')).hexdigest()


def _period_folders():
    return [d for d in sorted(os.listdir(BASE))
            if _FOLDER_RE.match(d) and os.path.isdir(os.path.join(BASE, d))]


def _folder_sig(folder):
    """单个数据期文件夹里所有 .xlsx 的修改指纹。"""
    items = []
    dp = os.path.join(BASE, folder)
    for root, _, files in os.walk(dp):
        for fn in files:
            if fn.startswith('~$') or not fn.lower().endswith('.xlsx'):
                continue
            p = os.path.join(root, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            items.append('%s:%d:%d' % (fn, st.st_mtime_ns, st.st_size))
    return hashlib.sha1(','.join(items).encode('utf-8')).hexdigest()


def _build_full():
    _run('build_data.py')
    _run('generate_html.py')


def _bump():
    with STATE['lock']:
        STATE['v'] += 1
    print('看板已更新（版本 v%d）' % STATE['v'], flush=True)


def _initial_build():
    try:
        if not BUILD_LOCK.acquire(blocking=False):
            return
        try:
            _build_full()
            _bump()
        finally:
            BUILD_LOCK.release()
    except Exception as e:
        print('首次构建失败：%s' % e, flush=True)


def _watch():
    folders = _period_folders()
    prev_sigs = {f: _folder_sig(f) for f in folders}
    prev_code = _code_sig()
    fails = {}
    while True:
        time.sleep(WATCH_INTERVAL)
        try:
            cur_folders = _period_folders()
            code = _code_sig()
            if code != prev_code:
                print('检测到脚本变化，全量重构建…', flush=True)
                if not BUILD_LOCK.acquire(blocking=False):
                    continue
                try:
                    _build_full()
                    prev_code = code
                    prev_sigs = {f: _folder_sig(f) for f in cur_folders}
                    fails = {}
                    _bump()
                finally:
                    BUILD_LOCK.release()
                continue

            changed = []
            for f in cur_folders:
                sig = _folder_sig(f)
                if f not in prev_sigs or prev_sigs[f] != sig:
                    changed.append(f)
            removed = [f for f in prev_sigs if f not in cur_folders]
            if not changed and not removed:
                prev_sigs = {f: prev_sigs.get(f) or _folder_sig(f) for f in cur_folders}
                continue

            if not BUILD_LOCK.acquire(blocking=False):
                continue
            try:
                built = []
                for f in changed:
                    try:
                        _run('build_data.py', '--folder', f)
                        prev_sigs[f] = _folder_sig(f)
                        fails[f] = 0
                        built.append(f)
                    except Exception as e:
                        fails[f] = fails.get(f, 0) + 1
                        print('构建 %s 失败：%s（将重试）' % (f, e), flush=True)
                        if fails[f] >= 6:
                            prev_sigs[f] = _folder_sig(f)
                            fails[f] = 0
                for f in removed:
                    c = os.path.join(BASE, '_data_cache', f + '.json')
                    if os.path.exists(c):
                        try:
                            os.remove(c)
                        except OSError:
                            pass
                    prev_sigs.pop(f, None)
                    fails.pop(f, None)
                if built or removed:
                    _run('build_data.py', '--merge')
                    _run('generate_html.py')
                    _bump()
            finally:
                BUILD_LOCK.release()
        except Exception as e:
            print('检测异常：%s' % e, flush=True)


class Handler(BaseHTTPRequestHandler):
    def _send_file(self, rel, ctype):
        fp = os.path.join(BASE, rel)
        try:
            with open(fp, 'rb') as f:
                data = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text):
        body = ('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" '
                'content="1"><body style="font-family:sans-serif;padding:40px">%s</body>' % text).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _guess_type(self, rel):
        import mimetypes
        t, _ = mimetypes.guess_type(rel)
        if t is None:
            return 'application/octet-stream'
        if t.startswith('text/') or t in ('application/javascript', 'application/json'):
            return t + '; charset=utf-8'
        return t

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/') or '/'
        if path == '/__reload__':
            qs = parse_qs(parsed.query)
            try:
                client_v = int(qs.get('v', ['0'])[0])
            except ValueError:
                client_v = 0
            with STATE['lock']:
                v = STATE['v']
            self._json({'v': v, 'changed': v > client_v})
            return
        if path in ('/', '/index.html', '/dashboard.html'):
            fp = os.path.join(BASE, 'dashboard.html')
            if os.path.exists(fp):
                self._send_file('dashboard.html', 'text/html; charset=utf-8')
            else:
                self._html('看板正在生成，请稍候…（会自动刷新）')
            return
        if path == '/data.json':
            self._send_file('data.json', 'application/json; charset=utf-8')
            return
        if path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        rel = path.lstrip('/').replace('/', os.sep)
        if rel and os.path.isfile(os.path.join(BASE, rel)):
            self._send_file(rel, self._guess_type(rel))
            return
        self.send_error(404, 'Not Found')

    def log_message(self, fmt, *args):
        pass


def main():
    port = 8000
    open_browser = True
    args = sys.argv[1:]
    if '--port' in args and args.index('--port') + 1 < len(args):
        port = int(args[args.index('--port') + 1])
    if '--no-open' in args:
        open_browser = False

    threading.Thread(target=_initial_build, daemon=True).start()
    threading.Thread(target=_watch, daemon=True).start()

    url = 'http://127.0.0.1:%d' % port
    print('看板已启动：%s' % url, flush=True)
    print('数据源：把新的 双周基础数据MMDD-MMDD 文件夹放进「每周数据看板」目录，页面会自动切换并刷新。', flush=True)
    print('按 Ctrl+C 停止服务。', flush=True)
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    except OSError as e:
        print('启动失败：%s（端口 %d 可能被占用，请改用 --port 指定其它端口）' % (e, port), flush=True)
        return
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止。', flush=True)
        server.server_close()


if __name__ == '__main__':
    main()
