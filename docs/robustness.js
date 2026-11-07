/* Interactive held-out terrain comparison. Controllers are preselected seed 42. */
const robustState={sim:null,playing:false,accumulator:0,status:'readyRobust'};
function setupRobustness(){
 if(!data.robustness_terrain)return;
 Object.assign(en,{robustSection:'Robustness',robustIntro:'Can a controller handle a world it did not train on? Compare seed-42 controllers on flat ground and the first held-out rough profile. Changing a control resets the trial.',controllerLabel:'Controller',flatNeural:'Flat-trained neural',randomFeedback:'Randomized neural feedback',randomSine:'Randomized sine',terrainLabel:'Terrain',flatTerrain:'Flat',roughTerrain:'Rough',runTrial:'Run trial',pauseTrial:'Pause trial',readyRobust:'Ready — choose a controller and terrain, then run.',rawLabel:'Raw distance',eligibleLabel:'Eligible distance',domainFigureTitle:'Train for a varied world',domainFigureText:'Five-seed feedback and clock-only ablations test whether varied training environments improve held-out distance and stability; error bars are sample standard deviations.',robustFootnote:'One fixed test profile is shown here; the study evaluates 10 rough profiles, 10 push settings, and flat ground. Passing the tilt rule measures stability, not necessarily forward locomotion.'});
 Object.assign(zh,{robustSection:'穩健性',robustIntro:'控制器能應付未曾訓練過的環境嗎？比較種子 42 的控制器在平地與第一個保留崎嶇地形的表現。切換選項會重設測試。',controllerLabel:'控制器',flatNeural:'平地訓練神經控制器',randomFeedback:'隨機環境訓練神經回授',randomSine:'隨機環境訓練正弦控制器',terrainLabel:'地形',flatTerrain:'平地',roughTerrain:'崎嶇地形',runTrial:'執行測試',pauseTrial:'暫停測試',readyRobust:'準備完成，選擇控制器與地形後執行。',rawLabel:'原始位移',eligibleLabel:'有效位移',domainFigureTitle:'為多變的環境訓練',domainFigureText:'五個種子的回授與純時鐘消融，測試多變環境訓練能否改善保留測試的位移與穩定性；誤差棒為樣本標準差。',robustFootnote:'此處展示一個固定測試地形；完整研究使用 10 個崎嶇地形、10 組推力與平地。通過傾倒規則衡量的是穩定性，不保證向前移動。'});
 const section=document.createElement('section');section.id='robustness';
 section.innerHTML=`<div class="section-heading"><div><span class="eyebrow">04 / DOMAIN RANDOMIZATION</span><h2 data-i18n="robustSection"></h2></div></div><p class="section-intro" data-i18n="robustIntro"></p><div class="robust-layout"><div class="editor-card"><label for="robust-controller" data-i18n="controllerLabel"></label><select id="robust-controller"><option value="flat_neural" data-i18n="flatNeural"></option><option value="randomized_neural_feedback" data-i18n="randomFeedback"></option><option value="randomized_sine" data-i18n="randomSine"></option></select><fieldset class="terrain-toggle"><legend data-i18n="terrainLabel"></legend><label><input type="radio" name="robust-terrain" value="flat" checked><span data-i18n="flatTerrain"></span></label><label><input type="radio" name="robust-terrain" value="rough"><span data-i18n="roughTerrain"></span></label></fieldset><div class="controls"><button id="robust-run" class="primary" data-i18n="runTrial"></button><button id="robust-pause" data-i18n="pauseTrial"></button></div><p id="robust-status" class="status" aria-live="polite"></p><p class="note" data-i18n="robustFootnote"></p></div><div class="design-preview"><canvas id="robust-canvas" width="800" height="660" aria-label="Controller robustness simulation"></canvas><div class="preview-footer"><span data-i18n="eligibleLabel"></span><strong id="robust-distance">0.00 m</strong></div><div class="preview-footer"><span data-i18n="rawLabel"></span><strong id="robust-raw">0.00 m</strong></div></div></div><figure class="domain-figure"><h3 data-i18n="domainFigureTitle"></h3><p class="section-intro" data-i18n="domainFigureText"></p><img src="assets/domain_randomization_plot.png" alt="Domain randomization held-out distance and success rate" loading="lazy"></figure>`;
 $('results').after(section);
 en.fullFigure='Open full-size figure ↗';zh.fullFigure='開啟完整尺寸圖表 ↗';
 const fullFigure=document.createElement('a');
 fullFigure.href='assets/domain_randomization_plot.png';fullFigure.target='_blank';fullFigure.rel='noopener';
 fullFigure.dataset.i18n='fullFigure';fullFigure.textContent=text('fullFigure');
 section.querySelector('.domain-figure').append(fullFigure);
 const nav=document.querySelector('nav');const link=document.createElement('a');link.href='#robustness';link.dataset.i18n='robustSection';nav.insertBefore(link,$('language'));
 section.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=text(el.dataset.i18n));link.textContent=text('robustSection');
 $('robust-controller').addEventListener('change',resetRobustness);
 section.querySelectorAll('input[name=robust-terrain]').forEach(input=>input.addEventListener('change',resetRobustness));
 $('robust-run').addEventListener('click',()=>{if(robustState.sim.done)resetRobustness();robustState.playing=true;robustState.status='running';translateRobustness();});
 $('robust-pause').addEventListener('click',()=>{robustState.playing=false;robustState.status='paused';translateRobustness();});
 resetRobustness();
}
function resetRobustness(){
 const robot=data.robots.find(r=>r.id===$('robust-controller').value),terrain=document.querySelector('input[name=robust-terrain]:checked').value;
 robustState.sim=new SoftRobot.Simulation(robot,data.constants,{terrain,terrain_heights:data.robustness_terrain.heights});
 robustState.playing=false;robustState.accumulator=0;robustState.status='readyRobust';translateRobustness();
}
function translateRobustness(){
 if(!robustState.sim)return;
 const sim=robustState.sim;
 $('robustness').querySelector('.eyebrow').textContent=language==='en'?'04 / DOMAIN RANDOMIZATION':'04 / 領域隨機化';
 $('robust-canvas').setAttribute('aria-label',text('robustSection'));
 $('robust-status').textContent=text(robustState.status)+` · ${sim.time.toFixed(2)} s`;
 $('robust-distance').textContent=distance(sim.distance);
 $('robust-raw').textContent=distance(sim.rawDistance);
 draw($('robust-canvas'),sim);
}
function advanceRobustness(elapsed){if(!robustState.playing||!robustState.sim)return;robustState.accumulator+=elapsed;while(robustState.accumulator>=data.constants.DT&&!robustState.sim.done){robustState.sim.step();robustState.accumulator-=data.constants.DT;}if(robustState.sim.done){robustState.playing=false;robustState.status=robustState.sim.fell?'fallen':'done';}translateRobustness();}
