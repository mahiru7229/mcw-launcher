// MCW Launcher - Translation Studio Client Logic
(function () {
  'use strict';

  const PLACEHOLDER_REGEX = /(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)[^{}]*\}(?!\})/g;

  function extractPlaceholders(text) {
    if (!text) return [];
    const matches = text.match(PLACEHOLDER_REGEX);
    if (!matches) return [];
    const names = matches.map(m => m.slice(1, -1).split('.')[0].split('[')[0]);
    return Array.from(new Set(names)).sort();
  }

  // Application State
  const state = {
    languages: [],
    currentLocale: 'vi-VN',
    meta: {},
    items: [],
    itemsMap: new Map(),
    modifiedKeys: new Set(),
    activeKey: null,
    filter: 'all',
    selectedNamespace: 'all',
    searchQuery: '',
    filteredItems: [],
    renderedCount: 150, // Initial batch size for infinite/progressive scrolling
  };

  // DOM Elements cache
  const el = {};

  function initElements() {
    el.languageSelect = document.getElementById('languageSelect');
    el.btnNewLanguage = document.getElementById('btnNewLanguage');
    el.progressText = document.getElementById('progressText');
    el.progressBar = document.getElementById('progressBar');
    el.btnSaveAll = document.getElementById('btnSaveAll');
    el.unsavedBadge = document.getElementById('unsavedBadge');
    el.btnAudit = document.getElementById('btnAudit');
    el.btnCsvModal = document.getElementById('btnCsvModal');
    el.btnFindReplace = document.getElementById('btnFindReplace');
    el.btnShortcuts = document.getElementById('btnShortcuts');
    el.btnToggleTheme = document.getElementById('btnToggleTheme');
    el.themeIconDark = document.getElementById('themeIconDark');
    el.themeIconLight = document.getElementById('themeIconLight');

    // Sidebar
    el.searchInput = document.getElementById('searchInput');
    el.btnClearSearch = document.getElementById('btnClearSearch');
    el.filterPills = document.querySelectorAll('.filter-pill');
    el.countAll = document.getElementById('countAll');
    el.countUntranslated = document.getElementById('countUntranslated');
    el.countMismatches = document.getElementById('countMismatches');
    el.countIdentical = document.getElementById('countIdentical');
    el.countUnsaved = document.getElementById('countUnsaved');
    el.namespaceSelect = document.getElementById('namespaceSelect');
    el.btnResetNamespace = document.getElementById('btnResetNamespace');
    el.filteredCountLabel = document.getElementById('filteredCountLabel');
    el.btnNextUntranslated = document.getElementById('btnNextUntranslated');
    el.stringListContainer = document.getElementById('stringListContainer');

    // Workbench
    el.workbenchEmpty = document.getElementById('workbenchEmpty');
    el.workbenchContent = document.getElementById('workbenchContent');
    el.itemNamespaceBadge = document.getElementById('itemNamespaceBadge');
    el.itemIndexLabel = document.getElementById('itemIndexLabel');
    el.itemKeyDisplay = document.getElementById('itemKeyDisplay');
    el.btnCopyKey = document.getElementById('btnCopyKey');
    el.itemStatusBadge = document.getElementById('itemStatusBadge');
    el.sourceTextDisplay = document.getElementById('sourceTextDisplay');
    el.btnCopySource = document.getElementById('btnCopySource');
    el.linkGoogleTranslate = document.getElementById('linkGoogleTranslate');
    el.targetFlagIcon = document.getElementById('targetFlagIcon');
    el.targetCardTitle = document.getElementById('targetCardTitle');
    el.charCountDisplay = document.getElementById('charCountDisplay');
    el.btnClearTarget = document.getElementById('btnClearTarget');
    el.placeholderBar = document.getElementById('placeholderBar');
    el.placeholderChips = document.getElementById('placeholderChips');
    el.targetTextarea = document.getElementById('targetTextarea');
    el.validationAlert = document.getElementById('validationAlert');
    el.validationIcon = document.getElementById('validationIcon');
    el.validationMessage = document.getElementById('validationMessage');
    el.btnPrev = document.getElementById('btnPrev');
    el.btnNext = document.getElementById('btnNext');
    el.btnApplyAndNext = document.getElementById('btnApplyAndNext');

    // Modals
    el.modalNewLanguage = document.getElementById('modalNewLanguage');
    el.newLocaleCode = document.getElementById('newLocaleCode');
    el.newLocaleName = document.getElementById('newLocaleName');
    el.copySourceCheckbox = document.getElementById('copySourceCheckbox');
    el.btnSubmitNewLanguage = document.getElementById('btnSubmitNewLanguage');

    el.modalAudit = document.getElementById('modalAudit');
    el.auditStatusBadge = document.getElementById('auditStatusBadge');
    el.auditStatsGrid = document.getElementById('auditStatsGrid');
    el.auditIssuesList = document.getElementById('auditIssuesList');
    el.btnReAudit = document.getElementById('btnReAudit');

    el.modalFindReplace = document.getElementById('modalFindReplace');
    el.findTextInput = document.getElementById('findTextInput');
    el.replaceTextInput = document.getElementById('replaceTextInput');
    el.matchCaseCheckbox = document.getElementById('matchCaseCheckbox');
    el.btnExecuteReplace = document.getElementById('btnExecuteReplace');

    el.modalCsv = document.getElementById('modalCsv');
    el.btnDownloadCsv = document.getElementById('btnDownloadCsv');
    el.csvFileInput = document.getElementById('csvFileInput');
    el.btnUploadCsv = document.getElementById('btnUploadCsv');

    el.modalShortcuts = document.getElementById('modalShortcuts');
    el.toastContainer = document.getElementById('toastContainer');
  }

  // Toast Notification
  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    let icon = '✓';
    if (type === 'error') icon = '✕';
    else if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `<span style="font-weight:700;">${icon}</span><span>${escapeHtml(message)}</span>`;
    el.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, 3500);
  }

  function escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // API Requests
  async function apiGet(endpoint) {
    const res = await fetch(endpoint);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return await res.json();
  }

  async function apiPost(endpoint, data) {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return await res.json();
  }

  // Load language list
  async function fetchLanguages() {
    try {
      const langs = await apiGet('/api/languages');
      state.languages = langs;
      el.languageSelect.innerHTML = '';
      langs.forEach(lang => {
        const opt = document.createElement('option');
        opt.value = lang.locale;
        opt.textContent = `${lang.name} (${lang.locale}) - ${lang.key_count.toLocaleString()} keys`;
        if (lang.locale === state.currentLocale) opt.selected = true;
        el.languageSelect.appendChild(opt);
      });
    } catch (e) {
      showToast(`Lỗi tải danh sách ngôn ngữ: ${e.message}`, 'error');
    }
  }

  // Load locale pack data
  async function loadLocaleData(locale) {
    try {
      if (state.modifiedKeys.size > 0) {
        if (!confirm(`Bạn có ${state.modifiedKeys.size} thay đổi chưa lưu. Bạn có chắc muốn chuyển ngôn ngữ mà không lưu?`)) {
          el.languageSelect.value = state.currentLocale;
          return;
        }
      }

      state.currentLocale = locale;
      state.modifiedKeys.clear();
      updateUnsavedBadge();

      const data = await apiGet(`/api/load?locale=${encodeURIComponent(locale)}`);
      state.meta = data.meta || {};
      state.items = data.items || [];
      state.itemsMap = new Map();
      state.items.forEach(item => state.itemsMap.set(item.key, item));

      // Target title & flag
      el.targetCardTitle.textContent = `Bản dịch (${data.meta.name || locale})`;
      el.targetFlagIcon.textContent = locale.startsWith('vi') ? '🇻🇳' : (locale.startsWith('ja') ? '🇯🇵' : (locale.startsWith('zh') ? '🇨🇳' : '🌐'));

      // Populate namespace dropdown
      populateNamespaces(data.namespaces);

      // Apply initial filters
      applyFilters();

      // Auto-select first item
      if (state.filteredItems.length > 0) {
        selectItem(state.filteredItems[0].key);
      } else {
        showEmptyWorkbench();
      }

      showToast(`Đã tải gói ngôn ngữ: ${data.meta.name || locale} (${state.items.length.toLocaleString()} chuỗi)`);
    } catch (e) {
      showToast(`Lỗi khi mở gói ngôn ngữ: ${e.message}`, 'error');
    }
  }

  function populateNamespaces(namespaces) {
    el.namespaceSelect.innerHTML = `<option value="all">Tất cả module (${state.items.length.toLocaleString()})</option>`;
    namespaces.forEach(ns => {
      const opt = document.createElement('option');
      opt.value = ns.name;
      opt.textContent = `${ns.name} (${ns.count.toLocaleString()})`;
      el.namespaceSelect.appendChild(opt);
    });
    el.namespaceSelect.value = 'all';
    state.selectedNamespace = 'all';
    el.btnResetNamespace.style.display = 'none';
  }

  // Filter & Search logic
  function applyFilters() {
    const q = state.searchQuery.trim().toLowerCase();
    const filter = state.filter;
    const ns = state.selectedNamespace;

    let allCount = 0;
    let untranslatedCount = 0;
    let mismatchCount = 0;
    let identicalCount = 0;
    let unsavedCount = state.modifiedKeys.size;

    const filtered = [];

    for (let i = 0; i < state.items.length; i++) {
      const item = state.items[i];
      allCount++;
      if (item.status === 'untranslated') untranslatedCount++;
      else if (item.status === 'placeholder_mismatch') mismatchCount++;
      else if (item.status === 'identical') identicalCount++;

      // Check namespace match
      if (ns !== 'all' && item.namespace !== ns) continue;

      // Check status filter match
      if (filter === 'untranslated' && item.status !== 'untranslated') continue;
      if (filter === 'placeholder_mismatch' && item.status !== 'placeholder_mismatch') continue;
      if (filter === 'identical' && item.status !== 'identical') continue;
      if (filter === 'unsaved' && !state.modifiedKeys.has(item.key)) continue;

      // Check search match
      if (q) {
        const keyMatch = item.key.toLowerCase().includes(q);
        const sourceMatch = item.source.toLowerCase().includes(q);
        const targetMatch = item.target.toLowerCase().includes(q);
        if (!keyMatch && !sourceMatch && !targetMatch) continue;
      }

      filtered.push(item);
    }

    state.filteredItems = filtered;

    // Update Pill Count Badges
    el.countAll.textContent = allCount.toLocaleString();
    el.countUntranslated.textContent = untranslatedCount.toLocaleString();
    el.countMismatches.textContent = mismatchCount.toLocaleString();
    el.countIdentical.textContent = identicalCount.toLocaleString();
    el.countUnsaved.textContent = unsavedCount.toLocaleString();

    // Update Progress Bar
    const translatedCount = allCount - untranslatedCount;
    const pct = allCount > 0 ? ((translatedCount / allCount) * 100).toFixed(1) : 0;
    el.progressText.textContent = `${translatedCount.toLocaleString()} / ${allCount.toLocaleString()} (${pct}%)`;
    el.progressBar.style.width = `${pct}%`;

    el.filteredCountLabel.textContent = `Hiển thị ${filtered.length.toLocaleString()} chuỗi`;

    // Reset pagination batch
    state.renderedCount = 150;
    renderStringList();

    // If activeKey is not in filtered list, select first match
    if (filtered.length > 0) {
      if (!filtered.some(it => it.key === state.activeKey)) {
        selectItem(filtered[0].key);
      }
    } else {
      showEmptyWorkbench();
    }
  }

  // Render string list in sidebar
  function renderStringList() {
    const container = el.stringListContainer;
    container.innerHTML = '';

    const limit = Math.min(state.renderedCount, state.filteredItems.length);
    const fragment = document.createDocumentFragment();

    for (let i = 0; i < limit; i++) {
      const item = state.filteredItems[i];
      const div = document.createElement('div');
      div.className = `string-item ${item.key === state.activeKey ? 'active' : ''}`;
      div.dataset.key = item.key;

      const isModified = state.modifiedKeys.has(item.key);
      const dotClass = isModified ? 'status-dot-unsaved' : `status-dot-${item.status}`;

      div.innerHTML = `
        <div class="string-item-top">
          <span class="string-key" title="${escapeHtml(item.key)}">${escapeHtml(item.key)}</span>
          <span class="string-status-dot ${dotClass}" title="${isModified ? 'Chưa lưu' : item.status}"></span>
        </div>
        <div class="string-source-preview">${escapeHtml(item.source)}</div>
        <div class="string-target-preview ${!item.target ? 'empty' : ''}">${item.target ? escapeHtml(item.target) : '(Chưa dịch)'}</div>
      `;

      div.addEventListener('click', () => {
        saveCurrentDraft();
        selectItem(item.key);
      });

      fragment.appendChild(div);
    }

    container.appendChild(fragment);

    // Scroll listener for progressive infinite loading
    container.onscroll = () => {
      if (container.scrollTop + container.clientHeight >= container.scrollHeight - 150) {
        if (state.renderedCount < state.filteredItems.length) {
          state.renderedCount += 100;
          renderStringList();
        }
      }
    };
  }

  // Save current textarea content to memory
  function saveCurrentDraft() {
    if (!state.activeKey) return;
    const item = state.itemsMap.get(state.activeKey);
    if (!item) return;

    const newTarget = el.targetTextarea.value;
    if (newTarget !== item.target) {
      item.target = newTarget;
      state.modifiedKeys.add(item.key);
      updateItemStatus(item);
      updateUnsavedBadge();
      updateSidebarItem(item.key);
    }
  }

  function updateItemStatus(item) {
    const is_empty = !item.target.trim();
    const source_ph = item.source_placeholders;
    const target_ph = extractPlaceholders(item.target);
    item.target_placeholders = target_ph;

    const ph_match = source_ph.length === target_ph.length && source_ph.every(p => target_ph.includes(p));
    const is_identical = Boolean(item.target) && item.target === item.source;

    if (is_empty) item.status = 'untranslated';
    else if (!ph_match) item.status = 'placeholder_mismatch';
    else if (is_identical) item.status = 'identical';
    else item.status = 'translated';
  }

  function updateSidebarItem(key) {
    const elem = el.stringListContainer.querySelector(`.string-item[data-key="${CSS.escape(key)}"]`);
    if (!elem) return;
    const item = state.itemsMap.get(key);
    if (!item) return;

    const dot = elem.querySelector('.string-status-dot');
    if (dot) {
      dot.className = `string-status-dot ${state.modifiedKeys.has(key) ? 'status-dot-unsaved' : `status-dot-${item.status}`}`;
    }
    const targetPreview = elem.querySelector('.string-target-preview');
    if (targetPreview) {
      targetPreview.className = `string-target-preview ${!item.target ? 'empty' : ''}`;
      targetPreview.textContent = item.target ? item.target : '(Chưa dịch)';
    }
  }

  function updateUnsavedBadge() {
    const count = state.modifiedKeys.size;
    if (count > 0) {
      el.unsavedBadge.style.display = 'inline-block';
      el.unsavedBadge.textContent = count.toLocaleString();
      el.countUnsaved.textContent = count.toLocaleString();
    } else {
      el.unsavedBadge.style.display = 'none';
      el.countUnsaved.textContent = '0';
    }
  }

  // Select item in workbench
  function selectItem(key) {
    state.activeKey = key;
    const item = state.itemsMap.get(key);
    if (!item) {
      showEmptyWorkbench();
      return;
    }

    el.workbenchEmpty.style.display = 'none';
    el.workbenchContent.style.display = 'flex';

    // Highlight in sidebar
    el.stringListContainer.querySelectorAll('.string-item').forEach(it => {
      it.classList.toggle('active', it.dataset.key === key);
    });

    // Header info
    el.itemNamespaceBadge.textContent = item.namespace;
    el.itemKeyDisplay.textContent = item.key;

    const curIndex = state.filteredItems.findIndex(it => it.key === key) + 1;
    el.itemIndexLabel.textContent = `#${curIndex.toLocaleString()} / ${state.filteredItems.length.toLocaleString()}`;

    // Status badge
    updateStatusBadge(item.status);

    // Source rendering with placeholder highlight
    renderSourceText(item.source, item.source_placeholders);

    // Google Translate link
    const gtUrl = `https://translate.google.com/?sl=en&tl=${state.currentLocale.split('-')[0]}&text=${encodeURIComponent(item.source)}&op=translate`;
    el.linkGoogleTranslate.href = gtUrl;

    // Placeholders injection bar
    renderPlaceholderChips(item.source_placeholders);

    // Target Textarea
    el.targetTextarea.value = item.target;
    updateCharCount();
    validateTargetText(item);

    // Scroll active item in sidebar into view if needed
    const activeElem = el.stringListContainer.querySelector(`.string-item[data-key="${CSS.escape(key)}"]`);
    if (activeElem) {
      activeElem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  function showEmptyWorkbench() {
    state.activeKey = null;
    el.workbenchEmpty.style.display = 'flex';
    el.workbenchContent.style.display = 'none';
  }

  function updateStatusBadge(status) {
    el.itemStatusBadge.className = `badge badge-status ${status}`;
    if (status === 'untranslated') el.itemStatusBadge.textContent = 'Chưa dịch';
    else if (status === 'placeholder_mismatch') el.itemStatusBadge.textContent = 'Lỗi biến';
    else if (status === 'identical') el.itemStatusBadge.textContent = 'Giống tiếng Anh';
    else el.itemStatusBadge.textContent = 'Đã dịch';
  }

  function renderSourceText(source, placeholders) {
    if (!placeholders || placeholders.length === 0) {
      el.sourceTextDisplay.textContent = source;
      return;
    }

    let html = escapeHtml(source);
    placeholders.forEach(ph => {
      const token = `{${ph}}`;
      const escapedToken = escapeHtml(token);
      html = html.split(escapedToken).join(`<span class="token-placeholder">${escapedToken}</span>`);
    });
    el.sourceTextDisplay.innerHTML = html;
  }

  function renderPlaceholderChips(placeholders) {
    if (!placeholders || placeholders.length === 0) {
      el.placeholderBar.style.display = 'none';
      return;
    }

    el.placeholderBar.style.display = 'flex';
    el.placeholderChips.innerHTML = '';

    placeholders.forEach(ph => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'chip-placeholder';
      chip.title = `Chèn {${ph}} vào vị trí con trỏ`;
      chip.innerHTML = `<span>+</span> <span>{${ph}}</span>`;
      chip.addEventListener('click', () => {
        insertTextAtCursor(el.targetTextarea, `{${ph}}`);
      });
      el.placeholderChips.appendChild(chip);
    });
  }

  function insertTextAtCursor(textarea, text) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const val = textarea.value;

    textarea.value = val.substring(0, start) + text + val.substring(end);
    textarea.selectionStart = textarea.selectionEnd = start + text.length;
    textarea.focus();

    // Trigger input event
    textarea.dispatchEvent(new Event('input'));
  }

  function updateCharCount() {
    const text = el.targetTextarea.value;
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    el.charCountDisplay.textContent = `${chars.toLocaleString()} ký tự | ${words.toLocaleString()} từ`;
  }

  function validateTargetText(item) {
    const text = el.targetTextarea.value;
    const sourcePh = item.source_placeholders || [];
    const targetPh = extractPlaceholders(text);

    const alert = el.validationAlert;
    const icon = el.validationIcon;
    const msg = el.validationMessage;

    if (!text.trim()) {
      alert.style.display = 'flex';
      alert.className = 'validation-alert warning';
      icon.textContent = 'ℹ️';
      msg.textContent = 'Chuỗi chưa có nội dung dịch.';
      return;
    }

    // Check placeholder parity
    const missing = sourcePh.filter(p => !targetPh.includes(p));
    const extra = targetPh.filter(p => !sourcePh.includes(p));

    if (missing.length > 0 || extra.length > 0) {
      alert.style.display = 'flex';
      alert.className = 'validation-alert error';
      icon.textContent = '⚠️';
      const parts = [];
      if (missing.length > 0) parts.push(`Thiếu biến: {${missing.join('}, {')}}`);
      if (extra.length > 0) parts.push(`Biến lạ không có trong tiếng Anh: {${extra.join('}, {')}}`);
      msg.textContent = parts.join(' | ');
      return;
    }

    if (text === item.source && text.length > 2) {
      alert.style.display = 'flex';
      alert.className = 'validation-alert warning';
      icon.textContent = '⚠️';
      msg.textContent = 'Bản dịch đang trùng khớp 100% với tiếng Anh gốc.';
      return;
    }

    // All good
    alert.style.display = 'flex';
    alert.className = 'validation-alert ok';
    icon.textContent = '✓';
    msg.textContent = sourcePh.length > 0 ? `Hợp lệ: Khớp toàn bộ ${sourcePh.length} biến placeholder.` : 'Hợp lệ.';
  }

  // Apply and move next
  function applyAndNext() {
    if (!state.activeKey) return;
    saveCurrentDraft();

    const curIndex = state.filteredItems.findIndex(it => it.key === state.activeKey);
    if (curIndex !== -1 && curIndex < state.filteredItems.length - 1) {
      selectItem(state.filteredItems[curIndex + 1].key);
    } else {
      showToast('Đã đến cuối danh sách bộ lọc!', 'warning');
    }
  }

  function applyAndPrev() {
    if (!state.activeKey) return;
    saveCurrentDraft();

    const curIndex = state.filteredItems.findIndex(it => it.key === state.activeKey);
    if (curIndex > 0) {
      selectItem(state.filteredItems[curIndex - 1].key);
    }
  }

  function jumpToNextUntranslated() {
    saveCurrentDraft();
    const curIndex = state.activeKey ? state.items.findIndex(it => it.key === state.activeKey) : -1;

    for (let i = curIndex + 1; i < state.items.length; i++) {
      if (state.items[i].status === 'untranslated') {
        // Change filter to all if needed
        if (state.filter !== 'all' && state.filter !== 'untranslated') {
          setActiveFilter('all');
        }
        selectItem(state.items[i].key);
        return;
      }
    }

    // Wrap around
    for (let i = 0; i <= curIndex; i++) {
      if (state.items[i].status === 'untranslated') {
        selectItem(state.items[i].key);
        return;
      }
    }

    showToast('Tất cả chuỗi đã được dịch hoàn tất! Không còn chuỗi trống nào.', 'success');
  }

  function setActiveFilter(filterName) {
    state.filter = filterName;
    el.filterPills.forEach(pill => {
      pill.classList.toggle('active', pill.dataset.filter === filterName);
    });
    applyFilters();
  }

  // Save all to server
  async function saveAllToFile() {
    saveCurrentDraft();
    try {
      const translations = {};
      state.items.forEach(it => {
        translations[it.key] = it.target;
      });

      const res = await apiPost('/api/save', {
        locale: state.currentLocale,
        meta: state.meta,
        translations: translations,
      });

      state.modifiedKeys.clear();
      updateUnsavedBadge();
      renderStringList();

      showToast(`Đã lưu thành công ${res.key_count.toLocaleString()} chuỗi vào lang/${state.currentLocale}.json!${res.backup ? ` (Sao lưu: ${res.backup})` : ''}`, 'success');
    } catch (e) {
      showToast(`Lỗi khi lưu file: ${e.message}`, 'error');
    }
  }

  // Run QA Preflight Audit
  async function runAudit() {
    saveCurrentDraft();
    try {
      const audit = await apiGet(`/api/audit?locale=${encodeURIComponent(state.currentLocale)}`);
      openModal(el.modalAudit);

      const isValid = audit.valid;
      el.auditStatusBadge.className = `audit-status-badge ${isValid ? 'success' : 'error'}`;
      el.auditStatusBadge.textContent = isValid ? 'ĐẠT CHUẨN SẴN SÀNG PHÁT HÀNH (PASSED)' : 'PHÁT HIỆN LỖI CẦN SỬA';

      const s = audit.stats;
      el.auditStatsGrid.innerHTML = `
        <div class="audit-stat-card">
          <span class="stat-num">${s.total_target_keys.toLocaleString()}</span>
          <span class="stat-label">Tổng số key</span>
        </div>
        <div class="audit-stat-card">
          <span class="stat-num" style="color: ${s.missing_count > 0 ? '#ef4444' : '#10b981'};">${s.missing_count}</span>
          <span class="stat-label">Thiếu key so với en-US</span>
        </div>
        <div class="audit-stat-card">
          <span class="stat-num" style="color: ${s.empty_count > 0 ? '#ef4444' : '#10b981'};">${s.empty_count}</span>
          <span class="stat-label">Chuỗi trống</span>
        </div>
        <div class="audit-stat-card">
          <span class="stat-num" style="color: ${s.placeholder_mismatch_count > 0 ? '#ef4444' : '#10b981'};">${s.placeholder_mismatch_count}</span>
          <span class="stat-label">Lỗi biến placeholder</span>
        </div>
        <div class="audit-stat-card">
          <span class="stat-num" style="color: #f59e0b;">${s.identical_count}</span>
          <span class="stat-label">Trùng nguyên văn tiếng Anh</span>
        </div>
      `;

      el.auditIssuesList.innerHTML = '';
      if (audit.errors.length === 0 && audit.warnings.length === 0) {
        el.auditIssuesList.innerHTML = '<p class="empty-hint" style="color: #10b981; font-weight: 600;">Tuyệt vời! Không phát hiện bất kỳ lỗi cú pháp hoặc thiếu biến nào.</p>';
      } else {
        audit.errors.forEach(err => {
          const div = document.createElement('div');
          div.className = 'audit-issue-item';
          div.textContent = `❌ ${err}`;
          // Extract key name if possible to jump
          const match = err.match(/(?:for|key:?|translation:?)\s+([a-zA-Z0-9_.-]+)/);
          if (match && state.itemsMap.has(match[1])) {
            div.title = 'Bấm để nhảy tới chuỗi này';
            div.addEventListener('click', () => {
              closeModal(el.modalAudit);
              setActiveFilter('all');
              selectItem(match[1]);
            });
          }
          el.auditIssuesList.appendChild(div);
        });

        audit.warnings.forEach(warn => {
          const div = document.createElement('div');
          div.className = 'audit-issue-item';
          div.style.backgroundColor = 'var(--badge-bg-warning)';
          div.style.color = 'var(--badge-text-warning)';
          div.style.borderColor = 'rgba(245, 158, 11, 0.3)';
          div.textContent = `⚠️ ${warn}`;
          el.auditIssuesList.appendChild(div);
        });
      }
    } catch (e) {
      showToast(`Lỗi kiểm tra QA: ${e.message}`, 'error');
    }
  }

  // Create new language pack
  async function submitNewLanguage() {
    const locale = el.newLocaleCode.value.trim();
    const name = el.newLocaleName.value.trim();
    const copySource = el.copySourceCheckbox.checked;

    if (!locale) {
      alert('Vui lòng nhập mã locale (ví dụ: ja-JP, zh-CN)');
      return;
    }
    if (!name) {
      alert('Vui lòng nhập tên ngôn ngữ (ví dụ: 日本語 - 日本)');
      return;
    }

    try {
      const res = await apiPost('/api/create-language', { locale, name, copy_source: copySource });
      closeModal(el.modalNewLanguage);
      await fetchLanguages();
      el.languageSelect.value = res.locale;
      await loadLocaleData(res.locale);
      showToast(`Đã tạo thành công gói ngôn ngữ ${res.name} (${res.locale})!`, 'success');
    } catch (e) {
      alert(`Lỗi: ${e.message}`);
    }
  }

  // Find & Replace
  function executeFindReplace() {
    const findText = el.findTextInput.value;
    const replaceText = el.replaceTextInput.value;
    const matchCase = el.matchCaseCheckbox.checked;

    if (!findText) {
      alert('Vui lòng nhập từ cần tìm');
      return;
    }

    let affectedCount = 0;
    state.items.forEach(item => {
      if (!item.target) return;
      let hasMatch = false;
      let newText = item.target;

      if (matchCase) {
        if (newText.includes(findText)) {
          newText = newText.replaceAll(findText, replaceText);
          hasMatch = true;
        }
      } else {
        const regex = new RegExp(findText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        if (regex.test(newText)) {
          newText = newText.replace(regex, replaceText);
          hasMatch = true;
        }
      }

      if (hasMatch) {
        item.target = newText;
        state.modifiedKeys.add(item.key);
        updateItemStatus(item);
        affectedCount++;
      }
    });

    closeModal(el.modalFindReplace);
    updateUnsavedBadge();
    applyFilters();
    if (state.activeKey) selectItem(state.activeKey);

    showToast(`Đã thay thế "${findText}" thành "${replaceText}" trong ${affectedCount} chuỗi!`, 'success');
  }

  // CSV Import / Export
  function downloadCsv() {
    window.location.href = `/api/export-csv?locale=${encodeURIComponent(state.currentLocale)}`;
  }

  async function uploadCsv() {
    const file = el.csvFileInput.files[0];
    if (!file) {
      alert('Vui lòng chọn một file CSV trước');
      return;
    }

    const reader = new FileReader();
    reader.onload = async (evt) => {
      try {
        const csvText = evt.target.result;
        const res = await apiPost('/api/import-csv', {
          locale: state.currentLocale,
          csv_text: csvText,
        });

        // Apply imported translations to state
        let updatedCount = 0;
        for (const [key, val] of Object.entries(res.translations)) {
          const item = state.itemsMap.get(key);
          if (item && item.target !== val) {
            item.target = val;
            state.modifiedKeys.add(key);
            updateItemStatus(item);
            updatedCount++;
          }
        }

        closeModal(el.modalCsv);
        updateUnsavedBadge();
        applyFilters();
        if (state.activeKey) selectItem(state.activeKey);

        showToast(`Đã cập nhật ${updatedCount} chuỗi từ file CSV thành công!`, 'success');
      } catch (e) {
        alert(`Lỗi khi nhập CSV: ${e.message}`);
      }
    };
    reader.readAsText(file, 'utf-8');
  }

  // Modals helper
  function openModal(modal) {
    modal.style.display = 'flex';
  }

  function closeModal(modal) {
    modal.style.display = 'none';
  }

  // Event Listeners
  function setupEvents() {
    // Language dropdown change
    el.languageSelect.addEventListener('change', (e) => {
      loadLocaleData(e.target.value);
    });

    // New Language modal
    el.btnNewLanguage.addEventListener('click', () => {
      el.newLocaleCode.value = '';
      el.newLocaleName.value = '';
      openModal(el.modalNewLanguage);
    });
    el.btnSubmitNewLanguage.addEventListener('click', submitNewLanguage);

    // Save all button
    el.btnSaveAll.addEventListener('click', saveAllToFile);

    // Audit / QA button
    el.btnAudit.addEventListener('click', runAudit);
    el.btnReAudit.addEventListener('click', runAudit);

    // CSV button
    el.btnCsvModal.addEventListener('click', () => openModal(el.modalCsv));
    el.btnDownloadCsv.addEventListener('click', downloadCsv);
    el.btnUploadCsv.addEventListener('click', uploadCsv);

    // Find and Replace button
    el.btnFindReplace.addEventListener('click', () => {
      el.findTextInput.value = '';
      el.replaceTextInput.value = '';
      openModal(el.modalFindReplace);
    });
    el.btnExecuteReplace.addEventListener('click', executeFindReplace);

    // Shortcuts button
    el.btnShortcuts.addEventListener('click', () => openModal(el.modalShortcuts));

    // Theme Toggle
    el.btnToggleTheme.addEventListener('click', () => {
      const isDark = document.body.classList.toggle('dark-theme');
      document.body.classList.toggle('light-theme', !isDark);
      el.themeIconDark.style.display = isDark ? 'block' : 'none';
      el.themeIconLight.style.display = isDark ? 'none' : 'block';
    });

    // Search input
    let searchDebounce = null;
    el.searchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounce);
      state.searchQuery = e.target.value;
      el.btnClearSearch.style.display = state.searchQuery ? 'block' : 'none';
      searchDebounce = setTimeout(applyFilters, 180);
    });

    el.btnClearSearch.addEventListener('click', () => {
      el.searchInput.value = '';
      state.searchQuery = '';
      el.btnClearSearch.style.display = 'none';
      applyFilters();
      el.searchInput.focus();
    });

    // Filter pills
    el.filterPills.forEach(pill => {
      pill.addEventListener('click', () => {
        setActiveFilter(pill.dataset.filter);
      });
    });

    // Namespace dropdown
    el.namespaceSelect.addEventListener('change', (e) => {
      state.selectedNamespace = e.target.value;
      el.btnResetNamespace.style.display = state.selectedNamespace !== 'all' ? 'inline-block' : 'none';
      applyFilters();
    });

    el.btnResetNamespace.addEventListener('click', () => {
      el.namespaceSelect.value = 'all';
      state.selectedNamespace = 'all';
      el.btnResetNamespace.style.display = 'none';
      applyFilters();
    });

    el.btnNextUntranslated.addEventListener('click', jumpToNextUntranslated);

    // Workbench buttons
    el.btnCopyKey.addEventListener('click', () => {
      if (state.activeKey) {
        navigator.clipboard.writeText(state.activeKey);
        showToast(`Đã sao chép key: ${state.activeKey}`);
      }
    });

    el.btnCopySource.addEventListener('click', () => {
      const item = state.itemsMap.get(state.activeKey);
      if (item) {
        el.targetTextarea.value = item.source;
        el.targetTextarea.dispatchEvent(new Event('input'));
        showToast('Đã chép nội dung tiếng Anh vào bản dịch');
      }
    });

    el.btnClearTarget.addEventListener('click', () => {
      el.targetTextarea.value = '';
      el.targetTextarea.dispatchEvent(new Event('input'));
    });

    el.targetTextarea.addEventListener('input', () => {
      updateCharCount();
      if (state.activeKey) {
        const item = state.itemsMap.get(state.activeKey);
        if (item) validateTargetText(item);
      }
    });

    el.btnPrev.addEventListener('click', applyAndPrev);
    el.btnNext.addEventListener('click', applyAndNext);
    el.btnApplyAndNext.addEventListener('click', applyAndNext);

    // Modal Close buttons
    document.querySelectorAll('[data-close]').forEach(btn => {
      btn.addEventListener('click', () => {
        const modalId = btn.dataset.close;
        const modal = document.getElementById(modalId);
        if (modal) closeModal(modal);
      });
    });

    // Global Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      // Ctrl+S: Save all
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        saveAllToFile();
        return;
      }

      // Ctrl+Enter: Apply and next
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        applyAndNext();
        return;
      }

      // Alt+Down: Next string
      if (e.altKey && e.key === 'ArrowDown') {
        e.preventDefault();
        applyAndNext();
        return;
      }

      // Alt+Up: Prev string
      if (e.altKey && e.key === 'ArrowUp') {
        e.preventDefault();
        applyAndPrev();
        return;
      }

      // Ctrl+F: Search focus
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
        e.preventDefault();
        el.searchInput.focus();
        el.searchInput.select();
        return;
      }

      // Esc: Close open modals
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop').forEach(modal => {
          if (modal.style.display !== 'none') {
            closeModal(modal);
          }
        });
      }
    });
  }

  // App Initialization
  async function init() {
    initElements();
    setupEvents();
    await fetchLanguages();
    await loadLocaleData(state.currentLocale);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
