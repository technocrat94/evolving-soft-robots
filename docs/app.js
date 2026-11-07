'use strict';
/* Soft Robot Lab — interactive site. Physics lives in sim.js (verified against Python). */
const $ = id => document.getElementById(id);
const $$ = sel => Array.from(document.querySelectorAll(sel));
const MAT = ['transparent', '#5d6c67', '#c9d3cd', '#f39c35', '#88ccee'];
const STROKE = '#0b1211';
const ORANGE = '#f39c35', BLUE = '#88ccee', VIOLET = '#b9a3ff', GREEN = '#7ad6a4', DIM = '#5f7069';
const ERA = {1: '#5f7069', 30: '#88ccee', 60: '#f39c35'};

/* ---------------- i18n ---------------- */
const I18N = {
  en: {},
  zh: {
    navEvolution: '演化', navRace: '競速', navHow: '原理', navBuild: '動手做', navExperiments: '實驗',
    hudSpecimen: '樣本',
    heroEyebrow: '質點彈簧物理 × 基因演算法',
    heroTitle: '沒有人教它走路。',
    heroLead: '這個頁面上的每一個身體、每一種節奏，都是在一個從零寫成的物理模擬器裡，由演化自己找到的。沒有預先設計任何步態，只有一個目標：往右前進。',
    heroCta: '看它怎麼演化 ↓',
    stat1: '次訓練回合', stat2: '倍於第 1 代的距離', stat3: '模擬 5 秒內前進', stat4: '次數值爆炸',
    exEyebrow: '逐個檢查點看演化', exTitle: '拖動滑桿，穿越 60 個世代。',
    exLead: '拖動滑桿，載入任一檢查點的最佳機器人。左邊是它的基因（身體結構），右邊是這組基因實際跑出來的樣子。',
    generation: '世代', autoEvolve: '▶ 自動演化', replay: '↺ 重播', genome: '基因 · 身體結構',
    distance: '距離', cells: '格數', actuators: '致動器',
    fitnessLabel: '適應度歷史 · 100 隻 × 60 代', best: '最佳', average: '平均', disq: '傾倒淘汰數',
    fitnessCaption: '進步不是平滑的。最佳距離在第 30 到 41 代停在 14.33 m，之後才突破——這種「間斷式」的進步，跟生物演化很像。把游標移到圖上可以查看每一代的數據。',
    raceEyebrow: '幽靈競速', raceTitle: '同樣的物理，同樣的 5 秒，誰會贏？',
    raceLead: '讓三個世代比賽，或讓開迴路和回授機器人在崎嶇地面、被推的情況下對決。唯一的差別，是演化寫進牠們基因裡的東西。',
    startRace: '▶ 開始比賽', reset: '重設',
    howEyebrow: '背後的原理', howTitle: '由彈簧與天擇組成。',
    materialHint: '點選材質，查看對應顏色與動作示意。',
    materialDescriptions: ['深灰色：硬材質，彈簧較硬（k = 1800），不主動改變自然長度。', '淺灰色：軟材質，彈簧較軟（k = 250），不主動改變自然長度。', '橘色 ↔：水平肌肉，主動改變水平彈簧的自然長度（k = 500）。', '藍色 ↕：垂直肌肉，主動改變垂直彈簧的自然長度（k = 500）。'],
    physicsLabel: 'A · 物理', physicsTitle: '每一格都是四個質點加六根彈簧',
    physicsText: '相鄰的格子共用頂點，所以整隻機器人是一張相連的網格。致動器格子會用 sin 波改變彈簧的自然長度；地面以摩擦力反推。積分方法為半隱式歐拉法，Δt = 2 ms。',
    gaLabel: 'B · 演化', gaTitle: '一個獎勵「走得遠」的迴圈',
    ga1: '評估', ga1t: '每隻機器人模擬 5 秒，量測前進距離。',
    ga2: '選擇', ga2t: '前 20% 直接保留；用錦標賽法挑選父母。',
    ga3: '交配', ga3t: '子代從父母各繼承一塊整列或整行。',
    ga4: '突變', ga4t: '隨機改變幾個格子、相位與頻率 ω。',
    gaText: '基因是一個 5 × 5 的材料網格，加上每一格的相位和一個全域頻率——身體和行為一起演化。',
    guardLabel: 'C · 防作弊', guardTitle: '演化會鑽任何漏洞',
    guardText: '早期實驗發現倒下後滑行可獲得高分，因此加入兩項檢核：傾角超過 30° 且持續 0.2 秒得零分，並將最佳個體關閉致動器重跑，量測被動沉降。這些檢核抑制取巧，但不保證動作符合真實物理。',
    guard1: '傾倒規則', guard2: '冠軍關掉肌肉後的位移',
    buildEyebrow: '換你試試', buildTitle: '你能贏過演化嗎？',
    buildLead: '點格子切換材料，選開迴路節奏或裝上演化出的回授大腦，再到平地、崎嶇地面或被推的情況下測試你的設計。',
    presets: '預設', pDemo: '步行者', pFb: '🧠 回授冠軍', pGen1: '第 1 代', pGen60: '冠軍', pRandom: '🎲 隨機', pClear: '清空',
    frequency: '頻率 ω', rhythm: '節奏',
    rSync: '所有格子同步', rWave: '行進波（前 → 後）', rAlt: '上下列交替', rEvolved: '演化出的相位（僅限預設）',
    ghostToggle: '跟冠軍的幽靈比賽', run: '▶ 執行', share: '🔗 複製連結',
    expEyebrow: '實驗', expTitle: '四個實驗，誠實的答案。',
    expLead: '一次漂亮的結果證明不了什麼。這些實驗全部用 5 到 6 個隨機種子重複，並照實呈現數據——包括數據和假設不一致的時候。',
    tabA: 'A · 身體 vs. 大腦', tabB: 'B · 回授有用嗎？', hyp: '假設',
    hypA: '同時演化身體和控制器，會比只演化其中一個更好。',
    ablationCaption: '每一代最佳距離的平均值，每種條件 5 個種子，60 隻 × 40 代。陰影 = ±1 標準差。點擊圖例可以切換顯示。',
    vPartial: '未獲證實',
    findA: '同時演化找到了全場最好的單一機器人（20.77 m），但也是最不穩定的。只在一個人工設計的好身體上演化控制器，結果最穩定。只有 5 個種子，經 Holm 校正後沒有任何差異達到統計顯著。',
    takeA: '結論：搜尋空間變大，上限變高、下限也變低。同時演化可能需要更多運算預算，才能每次都收斂。',
    hypB: '有感測器的閉迴路神經網路控制器，面對崎嶇地面和外力推擠時，會比開迴路 sin 波控制器更強健。',
    mEligible: '有效距離', mRaw: '原始位移',
    robustCaption: '長條 = 5 個種子的平均，點 = 各個種子。兩種控制器都驅動同一個冠軍身體，而且只在平地上訓練，再直接拿去測試。傾倒的機器人有效距離記為 0。',
    liveTest: '即時壓力測試', eFlat: '平地', eRough: '崎嶇地面', ePush: '向後推力',
    openLoop: '開迴路 sin 波', closedLoop: '閉迴路神經網路',
    vNo: '僅平地訓練時，假說未獲支持',
    findB: 'B 的原始測試中，平地訓練神經控制器的平均表現較差，五個最佳個體皆在崎嶇地形翻倒。C 測試多變環境訓練是否改變結果：保留崎嶇測試成功率由 8% 提升至 94%，但尚未在統計上確立回授特有的優勢。',
    takeB: '回授提供資訊；抗擾動需要控制器經過適當設計或訓練來使用資訊。請看 C 的隨機環境訓練與純時鐘消融。',
    modeEras: '三個世代', modeControl: '開迴路 vs. 回授',
    raceTitle2: '', brainLabel: '大腦', brainSine: '開迴路節奏', brainFeedback: '回授大腦 🧠',
    brainNote: '固定的 sin 波——機器人從不看感測器。',
    brainNoteFb: '共同演化的回授網路（種子 42）：每一格讀取傾斜、角速度、垂直速度、前後腳著地與時鐘訊號，再決定怎麼出力。它是為自己的身體演化的，放到你的身體上不一定好用——試試看！',
    terrainLabel: '測試地面',
    raceNoteEras: '第 1、30、60 代的最佳機器人（開迴路）。',
    raceNoteControl: '橘＝共同演化開迴路；紫＝共同演化回授；灰＝只在平地訓練、借用身體的回授。三者都用種子 42，事先決定。一場比賽只是一個樣本：在這塊崎嶇地形上平地訓練的剛好贏了，但被推時會翻倒；而在全部 10 塊保留崎嶇地形上，它只有 8% 的機率不翻倒（見下方 C、D 實驗）。',
    tabD: 'D · 從零開始共同演化',
    hypD: 'B 和 C 分頁借用的是搭配 sin 波演化出來的身體。如果讓每種控制器從零開始演化自己的身體，閉迴路回授應該會贏。',
    coevoCaption: '長條 = 6 個配對種子（42–47）的平均，點 = 各個種子，誤差線 = ±1 標準差。兩種條件都從隨機身體開始，用 C 分頁的領域隨機化訓練（60 隻 × 40 代，每隻 4 個情境），並接受相同的保留測試集。',
    bodiesLabel: '12 個優勝者的身體', coevoVerdict: '未獲支持——平手',
    findD: '起點公平之後，兩種控制器幾乎都不會翻倒（保留測試成功率 98.4% vs 99.2%）。開迴路平均走得比較遠（11.79 vs 10.19 m），但不同種子之間的差異大得多（標準差 4.01 vs 1.05 m）。兩項差異都不顯著。',
    takeD: '拿掉身體的偏差後，C 分頁裡的存活差距消失了：回授的成功率從 88.6%（借來的身體）升到 99.2%（自己演化的身體）。回授用一點速度換來了穩定性。',
    coevoCaveat: '兩者的成功率都接近 100%，代表這個測試集太簡單、分不出高下；下一步需要更難或訓練分布以外的地形。回授的優勝者關掉肌肉後位移較大（0.26 vs 0.02 m）。只有 6 個種子，兩種條件的參數數量也不同。',
    coevoSine: '共同演化・開迴路', coevoFeedback: '共同演化・回授',
    coevoLiveNote: '兩邊都用種子 42，依照和 C 分頁相同的慣例事先決定。在這塊崎嶇地形上回授走得比較遠——跟平均結果相反，所以只當作示範。',
    tabC: 'C · 領域隨機化', compareLeft: '控制器 1', compareRight: '控制器 2',
    seeDomain: '查看 C · 領域隨機化 →', tryDomain: '即時比較這些控制器 →',
    stressNote: '即時個體皆為種子 42，使用 C 的第一個保留崎嶇／推力設定；上方 B 圖表保留原始測試設定。單次結果可能不同於五個種子的平均。',
    hypC: '當控制器在回授可能有用的多變環境中訓練，回授能帶來幫助。',
    mSuccess: '成功率', heldoutSummary: '保留測試 · 全部 21 次回合',
    domainCaption: '五個最佳化種子的平均 ± 樣本標準差。每個最佳個體接受相同的平地、10 個崎嶇地形與 10 組推力測試。成功表示通過傾倒規則，不考慮位移大小。',
    domainSetup: '60 個體 × 40 代。每個體在四回合訓練：平地、兩個新崎嶇地形與隨機向後推力。環境每代更新，同一種子的所有個體與控制器組別共用環境。純時鐘網路將五個回授輸入歸零。',
    domainVerdict: '結果有潛力，但未達顯著',
    findC: '隨機環境回授達 11.26 公尺、88.57% 成功率；平地訓練神經為 5.95 公尺、40.00%。觀察平均值亦高於純時鐘，但預先規劃的 Holm 校正檢定皆不顯著。隨機環境正弦的總位移更高（12.28 公尺）。',
    takeC: '針對擾動訓練很重要。回授的觀察崎嶇成功率最高（94%），正弦則較能應付推力（98% vs 82%）。結果支持檢驗訓練分布，不代表回授普遍較優。',
    domainCaveat: '五個配對種子的檢定解析度粗，四項檢定共用 Holm 校正。隨機環境訓練回合預算為 B 的四倍。新測試樣本仍來自訓練分布，尚未確立廣泛轉移能力。',
    domainCond: {flat_sine:'平地 · 正弦',flat_neural:'平地 · 神經',randomized_sine:'隨機 · 正弦',randomized_neural_feedback:'隨機 · 回授',randomized_neural_clock_only:'隨機 · 純時鐘'},
    thDistance:'距離 (m)',thSuccess:'成功率 (%)',statDistance:'位移',statSuccess:'成功率',rawLive:'原始位移（1 / 2）',
    compareClock:'回授 vs 純時鐘',compareSine:'回授 vs 正弦',
    valEyebrow: '驗證與限制', valTitle: '怎麼知道這是真的？',
    val1: '次不穩定的訓練回合（NaN 或爆炸）', val2: '這個網頁的 JavaScript 物理與 Python 模擬器之間的相對誤差',
    val3: '個自動化單元測試', val4: '個隨機環境訓練最佳個體由存檔重現（容差 10⁻¹²）',
    limLabel: '已知限制',
    lim1: '只有 2D，而且沒有對應任何真實軟材料做校正。', lim2: '沒有自我碰撞：肢體可能穿過身體。',
    lim3: '冠軍的頻率頂到上限（6 rad/s）——演化還想動得更快。', lim4: 'D 測試 10 個新崎嶇地形與 10 組推力，皆來自訓練分布；五個種子與理想感測器仍限制泛化證據。',
    footer: '由彈簧、天擇和一點好奇心組成——一位機械系學生的作品。', source: '原始碼與完整 README ↗',
    // dynamic strings
    rank: ['冠軍', '第二', '第三'], gen: g => `第 ${g} 代`, fell: '翻倒', invalid: '無效的設計：所有格子要用邊相連，而且至少要有一個致動器（橘或藍）。',
    ready: '準備好了，按「執行」。', running: '模擬中…', copied: '連結已複製！', copyFail: '無法複製，請手動複製網址列。',
    beat: '你贏過了冠軍！🎉', close: '冠軍的', youFell: '你的機器人翻倒了，有效距離 = 0', ofChamp: '的冠軍距離', evolvedOnly: '「演化出的相位」只適用於預設的機器人。',
    tipGen: '第 {g} 代', tipBest: '最佳', tipAvg: '平均', tipDisq: '淘汰',
    cond: {co_evolution: '同時演化', control_only: '只演化控制器', body_only: '只演化身體'},
    thCond: '條件', thMean: '平均 ± 標準差', thBest: '最佳',
    envName: {flat: '平地', rough: '崎嶇', push: '推擠'}, ctrl: {open_loop: '開迴路', closed_loop: '閉迴路'},
    pushNow: '推！', mats: ['空', '硬', '軟', '水平肌肉', '垂直肌肉']
  }
};
const EN_DYN = {
  materialDescriptions: ['Dark grey: rigid material, stiffer springs (k = 1800); no active rest-length change.', 'Light grey: soft material, softer springs (k = 250); no active rest-length change.', 'Orange ↔: horizontal muscle actively changes horizontal spring rest lengths (k = 500).', 'Blue ↕: vertical muscle actively changes vertical spring rest lengths (k = 500).'],
  brainNoteFb: 'The co-evolved feedback network (seed 42): every cell reads tilt, angular velocity, vertical velocity, front/back foot contact and a clock, then decides how hard to push. It evolved for its own body, so it may struggle on yours — try it!',
  raceNoteEras: 'Best robot of generations 1, 30 and 60 (all open-loop).',
  raceNoteControl: 'Orange = co-evolved open-loop · violet = co-evolved feedback · grey = feedback trained on flat ground only, with a borrowed body. All seed 42, fixed in advance. One race is one sample: on this rough profile the flat-trained robot happens to win, but it falls under the push — and across all 10 held-out rough profiles it survives only 8% of the time (tabs C and D below).',
  domainCond: {flat_sine:'Flat · sine',flat_neural:'Flat · neural',randomized_sine:'Randomized · sine',randomized_neural_feedback:'Randomized · feedback',randomized_neural_clock_only:'Randomized · clock only'},
  thDistance:'Distance (m)',thSuccess:'Success (%)',statDistance:'distance',statSuccess:'success',rawLive:'Raw displacement (1 / 2)',
  compareClock:'Feedback vs clock-only',compareSine:'Feedback vs sine',
  rank: ['1st', '2nd', '3rd'], gen: g => `Gen ${g}`, fell: 'fell', invalid: 'Invalid design: every cell must connect by an edge, and you need at least one actuator (orange or blue).',
  ready: 'Ready — press Run.', running: 'Simulating…', copied: 'Link copied!', copyFail: 'Could not copy — copy the address bar instead.',
  beat: 'You beat the champion! 🎉', close: 'of the champion', youFell: 'Your robot tipped over — eligible distance = 0', ofChamp: 'of the champion’s distance', evolvedOnly: '“Evolved phases” only applies to preset robots.',
  tipGen: 'Gen {g}', tipBest: 'best', tipAvg: 'avg', tipDisq: 'disq.',
  cond: {co_evolution: 'Co-evolution', control_only: 'Controller only', body_only: 'Body only'},
  thCond: 'Condition', thMean: 'Mean ± SD', thBest: 'Best',
  envName: {flat: 'Flat', rough: 'Rough', push: 'Push'}, ctrl: {open_loop: 'Open-loop', closed_loop: 'Closed-loop'},
  pushNow: 'PUSH!', mats: ['Empty', 'Rigid', 'Soft', 'H-muscle', 'V-muscle']
};
let lang = 'en';
const t = k => (lang === 'zh' && I18N.zh[k] !== undefined) ? I18N.zh[k] : (EN_DYN[k] !== undefined ? EN_DYN[k] : (I18N.en[k] || k));
function captureEnglish() { $$('[data-i18n]').forEach(el => { I18N.en[el.dataset.i18n] = el.innerHTML; }); }
function applyLang() {
  document.documentElement.lang = lang === 'zh' ? 'zh-Hant' : 'en';
  $$('[data-i18n]').forEach(el => { el.innerHTML = t(el.dataset.i18n); });
  $('language').textContent = lang === 'zh' ? 'EN' : '繁中';
  listeners.forEach(f => f());
}
const listeners = [];
const fmt = (v, d = 2) => (v >= 0 ? '+' : '') + v.toFixed(d) + ' m';

