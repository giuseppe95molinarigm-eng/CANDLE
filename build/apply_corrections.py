"""Author-approved corrections to the manuscript text.

Reads build/book_raw.json (verbatim parse of the manuscript) and writes
build/book.json, which the print and EPUB renderers use. Every change is listed
in CORRECTIONS and logged to deliverables/final/corrections_log.md.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

book = json.load(open(os.path.join(ROOT, 'build/book_raw.json')))
R = {it['num']: it for s in book['sections'] for it in s['items'] if it.get('type') == 'recipe'}
S = {s['title']: s for s in book['sections']}
log = []


def set_runs(p, runs):
    p['runs'] = runs
    p['text'] = ''.join(t for t, _, _ in runs)


def replace_in_runs(p, old, new):
    for r in p['runs']:
        if old in r[0]:
            r[0] = r[0].replace(old, new)
            p['text'] = ''.join(t for t, _, _ in p['runs'])
            return True
    raise ValueError(f'not found: {old!r} in {p["text"][:80]!r}')


def add_diet(n, label, after=None):
    r = R[n]
    m = re.match(r'^(.*?\s{3,})([A-Z]{1,2}(?:\s·\s[A-Z]{1,2})*)$', r['meta'])
    labels = m.group(2).split(' · ')
    assert label not in labels
    if after and after in labels:
        labels.insert(labels.index(after) + 1, label)
    else:
        labels.append(label)
    old = r['meta']
    r['meta'] = m.group(1) + ' · '.join(labels)
    # Recipe Finder tick
    t = [it for it in S['Recipe Finder']['items'] if it.get('type') == 'table'][0]
    head = [c[0]['text'] for c in t['rows'][0]]
    col = head.index(label)
    for row in t['rows'][1:]:
        if row[0][0]['text'] == str(n):
            cell = row[col]
            assert not ''.join(p['text'] for p in cell).strip()
            if cell:
                set_runs(cell[0], [['✓', False, False]])
            else:
                cell.append({'type': 'p', 'style': '', 'shd': None, 'num': None, 'runs': [['✓', False, False]],
                             'html': '✓', 'text': '✓', 'pagebreak': False})
    log.append(f'Recipe {n} ({r["title"]}): added diet label {label} (recipe page and Recipe Finder). '
               f'Was "{old.split("   ")[-1].strip()}".')


def ingredient(n, old, new, why):
    for c in R[n]['ingredients'][0]['rows'][0]:
        for p in c:
            if old in p['text']:
                replace_in_runs(p, old, new)
                log.append(f'Recipe {n} ({R[n]["title"]}): ingredient "{old}" -> "{new}". {why}')
                return
    raise ValueError(old)


def move_step(n, idx, to, why):
    """Move method step idx (1-based) so that it becomes step `to` (1-based, in the final list)."""
    steps = R[n]['method']
    st = steps.pop(idx - 1)
    steps.insert(to - 1, st)
    log.append(f'Recipe {n} ({R[n]["title"]}): moved method step {idx} ("{st["text"][:60]}…") to step {to}. {why}')


def split_sentence_to_last(n, idx, sentence, why):
    steps = R[n]['method']
    p = steps[idx - 1]
    replace_in_runs(p, ' ' + sentence, '')
    new = json.loads(json.dumps(p))
    set_runs(new, [[sentence, False, False]])
    steps.append(new)
    log.append(f'Recipe {n} ({R[n]["title"]}): the sentence "{sentence}" moved from step {idx} to a new final step. {why}')


def meta_replace(n, old, new, why):
    r = R[n]
    assert old in r['meta']
    r['meta'] = r['meta'].replace(old, new)
    log.append(f'Recipe {n} ({r["title"]}): "{old}" -> "{new}". {why}')


def text_replace(section, old, new, why):
    for it in S[section]['items']:
        if it.get('type') == 'p' and old in it.get('text', ''):
            replace_in_runs(it, old, new)
            log.append(f'{section}: "{old}" -> "{new}". {why}')
            return
    raise ValueError(old)


# ---------------------------------------------------------------- corrections
NO_NUTS = 'No nuts in the ingredients (the diet key says coconut is not counted as a tree nut).'
add_diet(61, 'NF'); log[-1] += ' ' + NO_NUTS
add_diet(100, 'NF'); log[-1] += ' ' + NO_NUTS
add_diet(121, 'NF'); log[-1] += ' ' + NO_NUTS
add_diet(127, 'NF'); log[-1] += ' ' + NO_NUTS
add_diet(72, 'GF', after='V'); log[-1] += ' No gluten in the ingredients; the tip already says "the candle itself is gluten-free".'

ingredient(121, '1 teaspoon tamari or soy sauce', '1 teaspoon tamari',
           'The recipe is labelled GF and the method uses tamari; regular soy sauce contains wheat.')
ingredient(74, '1 teaspoon soy sauce or tamari', '1 teaspoon tamari (or soy sauce if gluten is not a concern)',
           'The recipe is labelled GF; tamari is now the default, consistent with the tip.')
ingredient(149, '¼ teaspoon almond extract (optional)', '¼ teaspoon almond extract (optional; leave out for a nut-free candle)',
           'The recipe is labelled NF; consistent with the tip.')

ORDER = 'Finishing step was placed before the candle is packed; moved after serving.'
move_step(103, 3, len(R[103]['method']), ORDER)
move_step(136, 2, len(R[136]['method']), ORDER)
move_step(147, 2, len(R[147]['method']), ORDER)
move_step(108, 3, len(R[108]['method']) - 1, 'The step applies once the candle is unmolded; moved after the core is set, before serving.')
move_step(140, 2, len(R[140]['method']) - 1, 'The step applies once the candle is unmolded; moved after the core is set, before serving.')
split_sentence_to_last(111, 4, 'Sprinkle the flaky salt over the top of the finished candle after lighting.',
                       'It describes a finishing step after lighting.')

meta_replace(137, 'Chill 4 hours', 'Chill 3½ hours', 'The method steps add up to 3½ hours (2 h + 1 h + 30 min).')
meta_replace(111, 'Chill 2½ hours', 'Chill 3 hours',
             'Steps add up to about 3 hours including the 20–30 minute brown-butter set, the same convention as recipe 4 (Brown Butter Candle).')

st = R[137]['method'][4]
replace_in_runs(st, 'pointing downward like branches, and dot with cranberries.',
                'pointing downward like branches, keeping the top 1 in (2.5 cm) around the wick bare, and dot with cranberries.')
log.append('Recipe 137 (Rosemary Christmas Tree Candle), step 5: added "keeping the top 1 in (2.5 cm) around the wick bare" '
           'so the rosemary stays away from the flame, as required by Part One (herbs never next to the wick).')

PLAN = 'Name aligned with the recipe title.'
text_replace('Part Four: Holiday & Party Plans', 'the Sage, Cranberry & Orange Candle and the Turkey-Day Pillar',
             'the Sage, Cranberry & Orange Thanksgiving Candle and the Turkey-Day Herb Butter Candle', PLAN)
text_replace('Part Four: Holiday & Party Plans', 'make the cone mold and the Christmas Tree Candle',
             'make the cone mold and the Rosemary Christmas Tree Candle', PLAN)
text_replace('Part Four: Holiday & Party Plans', 'Decorate the Christmas Tree Candle',
             'Decorate the Rosemary Christmas Tree Candle', PLAN)
text_replace('Part Four: Holiday & Party Plans', 'the Cacio e Pepe Candle and', 'the Cacio e Pepe Butter Candle and', PLAN)

LABEL = 'Labels aligned with the ones used on every recipe page.'
text_replace('How to Use This Book', 'Pair It With.', 'Pair.', LABEL)
text_replace('How to Use This Book', 'Serve It.', 'Serve.', LABEL)
text_replace('How to Use This Book', 'Make Ahead & Storage.', 'Make ahead.', LABEL)

json.dump(book, open(os.path.join(ROOT, 'build/book.json'), 'w'), ensure_ascii=False, indent=1)
os.makedirs(os.path.join(ROOT, 'deliverables/final'), exist_ok=True)
with open(os.path.join(ROOT, 'deliverables/final/corrections_log.md'), 'w') as f:
    f.write('# Corrections applied to the manuscript text\n\n')
    f.write('Approved by the author. Everything else is exactly as in the manuscript.\n\n')
    for i, l in enumerate(log, 1):
        f.write(f'{i}. {l}\n')
print(len(log), 'corrections applied')
