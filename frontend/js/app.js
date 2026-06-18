'use strict';

const API_BASE = "";  // 같은 서버에서 서빙

// ================================================================
// 상태
// ================================================================
let currentJobId = null;
let pollingTimer  = null;
let etaTimer      = null;
let selectedFile  = null;
let jobHistory    = [];          // { jobId, filename, status, pct, result }
let currentUser   = { name: 'ooo', email: 'user@example.com' };

// ================================================================
// 시작: 로그인 이벤트 바인딩
// ================================================================
document.getElementById('btnGoogleLogin').addEventListener('click', () => doLogin('google'));
document.getElementById('btnLogin').addEventListener('click',       () => doLogin('email'));
document.getElementById('btnSignup').addEventListener('click', e => { e.preventDefault(); doLogin('email'); });

// ================================================================
// 로그인 처리 (Mock)
// ================================================================
function doLogin(method) {
  const emailEl = document.getElementById('loginEmail');
  if (method === 'email' && emailEl && emailEl.value.trim()) {
    const parts = emailEl.value.trim().split('@');
    currentUser.name  = parts[0] || 'ooo';
    currentUser.email = emailEl.value.trim();
  } else {
    currentUser.name  = 'ooo';
    currentUser.email = 'user@google.com';
  }

  document.getElementById('loginPage').style.display  = 'none';
  document.getElementById('appShell').style.display   = 'flex';
  document.getElementById('topGreeting').textContent  = `환영합니다, ${currentUser.name}님.`;
  document.getElementById('settingsName').textContent  = currentUser.name;
  document.getElementById('settingsEmail').textContent = currentUser.email;

  initApp();
}

// ================================================================
// 앱 초기화 (로그인 후)
// ================================================================
async function initApp() {
  bindNavEvents();
  bindUploadEvents();
  bindResultsEvents();
  await loadCategories();
  navigate('dashboard');
  renderDashboard();
}

// ================================================================
// 내비게이션
// ================================================================
const ALL_VIEWS = ['dashboard', 'upload', 'loading', 'results', 'settings'];

function navigate(view) {
  ALL_VIEWS.forEach(v => {
    const el = document.getElementById('view' + cap(v));
    if (el) el.classList.toggle('active', v === view);
  });
  // 사이드바 활성화 (3개만)
  ['dashboard', 'upload', 'settings'].forEach(v => {
    const nav = document.getElementById('nav' + cap(v));
    if (nav) nav.classList.toggle('active', v === view);
  });
}

function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function bindNavEvents() {
  document.querySelectorAll('.nav-item[data-view]').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.view));
  });
  document.getElementById('btnGoUpload')
    ?.addEventListener('click', () => navigate('upload'));
  document.getElementById('btnBackToDashboard')
    ?.addEventListener('click', () => navigate('dashboard'));
}

// ================================================================
// 카테고리 로딩
// ================================================================
async function loadCategories() {
  const sel = document.getElementById('categorySelect');
  try {
    const res  = await fetch(`${API_BASE}/api/categories`);
    const data = await res.json();
    const cats = data.categories || [];
    sel.innerHTML = cats.length
      ? cats.map(c => `<option value="${c}">${c.replace(/_/g, ' ')}</option>`).join('')
      : '<option value="Entertainment">Entertainment</option>';
  } catch {
    if (sel) sel.innerHTML = '<option value="Entertainment">Entertainment</option>';
  }
}

// ================================================================
// 업로드 이벤트
// ================================================================
function bindUploadEvents() {
  const dropZone  = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const btnFile   = document.getElementById('btnFileSelect');
  const removeBtn = document.getElementById('removeFile');
  const analyzeBtn = document.getElementById('analyzeBtn');

  // 드롭존 클릭 → 파일 선택
  dropZone?.addEventListener('click', () => fileInput?.click());

  // "파일 불러오기" 버튼 (stopPropagation으로 dropZone 이벤트 중복 방지)
  btnFile?.addEventListener('click', e => {
    e.stopPropagation();
    fileInput?.click();
  });

  dropZone?.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });
  dropZone?.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone?.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  });

  fileInput?.addEventListener('change', e => {
    if (e.target.files[0]) setFile(e.target.files[0]);
  });

  removeBtn?.addEventListener('click', clearFile);
  analyzeBtn?.addEventListener('click', startAnalysis);
}

