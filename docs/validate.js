/* Run with node docs/validate.js after python export_robots.py. */
const fs=require('fs'),path=require('path'),assert=require('assert');
const {Simulation,valid}=require('./sim.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'robots.json'),'utf8'));
const rows=data.robots.map(robot=>{const start=performance.now(),sim=new Simulation(robot,data.constants),distance=sim.run(),error=Math.abs(distance-robot.python_distance_m)/Math.max(Math.abs(robot.python_distance_m),1e-9);
 assert(sim.stable,robot.id+' unstable');assert(error<=.10,robot.id+' exceeds 10% parity tolerance');
 return {robot:robot.id,python_m:robot.python_distance_m,javascript_m:distance,relative_error_percent:error*100,fell:sim.fell,milliseconds:performance.now()-start};});
assert(!valid([[3,0,3]]));assert(!valid([[1]]));assert(valid(data.demo_body));
const csv=Object.keys(rows[0]).join(',')+'\n'+rows.map(row=>Object.values(row).join(',')).join('\n')+'\n';
fs.writeFileSync(path.join(__dirname,'../assets/js_parity.csv'),csv);
console.table(rows);console.log('Four-robot parity and body validation passed.');
