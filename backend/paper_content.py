"""Shared source snapshots: keys stay server-side, independent of student state."""
from sqlalchemy.orm import selectinload, load_only
from .models import Question, QuestionOption, QuestionImage
from .engine import question_snapshot, question_order
from .content_cache import cached


def snapshots(paper_id):
    def load():
        with slim_session() as session:
            query=slim_question_query(session).options(
                selectinload(Question.options).load_only(QuestionOption.key,QuestionOption.text,QuestionOption.position),
                selectinload(Question.images).load_only(QuestionImage.id,QuestionImage.path,QuestionImage.alt,QuestionImage.option_key)
            ).filter(Question.paper_id==paper_id,Question.status=='AVAILABLE')
            rows=[]
            for q,*evidence in query.all():
                apply_slim_evidence(q,evidence);rows.append(q)
            unique_rows=list({q.id:q for q in rows}.values())
            result=[question_snapshot(q) for q in sorted(unique_rows,key=lambda q:(question_order(q.number),q.id))]
        # Older imports tagged comprehension questions but stored passage+prompt
        # together. Consecutive children share the exact passage prefix, so infer
        # it once at paper level instead of guessing from the first paragraph.
        i=0
        while i<len(result):
            if not result[i].get('shared_passage') or result[i].get('passage'):
                i+=1;continue
            j=i
            while j<len(result) and result[j].get('shared_passage') and not result[j].get('passage'):j+=1
            group=result[i:j]
            if len(group)>=2:
                texts=[x.get('text','') for x in group]
                prefix=texts[0]
                for value in texts[1:]:
                    n=0;limit=min(len(prefix),len(value))
                    while n<limit and prefix[n]==value[n]:n+=1
                    prefix=prefix[:n]
                    if not prefix:break
                cut=prefix.rfind('\n\n')
                if cut>20:
                    passage=prefix[:cut].strip()
                    for item in group:
                        if item['text'].startswith(passage):
                            item['passage']=passage
                            item['text']=item['text'][len(passage):].lstrip()
            i=j
        return result
    return cached('paper:'+str(paper_id)+':snapshots:msq-proportional-v1',load)


# Evidence keys that public snapshots and solution versions actually read.
# Extraction diagnostics (answer_indicators, answer_source, raw_answer, …) are
# often more than half of the column and are never shown to students, so they
# stay in Supabase instead of being sent to Render on every cache rebuild.
SNAPSHOT_EVIDENCE_KEYS=('shared_passage_text','subquestion_text','shared_passage','layout_assets','_active_image_ids')
SNAPSHOT_COLUMNS=(Question.id,Question.paper_id,Question.number,Question.kind,Question.text,
                  Question.answers,Question.answer_status,Question.explanation,Question.marks,
                  Question.negative_marks,Question.tolerance,Question.topic,Question.difficulty,
                  Question.source_page,Question.source_pages)


def slim_session():
    """A short-lived session for slim reads. Its objects never mix with the
    request identity map, so partial evidence cannot overwrite full evidence.
    Share its connection without owning the outer transaction or taking a
    second pool slot."""
    from sqlalchemy.orm import Session
    from .models import db
    return Session(db.session.connection(),autoflush=False,expire_on_commit=False,join_transaction_mode='rollback_only')


def slim_question_query(session,*entities):
    """Query Question (plus optional extra entities) with only the evidence keys
    snapshots need. Call apply_slim_evidence() on each result row."""
    extra=[Question.evidence[k] for k in SNAPSHOT_EVIDENCE_KEYS]
    return session.query(Question,*entities,*extra).options(load_only(*SNAPSHOT_COLUMNS))


def apply_slim_evidence(question,values):
    """Attach the slim evidence without marking the object changed."""
    from sqlalchemy.orm.attributes import set_committed_value
    set_committed_value(question,'evidence',{k:v for k,v in zip(SNAPSHOT_EVIDENCE_KEYS,values) if v is not None})