function setFile(file) {
  selectedFile = file;
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent = formatBytes(file.size);
  document.getElementById('filePreview').style.display = 'flex';
  document.getElementById('analyzeBtn').disabled = false;
}

function clearFile() {
  selectedFile = null;
  const fi = document.getElementById('fileInput');
  if (fi) fi.value = '';
  document.getElementById('filePreview').style.display = 'none';
  document.getElementById('analyzeBtn').disabled = true;
}

function formatBytes(b) {
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
  return (b / (1024 * 1024)).toFixed(1) + ' MB';
}

// ================================================================
// 분석 시작
// ================================================================
async function startAnalysis() {
  if (!selectedFile) return;

  const formData = new FormData();
  formData.append('video',         selectedFile);
  formData.append('category',      document.getElementById('categorySelect').value || 'Entertainment');
  formData.append('custom_prompt', document.getElementById('customPrompt').value   || '');

  // 히스토리 엔트리 추가
  const entry = { jobId: null, filename: selectedFile.name, status: 'processing', pct: 0, result: null };
  jobHistory.push(entry);
  const idx = jobHistory.length - 1;

  // 로딩 뷰로 전환
  navigate('loading');
  startEtaCountdown();

  try {
    const res  = await fetch(`${API_BASE}/api/analyze`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error(`서버 오류: ${res.status}`);
    const data = await res.json();
    currentJobId = data.job_id;
    entry.jobId  = data.job_id;
    startPolling(idx);
  } catch (err) {
    jobHistory.pop();
    clearTimers();
    alert('분석 요청 실패: ' + err.message);
    navigate('upload');
  }
}

// ================================================================
// 폴링
// ================================================================
function startPolling(histIdx) {
  clearPolling();
  pollingTimer = setInterval(() => pollStatus(histIdx), 2000);
}

function clearPolling() {
  clearInterval(pollingTimer);
  pollingTimer = null;
}

function clearTimers() {
  clearPolling();
  clearInterval(etaTimer);
  etaTimer = null;
}

async function pollStatus(histIdx) {
  if (!currentJobId) return;
  try {
    const res  = await fetch(`${API_BASE}/api/status/${currentJobId}`);
    const data = await res.json();

    if (jobHistory[histIdx]) {
      jobHistory[histIdx].status = data.status;
      if (data.status === 'processing') jobHistory[histIdx].pct = 55;
    }

    if (data.status === 'completed') {
      clearTimers();
      if (jobHistory[histIdx]) {
        jobHistory[histIdx].pct    = 100;
        jobHistory[histIdx].result = data.result;
        jobHistory[histIdx].status = 'completed';
      }
      renderDashboard();
      navigate('dashboard');
      // 짧은 딜레이 후 결과 뷰로
      setTimeout(() => showResults(data.result, jobHistory[histIdx]?.filename || 'video.mp4'), 300);

    } else if (data.status === 'failed') {
      clearTimers();
      if (jobHistory[histIdx]) jobHistory[histIdx].status = 'failed';
      alert(data.error || '분석 중 오류가 발생했습니다.');
      navigate('upload');
    }
  } catch (err) {
    console.error('폴링 오류:', err);
  }
}

// ================================================================
// ETA 카운트다운
// ================================================================
function startEtaCountdown() {
  clearInterval(etaTimer);
  let sec = 120;
  const el = document.getElementById('loadingEta');
  function tick() {
    if (!el) return;
    el.textContent = sec > 60 ? `약 ${Math.ceil(sec/60)}분` : `약 ${sec}초`;
    if (sec > 0) sec -= 5;
  }
  tick();
  etaTimer = setInterval(tick, 5000);
}

// ================================================================
// 대시보드 렌더링
// ================================================================
function renderDashboard() {
  const list       = document.getElementById('historyList');
  const emptyState = document.getElementById('emptyState');
  if (!list) return;

  if (!jobHistory.length) {
    list.innerHTML           = '';
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';
  list.innerHTML = [...jobHistory].reverse().map((job, i) => {
    const realIdx = jobHistory.length - 1 - i;
    const pct     = job.pct || 0;
    const pctText = job.status === 'completed' ? '100% Complete'
                  : job.status === 'failed'    ? '분석 실패'
                  : `${pct}% Complete`;
    const done    = job.status === 'completed';
    return `
      <div class="history-card">
        <div class="h-thumb">🎬</div>
        <div class="h-info">
          <div class="h-name">${escapeHtml(job.filename)}</div>
          <div class="h-bar-wrap"><div class="h-bar" style="width:${pct}%"></div></div>
          <div class="h-pct">${pctText}</div>
        </div>
        <button class="btn-result${done ? ' done' : ''}"
          ${done ? '' : 'disabled'}
          onclick="onHistoryClick(${realIdx})">결과 보기</button>
      </div>`;
  }).join('');
}

function onHistoryClick(idx) {
  const job = jobHistory[idx];
  if (!job?.result) return;
  currentJobId = job.jobId;
  showResults(job.result, job.filename);
}

// ================================================================
// 결과 표시
// ================================================================
function showResults(result, filename) {
  const fnEl = document.getElementById('resultFileName');
  if (fnEl) fnEl.textContent = filename || 'video.mp4';

  renderScore(result);
  renderThumbnails(result.thumbnails || []);
  renderTitles(result.titles    || []);
  renderReport(result.report    || '');
  navigate('results');
}

function bindResultsEvents() {
  document.getElementById('sendEmailBtn')?.addEventListener('click', sendReport);
}

// ================================================================
// 점수 게이지
// ================================================================
function renderScore(result) {
  const score = result.score || {};
  const total = score.total || 0;

  // 게이지: r=50 → 둘레 ≈ 314
  const circ = 2 * Math.PI * 50;
  const dash  = (total / 100) * circ;
  const fill  = document.getElementById('gaugeFill');
  if (fill) {
    fill.setAttribute('stroke-dasharray', `0 ${circ}`);
    requestAnimationFrame(() => {
      fill.style.transition = 'stroke-dasharray 1.2s ease';
      fill.setAttribute('stroke-dasharray', `${dash} ${circ}`);
    });
  }

  animateCount('gaugeScore', 0, total, 1200);

  const label = document.getElementById('gaugeLabel');
  if (label) label.textContent =
    total >= 80 ? 'High Viral Potential' :
    total >= 60 ? 'Good Potential'       : 'Needs Improvement';

  const vs = document.getElementById('valVisual');
  const ks = document.getElementById('valKeyword');
  const ts = document.getElementById('valTopic');
  if (vs) vs.textContent = score.visual_score  ?? '--';
  if (ks) ks.textContent = score.keyword_score ?? '--';
  if (ts) ts.textContent = score.topic_score   ?? '--';

  const cvEl = document.getElementById('cmtVisual');
  const ckEl = document.getElementById('cmtKeyword');
  const ctEl = document.getElementById('cmtTopic');
  if (cvEl) cvEl.textContent = score.visual_comment  || '';
  if (ckEl) ckEl.textContent = score.keyword_comment || '';
  if (ctEl) ctEl.textContent = score.topic_comment   || '';

  const cmt = document.getElementById('scoreComment');
  if (cmt) cmt.textContent = score.comment || '';

  const bias   = score.bias_metrics || {};
  const biasEl = document.getElementById('biasMetrics');
  if (biasEl) biasEl.innerHTML = [
    `<span class="bias-chip">Coverage ${bias.coverage ?? '-'}%</span>`,
    `<span class="bias-chip">Novelty ${bias.novelty ?? '-'}%</span>`,
    bias.bias_warning ? `<span class="bias-chip" style="color:#f59e0b">⚠ ${bias.bias_warning}</span>` : '',
  ].join('');

  const meta = document.getElementById('fileInfo');
  if (meta) meta.innerHTML = [
    `카테고리: ${result.category || '-'}`,
    `발화속도: ${result.wpm || '-'} WPM`,
    `프레임: ${result.frame_count || '-'}개`,
    result.analyzed_at ? `분석: ${new Date(result.analyzed_at).toLocaleString('ko-KR')}` : '',
  ].filter(Boolean).map(s => `<span>${s}</span>`).join('');
}

function animateCount(id, from, to, ms) {
  const el = document.getElementById(id);
  if (!el) return;
  const t0 = performance.now();
  const step = now => {
    const t = Math.min((now - t0) / ms, 1);
    el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - t, 3)));
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// ================================================================
// 썸네일
// ================================================================
function renderThumbnails(thumbnails) {
  const grid = document.getElementById('thumbnailGrid');
  if (!grid) return;
  if (!thumbnails.length) {
    grid.innerHTML = '<p style="color:#999;font-size:13px">썸네일 생성 결과가 없습니다.</p>';
    return;
  }
  const subtitles = [
    '모바일 피드에서 높은 클릭률이 예상됩니다',
    '교육/정보 채널에 최적화된 스타일입니다',
    '감성적 공감을 유도하여 시청 지속률을 높입니다',
  ];
  grid.innerHTML = thumbnails.map((t, i) => {
    const imgHtml = t.url
      ? `<img src="${API_BASE}${t.url}" alt="${escapeHtml(t.style||'')}" loading="lazy" />`
      : `<div class="thumb-img-placeholder">🎨</div>`;
    const dlHref = t.url ? `${API_BASE}${t.url}` : '#';
    const disabled = !t.url ? ' style="opacity:.4;pointer-events:none"' : '';
    return `
      <div class="thumb-card">
        <div class="thumb-img-wrap">${imgHtml}</div>
        <div class="thumb-info">
          <div class="thumb-style">${escapeHtml(t.style||'')}</div>
          <div style="font-size:11px;color:#aaa;margin-bottom:6px">${subtitles[i]||''}</div>
          <a href="${dlHref}" download class="thumb-download"${disabled}>
            <svg width="11" height="11" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd" transform="scale(1,-1) translate(0,-20)"/>
            </svg>
            다운로드
          </a>
        </div>
      </div>`;
  }).join('');
}

// ================================================================
// 제목 추천
// ================================================================
function renderTitles(titles) {
  const list = document.getElementById('titlesList');
  if (!list) return;
  if (!titles.length) {
    list.innerHTML = '<p style="color:#999;font-size:13px">제목 추천 결과가 없습니다.</p>';
    return;
  }
  list.innerHTML = titles.map((t, i) => `
    <div class="title-item">
      <span class="t-num">추천 ${i+1}</span>
      <div class="t-content">
        <div class="t-title">${escapeHtml(t.title||'')}</div>
        <div class="t-why">Reason: ${escapeHtml(t.why||'')}</div>
      </div>
      <button class="t-copy" title="복사" onclick="copyText('${escapeHtml(t.title||'')}', this)">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
          <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
          <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
        </svg>
      </button>
    </div>`).join('');
}

function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    btn.style.color = '#22c55e';
    setTimeout(() => { btn.style.color = ''; }, 1500);
    showToast('복사됨!');
  });
}

