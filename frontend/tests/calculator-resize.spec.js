import {describe,it,expect} from 'vitest';
import {mount} from '@vue/test-utils';
import Calculator from '../src/TcsCalculator.vue';

describe('calculator resize',()=>{
 it('opens at the requested ratio within the viewport',()=>{
  const w=mount(Calculator);
  const width=parseFloat(w.element.style.width),height=parseFloat(w.element.style.height);
  expect(width/height).toBeCloseTo(1709/822,5);
  expect(width).toBeLessThanOrEqual(window.innerWidth-16);
  expect(height).toBeLessThanOrEqual(window.innerHeight*.85);
  w.unmount();
 });
 it('resizes from the keyboard, clamps to the viewport and preserves the expression',async()=>{
  const w=mount(Calculator,{attachTo:document.body});
  let width=600,height=500;
  w.element.getBoundingClientRect=()=>({left:20,top:20,width,height});
  await w.get('input[aria-label="Calculator expression"]').setValue('2+3');
  const handle=w.get('button[aria-label="Resize calculator"]');
  await handle.trigger('keydown',{key:'ArrowRight'});
  expect(w.element.style.width).toBe('620px');
  width=10000;height=10000;
  await handle.trigger('keydown',{key:'ArrowDown'});
  expect(parseFloat(w.element.style.width)).toBeLessThanOrEqual(window.innerWidth-28);
  expect(parseFloat(w.element.style.height)).toBeLessThanOrEqual(window.innerHeight-28);
  expect(w.get('input[aria-label="Calculator expression"]').element.value).toBe('2+3');
  w.unmount();
 });
 it('supports pointer resizing and stops responding after release',async()=>{
  const w=mount(Calculator);
  w.element.getBoundingClientRect=()=>({left:20,top:20,width:500,height:400});
  await w.get('[aria-label="Resize calculator"]').trigger('pointerdown',{clientX:500,clientY:400,button:0});
  window.dispatchEvent(new MouseEvent('pointermove',{clientX:550,clientY:430}));
  expect(w.element.style.width).toBe('550px');expect(w.element.style.height).toBe('430px');
  window.dispatchEvent(new MouseEvent('pointerup'));
  window.dispatchEvent(new MouseEvent('pointermove',{clientX:700,clientY:600}));
  expect(w.element.style.width).toBe('550px');w.unmount();
 });
});