/* ---------------- rendering ---------------- */
function fitCanvas(canvas) {
  const r = canvas.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.max(1, Math.round(r.width * dpr)), h = Math.max(1, Math.round(r.height * dpr));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  return dpr;
}
function drawScene(canvas, entries, view) {
  const dpr = fitCanvas(canvas), ctx = canvas.getContext('2d'), W = canvas.width, H = canvas.height;
  if(view.fitHeight!==false){
    const highest=Math.max(0,...entries.flatMap(e=>e.sim?e.sim.p.map(p=>p[1]):[]));
    const width=Math.max(view.width,(highest+.9)*(W/H)/(view.ground||.8));
    view={...view,left:view.left-(width-view.width)/2,width};
  }
  const scale = W / view.width, left = view.left, groundY = H * (view.ground || 0.8);
  const S = (x, y) => [(x - left) * scale, groundY - y * scale];
  ctx.clearRect(0, 0, W, H);
  if (view.bg !== false) { ctx.fillStyle = view.bg || '#0e1715'; ctx.fillRect(0, 0, W, H); }
  // grid
  ctx.lineWidth = 1 * dpr; ctx.strokeStyle = 'rgba(143,163,155,.07)';
  for (let x = Math.floor(left); x <= left + view.width + 1; x++) { const [sx] = S(x, 0); ctx.beginPath(); ctx.moveTo(sx, 0); ctx.lineTo(sx, groundY); ctx.stroke(); }
  for (let y = 1; y * scale < groundY; y++) { const sy = groundY - y * scale; ctx.beginPath(); ctx.moveTo(0, sy); ctx.lineTo(W, sy); ctx.stroke(); }
  // ground
  const ref = entries[0] && entries[0].sim;
  ctx.beginPath();
  const step = view.width / 200;
  for (let x = left - 1; x <= left + view.width + 1; x += step) { const gy = ref && ref.options.terrain === 'rough' ? ref.ground(x)[0] : 0; const [sx, sy] = S(x, gy); x === left - 1 ? ctx.moveTo(sx, sy) : ctx.lineTo(sx, sy); }
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fillStyle = '#0a100f'; ctx.fill();
  ctx.strokeStyle = '#3b524b'; ctx.lineWidth = 2 * dpr; ctx.stroke();
  // ticks
  if (view.ticks !== false) {
    ctx.fillStyle = DIM; ctx.font = `${11 * dpr}px ui-monospace,Menlo,monospace`; ctx.textAlign = 'center';
    const every = view.width > 18 ? 2 : 1;
    for (let x = Math.ceil(left); x <= left + view.width; x++) { if (x % every) continue; const [sx] = S(x, 0); ctx.fillRect(sx - dpr / 2, groundY + 4 * dpr, dpr, 6 * dpr); ctx.fillText(x + (x === 0 ? ' m' : ''), sx, groundY + 24 * dpr); }
  }
  if (view.finish !== undefined) {
    const [fx] = S(view.finish, 0);
    ctx.save(); ctx.setLineDash([6 * dpr, 6 * dpr]); ctx.strokeStyle = 'rgba(243,156,53,.5)'; ctx.lineWidth = 1.5 * dpr;
    ctx.beginPath(); ctx.moveTo(fx, groundY * .12); ctx.lineTo(fx, groundY); ctx.stroke(); ctx.restore();
  }
  for (const e of entries) {
    const sim = e.sim; if (!sim) continue;
    // trail
    if (e.trail && e.trail.length > 1) {
      ctx.beginPath(); e.trail.forEach(([x, y], i) => { const [sx, sy] = S(x, y); i ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy); });
      ctx.strokeStyle = e.trailColor || 'rgba(243,156,53,.35)'; ctx.lineWidth = 2 * dpr; ctx.stroke();
    }
    ctx.globalAlpha = e.alpha ?? 1;
    for (const poly of sim.polygons) {
      ctx.beginPath(); poly.ids.forEach((id, i) => { const [x, y] = S(sim.p[id][0], sim.p[id][1]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.closePath();
      if (e.outline) { ctx.strokeStyle = e.outline; ctx.lineWidth = 2 * dpr; ctx.fillStyle = e.outlineFill || 'rgba(185,163,255,.10)'; ctx.fill(); ctx.stroke(); }
      else { ctx.fillStyle = MAT[poly.m]; ctx.fill(); ctx.strokeStyle = STROKE; ctx.lineWidth = 1.6 * dpr; ctx.stroke(); }
    }
    ctx.globalAlpha = 1;
    if (e.label) {
      const top = Math.max(...sim.p.map(p => p[1])), cx = sim.mean(0), [lx, ly] = S(cx, top);
      ctx.font = `600 ${12 * dpr}px ui-monospace,Menlo,monospace`; ctx.textAlign = 'center';
      ctx.fillStyle = e.labelColor || '#e8efe9'; ctx.fillText(e.label + (sim.fell ? ' ✕' : ''), lx, ly - (10 + (e.labelDy || 0)) * dpr);
    }
  }
  if (view.flash) { ctx.fillStyle = 'rgba(255,107,91,.9)'; ctx.font = `700 ${18 * dpr}px ui-monospace,Menlo,monospace`; ctx.textAlign = 'center'; ctx.fillText(view.flash, W / 2, H * .14); }
}

/* ---------------- animation runner ---------------- */
const players = new Set();
class Player {
  constructor(canvas, opts) { this.canvas = canvas; this.o = opts; this.playing = false; this.acc = 0; this.visible = true; this.reset(); players.add(this);
    new IntersectionObserver(es => { this.visible = es[0].isIntersecting; }, {threshold: 0.05}).observe(canvas); }
  reset() { this.entries = this.o.make(); this.acc = 0; this.frame = 0; this.draw(); this.o.onTick && this.o.onTick(this); }
  get done() { return this.entries.every(e => !e.sim || e.sim.done); }
  tick(dt) {
    if (!this.playing || !this.visible) return;
    this.acc += dt; const DT = DATA.C.DT; let n = 0;
    while (this.acc >= DT && n < 40) { for (const e of this.entries) if (e.sim && !e.sim.done) { e.sim.step(); } this.acc -= DT; n++; }
    this.frame++;
    if (this.frame % 2 === 0) for (const e of this.entries) if (e.trail && e.sim) { e.trail.push([e.sim.mean(0), Math.max(0, e.sim.mean(1))]); if (e.trail.length > 400) e.trail.shift(); }
    this.draw(); this.o.onTick && this.o.onTick(this);
    if (this.done) { this.playing = false; this.o.onDone && this.o.onDone(this); }
  }
  draw() { if (!this.visible && this.frame) return; drawScene(this.canvas, this.entries, this.o.view(this)); }
  play() { if (this.done) this.reset(); this.playing = true; }
}
let last = 0;
function loop(now) { const dt = last ? Math.min((now - last) / 1000, 0.05) : 0; last = now; players.forEach(p => p.tick(dt)); requestAnimationFrame(loop); }

/* ---------------- data ---------------- */
const DATA = {};
const newSim = (robot, opts = {}) => new SoftRobot.Simulation(robot, DATA.C, opts);
const followView = (sim, width, extra = {}) => { const cx = sim ? sim.mean(0) : 0; return {left: cx - width * 0.45, width, ...extra}; };
const viewWidth = (canvas, desktop, mobile) => (canvas.getBoundingClientRect().width < 560 ? mobile : desktop);

/* ---------------- hero ---------------- */
function initHero() {
  const champ = DATA.cp.at(-1);
  const p = new Player($('hero-canvas'), {
    make: () => [{sim: newSim(champ), trail: []}],
    view: pl => { const s = pl.entries[0].sim, w = viewWidth(pl.canvas, 26, 11), r = pl.canvas.getBoundingClientRect().width;
      const cx = s.mean(0), offset = r < 720 ? 0.55 : 0.68; return {left: cx - w * offset, width: r < 720 ? 14 : w, ground: r < 720 ? 0.36 : 0.78, bg: '#0b1211',fitHeight:false}; },
    onTick: pl => { const s = pl.entries[0].sim; $('hero-time').textContent = s.time.toFixed(2); $('hero-x').textContent = (s.distance >= 0 ? '+' : '') + s.rawDistance.toFixed(2); },
    onDone: pl => setTimeout(() => { pl.reset(); pl.play(); }, 900)
  });
  p.play();
}

/* ---------------- stats counter ---------------- */
function initCounters() {
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return; io.unobserve(e.target);
    const el = e.target, target = +el.dataset.count, dec = +(el.dataset.decimals || 0), suf = el.dataset.suffix || '', t0 = performance.now();
    const step = now => { const k = Math.min((now - t0) / 1400, 1), v = target * (1 - Math.pow(1 - k, 3));
      el.textContent = (dec ? v.toFixed(dec) : Math.round(v).toLocaleString('en-US')) + suf; if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }), {threshold: .4});
  $$('[data-count]').forEach(el => io.observe(el));
}

