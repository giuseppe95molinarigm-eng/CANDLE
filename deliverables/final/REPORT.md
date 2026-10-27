# The First-Try Edible Candle Cookbook — Rapporto di consegna (formattazione + 150 immagini)

Autrice: Margot Ellery · Lingua: inglese · Data: 27 ottobre 2026

## File consegnati (`deliverables/final/`)

| File | Contenuto |
|---|---|
| `The_First-Try_Edible_Candle_Cookbook_Paperback_Interior.pdf` | Interno paperback, pronto per KDP (99,8 MB) |
| `The_First-Try_Edible_Candle_Cookbook_Kindle.epub` | Ebook Kindle, EPUB 3 reflowable (9,2 MB) |
| `corrections_log.md` | Elenco delle correzioni al testo approvate dall'autrice |
| `image_manifest.csv` | 150 righe: codice ricetta/immagine, file, pixel, dimensione in pagina, ppi effettivi, modello, prompt |
| `../../images/final/NNN_nome_ricetta.jpg` | Le 150 immagini sorgente (2400 × 1792 px; 5 a 2752 × 1536) |

## Dati per dorso e cover paperback

- **Pagine: 225.**
- Formato al taglio: 8,5 × 11 in. Interno a colori, carta bianca.
- **Con abbondanza (bleed): sì.** Pagina PDF 8,625 × 11,25 in (0,125 in sui lati esterno, alto e basso).
- Spessore del dorso stimato:
  - **circa 0,53 in** con colore Premium (225 × 0,002347 in);
  - **circa 0,51 in** con colore Standard (225 × 0,002252 in).
- Cover completa stimata (Premium): circa **17,78 × 11,25 in** (0,125 + 8,5 + dorso + 8,5 + 0,125).
- Va confermato con il calcolatore cover di KDP dopo aver scelto il tipo di stampa.
- Il libro supera le 79 pagine, quindi il testo sul dorso è consentito.
- Stampa consigliata: **Premium Color**, per la qualità delle foto; la Standard Color costa meno ma rende meno.

## Specifiche adottate

- **Margini:** gutter 0,875 in (minimo KDP per 151–300 pagine: 0,5 in). Esterno 0,6 in dal taglio (minimo 0,375 in con bleed). Testatine e folio a circa 0,38 in dal taglio.
- **TrimBox e BleedBox** sono impostati pagina per pagina: abbondanza a destra sulle pagine dispari e a sinistra sulle pari, nessuna abbondanza sul lato dorso.
- **Font:** Playfair Display per i titoli, Cinzel per le etichette, Source Serif 4 per il testo. Licenza OFL, tutti incorporati (10/10).
  - Source Serif 4 è stato scelto perché contiene tutte le frazioni del manoscritto (½ ¼ ¾ ⅓ ⅔ ⅛) e la ✓.
- **Nessun segno di taglio.**
- **Palette ripresa dalla cover:**
  - verde foresta per aperture, barra dei tempi e intestazioni delle tabelle;
  - oro antico per titoletti, numeri dei passaggi e filetti;
  - crema per ingredienti e riquadri.
- **Aperture:** 14 pagine verde scuro al vivo (4 Parti e 10 Capitoli), sempre su pagina dispari. Nell'apertura del Capitolo 4 compare anche la nota del manoscritto sui formaggi vegetariani.
- **Modello ricetta** (sempre lo stesso):
  - numero, etichette dieta, titolo;
  - barra con resa, metodo e tempi;
  - introduzione;
  - ingredienti accanto alla foto;
  - procedimento su due colonne;
  - First-Try Tip;
  - Pair / Serve / Make ahead in tre colonne.
- **Foto adattiva**, scelta in automatico per non rimpicciolire il testo:
  - grande 4,4 × 3,3 in: 108 ricette;
  - media 4,0 × 2,85 in: 25;
  - piccola 3,6 × 2,45 in: 7.
  - Risultato: **140 ricette su una pagina**.
  - Le 10 più lunghe (16, 23, 36, 75, 86, 102, 107, 111, 116, 123) usano un layout su due pagine: foto a tutta larghezza e ingredienti nella prima, procedimento nella seconda, con "Continued on next page →" e il titolo ripetuto in testata. Nessun ingrediente o passaggio è diviso tra due pagine.
