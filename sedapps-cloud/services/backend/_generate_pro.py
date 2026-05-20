import time
from app.database import SessionLocal
from app.models import Project
from app.llm_site_generator import generate_site_single_shot
from app.config import settings

print('model =', settings.deepseek_model, flush=True)
pid = '38b0aa31-d3a9-4ca2-b646-8ab53b7d507d'
db = SessionLocal()
try:
    p = db.query(Project).filter(Project.id == pid).first()
    if p is None:
        raise SystemExit('project not found')
    brief = p.brief or {}
    def cb(e):
        print(f"[{e.get('progress')}%] {e.get('step')} - {e.get('label')}", flush=True)
    t = time.time()
    agents, output, sections, files = generate_site_single_shot(brief, on_progress=cb)
    status = agents[0].get('status')
    print('done', round(time.time()-t, 1), 's status=', status, 'files=', [f['path'] for f in files], 'tokens=', agents[0].get('tokens_out'), flush=True)
    if status == 'ok':
        p.design_tokens = output.get('design_tokens') or {}
        p.seo = output.get('seo') or {}
        p.sections = sections
        p.generated_files = files
        p.status = 'ready'
        db.add(p)
        db.commit()
        print('saved preview_nonce=', p.preview_nonce, flush=True)
    else:
        print('error=', agents[0].get('error'), flush=True)
finally:
    db.close()
