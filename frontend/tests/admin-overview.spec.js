import {it,expect,vi,beforeEach} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
const mocks=vi.hoisted(()=>({api:vi.fn(),session:{user:{id:1,name:'Ashish',email:'admin@example.com',role:'ADMIN'}},go:vi.fn(),loadSession:vi.fn(),loadCatalog:vi.fn(async()=>({courses:[],meta:{terms:[],exams:[]}})),invalidateCatalog:vi.fn()}));
vi.mock('../src/api',()=>mocks);
import Admin from '../src/Admin.vue';

beforeEach(()=>{localStorage.removeItem('pyq-admin-tab');mocks.api.mockReset();mocks.api.mockImplementation(async path=>{
 if(path==='/admin/stats')return {papers:12,processed:10,questions:340,queued:1,active_processing:0,failed:2};
 if(path.startsWith('/admin/content-reports'))return {items:[],total:3};
 if(path.startsWith('/admin/contact-messages'))return {items:[],total:5};
 if(path==='/admin/ai-solutions/summary')return {papers:[],statistics:{questions_total:340,questions_published:85,questions_review:7}};
 if(path.startsWith('/admin/analytics'))return {totals:{active_browsers:41,starts:60,completions:45,completion_rate:75},trend:[{day:'2026-11-01',starts:20},{day:'2026-11-02',starts:40}]};
 if(path.startsWith('/admin/catalog/batches/latest'))return {};
 if(path.startsWith('/admin/ingestion'))return {items:[],total:0};
 return {};
})});

it('opens on the overview with attention counts, badges and working navigation',async()=>{
 const w=mount(Admin,{attachTo:document.body});await flushPromises();
 expect(w.get('.adm-title h1').text()).toBe('Overview');
 const attention=w.findAll('.adm-attn').map(b=>b.text());
 expect(attention[0]).toContain('3');expect(attention[1]).toContain('5');expect(attention[2]).toContain('2');expect(attention[3]).toContain('7');
 expect(w.text()).toContain('25%');expect(w.text()).toContain('41');
 const nav=w.findAll('.adm-nav-item');
 expect(nav.find(b=>b.text().startsWith('Content Reports')).text()).toContain('3');
 expect(nav.find(b=>b.text().startsWith('Processing')).find('.adm-badge.danger').text()).toBe('2');
 await w.findAll('.adm-attn')[2].trigger('click');await flushPromises();
 expect(w.get('.adm-title h1').text()).toBe('Processing');expect(localStorage.getItem('pyq-admin-tab')).toBe('Processing');
 w.unmount();
});

it('shows settings in plain language',async()=>{
 localStorage.setItem('pyq-admin-tab','Settings');
 mocks.api.mockImplementation(async path=>path==='/admin/settings'?{llm_configured:false,llm_provider:'none',max_upload_size:115343360,ocr:true}:path==='/admin/stats'?{}:{});
 const w=mount(Admin);await flushPromises();
 const text=w.get('.settings-list').text();
 expect(text).toContain('AI-assisted extraction');expect(text).toContain('Off');expect(text).toContain('110 MB');expect(text).toContain('Not set');expect(text).toContain('On');
 expect(text).not.toContain('115343360');
 w.unmount();
});
