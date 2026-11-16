import pytest
from backend.numeric import parse_numeric_answer_block, numeric_correct
from backend.automatic_parser import parse_document

@pytest.mark.parametrize('raw,inside,outside',[
 ('16\nBDBN\nSection Id : 123\nSection Number : 2','16','17'),
 ('9.4 to 9.6\n\nSPG\fSection Id : 456\nSection Number : 2','9.5','9.7'),
 ('-36 to -30\nDesign Thinking\nSection Id : 123','-33','-29'),
 ('0\nSection Id : 123','0','1'),
 ('1\n2\nIndustry 4.0\nSection Id : 123','2','3'),
 ('87 to 88','87','89'),
])
def test_only_explicit_numeric_lines_are_keys(raw,inside,outside):
 key=parse_numeric_answer_block(raw)
 assert numeric_correct(inside,key) and not numeric_correct(outside,key)
 assert 'Section' not in key['raw']

@pytest.mark.parametrize('raw',['','foo\nSection Id : 123','16\nunknown','16\n9.4 to nope\nSection Id : 123','16\nfirst title\nsecond title\nSection Id : 123','1/0','16\nPossibly 17'])
def test_ambiguous_or_invalid_keys_are_not_invented(raw):
 with pytest.raises((ValueError,ArithmeticError)):parse_numeric_answer_block(raw)

def test_parser_grades_last_numeric_question_before_next_subject_without_changing_stem():
 text='Question Number : 9 Question Id : 12345678 Question Type : SA\nCorrect Marks : 3\nQuestion Label : Short Answer Question\nFind the increase.\nResponse Type : Numeric\nPossible Answers :\n9.4 to 9.6\nSPG\nSection Id : 123\nSection Number : 2\n'
 layout={'text':text,'pages':[(0,len(text),1)],'assets':{},'indicators':{},'warnings':[]}
 q=parse_document(layout)[0][0]
 assert q['kind']=='NAT' and q['answers']['kind']=='range'
 assert q['answers']['lower']=='9.4' and q['answers']['upper']=='9.6'
 assert q['text']=='Find the increase.'
 assert not any(w.startswith('UNPARSED_NUMERIC_KEY') for w in q['warnings'])
