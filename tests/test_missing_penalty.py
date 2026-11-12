import pytest
from types import SimpleNamespace as N
from backend.engine import grade,aggregate

@pytest.mark.parametrize('kind,key,response',[('MCQ',['A'],['A']),('TRUE_FALSE',['A'],['A']),('NAT',2.5,2.5),('SHORT_TEXT',{'values':['yes']},'yes')])
def test_correct_key_awards_known_marks_without_wrong_answer_penalty(kind,key,response):
    snap=dict(kind=kind,answers=key,answer_status='ANSWER_AVAILABLE',marks=1,negative_marks=None,tolerance=0)
    assert grade(snap,response)==dict(outcome='CORRECT',awarded=1)


def test_no_negative_marking_policy_applies_to_missing_and_legacy_penalties():
    snap=dict(kind='MCQ',answers=['A'],answer_status='ANSWER_AVAILABLE',marks=1,negative_marks=None)
    assert grade(snap,['B'])==dict(outcome='INCORRECT',awarded=0)
    assert grade({**snap,'negative_marks':0},['B'])==dict(outcome='INCORRECT',awarded=0)
    assert grade({**snap,'negative_marks':.25},['B'])==dict(outcome='INCORRECT',awarded=0)
    r=aggregate(N(items=[N(snapshot=snap,outcome='CORRECT',awarded=1)],started_at=0,submitted_at=10))
    assert r['score']==1 and r['percentage']==100 and not r['partial_score']
    assert grade({**snap,'marks':None},['A'])['outcome']=='UNGRADED'


def test_proportional_msq_keeps_its_explicit_zero_penalty_rule():
    snap=dict(kind='MSQ',answers=['A','B'],answer_status='ANSWER_AVAILABLE',marks=2,negative_marks=None,msq_scoring='proportional-v1')
    assert grade(snap,['A'])==dict(outcome='PARTIAL',awarded=1)
    assert grade(snap,['C'])==dict(outcome='INCORRECT',awarded=0)
