/* Shared browser/Node simulator. SI model units; no external dependencies. */
(function(root) {
 'use strict';
 const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
 function valid(body) {
  if(!Array.isArray(body)||!body.length||body.length>5||!body[0].length||body[0].length>5||body.some(r=>r.length!==body[0].length||r.some(v=>!Number.isInteger(v)||v<0||v>4)))return false;
  const cells=[];body.forEach((r,i)=>r.forEach((v,j)=>{if(v)cells.push([i,j]);}));
  if(!cells.length||!body.some(r=>r.some(v=>v===3||v===4)))return false;
  const seen=new Set(),stack=[cells[0]];
  while(stack.length){const [r,c]=stack.pop(),key=r+','+c;if(seen.has(key))continue;seen.add(key);for(const [y,x] of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]])if(body[y]?.[x]&&!seen.has(y+','+x))stack.push([y,x]);}
  return seen.size===cells.length;
 }
 function mesh(body,C) {
  const points=[],nodes=new Map(),edges=new Map(),polygons=[],actuators=[];
  body.forEach((row,r)=>row.forEach((m,c)=>{if(m===3||m===4)actuators.push([r,c]);}));
  body.forEach((row,r)=>row.forEach((m,c)=>{if(!m)return;const y=body.length-1-r,corners=[[c,y],[c+1,y],[c+1,y+1],[c,y+1]];
   const ids=corners.map(p=>{const key=p.join(',');if(!nodes.has(key)){nodes.set(key,points.length);points.push(p);}return nodes.get(key);});polygons.push({r,c,m,ids});
   for(const [u,v] of [[0,1],[1,2],[2,3],[3,0],[0,2],[1,3]]){const a=Math.min(ids[u],ids[v]),b=Math.max(ids[u],ids[v]),key=a+','+b;
    if(!edges.has(key))edges.set(key,{a,b,owners:[]});
    edges.get(key).owners.push({r,c,m,active:(m===3&&corners[u][1]===corners[v][1])||(m===4&&corners[u][0]===corners[v][0]),index:actuators.findIndex(p=>p[0]===r&&p[1]===c)});
   }
  }));
  const springs=Array.from(edges.values());for(const s of springs){s.rest=Math.hypot(points[s.b][0]-points[s.a][0],points[s.b][1]-points[s.a][1]);s.k=s.owners.reduce((n,o)=>n+C.STIFFNESS[o.m],0)/s.owners.length;}
  return {points,springs,polygons,actuators};
 }
 class Simulation {
  constructor(robot,constants,options={}) {
   if(!valid(robot.body))throw Error('invalid body');this.C=constants;this.body=robot.body;this.controller=robot.controller;this.options=options;
   const m=mesh(this.body,constants);Object.assign(this,m);this.p=m.points.map(p=>p.slice());this.v=this.p.map(()=>[0,0]);
   const lift=options.terrain==='rough'?Math.max(...this.p.map(p=>this.ground(p[0])[0])):0;
   for(const p of this.p)p[1]+=constants.START_HEIGHT+lift;
   this.initialX=this.mean(0);const cy=this.mean(1);this.reference=this.p.map(p=>[p[0]-this.initialX,p[1]-cy]);this.front=this.reference.map(p=>p[0]>=0);
   this.stepIndex=0;this.fell=false;this.stable=true;this.tiltTime=0;this.worstCosine=1;this.previousAngle=0;this.output=m.actuators.map(()=>0);this.omega=clamp(this.controller.omega,1,6);
   for(const s of this.springs){s.sin=0;s.cos=0;for(const o of s.owners)if(o.active){const phase=this.controller.phases?.[o.r]?.[o.c]||0;s.sin+=Math.cos(phase)/s.owners.length;s.cos+=Math.sin(phase)/s.owners.length;}}
  }
  mean(axis){return this.p.reduce((n,p)=>n+p[axis],0)/this.p.length;}
  ground(x){if(this.options.terrain!=='rough')return [0,0];const C=this.C,ys=C.ROUGH_Y,xx=(x-C.ROUGH_START)/C.ROUGH_SPACING,i=clamp(Math.floor(xx),0,ys.length-2);if(xx<0)return [ys[0],0];if(xx>ys.length-1)return [ys.at(-1),0];const slope=(ys[i+1]-ys[i])/C.ROUGH_SPACING;return [ys[i]+(x-(C.ROUGH_START+i*C.ROUGH_SPACING))*slope,slope];}
  rotation(){let dot=0,cross=0;for(let i=0;i<this.p.length;i++){const r=this.reference[i],p=this.p[i];dot+=r[0]*p[0]+r[1]*p[1];cross+=r[0]*p[1]-r[1]*p[0];}return [Math.atan2(cross,dot),dot/Math.max(Math.hypot(dot,cross),1e-12)];}
  control(t){const C=this.C,c=this.controller,angle=this.rotation()[0],delta=Math.atan2(Math.sin(angle-this.previousAngle),Math.cos(angle-this.previousAngle));let vy=0,front=0,back=0;
   for(let i=0;i<this.p.length;i++){vy+=this.v[i][1];if(this.p[i][1]<=this.ground(this.p[i][0])[0]+C.CONTACT_TOLERANCE){if(this.front[i])front=1;else back=1;}}
   const input=[angle/Math.PI,delta/(C.CONTROL_INTERVAL*C.DT)/10,vy/this.p.length/5,front,back,Math.sin(this.omega*t),Math.cos(this.omega*t)];this.previousAngle=angle;
   const hidden=c.w1.map((row,i)=>Math.tanh(row.reduce((s,w,j)=>s+w*input[j],c.b1[i])));
   this.output=c.w2.map((row,i)=>Math.tanh(row.reduce((s,w,j)=>s+w*hidden[j],c.b2[i])));
  }
  step(){const C=this.C;if(this.done)return;const t=this.stepIndex*C.DT,neural=this.controller.kind==='closed_loop';if(neural&&this.stepIndex%C.CONTROL_INTERVAL===0)this.control(t);
   const acc=this.p.map(()=>[0,-C.GRAVITY]);
   for(const s of this.springs){const a=this.p[s.a],b=this.p[s.b],va=this.v[s.a],vb=this.v[s.b],dx=b[0]-a[0],dy=b[1]-a[1],length=Math.hypot(dx,dy),nx=dx/Math.max(length,1e-12),ny=dy/Math.max(length,1e-12);
    let modulation=s.sin*Math.sin(this.omega*t)+s.cos*Math.cos(this.omega*t);if(neural){modulation=0;for(const o of s.owners)if(o.active)modulation+=this.output[o.index]/s.owners.length;}
    const target=s.rest*(1+(this.options.passive?0:C.AMPLITUDE)*modulation),touch=a[1]<=this.ground(a[0])[0]+C.CONTACT_TOLERANCE||b[1]<=this.ground(b[0])[0]+C.CONTACT_TOLERANCE;
    const f=s.k*(length-target)+(C.SPRING_DAMPING+C.CONTACT_SPRING_DAMPING*Number(touch))*((vb[0]-va[0])*nx+(vb[1]-va[1])*ny),fx=f*nx/C.MASS,fy=f*ny/C.MASS;
    acc[s.a][0]+=fx;acc[s.a][1]+=fy;acc[s.b][0]-=fx;acc[s.b][1]-=fy;
   }
   if(this.options.push&&this.stepIndex===Math.round(C.PUSH_TIME/C.DT))for(const v of this.v)v[0]+=C.PUSH_DELTA_V;
   for(let i=0;i<this.p.length;i++){const p=this.p[i],v=this.v[i];v[0]+=C.DT*acc[i][0];v[1]+=C.DT*acc[i][1];p[0]+=C.DT*v[0];p[1]+=C.DT*v[1];const [height,slope]=this.ground(p[0]);
    if(p[1]<height){p[1]=height;if(this.options.terrain!=='rough'){const normal=Math.max(-v[1],0);v[1]=Math.max(v[1],0);v[0]=Math.sign(v[0])*Math.max(Math.abs(v[0])-C.FRICTION*normal,0);}else{const norm=Math.sqrt(1+slope*slope),nx=-slope/norm,ny=1/norm,tx=ny,ty=-nx,dv=Math.max(-(v[0]*nx+v[1]*ny),0);v[0]+=dv*nx;v[1]+=dv*ny;const friction=clamp(v[0]*tx+v[1]*ty,-C.FRICTION*dv,C.FRICTION*dv);v[0]-=friction*tx;v[1]-=friction*ty;}}
    if(!Number.isFinite(p[0])||!Number.isFinite(p[1])||Math.max(Math.abs(p[0]),Math.abs(p[1]))>C.MAX_POSITION)this.stable=false;
   }
   this.stepIndex++;if(this.stepIndex%C.POSTURE_CHECK_INTERVAL===0){const cosine=this.rotation()[1];this.worstCosine=Math.min(this.worstCosine,cosine);this.tiltTime=cosine<Math.cos(C.FALL_ANGLE_DEGREES*Math.PI/180)?this.tiltTime+C.DT*C.POSTURE_CHECK_INTERVAL:0;this.fell=this.fell||this.tiltTime>=C.FALL_DURATION-1e-12;}
  }
  get done(){return !this.stable||this.stepIndex>=Math.round(this.C.SIM_SECONDS/this.C.DT);}
  get time(){return this.stepIndex*this.C.DT;}
  get rawDistance(){return this.mean(0)-this.initialX;}
  get distance(){return this.fell||!this.stable?0:this.rawDistance;}
  run(){while(!this.done)this.step();return this.distance;}
 }
 const api={Simulation,valid,mesh};if(typeof module!=='undefined')module.exports=api;root.SoftRobot=api;
})(typeof globalThis!=='undefined'?globalThis:this);
