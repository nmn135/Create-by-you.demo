// ============================================================
// src/ui_drag.js — UI 面板可拖动框架
// ============================================================
// 功能：
//   1. 指定面板可拖动（pointer 事件，排除按钮/输入等交互元素）
//   2. 位置持久化到 localStorage（刷新后保持）
//   3. 「调整布局 / 固定布局」切换（固定后不可拖）
//   4. 「重置布局」恢复默认
// 自包含 DOM + 样式；无第三方依赖。
// ============================================================

export function initDraggableUI(selectors) {
  const LS_POS = 'ui_drag_pos_';
  const LS_LOCK = 'ui_drag_locked';

  // --- 注入样式 ---
  const style = document.createElement('style');
  style.textContent = `
    #ui-layout-controls {
      position: fixed; right: 12px; bottom: 12px; z-index: 6000;
      display: flex; gap: 8px; padding: 6px 10px;
      background: rgba(10, 14, 20, 0.85); border: 1px solid rgba(92, 200, 216, 0.35);
      border-radius: 8px; font-size: 12px;
    }
    #ui-layout-controls button {
      padding: 4px 12px; border-radius: 6px; cursor: pointer;
      border: 1px solid rgba(92, 200, 216, 0.5); background: rgba(92, 200, 216, 0.12);
      color: #cfeef8; font-size: 12px;
    }
    #ui-layout-controls button:hover { background: rgba(92, 200, 216, 0.3); }
    #ui-layout-controls .btn-reset { border-color: rgba(212, 168, 67, 0.5); background: rgba(212, 168, 67, 0.1); color: #f0e0b8; }
    body.ui-edit-mode .ui-draggable {
      outline: 2px dashed rgba(92, 200, 216, 0.85); outline-offset: 3px;
      cursor: grab;
    }
    body.ui-edit-mode .ui-draggable:active { cursor: grabbing; }
    #ui-layout-tip {
      position: fixed; right: 12px; bottom: 52px; z-index: 6000;
      padding: 5px 12px; border-radius: 6px; font-size: 12px; color: #9fd8e8;
      background: rgba(10, 14, 20, 0.85); border: 1px solid rgba(92, 200, 216, 0.3);
      display: none;
    }
    #ui-layout-tip.visible { display: block; }
  `;
  document.head.appendChild(style);

  // --- 控制条 ---
  const controls = document.createElement('div');
  controls.id = 'ui-layout-controls';
  controls.innerHTML = '<button id="ui-lock-btn">🖱 调整布局</button><button id="ui-reset-btn" class="btn-reset">↺ 重置</button>';
  document.body.appendChild(controls);
  const tip = document.createElement('div');
  tip.id = 'ui-layout-tip';
  tip.textContent = '拖动面板到合适位置，然后点「固定布局」';
  document.body.appendChild(tip);

  // --- 收集面板 ---
  const entries = [];
  Object.entries(selectors).forEach(([key, sel]) => {
    const el = document.querySelector(sel);
    if (!el) {
      console.warn('[UI布局] 未找到面板: ' + sel);
      return;
    }
    el.classList.add('ui-draggable');
    entries.push({ key, el });
  });

  const isLocked = () => localStorage.getItem(LS_LOCK) === '1';

  // --- 绑定拖动 ---
  entries.forEach(({ key, el }) => {
    // 恢复上次位置
    try {
      const saved = localStorage.getItem(LS_POS + key);
      if (saved) {
        const { left, top } = JSON.parse(saved);
        if (typeof left === 'number' && typeof top === 'number') {
          el.style.left = left + 'px';
          el.style.top = top + 'px';
          el.style.right = 'auto';
          el.style.bottom = 'auto';
        }
      }
    } catch (e) { /* 忽略损坏数据 */ }

    let dragging = false, moved = false, ox = 0, oy = 0, startLeft = 0, startTop = 0;
    const DRAG_THRESHOLD = 5; // px：超过才算拖动，保证 button/链接的 click 不被吞

    el.addEventListener('pointerdown', (e) => {
      if (isLocked()) return;
      // 仅排除输入类元素（button 允许拖：阈值机制保证点击仍有效）
      if (e.target.closest('input, textarea, select, a')) return;
      dragging = true;
      moved = false;
      ox = e.clientX; oy = e.clientY;
      const rect = el.getBoundingClientRect();
      startLeft = rect.left; startTop = rect.top;
      try { el.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    });

    el.addEventListener('pointermove', (e) => {
      if (!dragging) return;
      if (!moved && (Math.abs(e.clientX - ox) + Math.abs(e.clientY - oy)) < DRAG_THRESHOLD) return;
      moved = true;
      let x = startLeft + (e.clientX - ox);
      let y = startTop + (e.clientY - oy);
      x = Math.min(Math.max(0, x), window.innerWidth - 60);
      y = Math.min(Math.max(0, y), window.innerHeight - 40);
      el.style.left = x + 'px';
      el.style.top = y + 'px';
      el.style.right = 'auto';
      el.style.bottom = 'auto';
    });

    const endDrag = (e) => {
      if (!dragging) return;
      dragging = false;
      try { el.releasePointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      if (!moved) return; // 未拖动：不保存位置，不干扰 button 点击
      const left = parseFloat(el.style.left);
      const top = parseFloat(el.style.top);
      if (!isNaN(left) && !isNaN(top)) {
        localStorage.setItem(LS_POS + key, JSON.stringify({ left, top }));
      }
    };
    el.addEventListener('pointerup', endDrag);
    el.addEventListener('pointercancel', endDrag);
  });

  // --- 编辑/固定切换 ---
  const lockBtn = document.getElementById('ui-lock-btn');
  const applyLockUI = () => {
    const locked = isLocked();
    document.body.classList.toggle('ui-edit-mode', !locked);
    lockBtn.textContent = locked ? '🖱 调整布局' : '🔒 固定布局';
    tip.classList.toggle('visible', !locked);
  };
  lockBtn.addEventListener('click', () => {
    localStorage.setItem(LS_LOCK, isLocked() ? '0' : '1');
    applyLockUI();
  });

  // --- 重置布局 ---
  document.getElementById('ui-reset-btn').addEventListener('click', () => {
    entries.forEach(({ key, el }) => {
      localStorage.removeItem(LS_POS + key);
      el.style.left = '';
      el.style.top = '';
      el.style.right = '';
      el.style.bottom = '';
    });
    alert('布局已重置为默认。如需继续调整，点「调整布局」。');
  });

  applyLockUI();
  return { isLocked };
}
