import {test} from 'node:test';
import assert from 'node:assert/strict';
import {displayExamTitle} from '../src/displayTitle.js';
test('exam heading preserves paper context without filename or verbose timer suffix',()=>{
 assert.equal(displayExamTitle('Deep Learning · Quiz 1 · May 2026 · cs3004_2026T2_Q1_NA.pdf · timed practice (user-selected duration)'),'Deep Learning · Quiz 1 · May 2026');
 assert.equal(displayExamTitle('Practice bookmarks'),'Practice bookmarks');
});
test('paper name that only repeats exam and term is not shown twice',()=>{
 assert.equal(displayExamTitle('Software Testing · Quiz 1 · May 2026 · Quiz 1 May 2026'),'Software Testing · Quiz 1 · May 2026');
 assert.equal(displayExamTitle('Software Testing · Quiz 1 · May 2026 · Set A (Morning)'),'Software Testing · Quiz 1 · May 2026 · Set A (Morning)');
 assert.equal(displayExamTitle('Wrong-answer practice · Statistics I · Quiz 1 · Jan 2026 · Quiz 1 Jan 2026'),'Wrong-answer practice · Statistics I · Quiz 1 · Jan 2026');
});