/* ---------------- blueprint ---------------- */
function blueprint(svg, body) {
  const ns = 'http://www.w3.org/2000/svg'; svg.replaceChildren();
  for (let r = 0; r < 5; r++) for (let c = 0; c < 5; c++) {
    const m = body[r]?.[c] || 0, rect = document.createElementNS(ns, 'rect');
    rect.setAttribute('x', c + .06); rect.setAttribute('y', r + .06); rect.setAttribute('width', .88); rect.setAttribute('height', .88); rect.setAttribute('rx', .1);
    rect.setAttribute('fill', m ? MAT[m] : 'rgba(143,163,155,.06)'); if (!m) { rect.setAttribute('stroke', 'rgba(143,163,155,.15)'); rect.setAttribute('stroke-width', .02); }
    svg.append(rect);
  }
}

/* ---------------- 01 explorer ---------------- */
function initExplorer() {
  const cps = DATA.cp; let idx = cps.length - 1, auto = null;
  $('gen-ticks').innerHTML = cps.map(c => `<span>${c.generation}</span>`).join('');
  const player = new Player($('explorer-canvas'), {
    make: () => [{sim: newSim(cps[idx]), trail: [], trailColor: 'rgba(243,156,53,.3)'}],
    view: pl => followView(pl.entries[0].sim, viewWidth(pl.canvas, 15, 11), {ground: .78}),
    onTick: pl => { const s = pl.entries[0].sim; $('ex-time').textContent = s.time.toFixed(2) + ' s'; $('ex-dist').textContent = fmt(s.distance); },
    onDone: () => { if (auto) { idx = (idx + 1) % cps.length; select(idx, true); } }
  });
  function select(i, play = true) {
    idx = i; const cp = cps[i]; $('gen-slider').value = i; $('gen-label').textContent = cp.generation;
    blueprint($('blueprint'), cp.body);
    const flat = cp.body.flat(); $('spec-distance').textContent = cp.python_distance_m.toFixed(2) + ' m';
    $('spec-omega').textContent = cp.controller.omega.toFixed(2) + ' rad/s'; $('spec-cells').textContent = flat.filter(v => v).length + ' / 25';
    $('spec-act').textContent = flat.filter(v => v >= 3).length;
    chart.mark(cp.generation); player.reset(); if (play) player.play();
  }
  const chart = fitnessChart($('fitness-chart'), DATA.L.showcase_history, cps.map(c => c.generation), g => { const j = cps.findIndex(c => c.generation === g); if (j >= 0) { stopAuto(); select(j); } });
  const stopAuto = () => { auto = null; $('evolve-play').classList.remove('active'); $('evolve-play').innerHTML = t('autoEvolve'); };
  $('gen-slider').addEventListener('input', e => { stopAuto(); select(+e.target.value); });
  $('gen-replay').addEventListener('click', () => { player.reset(); player.play(); });
  $('evolve-play').addEventListener('click', () => { if (auto) return stopAuto(); auto = true; $('evolve-play').textContent = lang === 'zh' ? '■ 停止' : '■ Stop'; select(0); });
  listeners.push(() => { if (auto) $('evolve-play').textContent = lang === 'zh' ? '■ 停止' : '■ Stop'; chart.redraw(); });
  select(idx, false);
  const io = new IntersectionObserver(es => { if (es[0].isIntersecting) { player.play(); io.disconnect(); } }, {threshold: .3}); io.observe($('explorer-canvas'));
}

