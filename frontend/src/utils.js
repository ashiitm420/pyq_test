export function clock(seconds){const s=Math.max(0,Math.floor(seconds));return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;}
export function answerText(value){if(value===null||value===undefined||value==='')return 'Not available';if(typeof value==='object'&&!Array.isArray(value))return value.raw||JSON.stringify(value);return Array.isArray(value)?value.join(', '):String(value);}
export function remaining(deadline,serverNow,elapsed){return deadline?Math.max(0,deadline-serverNow-elapsed):null;}
export function paletteLabel(state){return ({NOT_VISITED:'Not visited',VISITED:'Visited',NOT_ANSWERED:'Not answered',ANSWERED:'Answered',MARKED_FOR_REVIEW:'Marked for review',ANSWERED_AND_MARKED_FOR_REVIEW:'Answered and marked'})[state]||state;}

// "1 paper", "2 papers": counts shown to students read naturally.
export function plural(n,word,many=word+'s'){const v=Number(n)||0;return v+' '+(v===1?word:many)}
