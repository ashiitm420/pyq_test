// One request at a time; no work for hidden tabs or an idle queue.
export function createAdminPoller({refresh,shouldPoll,onError=()=>{},interval=15000,doc=document}){
 let timer=null,stopped=true,pending=false,failures=0;
 function schedule(){clearTimeout(timer);if(!stopped&&!doc.hidden)timer=setTimeout(tick,Math.min(60000,interval*2**failures))}
 async function tick(){
  if(stopped||pending||doc.hidden)return;
  if(!shouldPoll()){schedule();return}
  pending=true;
  try{await refresh();failures=0}catch(e){failures=Math.min(3,failures+1);onError(e)}
  finally{pending=false;schedule()}
 }
 function visibility(){clearTimeout(timer);if(!doc.hidden)schedule()}
 return {start({immediate=false}={}){if(!stopped)return;stopped=false;doc.addEventListener('visibilitychange',visibility);if(immediate)void tick();else schedule()},stop(){stopped=true;clearTimeout(timer);doc.removeEventListener('visibilitychange',visibility)}}
}