- **Immagini in stampa:** 2200 px, JPEG di qualità 88, **313–611 ppi effettivi** alla dimensione d'uso (minimo 300).
- **EPUB:**
  - reflowable, senza colonne né numeri di pagina;
  - indice navigabile (parti, capitoli, sezioni e tutte le 150 ricette), landmarks e NCX;
  - indice A–Z e Recipe Finder con link;
  - i rimandi "(recipe N)" e "(Bread Bn)" sono link;
  - foto a 800 px che si adattano allo schermo, con testo alternativo tratto dalle descrizioni del manoscritto.
  - Nella Recipe Finder dell'EPUB le quattro colonne con ✓ sono raggruppate in una colonna "Diet", per la leggibilità su telefono.

## Immagini

- **150 immagini originali, una per ricetta**, codificate `NNN_nome_ricetta` (per esempio `001_classic_sea_salt_butter_candle.jpg`), nessuna duplicata.
- Generate con Google Nano Banana Pro (via Replicate) a partire dalle descrizioni [IMAGE nnn] del manoscritto, con la cover come riferimento di palette.
- Vincoli dati al modello, tratti dalla Part One:
  - un solo stoppino di cotone con fiamma piccola;
  - candela sformata su un piatto o tagliere resistente al calore;
  - niente carta, tovaglioli o decorazioni vicino alla fiamma;
  - nessun'altra candela;
  - niente persone, bambini o animali;
  - nessun testo.
- **Revisione:** sei giri di controllo visivo hanno portato a **circa 40 rigenerazioni**. I problemi corretti:
  - candele o lumini sullo sfondo;
  - candela in barattolo invece che sformata;
  - forme sbagliate;
  - in un caso la candela mancava del tutto;
  - ragnatele o carta vicino alla fiamma;
  - scritte finte su buste, giornale, boccale e lavagna.
- Le 5 immagini del campione approvato (001, 030, 045, 103, 137) sono in 16:9 e ritagliate al formato della pagina; le altre 145 sono in 4:3.
- Spesa totale stimata su Replicate: **circa $30**, tra test, circa 200 immagini Pro e scarti.

## Verifiche svolte

1. **Testo:** script che confronta parola per parola i **4.971 paragrafi e celle di tabella** del manoscritto, esclusi i 150 segnaposto [IMAGE]. Risultato: 4.971/4.971 presenti nel PDF; tutti presenti anche nell'EPUB, salvo le modifiche intenzionali della Recipe Finder e del Contents descritte sopra.
2. **QA contenuti indipendente** (agente separato):
   - 150 ricette in ordine, 721 passaggi e tutte le liste ingredienti identici al manoscritto, frazioni e gradi compresi;
   - tutte le sezioni presenti;
   - nessun segnaposto, duplicazione o testo troncato;
   - titolo, sottotitolo e autrice coerenti tra frontespizio, copyright, metadati PDF ed EPUB;
   - 54/54 voci del Contents e 150/150 voci dell'indice A–Z con la pagina giusta;
   - 150/150 foto abbinate alla ricetta giusta, nessuna doppia.
3. **QA grafico/stampa indipendente:** tutte le 225 pagine ispezionate, 57 ad alta risoluzione.
   - box di pagina, margini (misurati sul testo), font, risoluzione, aperture e folio a posto;
   - nessuna sovrapposizione o testo tagliato;
   - nessun titolo isolato a fondo pagina.
   - I suoi rilievi sono stati corretti: tabelle spezzate, firma, Capitolo 9, gerarchia dei titoli dei pani, pallino a inizio riga nella barra dei tempi, pagina quasi vuota dopo il Capitolo 4, foto 141 con caratteri finti.
4. **QA EPUB indipendente:**
   - EPUBCheck 3.3: 0 errori, 0 avvisi;
   - tutti i 217 link della nav e tutti i link di Contents e indice funzionanti;
   - test su telefono e tablet con carattere al 100% e al 170%.
   - Correzioni applicate: colore del testo nei riquadri (modalità scura), tabelle più compatte, testo alternativo descrittivo, peso del file da 13,4 a 9,2 MB, rimandi trasformati in link, gerarchia dei titoli.