/* ---------------- SVG chart helpers ---------------- */
const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs = {}, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent && parent.append(e); return e; }
function axes(svg, W, H, m, xmax, ymax, xlabel, ylabel, yticks = 5, xticks = [1, 10, 20, 30, 40, 50, 60]) {
  const X = v => m.l + (v - 1) / (xmax - 1) * (W - m.l - m.r), Y = v => H - m.b - v / ymax * (H - m.t - m.b);
  for (let i = 0; i <= yticks; i++) { const v = ymax * i / yticks; el('line', {x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), stroke: '#22332f'}, svg); el('text', {x: m.l - 8, y: Y(v) + 4, 'text-anchor': 'end'}, svg).textContent = Math.round(v); }
  for (const g of xticks) if (g <= xmax) el('text', {x: X(g), y: H - m.b + 18, 'text-anchor': 'middle'}, svg).textContent = g;
  el('text', {x: W - m.r, y: H - 4, 'text-anchor': 'end'}, svg).textContent = xlabel;
  el('text', {x: m.l, y: m.t - 10, 'text-anchor': 'start'}, svg).textContent = ylabel;
  return {X, Y};
}
function tooltipFor(container) { let tip = container.querySelector('.tooltip'); if (!tip) { tip = document.createElement('div'); tip.className = 'tooltip'; container.append(tip); } return tip; }

