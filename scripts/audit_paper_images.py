"""Read-only, bounded R2 existence audit. Run outside the web request path."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paper_id',type=int)
    args=parser.parse_args()
    from backend import create_app
    from backend.models import db,Paper,Question,QuestionImage
    from backend.storage import remote_head
    app=create_app()
    with app.app_context():
        if app.config['STORAGE_BACKEND']!='r2':raise SystemExit('R2 configuration is required.')
        paper=db.session.get(Paper,args.paper_id)
        if paper is None:raise SystemExit('Paper not found.')
        pid=paper.canonical_paper_id or paper.id
        # Project only paths and close the DB transaction before remote I/O.
        paths=[p for p, in db.session.query(QuestionImage.path).join(Question).filter(Question.paper_id==pid).distinct().limit(501)]
        db.session.remove()
        if len(paths)>500:raise SystemExit('More than 500 assets: split this audit before proceeding.')
        missing=[]
        for index,path in enumerate(paths,1):
            head=remote_head(path)
            if not head or not head.get('ContentLength'):missing.append(index)
        print(f'paper_id={args.paper_id} checked={len(paths)} missing_or_empty={len(missing)}')
        print('Read-only existence check; no publication flags or objects changed.')
        return 1 if missing else 0

if __name__=='__main__':raise SystemExit(main())