function showToast(msg) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 1800);
}

// ================================================================
// 리포트
// ================================================================
function renderReport(text) {
  const el = document.getElementById('reportBody');
  if (!el) return;
  el.innerHTML = (typeof marked !== 'undefined') ? marked.parse(text) : text.replace(/\n/g, '<br>');
}

// ================================================================
// 이메일 발송
// ================================================================
async function sendReport() {
  const email    = document.getElementById('emailInput').value.trim();
  const statusEl = document.getElementById('emailStatus');

  if (!email)        { setStatus(statusEl, '이메일 주소를 입력해주세요.', 'error'); return; }
  if (!currentJobId) { setStatus(statusEl, '분석 결과가 없습니다.',       'error'); return; }

  setStatus(statusEl, '발송 중...', '');

  const fd = new FormData();
  fd.append('job_id', currentJobId);
  fd.append('email',  email);

  try {
    const res  = await fetch(`${API_BASE}/api/send-report`, { method: 'POST', body: fd });
    const data = await res.json();
    setStatus(statusEl,
      data.status === 'sent' ? `✅ ${data.message}` : `❌ ${data.message}`,
      data.status === 'sent' ? 'success' : 'error');
  } catch (err) {
    setStatus(statusEl, `❌ 발송 실패: ${err.message}`, 'error');
  }
}

function setStatus(el, msg, cls) {
  if (!el) return;
  el.textContent = msg;
  el.className   = 'email-status' + (cls ? ` ${cls}` : '');
}

// ================================================================
// 유틸
// ================================================================
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// inline onclick에서 사용할 수 있도록 전역 노출
window.navigate       = navigate;
window.onHistoryClick = onHistoryClick;
window.copyText       = copyText;
window.showToast      = showToast;