function fitnessChart(container, hist, checkpoints, onPick) {
  let marked = 60;
  function redraw() {
    container.replaceChildren();
    const W = 1000, H = 320, m = {l: 44, r: 44, t: 26, b: 34}, svg = el('svg', {viewBox: `0 0 ${W} ${H}`}); container.append(svg);
    const {X, Y} = axes(svg, W, H, m, 60, 20, lang === 'zh' ? '世代' : 'generation', lang === 'zh' ? '距離 (m)' : 'distance (m)', 4);
    const Yd = v => H - m.b - v / 100 * (H - m.t - m.b);
    // plateau band
    el('rect', {x: X(30), y: m.t, width: X(41) - X(30), height: H - m.t - m.b, fill: 'rgba(243,156,53,.06)'}, svg);
    el('text', {x: (X(30) + X(41)) / 2, y: m.t + 14, 'text-anchor': 'middle', style: 'fill:#f39c35'}, svg).textContent = lang === 'zh' ? '停滯期' : 'plateau';
    const bw = (W - m.l - m.r) / 60 * .6;
    hist.forEach(h => el('rect', {x: X(h.generation) - bw / 2, y: Yd(h.tilt_disqualified), width: bw, height: H - m.b - Yd(h.tilt_disqualified), fill: '#22332f'}, svg));
    el('text', {x: W - m.r + 8, y: m.t + 4}, svg).textContent = '';
    const line = (key, color, w) => el('path', {d: hist.map((h, i) => (i ? 'L' : 'M') + X(h.generation) + ',' + Y(h[key])).join(''), fill: 'none', stroke: color, 'stroke-width': w, 'stroke-linejoin': 'round'}, svg);
    line('average', BLUE, 2); const best = line('best', ORANGE, 3);
    const len = best.getTotalLength ? best.getTotalLength() : 0; if (len) { best.style.strokeDasharray = len; best.style.strokeDashoffset = len; best.getBoundingClientRect(); best.style.transition = 'stroke-dashoffset 1.6s ease'; requestAnimationFrame(() => best.style.strokeDashoffset = 0); }
    checkpoints.forEach(g => { const h = hist[g - 1]; const c = el('circle', {cx: X(g), cy: Y(h.best), r: g === marked ? 7 : 4.5, fill: g === marked ? ORANGE : '#0b1211', stroke: ORANGE, 'stroke-width': 2, style: 'cursor:pointer'}, svg); c.addEventListener('click', () => onPick(g)); });
    const cursor = el('line', {y1: m.t, y2: H - m.b, stroke: '#8fa39b', 'stroke-dasharray': '3 4', opacity: 0}, svg);
    el('line', {x1: X(marked), x2: X(marked), y1: m.t, y2: H - m.b, stroke: ORANGE, opacity: .5}, svg);
    const tip = tooltipFor(container);
    const hit = el('rect', {x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: 'transparent'}, svg);
    const move = ev => { const r = svg.getBoundingClientRect(), px = (ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left, vx = px / r.width * W;
      const g = Math.max(1, Math.min(60, Math.round((vx - m.l) / (W - m.l - m.r) * 59 + 1))), h = hist[g - 1];
      cursor.setAttribute('x1', X(g)); cursor.setAttribute('x2', X(g)); cursor.setAttribute('opacity', 1);
      tip.innerHTML = `${t('tipGen').replace('{g}', g)} · <b>${t('tipBest')} ${h.best.toFixed(2)} m</b> · ${t('tipAvg')} ${h.average.toFixed(2)} m · ${t('tipDisq')} ${h.tilt_disqualified}`;
      tip.style.left = (X(g) / W * r.width) + 'px'; tip.style.top = (Y(h.best) / H * r.height) + 'px'; tip.style.opacity = 1; };
    hit.addEventListener('mousemove', move); hit.addEventListener('touchmove', move, {passive: true});
    hit.addEventListener('mouseleave', () => { tip.style.opacity = 0; cursor.setAttribute('opacity', 0); });
    hit.addEventListener('click', ev => { const r = svg.getBoundingClientRect(), vx = (ev.clientX - r.left) / r.width * W, g = Math.round((vx - m.l) / (W - m.l - m.r) * 59 + 1);
      const nearest = checkpoints.reduce((a, b) => Math.abs(b - g) < Math.abs(a - g) ? b : a); onPick(nearest); });
  }
  redraw();
  return {redraw, mark(g) { marked = g; redraw(); }};
}

/* ---------------- 02 race ---------------- */
function envOptions(env) { return env === 'rough' ? {terrain: 'rough', terrain_heights: DATA.R.robustness_terrain.heights} : env === 'push' ? DATA.R.robustness_push : {}; }
function initRace() {
  let mode = 'eras', env = 'flat';
  const eras = [1, 30, 60].map(g => DATA.cp.find(c => c.generation === g));
  const E = DATA.L.coevolution, D = DATA.L.domain_randomization;
  const contenders = () => [
    {robot: E.controllers.coevo_sine, key: 'cs', color: ORANGE, name: t('coevoSine')},
    {robot: E.controllers.coevo_feedback, key: 'cf', color: VIOLET, name: t('coevoFeedback'), outline: VIOLET, outlineFill: 'rgba(185,163,255,.10)'},
    {robot: D.controllers.flat_neural, key: 'fn', color: '#8fa39b', name: lang === 'zh' ? '平地訓練回授' : 'Flat-trained feedback', outline: '#8fa39b', outlineFill: 'rgba(143,163,155,.08)'}];
  const player = new Player($('race-canvas'), {
    make: () => {
      const o = envOptions(env);
      if (mode === 'eras') return eras.map(r => ({sim: newSim(r, o), gen: r.generation, color: ERA[r.generation], name: t('gen')(r.generation), outline: r.generation === 60 ? null : ERA[r.generation], outlineFill: r.generation === 1 ? 'rgba(143,163,155,.08)' : 'rgba(136,204,238,.08)', label: t('gen')(r.generation), labelColor: ERA[r.generation], labelDy: r.generation === 30 ? 16 : 0, trail: [], trailColor: ERA[r.generation] + '66'}));
      return contenders().map((c, i) => ({sim: newSim(c.robot, o), color: c.color, name: c.name, outline: c.outline || null, outlineFill: c.outlineFill, label: c.name, labelColor: c.color, labelDy: i * 16, trail: [], trailColor: c.color + '66'}));
    },
    view: pl => { const w = viewWidth(pl.canvas, 25, 24); return {left: -2.2, width: w, ground: .84, finish: mode === 'eras' && env === 'flat' ? 19.24 : undefined, flash: env === 'push' && pl.entries[0].sim.time > DATA.R.robustness_push.push_time && pl.entries[0].sim.time < DATA.R.robustness_push.push_time + .6 ? '← ' + t('pushNow') : ''}; },
    onTick: pl => board(pl)
  });
  function board(pl) {
    const sorted = pl.entries.slice().sort((a, b) => (b.sim.fell ? -1e9 : b.sim.distance) - (a.sim.fell ? -1e9 : a.sim.distance));
    $('leaderboard').innerHTML = sorted.map((e, i) => `<div><span class="rank">${t('rank')[i]}</span><i style="background:${e.color}"></i>${e.name}<b>${e.sim.fell ? t('fell') : fmt(e.sim.distance)}</b></div>`).join('');
  }
  function note() { $('race-note').textContent = t(mode === 'eras' ? 'raceNoteEras' : 'raceNoteControl'); }
  const restart = () => { note(); player.reset(); player.play(); };
  $$('#race-mode .chip').forEach(b => b.addEventListener('click', () => { $$('#race-mode .chip').forEach(x => x.classList.toggle('active', x === b)); mode = b.dataset.raceMode; restart(); }));
  $$('#race-env .chip').forEach(b => b.addEventListener('click', () => { $$('#race-env .chip').forEach(x => x.classList.toggle('active', x === b)); env = b.dataset.raceEnv; restart(); }));
  $('race-start').addEventListener('click', restart);
  $('race-reset').addEventListener('click', () => { player.playing = false; player.reset(); });
  listeners.push(() => { note(); player.reset(); board(player); });
  note();
  const io = new IntersectionObserver(es => { if (es[0].isIntersecting) { player.reset(); player.play(); io.disconnect(); } }, {threshold: .5}); io.observe($('race-canvas'));
}

/* ---------------- 03 materials legend ---------------- */
let selectedMaterial = 3;
function renderMaterials() {
  const diagram = document.querySelector('.voxel-diagram');
  $('materials').setAttribute('aria-label', lang === 'zh' ? '材質' : 'Material');
  $('materials').innerHTML = [1, 2, 3, 4].map(m => `<button type="button" aria-pressed="${m === selectedMaterial}" data-material="${m}"><i style="background:${MAT[m]}"></i>${t('mats')[m]}${m === 3 ? ' ↔' : m === 4 ? ' ↕' : ''}</button>`).join('');
  $('materials').querySelectorAll('button').forEach(button => button.addEventListener('click', () => {
    selectedMaterial = Number(button.dataset.material); renderMaterials();
  }));
  diagram.dataset.material = selectedMaterial;
  diagram.style.setProperty('--material-color', MAT[selectedMaterial]);
  diagram.querySelectorAll('.sp:not(.diag)').forEach(line => {
    const horizontal = line.getAttribute('y1') === line.getAttribute('y2');
    line.classList.toggle('act', selectedMaterial === (horizontal ? 3 : 4));
  });
  $('material-description').textContent = t('materialDescriptions')[selectedMaterial - 1];
}

/* ---------------- 04 build ---------------- */
function initBuild() {
  let grid = Array.from({length: 5}, () => Array(5).fill(0)), brush = null, presetPhases = null, statusKey = 'ready';
  const champ = DATA.cp.at(-1);
  const editor = $('editor');
  function cellButtons() {
    editor.replaceChildren();
    grid.forEach((row, r) => row.forEach((m, c) => {
      const b = document.createElement('button'); b.type = 'button'; b.className = m ? '' : 'empty'; b.style.background = m ? MAT[m] : '';
      b.setAttribute('aria-label', `${r + 1},${c + 1}: ${t('mats')[m]}`);
      b.addEventListener('click', () => { grid[r][c] = brush === null ? (grid[r][c] + 1) % 5 : (grid[r][c] === brush ? 0 : brush); presetPhases = null; if ($('rhythm').value === 'evolved') $('rhythm').value = 'wave'; refresh(); });
      editor.append(b);
    }));
  }
  function paletteButtons() {
    $('palette').innerHTML = '';
    const opts = [[null, lang === 'zh' ? '循環切換' : 'Cycle'], ...[0, 1, 2, 3, 4].map(m => [m, t('mats')[m]])];
    for (const [m, name] of opts) { const b = document.createElement('button'); b.type = 'button'; b.className = brush === m ? 'active' : '';
      b.innerHTML = (m === null ? '↻ ' : `<i style="background:${m ? MAT[m] : 'transparent'}"></i>`) + name; b.addEventListener('click', () => { brush = m; paletteButtons(); }); $('palette').append(b); }
  }
  function phases() {
    const mode = $('rhythm').value;
    if (mode === 'evolved' && presetPhases) return presetPhases;
    return grid.map((row, r) => row.map((_, c) => mode === 'wave' ? -c * Math.PI / 2 : mode === 'alt' ? (r % 2) * Math.PI : 0));
  }
  let brain = 'sine', benv = 'flat';
  function robot() {
    const body = grid.map(r => r.slice());
    if (brain === 'feedback') {
      const B = DATA.L.coevolution.brain25, cells = [];
      body.forEach((row, r) => row.forEach((m, c) => { if (m === 3 || m === 4) cells.push(r * 5 + c); }));
      return {body, controller: {kind: 'closed_loop', omega: B.omega, w1: B.w1, b1: B.b1, w2: cells.map(i => B.w2[i]), b2: cells.map(i => B.b2[i])}};
    }
    return {body, controller: {kind: 'open_loop', omega: +$('omega').value, phases: phases()}};
  }
  function status(key, extra = '', err = false) { statusKey = key; $('build-status').textContent = t(key) + extra; $('build-status').classList.toggle('error', err); }
  const player = new Player($('build-canvas'), {
    make: () => {
      const out = [], o = envOptions(benv); if ($('ghost').checked) out.push({sim: newSim(champ, o), outline: 'rgba(243,156,53,.55)', outlineFill: 'rgba(243,156,53,.05)', label: lang === 'zh' ? '冠軍幽靈' : 'champion ghost', labelColor: 'rgba(243,156,53,.7)', labelDy: 18});
      if (SoftRobot.valid(grid)) out.push({sim: newSim(robot(), o), you: true, trail: [], label: lang === 'zh' ? '你' : 'you', labelColor: GREEN});
      return out.length ? out : [{sim: null}];
    },
    view: pl => { const you = pl.entries.find(e => e.you); return followView(you ? you.sim : null, viewWidth(pl.canvas, 16, 11), {ground: .8}); },
    onTick: pl => { const you = pl.entries.find(e => e.you); if (!you) return; $('b-time').textContent = you.sim.time.toFixed(2) + ' s'; $('b-dist').textContent = fmt(you.sim.distance); },
    onDone: pl => { const you = pl.entries.find(e => e.you), ghost = pl.entries.find(e => !e.you && e.sim); if (you) verdict(you.sim, ghost ? ghost.sim.distance : champ.python_distance_m); }
  });
  function verdict(sim, target) {
    const v = $('verdict'), d = sim.distance, ratio = target > 0 ? d / target * 100 : 100;
    v.hidden = false; v.className = 'verdict' + (d > target ? ' win' : '');
    v.innerHTML = sim.fell ? `<strong>0.00 m</strong>${t('youFell')}` : d > target ? `<strong>${d.toFixed(2)} m</strong>${t('beat')}` : `<strong>${d.toFixed(2)} m</strong>${Math.max(ratio, 0).toFixed(0)}% ${t('ofChamp')}`;
    status('ready');
  }
  function refresh() { cellButtons(); $('verdict').hidden = true; player.playing = false; player.reset();
    if (!SoftRobot.valid(grid)) status('invalid', '', true); else status('ready'); writeHash(); }
  function load(preset) {
    presetPhases = null;
    if (preset === 'clear') grid = grid.map(r => r.map(() => 0));
    else if (preset === 'demo') { grid = Array.from({length: 5}, () => Array(5).fill(0)); DATA.R.demo_body.forEach((row, i) => row.forEach((v, j) => grid[i + 1][j + 1] = v)); presetPhases = null; $('rhythm').value = 'wave'; $('omega').value = 3; }
    else if (preset === 'random') { do { grid = grid.map(r => r.map(() => Math.random() < .3 ? 0 : 1 + Math.floor(Math.random() * 4))); } while (!SoftRobot.valid(grid)); $('rhythm').value = 'wave'; }
    else if (preset === 'fbchamp') { const c = DATA.L.coevolution.controllers.coevo_feedback; grid = c.body.map(r => r.slice()); brain = 'feedback'; $$('#brain-seg .chip').forEach(x => x.classList.toggle('active', x.dataset.brain === 'feedback')); brainUi(); }
    else { const cp = DATA.cp.find(c => c.id === preset); grid = cp.body.map(r => r.slice()); presetPhases = cp.controller.phases; $('omega').value = cp.controller.omega; $('rhythm').value = 'evolved'; }
    $('omega-out').textContent = (+$('omega').value).toFixed(1) + ' rad/s'; refresh();
  }
  function writeHash() { const s = grid.flat().join('') + '-' + (+$('omega').value).toFixed(1) + '-' + $('rhythm').value; history.replaceState(null, '', '#build=' + s); }
  function readHash() { const m = location.hash.match(/build=([0-4]{25})-([\d.]+)-(\w+)/); if (!m) return false;
    grid = Array.from({length: 5}, (_, r) => Array.from({length: 5}, (_, c) => +m[1][r * 5 + c])); $('omega').value = Math.min(6, Math.max(1, +m[2]));
    $('rhythm').value = m[3] === 'evolved' ? 'wave' : m[3]; $('omega-out').textContent = (+$('omega').value).toFixed(1) + ' rad/s'; return true; }
  $$('[data-preset]').forEach(b => b.addEventListener('click', () => load(b.dataset.preset)));
  $('omega').addEventListener('input', () => { $('omega-out').textContent = (+$('omega').value).toFixed(1) + ' rad/s'; refresh(); });
  $('rhythm').addEventListener('change', () => { if ($('rhythm').value === 'evolved' && !presetPhases) { $('rhythm').value = 'wave'; status('evolvedOnly', '', true); return; } refresh(); });
  $('ghost').addEventListener('change', refresh);
  function brainUi() { $('brain-note').textContent = t(brain === 'feedback' ? 'brainNoteFb' : 'brainNote'); $('rhythm-field').style.opacity = brain === 'feedback' ? .4 : 1; $('omega').disabled = $('rhythm').disabled = brain === 'feedback'; }
  $$('#brain-seg .chip').forEach(b => b.addEventListener('click', () => { $$('#brain-seg .chip').forEach(x => x.classList.toggle('active', x === b)); brain = b.dataset.brain; brainUi(); refresh(); }));
  $$('#build-env .chip').forEach(b => b.addEventListener('click', () => { $$('#build-env .chip').forEach(x => x.classList.toggle('active', x === b)); benv = b.dataset.buildEnv; refresh(); }));
  listeners.push(brainUi);
  $('run').addEventListener('click', () => { if (!SoftRobot.valid(grid)) return status('invalid', '', true); $('verdict').hidden = true; player.reset(); player.play(); status('running'); });
  $('share').addEventListener('click', async () => { writeHash(); try { await navigator.clipboard.writeText(location.href); status('copied'); } catch { status('copyFail', '', true); } });
  listeners.push(() => { paletteButtons(); cellButtons(); $('build-status').textContent = t(statusKey); player.reset(); });
  paletteButtons();
  if (readHash()) { refresh(); document.getElementById('build').scrollIntoView(); } else load('demo');
}

/* ---------------- 05 experiments ---------------- */
const COND = [['co_evolution', ORANGE], ['control_only', BLUE], ['body_only', DIM]];
function initAblation() {
  const curves = DATA.L.ablation.curves, hidden = new Set();
  function legend() {
    $('ablation-legend').innerHTML = '';
    for (const [k, c] of COND) { const s = document.createElement('span'); s.style.cursor = 'pointer'; s.className = hidden.has(k) ? 'off' : '';
      s.innerHTML = `<i style="background:${c}"></i>${t('cond')[k]}`; s.addEventListener('click', () => { hidden.has(k) ? hidden.delete(k) : hidden.add(k); draw(); }); $('ablation-legend').append(s); }
  }
  function draw() {
    legend(); const box = $('ablation-chart'); box.replaceChildren();
    const W = 760, H = 380, m = {l: 44, r: 16, t: 26, b: 34}, svg = el('svg', {viewBox: `0 0 ${W} ${H}`}); box.append(svg);
    const {X, Y} = axes(svg, W, H, m, 40, 20, lang === 'zh' ? '世代' : 'generation', lang === 'zh' ? '最佳距離 (m)' : 'best distance (m)', 4, [1, 10, 20, 30, 40]);
    for (const [k, c] of COND) { if (hidden.has(k)) continue; const d = curves[k];
      el('path', {d: d.map((p, i) => (i ? 'L' : 'M') + X(p[0]) + ',' + Y(p[1] + p[2])).join('') + d.slice().reverse().map(p => 'L' + X(p[0]) + ',' + Y(Math.max(0, p[1] - p[2]))).join('') + 'Z', fill: c, opacity: .13}, svg);
      el('path', {d: d.map((p, i) => (i ? 'L' : 'M') + X(p[0]) + ',' + Y(p[1])).join(''), fill: 'none', stroke: c, 'stroke-width': 3}, svg);
      const lastp = d.at(-1); el('text', {x: X(lastp[0]) - 4, y: Y(lastp[1]) - 8, 'text-anchor': 'end', style: `fill:${c}`}, svg).textContent = lastp[1].toFixed(1) + ' m';
    }
    const tbl = DATA.L.ablation.table;
    $('ablation-table').innerHTML = `<tr><th>${t('thCond')}</th><th>${t('thMean')}</th><th>${t('thBest')}</th></tr>` +
      COND.map(([k, c]) => { const r = tbl.find(x => x.condition === k); return `<tr><td><i style="background:${c}"></i>${t('cond')[k]}</td><td>${r.mean_m.toFixed(2)} ± ${r.std_m.toFixed(2)}</td><td>${r.max_m.toFixed(2)}</td></tr>`; }).join('');
    $('ablation-stats').innerHTML = DATA.L.ablation.statistics.map(s => { const [a, , b] = s.comparison.split(' ');
      return `<div><span>${t('cond')[a]} vs ${t('cond')[b]}</span><span>p = <b>${s.p_value.toFixed(3)}</b> · Holm <b>${s.holm_adjusted_p_value.toFixed(3)}</b></span></div>`; }).join('');
  }
  draw(); listeners.push(draw);
}
const DOMAIN_CONDITIONS=[['flat_sine','#a37b44'],['flat_neural',VIOLET],
 ['randomized_sine',ORANGE],['randomized_neural_feedback',GREEN],['randomized_neural_clock_only',BLUE]];
function initDomain() {
  let metric='distance';
  const summary=DATA.L.domain_randomization.table;
  function draw() {
    $('domain-legend').innerHTML=DOMAIN_CONDITIONS.map(([key,color])=>`<span><i style="background:${color}"></i>${t('domainCond')[key]}</span>`).join('');
    const box=$('domain-chart');box.replaceChildren();
    const W=760,H=380,m={l:48,r:16,t:30,b:40},svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':metric==='distance'?t('thDistance'):t('thSuccess')});box.append(svg);
    const key=metric==='distance'?'distance':'success',mult=metric==='distance'?1:100;
    const values=summary.filter(r=>r.subset!=='all');
    const low=Math.min(0,...values.map(r=>(r[key+'_mean'+(metric==='distance'?'_m':'')]-r[key+'_std'+(metric==='distance'?'_m':'')])*mult));
    const high=Math.max(metric==='success'?100:1,...values.map(r=>(r[key+'_mean'+(metric==='distance'?'_m':'')]+r[key+'_std'+(metric==='distance'?'_m':'')])*mult));
    const unit=metric==='success'?20:5,ymin=Math.floor(low/unit)*unit,ymax=Math.ceil(high/unit)*unit;
    const Y=v=>H-m.b-(v-ymin)/(ymax-ymin)*(H-m.t-m.b);
    for(let v=ymin;v<=ymax;v+=unit){el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:'#22332f'},svg);el('text',{x:m.l-8,y:Y(v)+4,'text-anchor':'end'},svg).textContent=v.toFixed(0);}
    el('text',{x:m.l,y:16},svg).textContent=metric==='distance'?t('thDistance'):t('thSuccess');
    const gw=(W-m.l-m.r)/3,bw=gw*.15;
    ['flat','rough','push'].forEach((environment,group)=>{
      const gx=m.l+gw*(group+.5);
      el('text',{x:gx,y:H-12,'text-anchor':'middle'},svg).textContent=t('envName')[environment];
      DOMAIN_CONDITIONS.forEach(([condition,color],i)=>{
        const row=summary.find(r=>r.condition===condition&&r.subset===environment);
        const suffix=metric==='distance'?'_m':'',mean=row[key+'_mean'+suffix]*mult,sd=row[key+'_std'+suffix]*mult,x=gx+(i-2.5)*bw;
        const rect=el('rect',{x,y:Y(0),width:bw-3,height:0,rx:3,fill:color,opacity:.85},svg);
        el('title',{},rect).textContent=`${t('domainCond')[condition]} · ${t('envName')[environment]}: ${mean.toFixed(2)} ± ${sd.toFixed(2)}`;
        requestAnimationFrame(()=>{rect.style.transition='all .7s ease';rect.setAttribute('y',Y(mean));rect.setAttribute('height',Y(0)-Y(mean));});
        const cx=x+(bw-3)/2;el('line',{x1:cx,x2:cx,y1:Y(mean-sd),y2:Y(mean+sd),stroke:'#e8efe9','stroke-width':1.5},svg);
        for(const end of [mean-sd,mean+sd])el('line',{x1:cx-4,x2:cx+4,y1:Y(end),y2:Y(end),stroke:'#e8efe9','stroke-width':1.5},svg);
      });
    });
    $('domain-table').innerHTML=`<tr><th>${t('thCond')}</th><th>${t('thDistance')}</th><th>${t('thSuccess')}</th></tr>`+
      DOMAIN_CONDITIONS.map(([condition,color])=>{const r=summary.find(row=>row.condition===condition&&row.subset==='all');return `<tr><td><i style="background:${color}"></i>${t('domainCond')[condition]}</td><td>${r.distance_mean_m.toFixed(2)} ± ${r.distance_std_m.toFixed(2)}</td><td>${(r.success_mean*100).toFixed(2)} ± ${(r.success_std*100).toFixed(2)}</td></tr>`;}).join('');
    $('domain-stats').innerHTML=DATA.L.domain_randomization.statistics.map(row=>`<div><span>${t(row.comparison.includes('clock_only')?'compareClock':'compareSine')} · ${t(row.metric==='success_rate'?'statSuccess':'statDistance')}</span><span>p <b>${row.p_value.toFixed(4)}</b> · Holm <b>${row.holm_adjusted_p_value.toFixed(4)}</b></span></div>`).join('');
  }
  $$('#domain-metric .chip').forEach(button=>button.addEventListener('click',()=>{metric=button.dataset.domainMetric;$$('#domain-metric .chip').forEach(b=>b.classList.toggle('active',b===button));draw();}));
  draw();listeners.push(draw);
  window.addEventListener('lab-tab',event=>{if(event.detail==='domain')draw();});
}
function initRobust() {
  let metric = 'fitness_m', env = 'flat';
  const runs = DATA.L.robustness.runs, ENVS = ['flat', 'rough', 'push'], CTRL = [['open_loop', ORANGE], ['closed_loop', VIOLET]];
  function chart() {
    const box = $('robust-chart'); box.replaceChildren();
    const W = 760, H = 360, m = {l: 44, r: 16, t: 26, b: 40}, svg = el('svg', {viewBox: `0 0 ${W} ${H}`}); box.append(svg);
    const ymax = 25, Y = v => H - m.b - v / ymax * (H - m.t - m.b);
    for (let i = 0; i <= 5; i++) { const v = i * 5; el('line', {x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), stroke: '#22332f'}, svg); el('text', {x: m.l - 8, y: Y(v) + 4, 'text-anchor': 'end'}, svg).textContent = v; }
    el('text', {x: m.l, y: m.t - 10}, svg).textContent = metric === 'fitness_m' ? (lang === 'zh' ? '有效距離 (m)' : 'eligible distance (m)') : (lang === 'zh' ? '原始位移 (m)' : 'raw displacement (m)');
    const gw = (W - m.l - m.r) / 3, bw = gw * .28;
    ENVS.forEach((e, gi) => {
      const gx = m.l + gw * gi + gw / 2;
      el('text', {x: gx, y: H - m.b + 22, 'text-anchor': 'middle', style: 'fill:#c4d1cb;font-size:13px'}, svg).textContent = t('envName')[e];
      CTRL.forEach(([c, col], ci) => {
        const vals = runs.filter(r => r.controller === c && r.environment === e).map(r => r[metric]), mean = vals.reduce((a, b) => a + b, 0) / vals.length;
        const x = gx + (ci ? 6 : -6 - bw), rect = el('rect', {x, y: Y(0), width: bw, height: 0, rx: 4, fill: col, opacity: c === 'open_loop' ? .85 : .55}, svg);
        requestAnimationFrame(() => { rect.style.transition = 'all .8s cubic-bezier(.2,.8,.2,1)'; rect.setAttribute('y', Y(mean)); rect.setAttribute('height', Y(0) - Y(mean)); });
        el('text', {x: x + bw / 2, y: H - m.b - 8, 'text-anchor': 'middle', style: 'fill:#0b1211;font-size:12px;font-weight:700'}, svg).textContent = mean.toFixed(1);
        vals.forEach((v, k) => { const fell = runs.find(r => r.controller === c && r.environment === e && r[metric] === v).fell;
          el('circle', {cx: x + bw * (.2 + .15 * k), cy: Y(v), r: 4.5, fill: fell ? '#ff6b5b' : '#e8efe9', stroke: '#0b1211', 'stroke-width': 1.5}, svg); });
      });
    });
    const lg = el('g', {transform: `translate(${W - m.r - 260},${m.t - 4})`}, svg);
    el('circle', {cx: 0, cy: -4, r: 4.5, fill: '#e8efe9'}, lg); el('text', {x: 10, y: 0}, lg).textContent = lang === 'zh' ? '一個種子' : 'one seed';
    el('circle', {cx: 110, cy: -4, r: 4.5, fill: '#ff6b5b'}, lg); el('text', {x: 120, y: 0}, lg).textContent = lang === 'zh' ? '翻倒 → 0' : 'tipped over → 0';
  }
  $$('#metric-seg .chip').forEach(b => b.addEventListener('click', () => { $$('#metric-seg .chip').forEach(x => x.classList.toggle('active', x === b)); metric = b.dataset.metric; chart(); }));
  const controllers=DATA.L.domain_randomization.controllers;
  let left='flat_neural',right='randomized_neural_feedback';
  let autoTimer=null;
  function choices(){
    for(const [id,value] of [['stress-left',left],['stress-right',right]]){
      $(id).innerHTML=DOMAIN_CONDITIONS.map(([key])=>`<option value="${key}">${t('domainCond')[key]} · ${lang==='zh'?'種子':'seed'} 42</option>`).join('');$(id).value=value;
    }
    $('stress-name-left').textContent=t('domainCond')[left];$('stress-name-right').textContent=t('domainCond')[right];
    $('stress-name-left').previousElementSibling.style.background=DOMAIN_CONDITIONS.find(r=>r[0]===left)[1];
    $('stress-name-right').previousElementSibling.style.borderColor=DOMAIN_CONDITIONS.find(r=>r[0]===right)[1];
  }
  choices();
  const player = new Player($('robust-canvas'), {
    make: () => { const o = env === 'rough' ? {terrain:'rough',terrain_heights:DATA.R.robustness_terrain.heights} : env === 'push' ? DATA.R.robustness_push : {};
      return [left,right].map((key,index)=>{const color=DOMAIN_CONDITIONS.find(r=>r[0]===key)[1];return {sim:newSim(controllers[key],o),label:t('domainCond')[key],labelColor:color,outline:index?color:null,labelDy:index?18:0,trail:[],trailColor:color+'66'};}); },
    view: pl => { const s = pl.entries[0].sim, n = pl.entries[1].sim, cx = (s.mean(0) + n.mean(0)) / 2;
      const points=pl.entries.flatMap(e=>e.sim.p.map(p=>p[0])),w=Math.max(viewWidth(pl.canvas,16,13),Math.max(...points)-Math.min(...points)+2);
      const pushTime=DATA.R.robustness_push.push_time;
      const showFlash = env === 'push' && s.time > pushTime && s.time < pushTime + .6;
      return {left: cx - w / 2, width: w, ground: .8, flash: showFlash ? '← ' + t('pushNow') : ''}; },
    onTick: pl => { const [s, n] = pl.entries; $('d-sine').textContent = s.sim.fell ? '0.00 m · '+t('fell') : fmt(s.sim.distance); $('d-nn').textContent = n.sim.fell ? '0.00 m · '+t('fell') : fmt(n.sim.distance);$('stress-raw').textContent=t('rawLive')+': '+fmt(s.sim.rawDistance)+' / '+fmt(n.sim.rawDistance); },
    onDone: pl => {autoTimer=setTimeout(() => {autoTimer=null;if (pl.visible) {pl.reset();pl.play();}},1500);}
  });
  function restartStress(){clearTimeout(autoTimer);autoTimer=null;player.reset();player.play();}
  $$('#env-seg .chip').forEach(b => b.addEventListener('click', () => { $$('#env-seg .chip').forEach(x => x.classList.toggle('active', x === b)); env = b.dataset.env;restartStress();}));
  $('stress-left').addEventListener('change',()=>{left=$('stress-left').value;choices();restartStress();});
  $('stress-right').addEventListener('change',()=>{right=$('stress-right').value;choices();restartStress();});
  $('stress-replay').addEventListener('click',restartStress);
  listeners.push(() => { chart();choices();player.entries[0].label=t('domainCond')[left];player.entries[1].label=t('domainCond')[right];player.draw(); });
  chart();
  const io = new IntersectionObserver(es => { if (es[0].isIntersecting)restartStress();else{clearTimeout(autoTimer);autoTimer=null;player.playing=false;} }, {threshold: .3}); io.observe($('robust-canvas'));
}

