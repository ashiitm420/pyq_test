import test from 'node:test';
import assert from 'node:assert/strict';
import {saveResult,paperProgress,progressRows,setBookmark,bookmarkRows} from '../src/browserStore.js';
const memory=new Map();globalThis.localStorage={getItem:key=>memory.get(key)||null,setItem:(key,value)=>memory.set(key,value)};
test('latest score survives reloading storage and older results never replace the latest attempt',()=>{
 memory.clear();
 const a={status:'SUBMITTED',paper_id:5,records_progress:true,title:'Course · Quiz 1 · Jan 2026 · Paper',result:{percentage:80},submitted_at:1};
 for(const [percentage,time] of [[80,1],[90,2],[85,3]])saveResult({...a,result:{percentage},submitted_at:time});
 assert.equal(paperProgress(5).last_score,85);assert.equal(progressRows().length,1);
 saveResult(a);assert.equal(paperProgress(5).last_score,85);
 saveResult({...a,submitted_at:4,records_progress:false,result:{percentage:100}});assert.equal(paperProgress(5).last_score,85);
 saveResult({...a,status:'ACTIVE',submitted_at:5});assert.equal(paperProgress(5).last_score,85);
});
test('bookmarks persist independently of account identity and can be removed',()=>{
 memory.clear();setBookmark({id:12,paper_id:5,text:'Question',images:[]},true);
 assert.equal(bookmarkRows()[0].id,12);
 setBookmark({id:12},false);assert.deepEqual(bookmarkRows(),[]);
});
test('storage failures do not silently claim progress was saved',()=>{
 const set=localStorage.setItem;localStorage.setItem=()=>{throw new Error('blocked')};
 assert.throws(()=>setBookmark({id:1},true),/could not save/);localStorage.setItem=set;
});
test('bookmarks keep paper title and date but never an expiring signed image link',()=>{
 memory.clear();
 setBookmark({id:7,paper_id:3,text:'Q',images:[{id:41,token:'a',alt:'diagram',url:'https://acct.r2.cloudflarestorage.com/x.png?X-Amz-Signature=abc'}]},true,{paper_title:'Statistics I · Quiz 1 · May 2026'});
 const raw=JSON.parse(memory.get('pyq-browser-bookmarks-v1'))['7'];
 assert.equal(raw.paper_title,'Statistics I · Quiz 1 · May 2026');assert.ok(raw.saved_at>0);
 assert.equal(raw.images[0].url,'/api/images/41');assert.ok(!JSON.stringify(raw).includes('Signature'));
 // Old bookmarks saved with a signed link are normalised when read.
 memory.set('pyq-browser-bookmarks-v1',JSON.stringify({'8':{id:8,images:[{id:9,url:'https://x/y?X-Amz-Signature=old'}]}}));
 assert.equal(bookmarkRows()[0].images[0].url,'/api/images/9');
});
