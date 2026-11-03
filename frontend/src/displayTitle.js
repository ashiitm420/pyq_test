const words=part=>part.toLowerCase().match(/[a-z0-9]+/g)||[];

// Attempt titles are "Course · Exam · Term · Paper name". The paper name often
// repeats the exam and term ("Quiz 1 May 2026"), so a part whose words all
// appeared earlier is dropped. File names and the verbose timer suffix are hidden.
export function displayExamTitle(title=''){
 const seen=new Set(),kept=[];
 for(const raw of String(title).split(' · ')){
  const part=raw.trim();
  if(!part||/\.pdf\b/i.test(part)||/^timed practice \(user-selected duration\)$/i.test(part))continue;
  const w=words(part);
  if(kept.length&&w.length&&w.every(x=>seen.has(x)))continue;
  w.forEach(x=>seen.add(x));kept.push(part);
 }
 return kept.join(' · ')||'Practice session';
}