/* ---------------- tab D: co-evolution from scratch ---------------- */
const COEVO=[['coevo_sine',ORANGE],['coevo_feedback',VIOLET]];
function initCoevo() {
  const E=DATA.L.coevolution; if(!E) return;
  let metric='distance_m', env='flat';
  const name=k=>t(k==='coevo_sine'?'coevoSine':'coevoFeedback');
  const sum=(c,e)=>E.summary.find(r=>r.condition===c&&r.environment===e);
  function chart(){
    $('coevo-legend').innerHTML=COEVO.map(([k,c])=>`<span><i style="background:${c}"></i>${name(k)}</span>`).join('');
    const box=$('coevo-chart');box.replaceChildren();
    const W=760,H=340,m={l:48,r:16,t:26,b:40},svg=el('svg',{viewBox:`0 0 ${W} ${H}`});box.append(svg);
    const pct=metric==='success_rate',ymax=pct?100:20,Y=v=>H-m.b-Math.max(0,Math.min(v,ymax))/ymax*(H-m.t-m.b);
    for(let i=0;i<=4;i++){const v=ymax*i/4;el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:'#22332f'},svg);el('text',{x:m.l-8,y:Y(v)+4,'text-anchor':'end'},svg).textContent=Math.round(v)+(pct?'%':'');}
    el('text',{x:m.l,y:m.t-10},svg).textContent=pct?(lang==='zh'?'成功率':'success rate'):(lang==='zh'?'有效距離 (m)':'eligible distance (m)');
    const envs=['all','flat','rough','push'],gw=(W-m.l-m.r)/envs.length,bw=gw*.28;
    envs.forEach((e,gi)=>{
      const gx=m.l+gw*gi+gw/2;
      el('text',{x:gx,y:H-m.b+22,'text-anchor':'middle',style:'fill:#c4d1cb;font-size:13px'},svg).textContent=e==='all'?(lang==='zh'?'全部 21 個':'All 21'):t('envName')[e];
      COEVO.forEach(([c,col],ci)=>{
        const s=sum(c,e),mean=(pct?100:1)*s[metric+'_mean'],sd=(pct?100:1)*s[metric+'_sd'],x=gx+(ci?6:-6-bw);
        const rect=el('rect',{x,y:Y(0),width:bw,height:0,rx:4,fill:col,opacity:ci?.6:.85},svg);
        requestAnimationFrame(()=>{rect.style.transition='all .8s cubic-bezier(.2,.8,.2,1)';rect.setAttribute('y',Y(mean));rect.setAttribute('height',Y(0)-Y(mean));});
        el('line',{x1:x+bw/2,x2:x+bw/2,y1:Y(mean-sd),y2:Y(mean+sd),stroke:'#e8efe9','stroke-width':1.5,opacity:.7},svg);
        el('text',{x:x+bw/2,y:H-m.b-8,'text-anchor':'middle',style:'fill:#0b1211;font-size:11px;font-weight:700'},svg).textContent=pct?mean.toFixed(0):mean.toFixed(1);
        E.runs.filter(r=>r.condition===c&&r.environment===e).forEach((r,k)=>el('circle',{cx:x+bw*(.15+.14*k),cy:Y((pct?100:1)*r[metric]),r:3.8,fill:'#e8efe9',stroke:'#0b1211','stroke-width':1.2},svg));
      });
    });
    $('coevo-table').innerHTML=`<tr><th>${t('thCond')}</th><th>${t('thDistance')}</th><th>${t('thSuccess')}</th></tr>`+COEVO.map(([c,col])=>{const s=sum(c,'all');return `<tr><td><i style="background:${col}"></i>${name(c)}</td><td>${s.distance_m_mean.toFixed(2)} ± ${s.distance_m_sd.toFixed(2)}</td><td>${(100*s.success_rate_mean).toFixed(1)} ± ${(100*s.success_rate_sd).toFixed(1)}</td></tr>`;}).join('');
    $('coevo-stats').innerHTML=E.tests.map(r=>`<div><span>${lang==='zh'?'回授 − 開迴路':'feedback − sine'} · ${t(r.metric==='success_rate'?'statSuccess':'statDistance')}</span><span>Δ <b>${r.metric==='success_rate'?(100*r.mean_paired_difference).toFixed(1)+' pp':r.mean_paired_difference.toFixed(2)+' m'}</b> · p <b>${r.p_value.toFixed(3)}</b> · Holm <b>${r.holm_adjusted_p_value.toFixed(3)}</b></span></div>`).join('');
    const g=$('coevo-bodies');g.replaceChildren();
    COEVO.forEach(([c,col])=>{
      const lab=document.createElement('div');lab.className='row-label';lab.style.color=col;lab.textContent=name(c);g.append(lab);
      E.bodies[c].forEach(b=>{const f=document.createElement('figure'),sv=document.createElementNS(NS,'svg');sv.setAttribute('viewBox','0 0 5 5');blueprint(sv,b.body);
        const run=E.runs.find(r=>r.condition===c&&r.seed===b.seed&&r.environment==='all'),cap=document.createElement('figcaption');
        cap.textContent=`${lang==='zh'?'種子':'seed'} ${b.seed} · ${run.distance_m.toFixed(1)} m`;f.append(sv,cap);g.append(f);});
    });
    const a=sum('coevo_sine','all'),b=sum('coevo_feedback','all');
    $('coevo-body-stats').textContent=lang==='zh'?`平均格數／致動器：開迴路 ${a.cells_mean.toFixed(1)} / ${a.actuators_mean.toFixed(1)}，回授 ${b.cells_mean.toFixed(1)} / ${b.actuators_mean.toFixed(1)}。回授演化出的身體稍微小一點。`
      :`Mean cells / actuators: sine ${a.cells_mean.toFixed(1)} / ${a.actuators_mean.toFixed(1)}, feedback ${b.cells_mean.toFixed(1)} / ${b.actuators_mean.toFixed(1)}. Feedback evolved slightly smaller bodies.`;
  }
  const ctl=E.controllers;
  const player=new Player($('coevo-canvas'),{
    make:()=>{const o=env==='rough'?{terrain:'rough',terrain_heights:DATA.R.robustness_terrain.heights}:env==='push'?DATA.R.robustness_push:{};
      return [{sim:newSim(ctl.coevo_sine,o),label:name('coevo_sine'),labelColor:ORANGE,trail:[]},{sim:newSim(ctl.coevo_feedback,o),outline:VIOLET,label:name('coevo_feedback'),labelColor:VIOLET,labelDy:18,trail:[],trailColor:'rgba(185,163,255,.35)'}];},
    view:pl=>{const s=pl.entries[0].sim,n=pl.entries[1].sim,cx=(s.mean(0)+n.mean(0))/2,w=viewWidth(pl.canvas,20,15),pt=DATA.R.robustness_push.push_time;
      return {left:cx-w/2,width:w,ground:.8,flash:env==='push'&&s.time>pt&&s.time<pt+.6?'← '+t('pushNow'):''};},
    onTick:pl=>{const [s,n]=pl.entries;$('cd-sine').textContent=s.sim.fell?t('fell'):fmt(s.sim.distance);$('cd-nn').textContent=n.sim.fell?t('fell'):fmt(n.sim.distance);},
    onDone:pl=>{clearTimeout(pl.again);pl.again=setTimeout(()=>{if(pl.visible){pl.reset();pl.play();}},1500);}
  });
  $$('#coevo-metric .chip').forEach(b=>b.addEventListener('click',()=>{$$('#coevo-metric .chip').forEach(x=>x.classList.toggle('active',x===b));metric=b.dataset.coevoMetric;chart();}));
  $$('#coevo-env .chip').forEach(b=>b.addEventListener('click',()=>{$$('#coevo-env .chip').forEach(x=>x.classList.toggle('active',x===b));env=b.dataset.coevoEnv;player.reset();player.play();}));
  new IntersectionObserver(es=>{if(es[0].isIntersecting){if(!player.playing){player.reset();player.play();}}else player.playing=false;},{threshold:.3}).observe($('coevo-canvas'));
  listeners.push(()=>{chart();player.entries[0].label=name('coevo_sine');player.entries[1].label=name('coevo_feedback');player.draw();});
  chart();
}
function initTabs() {
  // All experiments stay visible; the tab row is a sticky jump bar with scroll-spy.
  const tabs=$$('.tab'),panels=$$('.tabpanel'),seen=new Set();
  const mark=key=>tabs.forEach(tab=>{const on=tab.dataset.tab===key;tab.classList.toggle('active',on);if(on){tab.setAttribute('aria-current','true');const bar=tab.parentElement;if(bar.scrollWidth>bar.clientWidth)bar.scrollTo({left:tab.offsetLeft-16,behavior:'smooth'});}else tab.removeAttribute('aria-current');});
  const go=key=>{const panel=document.querySelector(`[data-panel=${key}]`);const bar=document.querySelector('.tabs');
    window.scrollTo({top:panel.getBoundingClientRect().top+window.scrollY-(bar?bar.offsetHeight:0)-70,behavior:'smooth'});};
  panels.forEach(panel=>{panel.id='panel-'+panel.dataset.panel;panel.hidden=false;});
  tabs.forEach(tab=>tab.addEventListener('click',()=>go(tab.dataset.tab)));
  $$('[data-show-tab]').forEach(button=>button.addEventListener('click',()=>{if(button.dataset.showTab==='robust')$('robust-canvas').scrollIntoView({behavior:'smooth',block:'center'});else go(button.dataset.showTab);}));
  const io=new IntersectionObserver(entries=>entries.forEach(entry=>{const key=entry.target.dataset.panel;
    if(entry.isIntersecting){mark(key);if(!seen.has(key)){seen.add(key);window.dispatchEvent(new CustomEvent('lab-tab',{detail:key}));}}}),{rootMargin:'-35% 0px -55% 0px'});
  panels.forEach(panel=>io.observe(panel));
  mark('ablation');
}