5. **Controllo automatico del layout:** 0 overflow, 0 immagini mancanti, 0 duplicati, nessun titolo a meno di 0,45 in dal fondo pagina.
6. **Coerenza interna:** indice A–Z, Recipe Finder (titoli, metodi, diete) e riferimenti dei Party Plans corrispondono alle ricette.

## Correzioni al testo (approvate dall'autrice)

Su indicazione dell'autrice ho corretto direttamente nel PDF e nell'EPUB le incongruenze del manoscritto. L'elenco completo, con il testo prima e dopo, è in `corrections_log.md` (24 interventi). In sintesi:

1. **Etichette dieta:** aggiunto NF alle ricette 61, 100, 121 e 127 (senza frutta a guscio) e GF alla 72, anche nella Recipe Finder.
2. **Ingredienti:** la 121 usa solo tamari; nella 74 il tamari è l'opzione predefinita; nella 149 l'almond extract è indicato come da omettere per una candela nut-free.
3. **Ordine dei passaggi:** i passaggi di finitura delle ricette 103, 108, 111, 136, 140 e 147 sono spostati dopo la formatura.
4. **Tempi di raffreddamento:** 137 da 4 a 3½ ore (somma dei passaggi); 111 da 2½ a 3 ore, stessa convenzione della ricetta 4.
5. **Sicurezza, ricetta 137:** il rosmarino lascia libera la parte alta vicino allo stoppino (la foto lo mostra già così).
6. **Nomi:** i Party Plans usano i titoli completi delle ricette; le etichette di "How to Use This Book" coincidono con quelle delle ricette.

Dopo le correzioni ho ripetuto tutti i controlli:
- etichette dieta e Recipe Finder coerenti su 150/150;
- nessun altro passaggio fuori ordine;
- tempi coerenti con i passaggi;
- nel PDF le uniche differenze dal manoscritto sono le correzioni elencate.

Le descrizioni [IMAGE] della 148 (ragnatele) e della 149 (decorazioni da festa) contrastavano con le regole di sicurezza: nelle foto quegli elementi sono solo sullo sfondo, lontani dalla fiamma.

Altri punti:

8. **Pagine 7 e 18:** contengono solo l'ultimo riquadro della sezione (nota sugli allergeni; nota "Burn times"). È l'ordine del manoscritto; il contenuto è completo.
9. **Copyright:** nessun ISBN né editore nei materiali forniti, quindi non ne ho inventati. Se si usa l'ISBN gratuito KDP, può essere aggiunto alla pagina copyright prima del caricamento.
10. **Cover dell'ebook:** quella inclusa nell'EPUB è la cover fornita, 1103 × 1426 px, sotto i 1600 × 2560 px raccomandati da Kindle. Su KDP va caricata a parte la cover ebook in alta risoluzione.
11. **Cover, ripetizione:** "150 TESTED RECIPES" sta proprio sopra un sottotitolo che inizia con "150 Tested…". È una ripetizione da valutare con chi cura la cover.
12. **Costo di consegna Kindle:** con l'opzione royalty 70% KDP applica un costo di consegna per MB. A 9,2 MB e $0,15/MB (tariffa USA nota) sono circa $1,40 a copia. Se serve, si può alleggerire ulteriormente.
13. **Modalità scura su Kindle:** testata in Chromium; va confermata in Kindle Previewer, che non è disponibile in questo ambiente.
14. **Manifest immagini:** per 78 immagini il prompt è ricostruito dal modello di prompt, perché le esecuzioni interrotte non hanno salvato il log; è indicato nella colonna `prompt_source`.

## Riproducibilità

Script in `build/`:

| Script | Funzione |
|---|---|
| `parse_manuscript.py` | lettura del manoscritto |
| `generate_images.py` | generazione immagini; chiave API letta da variabile d'ambiente, non salvata |
| `finalize_images.py`, `print_images.py` | preparazione delle immagini |
| `fit_recipes.py` | scelta del formato foto |
| `render_print.py`, `print.css`, `make_pdf.py`, `set_boxes.py` | PDF di stampa |
| `render_epub.py` | EPUB |
| `verify_text.py`, `check_layout.py` | controlli |

**Sicurezza:** la chiave Replicate è stata condivisa in chat. Va revocata e sostituita su replicate.com a fine progetto.
