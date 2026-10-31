import{a as H,c as X,S as Z}from"./utils-3dx3yWUg.js";import{a,c as o,t as r,F as k,m as x,b as t,j as h,J as K,u as P,x as ee,o as te,e as u,d as se,E as U,p as ae,g as q,K as $,r as p,A as W,w as Ta}from"./app-DTVF7wfu.js";import{_ as T,a as Q}from"./QuestionContent-CWz7fQ6M.js";import"./textFormatting-yRfyjnt1.js";import"./auto-render-CQOzBJvr.js";
const ne={class:"answer-value"},oe={key:0},le={key:1},j={__name:"AnswerValue",props:{question:Object,value:null,empty:{type:String,default:"Not available"}},setup(v){const c=v,b=ee(()=>{var w;return["MCQ","MSQ","TRUE_FALSE"].includes((w=c.question)==null?void 0:w.kind)&&Array.isArray(c.value)?c.value.map(d=>{const i=c.question.options.findIndex(n=>n.key===d);return i<0?null:{...c.question.options[i],letter:String.fromCharCode(65+i),images:(c.question.images||[]).filter(n=>n.option_key===d)}}):null});return(w,d)=>(a(),o("div",ne,[v.value===null||v.value===void 0||v.value===""||Array.isArray(v.value)&&!v.value.length?(a(),o("span",oe,r(v.empty),1)):b.value?(a(!0),o(k,{key:1},x(b.value,(i,n)=>(a(),o("div",{key:n,class:"answer-choice"},[i?(a(),o(k,{key:0},[t("strong",null,"Option "+r(i.letter),1),h(T,{text:i.text,images:i.images},null,8,["text","images"])],64)):(a(),o("span",le,"Option no longer available in this attempt"))]))),128)):(a(),K(Q,{key:2,text:P(H)(v.value)},null,8,["text"]))]))}};
const re={key:0,class:"alert alert-danger"},ie={class:"muted"},ue={class:"notice"},ce={key:0,class:"muted"},de={key:1,class:"result-panel panel"},pe={class:"result-score"},ve={class:"eyebrow"},me={class:"result-question-summary"},_e={class:"result-question-palette","aria-label":"Result question palette"},ye=["aria-label","aria-current","onClick"],ge={key:0,role:"status"},ke={key:2,class:"alert alert-warning"},be={class:"muted"},we={class:"d-flex gap-3 flex-wrap"},he=["href"],fe={key:4,class:"mt-3"},qe=["id"],xe={class:"section-row"},Ce={class:"status review-outcome"},Ee={class:"answer-comparison"},Se={key:1},Pe={key:2,class:"empty panel"},Te={key:0},Oe={key:1},Ae={class:"section-row"},Ne={key:0,class:"muted"},Ie={key:1,class:"empty panel"},Le={class:"eyebrow"},$e={class:"d-flex gap-2 mt-3"},De=["href"],Ve=["onClick"],Me={class:"paper-info"},Be={class:"eyebrow"},Ue=["href"],We={key:4,class:"pagination-row"},je=["disabled"],Ke=["disabled"];
const He={__name:"Records",props:{route:String},setup(v){
 const c=v,b=p([]),w=p(0),d=p(1),i=p(""),n=p(null),O=p(!1),C=p([]),Y=p(0),A=p(1),N=p(!1),I=p(null),allR=p([]),rFilter=p("ALL"),vMode=p("all"),rCache=new Map();
 const fbItems=p([]),fbTotal=p(0),fbAvg=p(0),fbCounts=p({5:0,4:0,3:0,2:0,1:0}),fbName=p(""),fbStars=p(5),fbText=p(""),fbBusy=p(!1),fbMsg=p(""),fbErr=p("");
 let R=0;
 function D(l){var s;return(s=l.state)!=null&&s.startsWith("ANSWERED")?l.outcome||"UNGRADED":"SKIPPED"}
 const L=c.route.startsWith("/result/"),f=c.route==="/bookmarks",fbPage=c.route==="/feedback";
 const hasFull=ee(()=>allR.value.length>0);
 const fCounts=ee(()=>{
  const src=allR.value.length?allR.value:((n.value&&n.value.palette)||[]).map(x=>({outcome:D(x)}));
  return{ALL:src.length,WRONG:src.filter(x=>["INCORRECT","PARTIAL"].includes(x.outcome)).length,CORRECT:src.filter(x=>x.outcome==="CORRECT").length,SKIPPED:src.filter(x=>!x.outcome||["SKIPPED","UNGRADED"].includes(x.outcome)).length};
 });
 const visReview=ee(()=>{
  if(!hasFull.value)return C.value;
  let list=allR.value;
  if(rFilter.value==="WRONG")list=list.filter(x=>["INCORRECT","PARTIAL"].includes(x.outcome));
  else if(rFilter.value==="CORRECT")list=list.filter(x=>x.outcome==="CORRECT");
  else if(rFilter.value==="SKIPPED")list=list.filter(x=>!x.outcome||["SKIPPED","UNGRADED"].includes(x.outcome));
  if(vMode.value==="single"&&I.value!==null){
   const m=list.find(x=>x.question.id===I.value);
   return m?[m]:list.slice(0,1);
  }
  return list;
 });
 const curIdx=ee(()=>visReview.value.length&&I.value!==null?allR.value.findIndex(x=>x.question.id===I.value):0);
 function optCls(qObj,ans,k){
  const ok=Array.isArray(qObj.answers)&&qObj.answers.includes(k),ch=Array.isArray(ans)&&ans.includes(k);
  return{"review-option":!0,"review-option-correct":ok,"review-option-incorrect":ch&&!ok,"review-option-chosen":ch};
 }
 function optBdg(qObj,ans,k){
  const ok=Array.isArray(qObj.answers)&&qObj.answers.includes(k),ch=Array.isArray(ans)&&ans.includes(k);
  return ok&&ch?"✓ Your answer · Correct":ok?"✓ Correct answer":ch?"✗ Your answer":"";
 }
 async function loadFb(){
  try{
   const res=await q("/feedback");
   fbItems.value=res.items||[];fbTotal.value=res.total||0;fbAvg.value=res.average_rating||0;
   if(res.rating_counts)fbCounts.value=res.rating_counts;
  }catch{}
 }
 async function sendFb(){
  if(fbBusy.value)return;
  fbErr.value="";fbMsg.value="";
  if(fbText.value.trim().length<3){fbErr.value="Please write at least a few words of feedback.";return}
  fbBusy.value=!0;
  try{
   const res=await q("/feedback",{method:"POST",body:{name:fbName.value.trim(),stars:fbStars.value,message:fbText.value.trim()}});
   fbItems.value=res.items||[];fbTotal.value=res.total||0;fbAvg.value=res.average_rating||0;
   if(res.rating_counts)fbCounts.value=res.rating_counts;
   fbText.value="";
   fbMsg.value="Thank you! Your feedback has been published.";
  }catch(err){fbErr.value=err.message||"Could not submit feedback."}
  finally{fbBusy.value=!1}
 }
 function toFb(){var m,_;(_=(m=document.getElementById("result-feedback-section"))==null?void 0:m.scrollIntoView)==null||_.call(m,{behavior:"smooth",block:"start"})}
 async function E(){
  try{
   if(fbPage){await loadFb()}
   else if(L){
    n.value=await q("/attempts/"+c.route.split("/")[2]);
    if(n.value.status==="ACTIVE"){$( "/attempt/"+n.value.id);return}
    if(Array.isArray(n.value.review_items)&&n.value.review_items.length){
     allR.value=n.value.review_items;C.value=n.value.review_items;Y.value=n.value.review_items.length;O.value=!0;
     var p0;I.value=((p0=n.value.palette&&n.value.palette[0])==null?void 0:p0.question_id)??n.value.review_items[0].question.id;
    }
    void loadFb();
   }else if(f){const l=await q("/bookmarks?page="+d.value);b.value=l.items,w.value=l.total}
   else{const l=await q("/progress?page="+d.value);b.value=l.items,w.value=l.total}
  }catch(l){i.value=l.message}
 }
 te(E);
 async function V(l){try{const s=await q("/attempts",{method:"POST",body:f?{collection:c.route.slice(1),mode:"practice"}:{paper_id:l,mode:"practice"}});$("/attempt/"+s.id)}catch(s){i.value=s.message}}
 async function z(){try{const l=await q("/attempts",{method:"POST",body:{collection:"mistakes",attempt_id:n.value.id,mode:"practice"}});$("/attempt/"+l.id)}catch(l){i.value=l.message}}
 async function F(l=null){
  var m,_;const s=++R;N.value=!0,i.value="";
  try{
   const cItem=rCache.get(A.value),y=cItem?{items:[cItem],total:Y.value}:await q("/attempts/"+n.value.id+"/review?page="+A.value+"&limit=1");
   if(s!==R)return;if(y.items&&y.items[0])rCache.set(A.value,y.items[0]);
   C.value=y.items,Y.value=y.total,O.value=!0,await W(),l!==null&&((_=(m=document.getElementById("review-question-"+l))==null?void 0:m.scrollIntoView)==null||_.call(m,{behavior:"smooth",block:"start"}))
  }catch(y){s===R&&(i.value=y.message)}finally{s===R&&(N.value=!1)}
 }
 async function G(l,s){
  var _,y;I.value=l.question_id;
  if(hasFull.value){
   O.value=!0;
   if(rFilter.value!=="ALL"&&!visReview.value.some(S=>S.question.id===l.question_id))rFilter.value="ALL";
   await W();(y=(_=document.getElementById("review-question-"+l.question_id))==null?void 0:_.scrollIntoView)==null||y.call(_,{behavior:"smooth",block:"start"});
   return;
  }
  const m=(l.review_index??s)+1;
  if(O.value&&A.value===m&&C.value.some(S=>S.question.id===l.question_id)){await W(),(y=(_=document.getElementById("review-question-"+l.question_id))==null?void 0:_.scrollIntoView)==null||y.call(_,{behavior:"smooth",block:"start"});return}
  A.value=m,C.value=[],await F(l.question_id)
 }
 function setF(val){rFilter.value=val;if(vMode.value==="single"&&visReview.value[0])I.value=visReview.value[0].question.id}
 async function stepS(delta){
  var _,y;const idx=curIdx.value+delta;
  if(idx>=0&&idx<allR.value.length){rFilter.value="ALL";I.value=allR.value[idx].question.id;await W();(y=(_=document.getElementById("review-question-"+I.value))==null?void 0:_.scrollIntoView)==null||y.call(_,{behavior:"smooth",block:"start"})}
 }
 function toTop(){var m,_;(_=(m=document.querySelector(".result-panel"))==null?void 0:m.scrollIntoView)==null||_.call(m,{behavior:"smooth",block:"start"})}
 async function J(l){await q("/questions/"+l+"/bookmark",{method:"DELETE"}),await E()}
 function renderFbForm(rowsCount,showSeeAllLink){
  return t("form",{class:"feedback-form mt-3",onSubmit:Ta(sendFb,["prevent"])},[
   t("div",{class:"feedback-form-row"},[
    t("label",{class:"feedback-label"},[
     se("1. Your name "),t("small",{class:"muted"},"(optional)"),
     t("input",{class:"form-control",type:"text",maxlength:"80",placeholder:"Anonymous Student",value:fbName.value,onInput:e=>{fbName.value=e.target.value}},null,40,["value"])
    ]),
    t("div",{class:"feedback-label"},[
     t("span",null,[se("2. Rating "),t("small",{class:"muted"},"(out of 5)")]),
     t("div",{class:"feedback-stars-picker",role:"radiogroup","aria-label":"Star rating out of 5"},[
      (a(),o(k,null,x([1,2,3,4,5],st=>t("button",{key:st,type:"button",class:U(["star-pick-btn",{active:st<=fbStars.value}]),"aria-label":st+" out of 5 stars",onClick:()=>{fbStars.value=st}},"★",10,["aria-label"])),64)),
      t("span",{class:"star-pick-count"},r(fbStars.value)+" / 5",1)
     ])
    ])
   ]),
   t("label",{class:"feedback-label mt-2"},[
    se("3. Your feedback about MauryaHub"),
    t("textarea",{class:"form-control",rows:rowsCount,maxlength:"1500",placeholder:"Tell us what you like about the site or what feature we should improve next…",value:fbText.value,onInput:e=>{fbText.value=e.target.value},required:""},null,40,["rows","value"])
   ]),
   fbErr.value?(a(),o("p",{key:0,class:"alert alert-danger mt-2 mb-0",role:"alert"},r(fbErr.value),1)):u("",!0),
   fbMsg.value?(a(),o("p",{key:1,class:"alert alert-success mt-2 mb-0",role:"status"},[
    se(r(fbMsg.value)+" "),
    showSeeAllLink?t("a",{href:"/feedback",class:"fw-semibold ms-1"},"See all student feedbacks →"):u("",!0)
   ],1)):u("",!0),
   t("div",{class:"mt-3"},[
    t("button",{type:"submit",class:"btn btn-primary",disabled:fbBusy.value},r(fbBusy.value?"Posting…":"Post feedback"),9,["disabled"])
   ])
  ],32);
 }
 return(l,s)=>{
  var m,_,y,S,M;
  return a(),o(k,null,[
   i.value?(a(),o("div",re,r(i.value),1)):u("",!0),
   P(fbPage)?(a(),o(k,{key:0},[
    t("div",{class:"eyebrow"},"COMMUNITY REVIEWS"),
    t("div",Ae,[t("h1",null,"MauryaHub Site Feedback")]),
    t("p",ie,"Share your experience using MauryaHub PYQ Practice and read real feedback from fellow students."),
    t("div",{class:"panel feedback-summary-bar mt-3"},[
     t("div",{class:"feedback-avg-box"},[
      t("span",{class:"eyebrow"},"OVERALL RATING"),
      t("strong",null,r(fbTotal.value?fbAvg.value+" / 5":"—"),1),
      t("span",{class:"feedback-stars-static"},r("★".repeat(Math.round(fbAvg.value||5))+"☆".repeat(5-Math.round(fbAvg.value||5))),1),
      t("small",{class:"muted"},r(fbTotal.value?fbTotal.value+" verified student "+(fbTotal.value===1?"review":"reviews"):"No reviews yet · Be the first!"),1)
     ]),
     t("div",{class:"feedback-form-box"},[
      t("h2",{class:"h5 mb-2"},"Share your feedback"),
      renderFbForm(3,!1)
     ])
    ]),
    t("section",{class:"mt-4"},[
     t("div",Ae,[t("h2",{class:"h4 mb-0"},"Student Feedbacks ("+r(fbTotal.value)+")",1)]),
     fbItems.value.length?(a(),o("div",{key:1,class:"feedback-wall-grid mt-3"},[
      (a(!0),o(k,null,x(fbItems.value,item=>(a(),o("article",{key:item.id,class:"panel feedback-item-card"},[
       t("div",{class:"feedback-item-head"},[
        t("div",{class:"feedback-author"},[
         t("span",{class:"feedback-avatar"},r((item.name||"A").slice(0,1).toUpperCase()),1),
         t("div",null,[
          t("strong",null,r(item.name),1),
          t("small",{class:"muted d-block"},r(new Date(item.created_at*1e3).toLocaleDateString()),1)
         ])
        ]),
        t("span",{class:"feedback-item-stars","aria-label":item.stars+" out of 5 stars"},r("★".repeat(item.stars)+"☆".repeat(5-item.stars)),9,["aria-label"])
       ]),
       t("p",{class:"feedback-item-text mb-0"},r(item.message),1)
      ]))),128))
     ])):(a(),o("div",{key:0,class:"empty panel mt-3"},[
      t("h3",null,"No student feedbacks yet."),
      t("p",{class:"muted mb-0"},"Submit the form above to share the first review of MauryaHub!")
     ]))
    ])
   ],64)):P(L)&&n.value?(a(),o(k,{key:1},[
    s[8]||(s[8]=t("div",{class:"eyebrow"},"ATTEMPT COMPLETE",-1)),
    s[9]||(s[9]=t("h1",null,"Your results",-1)),
    t("p",ie,r(n.value.title),1),
    t("p",ue,"Results and question review are temporary, available until "+r(new Date(n.value.expires_at*1e3).toLocaleString())+". Only your latest paper percentage is saved in this browser.",1),
    n.value.records_progress===!1?(a(),o("p",ce,"This targeted practice does not replace your full-paper score.")):u("",!0),
    n.value.result?(a(),o("div",de,[
     t("div",pe,[
      t("span",ve,r(n.value.result.pending_manual?"PROVISIONAL SCORE":"YOUR SCORE"),1),
      t("strong",null,[se(r(n.value.result.score),1),t("small",null," / "+r(n.value.result.total_marks??"—"),1)]),
      t("span",null,r(n.value.result.percentage===null?"Percentage unavailable":n.value.result.percentage+"%"),1)
     ]),
     t("div",me,[
      t("div",{class:"result-stats-strip"},[
       t("div",{class:"stat-pill"},[t("span",null,"Attempted"),t("strong",null,r(n.value.result.attempted??0)+" / "+r((n.value.palette&&n.value.palette.length)||0),1)]),
       t("div",{class:"stat-pill stat-pill-green"},[t("span",null,"Correct"),t("strong",null,r(n.value.result.correct??0),1)]),
       t("div",{class:"stat-pill stat-pill-red"},[t("span",null,"Incorrect"),t("strong",null,r(n.value.result.incorrect??0),1)]),
       n.value.result.partial?(a(),o("div",{key:0,class:"stat-pill stat-pill-amber"},[t("span",null,"Partial"),t("strong",null,r(n.value.result.partial),1)])):u("",!0),
       t("div",{class:"stat-pill"},[t("span",null,"Accuracy"),t("strong",null,r(n.value.result.accuracy!=null?n.value.result.accuracy+"%":"—"),1)]),
       t("div",{class:"stat-pill"},[t("span",null,"Time taken"),t("strong",null,r(P(X)(n.value.result.time_taken||0)),1)])
      ]),
      s[4]||(s[4]=t("h2",null,[se("Question review "),t("small",{class:"muted fw-normal fs-6"},"— click any number to jump directly")],-1)),
      t("div",_e,[(a(!0),o(k,null,x(n.value.palette,(e,g)=>(a(),o("button",{key:e.question_id,type:"button",class:U(["result-"+D(e).toLowerCase(),{current:I.value===e.question_id}]),"aria-label":"Review question "+e.number+", "+D(e).toLowerCase(),"aria-current":I.value===e.question_id?"step":void 0,onClick:B=>G(e,g)},r(e.number),11,ye))),128))]),
      s[5]||(s[5]=t("div",{class:"result-palette-legend"},[t("span",null,"🟩 Correct"),t("span",null,"🟥 Incorrect"),t("span",{class:"partial-label"},"▣ Partial"),t("span",null,"□ Not attempted"),t("span",null,"▧ Ungraded")],-1)),
      N.value?(a(),o("p",ge,"Loading question review…")):u("",!0)
     ])
    ])):u("",!0),
    (m=n.value.result)!=null&&m.pending_manual?(a(),o("p",ke,"Some responses have no reliable source key/marks or cannot be automatically graded. The score is provisional.")):u("",!0),
    t("p",be,"Time taken: "+r(P(X)(((_=n.value.result)==null?void 0:_.time_taken)||0))+" · Negative marks: "+r((y=n.value.result)==null?void 0:y.negative_marks),1),
    t("div",we,[
     (((S=n.value.result)==null?void 0:S.incorrect)||0)+(((M=n.value.result)==null?void 0:M.partial)||0)>0?(a(),o("button",{key:0,class:"btn btn-outline-primary",onClick:z},"Practice incomplete / wrong answers ("+r((n.value.result.incorrect||0)+(n.value.result.partial||0))+")",1)):u("",!0),
     n.value.paper_id?(a(),o("button",{key:1,class:"btn btn-outline-primary",onClick:s[0]||(s[0]=e=>V(n.value.paper_id))},"Practice again")):u("",!0),
     t("button",{type:"button",class:"btn btn-outline-primary",onClick:toFb},"★ Rate MauryaHub"),
     t("a",{class:"btn btn-light",href:n.value.paper_id?"/paper/"+n.value.paper_id:"/progress"},"Back to "+r(n.value.paper_id?"paper":"progress"),9,he)
    ]),
    hasFull.value?(a(),o("div",{key:3,class:"review-toolbar panel mt-4"},[
     t("div",{class:"review-filter-pills",role:"tablist","aria-label":"Filter questions by outcome"},[
      t("button",{type:"button",class:U(["filter-pill",{active:rFilter.value==="ALL"}]),onClick:()=>setF("ALL")},"All questions ("+r(fCounts.value.ALL)+")",3),
      t("button",{type:"button",class:U(["filter-pill filter-pill-wrong",{active:rFilter.value==="WRONG"}]),onClick:()=>setF("WRONG")},"Incorrect / Partial ("+r(fCounts.value.WRONG)+")",3),
      t("button",{type:"button",class:U(["filter-pill filter-pill-correct",{active:rFilter.value==="CORRECT"}]),onClick:()=>setF("CORRECT")},"Correct ("+r(fCounts.value.CORRECT)+")",3),
      t("button",{type:"button",class:U(["filter-pill",{active:rFilter.value==="SKIPPED"}]),onClick:()=>setF("SKIPPED")},"Not attempted ("+r(fCounts.value.SKIPPED)+")",3)
     ]),
     t("div",{class:"review-mode-toggle"},[
      t("button",{type:"button",class:U(["btn btn-sm",vMode.value==="all"?"btn-primary":"btn-light"]),onClick:()=>{vMode.value="all"}},"Scroll all",2),
      t("button",{type:"button",class:U(["btn btn-sm",vMode.value==="single"?"btn-primary":"btn-light"]),onClick:()=>{vMode.value="single"}},"One by one",2)
     ])
    ])):u("",!0),
    O.value?(a(),o("section",fe,[
     hasFull.value&&!visReview.value.length?(a(),o("p",{key:0,class:"empty panel"},[se("No questions in this filter. "),t("button",{type:"button",class:"text-btn",onClick:()=>setF("ALL")},"Show all questions")])):(a(!0),o(k,{key:1},x(visReview.value,e=>(a(),o("article",{key:e.question.id,id:"review-question-"+e.question.id,class:U(["panel review-card","review-"+String(e.outcome||"UNGRADED").toLowerCase()])},[
      t("div",xe,[
       t("div",null,[
        t("span",{class:"eyebrow"},r((e.question.kind||"").replace("_"," / "))+" · "+r(e.question.marks!=null?e.question.marks+" marks":"Marks not specified"),1),
        t("h3",{class:"mb-0"},"Question "+r(e.question.number),1)
       ]),
       t("div",{class:"d-flex align-items-center gap-2 flex-wrap"},[
        t("span",Ce,r(e.outcome==="CORRECT"?"Correct":e.outcome==="PARTIAL"?"Partially correct":e.outcome==="INCORRECT"?"Incorrect":e.outcome==="SKIPPED"?"Not attempted":"Ungraded")+" · "+r(e.awarded??"—")+" marks",1),
        hasFull.value&&vMode.value==="all"?(a(),o("button",{key:0,type:"button",class:"btn btn-light btn-sm",onClick:toTop},"↑ Palette")):u("",!0)
       ])
      ]),
      h(T,{lazy:"",text:[e.question.passage,e.question.text].filter(Boolean).join("\n\n"),images:(e.question.images||[]).filter(g=>!g.option_key)},null,8,["text","images"]),
      (a(!0),o(k,null,x(e.question.options,(g,gi)=>(a(),o("div",{key:g.key,class:U(optCls(e.question,e.answer,g.key))},[
       t("strong",null,r(String.fromCharCode(65+gi))+".",1),
       t("div",{class:"review-option-body"},[h(T,{lazy:"",text:g.text,images:(e.question.images||[]).filter(B=>B.option_key===g.key)},null,8,["text","images"])]),
       optBdg(e.question,e.answer,g.key)?(a(),o("span",{key:0,class:"review-option-badge"},r(optBdg(e.question,e.answer,g.key)),1)):u("",!0)
      ],2))),128)),
      t("div",Ee,[
       t("div",null,[s[6]||(s[6]=t("span",null,"Your answer",-1)),h(j,{question:e.question,value:e.answer,empty:"Not answered"},null,8,["question","value"])]),
       t("div",null,[s[7]||(s[7]=t("span",null,"Correct answer",-1)),h(j,{question:e.question,value:e.question.answers},null,8,["question","value"])])
      ]),
      e.question.explanation?(a(),K(Q,{key:0,text:e.question.explanation},null,8,["text"])):u("",!0),
      h(Z,{"attempt-id":n.value.id,"question-id":e.question.id,saved:e.ai_solution},null,8,["attempt-id","question-id","saved"]),
      e.manual_note?(a(),o("p",Se,"Reviewer: "+r(e.manual_note),1)):u("",!0),
      hasFull.value&&vMode.value==="single"?(a(),o("div",{key:2,class:"d-flex justify-content-between mt-3 pt-3 border-top"},[
       t("button",{type:"button",class:"btn btn-light",disabled:curIdx.value<=0,onClick:()=>stepS(-1)},"← Previous question",8,["disabled"]),
       t("button",{type:"button",class:"btn btn-primary",disabled:curIdx.value>=allR.value.length-1,onClick:()=>stepS(1)},"Next question →",8,["disabled"])
      ])):u("",!0)
     ],10,qe))),128))
    ])):u("",!0),
    t("section",{id:"result-feedback-section",class:"panel feedback-result-card mt-4"},[
     t("div",xe,[
      t("div",null,[
       t("span",{class:"eyebrow"},"SITE FEEDBACK"),
       t("h2",{class:"h4 mb-1"},"Enjoying MauryaHub? Share your feedback"),
       t("p",{class:"muted mb-0"},"Your review helps us improve the site for all students.")
      ]),
      t("a",{href:"/feedback",class:"btn btn-light btn-sm"},"View all feedbacks ("+r(fbTotal.value)+") →",1)
     ]),
     renderFbForm(2,!0)
    ])
   ],64)):P(L)?(a(),o("section",Pe,[i.value?(a(),o("p",Oe,"Open My progress to see your latest paper score or retake a paper.")):(a(),o("p",Te,"Loading result…")),s[10]||(s[10]=t("a",{class:"btn btn-primary",href:"/progress"},"My progress",-1))])):(a(),o(k,{key:3},[s[12]||(s[12]=t("div",{class:"eyebrow"},"YOUR PRACTICE WORKSPACE",-1)),t("div",Ae,[t("h1",null,r(f?"My bookmarks":"My progress"),1),f&&b.value.length?(a(),o("button",{key:0,class:"btn btn-primary",onClick:s[1]||(s[1]=e=>V())},"Practice bookmarks")):u("",!0)]),f?u("",!0):(a(),o("p",Ne,"One latest score per paper. Retaking a paper replaces its previous score; scores and bookmarks stay on this browser only. Clearing site data removes them.")),b.value.length?f?(a(!0),o(k,{key:2},x(b.value,e=>(a(),o("article",{class:"panel review-card",key:e.id},[t("span",Le,r(e.kind)+" · "+r(e.topic||"Topic not specified"),1),h(T,{text:e.text,images:(e.images||[]).filter(g=>!g.option_key)},null,8,["text","images"]),t("div",$e,[t("a",{href:"/paper/"+e.paper_id,class:"btn btn-light"},"Open paper",8,De),t("button",{class:"text-btn",onClick:g=>J(e.id)},"Remove bookmark",8,Ve)])]))),128)):(a(!0),o(k,{key:3},x(b.value,e=>(a(),o("article",{key:e.paper_id,class:"paper-row panel"},[t("div",Me,[t("span",Be,r(e.course)+" · "+r(e.exam)+" · "+r(e.term),1),t("h3",null,r(e.name),1),h(ae,{progress:e},null,8,["progress"])]),t("a",{class:"btn btn-primary",href:"/paper/"+e.paper_id},"Retake Test",8,Ue)]))),128)):(a(),o("div",Ie,[t("h3",null,r(f?"No bookmarks yet.":"No completed papers yet."),1),s[11]||(s[11]=t("a",{href:"/",class:"btn btn-primary"},"Explore courses",-1))])),w.value>24?(a(),o("div",We,[t("button",{class:"btn btn-light",disabled:d.value===1,onClick:s[2]||(s[2]=e=>{d.value--,E()})},"Previous",8,je),t("span",null,"Page "+r(d.value),1),t("button",{class:"btn btn-light",disabled:d.value*24>=w.value,onClick:s[3]||(s[3]=e=>{d.value++,E()})},"Next",8,Ke)])):u("",!0)],64))
  ],64)
 }
}};export{He as default};
