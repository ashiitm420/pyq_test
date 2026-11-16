// Browser preferences: no timers, polling, or per-homepage API calls.
const prefix='mauryahub-engagement:';
export function readPreference(key,fallback=null){try{const s=localStorage.getItem(prefix+key);return s===null?fallback:JSON.parse(s)}catch{return fallback}}
export function savePreference(key,value){try{localStorage.setItem(prefix+key,JSON.stringify(value))}catch{}}
export function markFeedbackSubmitted(){savePreference('feedback-submitted',true)}
export function promptFor(attempt,now=Date.now()){
 if(!attempt||attempt.mode!=='exam'||attempt.status!=='SUBMITTED'||attempt.custom_exam)return null;
 if(readPreference('seen-attempts',[]).includes(attempt.id))return null;
 if(!readPreference('feedback-submitted',false))return now-Number(readPreference('feedback-skip',0))>=86400000?'feedback':null;
 return now-Number(readPreference('support-shown',0))>=7*86400000?'support':null;
}
export function rememberPrompt(id,kind,now=Date.now()){
 savePreference('seen-attempts',[...readPreference('seen-attempts',[]).filter(x=>x!==id),id].slice(-30));
 if(kind==='support')savePreference('support-shown',now);
}
