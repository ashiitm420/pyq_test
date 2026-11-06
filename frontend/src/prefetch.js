// Optional work only: never start network warmups on a constrained connection.
export function schedulePrefetch(work){
 const connection=navigator.connection||navigator.mozConnection||navigator.webkitConnection;
 if(document.visibilityState==='hidden'||connection?.saveData||['slow-2g','2g','3g'].includes(connection?.effectiveType))return ()=>{};
 let cancelled=false,idleId;
 const run=()=>{if(!cancelled&&document.visibilityState!=='hidden')Promise.resolve().then(work).catch(()=>{})};
 const timer=setTimeout(()=>{
  if(typeof requestIdleCallback==='function')idleId=requestIdleCallback(run,{timeout:1200});
  else run();
 },200);
 return ()=>{cancelled=true;clearTimeout(timer);if(idleId!==undefined&&typeof cancelIdleCallback==='function')cancelIdleCallback(idleId)};
}
