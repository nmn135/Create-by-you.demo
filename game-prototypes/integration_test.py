# -*- coding: utf-8 -*-
"""封印之殿 端到端冒烟测试——模拟玩家完整流程"""
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error


def api(path, method='GET', body=None):
    # /api/chat 在 AI 模式下可能耗时较长（意图解析 Pro + 回复 Flash）
    timeout = 45 if path == '/api/chat' else 8
    req = urllib.request.Request('http://localhost:8080' + path, method=method)
    if body is not None:
        req.data = json.dumps(body).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'HTTP_ERROR': e.code, 'body': e.read().decode('utf-8')[:300]}
    except Exception as e:
        return {'ERROR': str(e)}


def main():
    # --no-ai：强制关键词回退 + 模拟回复，保证端到端行为确定性
    #（AI 意图解析有随机性，且 API 不可用时每次 chat 会挂起 30s+，不宜作为冒烟测试的依赖）
    proc = subprocess.Popen(
        [sys.executable, '-X', 'utf8', 'server.py', '--no-ai'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=r'D:\Create by you.demo\game-prototypes')
    time.sleep(3.5)

    fails = []
    def check(name, cond, extra=''):
        status = 'OK' if cond else 'FAIL'
        print('[%s] %s %s' % (status, name, extra))
        if not cond:
            fails.append(name)

    try:
        # 1. 重置
        r = api('/api/reset', 'POST', {})
        check('重置', r.get('message') == '游戏已重置', str(r)[:80])

        # 2. 推进 4 次，全员入场
        expected = ['rog', 'baruk', 'liana', 'margaret']
        for i, npc in enumerate(expected):
            ad = api('/api/advance', 'POST', {'phase': i})
            check('推进%d %s入场' % (i + 1, npc), ad.get('new_npc') == npc,
                  'got %s, npc_name=%s' % (ad.get('new_npc'), ad.get('npc_name')))
            if ad.get('new_npc') != npc:
                return

        # 3. 全员入场后再次推进 → 应提示已全部到场
        ad = api('/api/advance', 'POST', {'phase': 4})
        check('全员后推进', ad.get('new_npc') is None and ad.get('message') == '所有角色已到场',
              str(ad)[:100])

        # 4. 与每个人对话（公共模式，前端格式 message+target，验证显式目标解析）
        for npc, expect_name in [('rog', '罗格'), ('baruk', '巴鲁克'), ('liana', '莉安娜'), ('margaret', '玛格丽特')]:
            r = api('/api/chat', 'POST', {
                'message': '你最近还好吗', 'mode': 'public', 'target': npc, 'phase': 4})
            got_name = r.get('npc_name', '')
            check('对话 %s 有回复且目标正确' % npc,
                  bool(r.get('reply')) and expect_name in got_name,
                  'reply=%r npc_name=%s' % (r.get('reply', '')[:18], got_name))

        # 5. 悄悄话模式（前端格式 target=whisper目标）
        r = api('/api/chat', 'POST', {
            'message': '我想跟你做个交易，告诉你关于罗格的秘密', 'mode': 'whisper', 'target': 'baruk'})
        check('悄悄话可发', 'HTTP_ERROR' not in r and 'ERROR' not in r, str(r)[:120])

        # 6. 全状态检查（此时应为 stage4 全员在场）
        st = api('/api/state')
        check('state.npcs 5个', len(st.get('npcs', {})) >= 4, 'keys=%s' % list(st.get('npcs', {}).keys()))
        check('state.game.present_npcs=4', len(st.get('game', {}).get('present_npcs', [])) == 4)

        # 7. 中间阶段（stage1，只有罗格）连续无新信息 → pacing_hint 应出现
        api('/api/reset', 'POST', {})
        api('/api/advance', 'POST', {'phase': 0})  # 罗格入场
        api('/api/chat', 'POST', {'message': '你是谁', 'mode': 'public', 'target': 'rog'})
        r = api('/api/chat', 'POST', {'message': '没别的事了吗', 'mode': 'public', 'target': 'rog'})
        check('节奏提示出现', bool(r.get('pacing_hint')), 'hint=%r' % (r.get('pacing_hint') or '')[:50])

        # 8. 重置后再查 /api/state（只有罗格）
        st2 = api('/api/state')
        check('重置后 stage=1', st2.get('game', {}).get('current_stage') == 1)

        # 9. /api/memories
        mem = api('/api/memories')
        check('memories.present_npcs', 'present_npcs' in mem, str(mem)[:100])
    finally:
        proc.terminate()
        proc.wait()

    print('=' * 50)
    if fails:
        print('失败 %d 项: %s' % (len(fails), fails))
        sys.exit(1)
    print('全部通过 ✅')


if __name__ == '__main__':
    main()
