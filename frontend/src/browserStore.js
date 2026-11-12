const PROGRESS='pyq-browser-progress-v1',BOOKMARKS='pyq-browser-bookmarks-v1';
function read(key){try{const value=JSON.parse(localStorage.getItem(key)||'{}');return value&&typeof value==='object'&&!Array.isArray(value)?value:{}}catch{return {}}}
function write(key,value){try{localStorage.setItem(key,JSON.stringify(value))}catch{throw new Error('Your browser could not save progress or bookmarks. Allow site storage to keep them after closing this page.')}}
export function paperProgress(id){return read(PROGRESS)[String(id)]||null}
export function progressRows(){return Object.values(read(PROGRESS)).sort((a,b)=>b.last_attempted_at-a.last_attempted_at)}
export function saveResult(attempt){
 if(attempt.status!=='SUBMITTED'||!attempt.paper_id||attempt.records_progress===false||!attempt.result)return;
 const rows=read(PROGRESS),old=rows[String(attempt.paper_id)],time=attempt.submitted_at;
 if(old&&old.last_attempted_at>time)return;
 const parts=(attempt.title||'').replace(/^(?:(?:Assisted timed continuation|Practice continuation) · )+/,'').split(' · ');
 rows[String(attempt.paper_id)]={paper_id:attempt.paper_id,attempted:true,last_score:attempt.result.partial_score?null:attempt.result.percentage,last_attempted_at:time,course:parts[0]||'',exam:parts[1]||'',term:parts[2]||'',name:parts[3]||attempt.title};
 write(PROGRESS,rows);
}
// Signed image links expire, so bookmarks keep only the image identity. When a
// bookmark is shown, /api/images/<id> answers with a short redirect to a fresh
// link instead of Flask streaming every image byte through the proxy fallback.
const IMAGE_KEYS=['id','token','alt','option_key','inline','width','page'];
function bookmarkImage(image){const out={};for(const k of IMAGE_KEYS)if(image?.[k]!==undefined)out[k]=image[k];out.url='/api/images/'+image.id;return out}
function storedBookmark(question,extra={}){return {...question,...extra,images:(question.images||[]).filter(i=>i&&i.id!=null).map(bookmarkImage)}}
export function bookmarkRows(){return Object.values(read(BOOKMARKS)).map(q=>({...q,images:(q.images||[]).filter(i=>i&&i.id!=null).map(bookmarkImage)}))}
export function isBookmarked(id){return Boolean(read(BOOKMARKS)[String(id)])}
export function setBookmark(question,on,meta={}){const rows=read(BOOKMARKS);if(on){if(!question?.id)throw new Error('Question unavailable for bookmarking.');const old=rows[String(question.id)];rows[String(question.id)]=storedBookmark(question,{saved_at:old?.saved_at||Date.now(),paper_title:meta.paper_title||old?.paper_title||question.paper_title||''})}else delete rows[String(question.id)];write(BOOKMARKS,rows);return {bookmarked:on}}
// Restores a bookmark exactly as it was (used by Undo on the bookmarks page).
export function restoreBookmark(question){if(!question?.id)return;const rows=read(BOOKMARKS);rows[String(question.id)]=storedBookmark(question);write(BOOKMARKS,rows)}
export function clearBookmarks(){write(BOOKMARKS,{})}
export function localPage(rows,path){const params=new URLSearchParams(path.split('?')[1]||'');const page=Math.max(1,Number(params.get('page'))||1),limit=Math.min(100,Math.max(1,Number(params.get('limit'))||24));return {items:rows.slice((page-1)*limit,page*limit),total:rows.length,page,limit}}
