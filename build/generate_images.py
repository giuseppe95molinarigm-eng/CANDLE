"""Generate recipe photographs on Replicate.

The API token is read from REPLICATE_API_TOKEN (never stored in the repo).
Prompts are built from the approved [IMAGE nnn] briefs in the manuscript plus a
shared style block and the safety constraints from Part One.
"""
import argparse, base64, json, os, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

API = 'https://api.replicate.com/v1'
TOKEN = os.environ.get('REPLICATE_API_TOKEN', '')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STYLE = (
    "Professional editorial food photography for a premium cookbook, shot with a full-frame camera and 85mm lens, "
    "shallow depth of field, soft creamy bokeh, rich warm color grading. Overall palette and mood inspired by the "
    "cookbook cover: deep forest-green background tones, warm golden glow, rustic dark wood or slate, "
    "appetizing and realistic textures. The edible candle is the clear hero, sharp and centered, fully visible from "
    "base to flame, centered, with comfortable space above the flame and around it. Landscape 4:3 composition."
)
SAFETY = (
    "Safety details that must be respected: one single plain natural cotton wick in the center of the candle, "
    "trimmed short, with one small calm steady flame (no tall or smoky flame, no metal wick tab); the candle stands "
    "on a heatproof plate, board, cake stand or bread bowl; no paper napkins, paper decorations, dried flowers, "
    "curtains or other flammable items near the flame; herbs and garnishes never touch the flame; no people, "
    "hands, children or pets. The edible candle is the ONLY candle and the ONLY flame in the whole picture: no other "
    "candles, tea lights, tapers or candle holders anywhere, not even blurred in the background."
)
NEGATIVE = (
    "Absolutely no text, letters, numbers, labels, logos, watermarks, borders or frames anywhere in the image."
)
REF_NOTE = (
    "The attached reference image is the book cover: use it ONLY as a guide for color palette, lighting and "
    "photographic mood. Do not copy its composition, do not reproduce its title lettering, and show only the "
    "single candle described here."
)


def prompt_for(recipe, with_ref):
    p = (f"{recipe['image_brief']} The candle is the '{recipe['title']}', an edible candle made of "
         f"{ingredient_hint(recipe)}. {STYLE} {SAFETY} {NEGATIVE}")
    if with_ref:
        p += ' ' + REF_NOTE
    return p


def ingredient_hint(r):
    items = [p['text'] for c in r['ingredients'][0]['rows'][0] for p in c]
    items = [i for i in items if 'wick' not in i and not i.startswith('For ')]
    return '; '.join(items)


def call(method, url, body=None, headers=None):
    h = {'Authorization': 'Bearer ' + TOKEN}
    h.update(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def upload_reference(path):
    """Return a data URI for the cover reference (Replicate accepts data URIs)."""
    from PIL import Image
    import io
    im = Image.open(path).convert('RGB')
    im.thumbnail((768, 768))
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=85)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


MODELS = {
    'seedream4': ('bytedance/seedream-4', lambda p, ref: {
        'prompt': p, 'size': '2K', 'aspect_ratio': '16:9', 'image_input': [ref] if ref else [],
        'enhance_prompt': False, 'max_images': 1}),
    'fluxultra': ('black-forest-labs/flux-1.1-pro-ultra', lambda p, ref: {
        'prompt': p, 'aspect_ratio': '16:9', 'output_format': 'png', 'raw': False, 'safety_tolerance': 2}),
    'nanobananapro': ('google/nano-banana-pro', lambda p, ref: {
        'prompt': p, 'resolution': '2K', 'aspect_ratio': '4:3', 'output_format': 'png',
        'image_input': [ref] if ref else []}),
}
USES_REF = {'seedream4': True, 'fluxultra': False, 'nanobananapro': True}


def run(model_key, recipe, outdir, ref, log):
    model, build = MODELS[model_key]
    p = prompt_for(recipe, USES_REF[model_key] and ref)
    body = {'input': build(p, ref if USES_REF[model_key] else None)}
    for attempt in range(8):
        try:
            pred = call('POST', f'{API}/models/{model}/predictions', body, {'Prefer': 'wait=60'})
            while pred['status'] not in ('succeeded', 'failed', 'canceled'):
                time.sleep(3)
                pred = call('GET', pred['urls']['get'])
            if pred['status'] != 'succeeded':
                raise RuntimeError(pred.get('error'))
            out = pred['output']
            url = out[0] if isinstance(out, list) else out
            ext = os.path.splitext(url.split('?')[0])[1] or '.png'
            dest = os.path.join(outdir, recipe['code'] + ext)
            urllib.request.urlretrieve(url, dest)
            log.append({'code': recipe['code'], 'model': model, 'prediction': pred['id'], 'file': os.path.relpath(dest, ROOT),
                        'predict_time': pred.get('metrics', {}).get('predict_time'), 'prompt': p})
            print('ok', model_key, recipe['code'], flush=True)
            return dest
        except urllib.error.HTTPError as e:
            wait = 12 * (attempt + 1)
            if e.code == 429:
                try:
                    wait = max(wait, int(json.load(e).get('retry_after', 10)) + 2)
                except Exception:
                    pass
            print('retry', model_key, recipe['code'], attempt, e, flush=True)
            time.sleep(wait)
        except Exception as e:
            print('retry', model_key, recipe['code'], attempt, e, flush=True)
            time.sleep(10 * (attempt + 1))
    print('FAILED', model_key, recipe['code'], flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--models', default='seedream4')
    ap.add_argument('--recipes', default='all', help='comma list of numbers or "all"')
    ap.add_argument('--out', default='images')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--skip-existing', action='store_true')
    a = ap.parse_args()
    book = json.load(open(os.path.join(ROOT, 'build/book.json')))
    rs = [it for s in book['sections'] for it in s['items'] if it.get('type') == 'recipe']
    if a.recipes != 'all':
        want = {int(x) for x in a.recipes.split(',')}
        rs = [r for r in rs if r['num'] in want]
    ref = upload_reference(os.path.join(ROOT, 'source/cover.jpg'))
    log = []
    jobs = []
    with ThreadPoolExecutor(a.workers) as ex:
        for mk in a.models.split(','):
            outdir = os.path.join(ROOT, a.out, mk)
            os.makedirs(outdir, exist_ok=True)
            for r in rs:
                if a.skip_existing and any(f.startswith(r['code'] + '.') for f in os.listdir(outdir)):
                    continue
                jobs.append(ex.submit(run, mk, r, outdir, ref, log))
        [j.result() for j in jobs]
    logpath = os.path.join(ROOT, a.out, 'generation_log.jsonl')
    with open(logpath, 'a') as f:
        for l in log:
            f.write(json.dumps(l, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
