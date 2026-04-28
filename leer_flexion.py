import os, pdfplumber, sys
sys.stdout.reconfigure(encoding='utf-8')

base = os.path.expandvars('%USERPROFILE%') + '/Desktop'
dirs = os.listdir(base)
hormigon_dir = next(d for d in dirs if 'HORMIG' in d)
path = os.path.join(base, hormigon_dir, 'REGLAMENTOS Y EJERCICIOS',
                    'CIRSOC 201-2005 - Ejemplos de aplicación - Parte 1.pdf')

with pdfplumber.open(path) as pdf:
    # Ejemplos de flexion estan aprox en pag 15-40 del PDF
    for i in range(14, 40):
        text = pdf.pages[i].extract_text()
        if text:
            print(f'\n=== Pagina {i+1} ===')
            print(text[:2000])