/* ---------------- reveal on scroll ---------------- */
function initReveal() {
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), {threshold: .12});
  $$('.block-head, .card, .stats div').forEach(n => { n.classList.add('reveal'); io.observe(n); });
}

/* ---------------- boot ---------------- */
async function init() {
  captureEnglish();
  try {
    const [r, l] = await Promise.all([fetch('robots.json').then(x => x.json()), fetch('lab.json').then(x => x.json())]);
    Object.assign(DATA, {R: r, L: l, C: r.constants, cp: l.checkpoints});
  } catch (e) { document.querySelector('.lead').textContent = 'Could not load data. Serve this folder over HTTP (python -m http.server) and reload.'; console.error(e); return; }
  initHero(); initCounters(); initExplorer(); initRace(); renderMaterials(); initBuild(); initTabs(); initAblation(); initRobust(); initDomain(); initCoevo(); initReveal();
  listeners.push(renderMaterials);
  $('language').addEventListener('click', () => { lang = lang === 'en' ? 'zh' : 'en'; applyLang(); });
  if (/^zh/i.test(navigator.language || '')) { lang = 'zh'; applyLang(); }
  window.addEventListener('resize', () => players.forEach(p => { p.visible = true; p.draw(); }));
  requestAnimationFrame(loop);
}
document.addEventListener('DOMContentLoaded', init);
