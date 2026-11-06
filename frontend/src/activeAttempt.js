import {ref} from 'vue';
const key='pyq-active-attempt';
function read(){try{const a=JSON.parse(localStorage.getItem(key)||'null');return a&&Number.isInteger(a.id)&&a.expires_at>Date.now()/1000&&(!a.deadline||a.deadline>Date.now()/1000)?a:null}catch{return null}}
export const activeAttempt=ref(read());
export function rememberAttempt(a){
 if(a?.status!=='ACTIVE')return;
 const value={id:a.id,title:a.title,mode:a.mode,expires_at:a.expires_at,deadline:a.deadline};
 activeAttempt.value=value;try{localStorage.setItem(key,JSON.stringify(value))}catch{}
}
export function clearActiveAttempt(id){
 if(id!==undefined&&activeAttempt.value?.id!==Number(id))return;
 activeAttempt.value=null;try{localStorage.removeItem(key)}catch{}
}
