/* Run with node docs/validate.js after python export_robots.py. */
const fs=require('fs'),path=require('path'),assert=require('assert');
const {Simulation,valid}=require('./sim.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'robots.json'),'utf8'));
const rows=[];
for(const robot of data.robots){
 for(const terrain of robot.references?Object.keys(robot.references):['flat']){
  const reference=robot.references?.[terrain]||{distance_m:robot.python_distance_m};
  const options=terrain==='push'?data.robustness_push:{terrain};
  const sim=new Simulation(robot,data.constants,{...options,terrain_heights:data.robustness_terrain?.heights});
  const distance=sim.run(),error=Math.abs(distance-reference.distance_m)/Math.max(Math.abs(reference.distance_m),1),raw=reference.raw_distance_m??reference.distance_m;
  const rawError=Math.abs(sim.rawDistance-raw)/Math.max(Math.abs(raw),1);
  assert(sim.stable,robot.id+' unstable');assert(error<=.10&&rawError<=.10,robot.id+' '+terrain+' exceeds parity tolerance');
  if(reference.fell!==undefined)assert.equal(sim.fell,reference.fell,robot.id+' fall-status mismatch');
  rows.push({robot:robot.id,terrain,python_m:reference.distance_m,javascript_m:distance,
   relative_error_percent:error*100,python_raw_m:raw,javascript_raw_m:sim.rawDistance,
   raw_error_percent:rawError*100,fell:sim.fell});
 }
}
assert(!valid([[3,0,3]]));assert(!valid([[1]]));assert(valid(data.demo_body));
const csv=Object.keys(rows[0]).join(',')+'\n'+rows.map(row=>Object.values(row).join(',')).join('\n')+'\n';
fs.writeFileSync(path.join(__dirname,'../assets/js_parity.csv'),csv);
console.table(rows);console.log(rows.length+' robot/environment parity checks and body validation passed.');
