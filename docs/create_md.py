from pathlib import Path
from openmc.data import ELEMENT_SYMBOL
element_names = {v: k for k, v in ELEMENT_SYMBOL.items()}

here = Path('docs/fns')
assert(here.exists()), 'fns folder does not seem to exist. Run `download_fns_fusion_decay.py` first to download and unzip FNS benchmark files.'
data = {}
files = [q for q in here.glob('*') if q.is_dir()]
for f in files:
    if '_' in f.name: continue
    l = list(f.glob('*fluxes*'))
    data[f.name] = []
    for name in l:
        x = name.name.replace('_fluxes', '')
        data[f.name].append(x)

chapters = []
for element, experiments in data.items():
    filename = f"docs/{element}.md"
    with open(filename, 'w') as file:
        if element in element_names.keys():
            file.write(f"# {element} - {element_names[element]}\n\n")  # Title
        else:
            file.write(f"# {element}\n\n")  # Title

        for experiment in experiments:
            file.write(f"## {experiment}\n\n")  # Subtitle
            image_filename = f"{element}_{experiment}.png"
            file.write(f'![Alt text]({image_filename})\n\n')  # Image with optional title


    chapters.append(f"- file: docs/{element}")

chapters.sort()

for chapter in chapters:
    print(chapter)
