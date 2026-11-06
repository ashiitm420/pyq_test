import {it,expect,vi} from 'vitest';
import {mount,flushPromises} from '@vue/test-utils';
vi.mock('../src/api',()=>({api:vi.fn(),go:vi.fn(),session:{},loadCatalog:vi.fn(),loadHome:async()=>({stats:{},meta:{},courses:[]})}));
import Catalog from '../src/Catalog.vue';
it('keeps coding practice as an external home link',async()=>{
 const w=mount(Catalog,{props:{route:'/'},global:{stubs:{FeaturedStudy:true}}});
 await flushPromises();const link=w.get('a[href="https://oppe.rangalabs.cloud/"]');
 expect(link.attributes('target')).toBe('_blank');
 expect(link.attributes('rel')).toContain('noopener');
 expect(w.find('a[href="/admin/oppe"]').exists()).toBe(false);w.unmount();
});
