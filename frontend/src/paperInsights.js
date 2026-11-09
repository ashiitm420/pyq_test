// Optional per-tab learning notes. Never sent to the API or used for grading.
const PREFIX='pyq-paper-insights-v1-';
const key=a=>PREFIX+a.id;
function clean(a,data){
 if(!data||data.version!==1||!Number.isFinite(data.expiresAt)||data.expiresAt<Date.now())return null;
 const paperIds=new Set((a.papers||[]).map(p=>String(p.source_paper_id)));
 const questionIds=new Set((a.palette||[]).map(p=>p.question_id));
 const time={};for(const id of paperIds){const n=data.time?.[id];time[id]=Number.isFinite(n)&&n>=0&&n<=30*86400000?n:0}
 return {version:1,expiresAt:data.expiresAt,time,unsure:[...new Set(Array.isArray(data.unsure)?data.unsure.filter(id=>questionIds.has(id)):[])].slice(0,125),partial:data.partial===true};
}
export function readPaperInsights(a,storage=sessionStorage){
 try{return clean(a,JSON.parse(storage.getItem(key(a))||'null'))}catch{return null}
}
export function createPaperInsights(a,{storage=sessionStorage,now=()=>performance.now(),onError=()=>{}}={}){
 const stored=readPaperInsights(a,storage);
 const data=stored||{version:1,expiresAt:a.expires_at*1000,time:Object.fromEntries(a.papers.map(p=>[p.source_paper_id,0])),unsure:[],partial:a.server_time-a.started_at>30};
 const questions=new Set(a.palette.map(q=>q.question_id));
 let paper=null,anchor=null,endAt=Infinity,finished=false,lastSaved=now(),warned=false;
 function save(){
  data.expiresAt=a.expires_at*1000;
  try{
   // Bound old temporary records, without touching answer/progress storage.
   const keys=[];for(let i=0;i<storage.length;i++){const k=storage.key(i);if(k?.startsWith(PREFIX)&&k!==key(a))keys.push(k)}
   const live=[];for(const k of keys){let v;try{v=JSON.parse(storage.getItem(k))}catch{};if(!v||!Number.isFinite(v.expiresAt)||v.expiresAt<Date.now())storage.removeItem(k);else live.push(k)}
   for(const k of live.slice(0,Math.max(0,live.length-9)))storage.removeItem(k);
   storage.setItem(key(a),JSON.stringify(data));lastSaved=now();return true;
  }catch{if(!warned){warned=true;onError('Paper time and unsure flags could not be saved in this tab. Exam answers still use normal autosave.')}return false}
 }
 function checkpoint(persist=true){
  const t=now();if(anchor!==null&&paper!==null&&!finished){data.time[paper]+=Math.max(0,Math.min(t,endAt)-anchor);anchor=t}
  if(persist)save();
 }
 function active(id,visible=true){checkpoint(false);paper=Object.hasOwn(data.time,String(id))?String(id):null;anchor=!finished&&visible&&paper!==null?now():null;save()}
 function deadline(seconds){checkpoint(false);endAt=seconds==null?Infinity:now()+Math.max(0,seconds)*1000}
 function toggle(qid){if(!questions.has(qid))return;data.unsure=data.unsure.includes(qid)?data.unsure.filter(id=>id!==qid):[...data.unsure,qid];save()}
 function finish(){checkpoint(false);finished=true;anchor=null;save()}
 save();
 return {active,deadline,toggle,finish,checkpoint,unsure:()=>[...data.unsure],pulse:()=>{if(now()-lastSaved>=30000)checkpoint()}};
}
export function paperResultRows(a,insights){
 return (a.result?.papers||[]).map(p=>{
  const qs=(a.palette||[]).filter(q=>q.paper_id===p.source_paper_id);
  return {...p,active_seconds:insights?Math.round((insights.time[p.source_paper_id]||0)/1000):null,
   marked:qs.filter(q=>q.marked||q.state?.includes('MARKED_FOR_REVIEW')).length,
   unsure:insights?qs.filter(q=>q.state?.startsWith('ANSWERED')&&insights.unsure.includes(q.question_id)).length:null};
 });
}
