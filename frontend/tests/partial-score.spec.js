import {it,expect} from 'vitest';
import {shareSummary,shareText} from '../src/shareCard';
import {saveResult,paperProgress} from '../src/browserStore';
it('labels subset scores when sharing and does not store them as full paper percentages',()=>{
 localStorage.clear();const a={id:1,paper_id:7,status:'SUBMITTED',submitted_at:100,title:'Finance · Quiz 1',palette:[],result:{score:4,total_marks:8,percentage:50,partial_score:true,excluded_from_score:2}};
 const s=shareSummary(a,'https://example.test');expect(shareText(s)).toContain('available graded questions only');
 saveResult(a);expect(paperProgress(7).last_score).toBeNull();localStorage.clear();
});
