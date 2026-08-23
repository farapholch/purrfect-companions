# Ej publicerat på CurseForge ännu

(tomt — allt fram till 3.31.7 flyttades in i publish/changelog.md vid släppet
2026-08-20. Nya opublicerade poster skrivs HÄR, inte i publish/, eftersom
publish_site.sh lägger ut publish/*.md på purrfect.pelleops.se och en
changelog på sajten som CurseForge inte har blir en mismatch.)

## Kolonin

Katterna förhåller sig till VARANDRA, inte bara till spelaren. Fram till nu
betedde sig nio katter i en bas som nio kopior av en enda katt.

- **Tvättningen.** Två tämjda katter som står nära varandra tvättar varandra då
  och då — hjärtan, spinnande och lite läkning för båda. Kattungar leker i
  stället, med ljusare jamande och egna partiklar.
- **Sovhögen.** På natten byts `mjau:fri` mot en ny grupp `mjau:sovdags` som
  bara söker sovplatser (bädd och kartong) i stället för åtta möbeltyper, så
  flocken samlas i stället för att sprida sig över matskål och fiskdamm.
- **Och högen SYNS.** `animation.katt.sova` fanns redan men hängde på
  `q.is_sleeping`, en vaniljfråga som aldrig blir sann för en katt — staten
  fanns i styrfilen men gick inte att nå. Den nya egenskapen `mjau:sover`
  driver den nu, så katterna ligger hopkurade på riktigt.
- Inga meddelanden för tvätt och lek. Varningssystemet bär redan en hel
  kommentar om vad som händer när paketet tjatar; tvättningen syns och behöver
  inga ord. Bara sovhögen säger till, en gång per natt och spelare.

### Fyra fel som testet hittade, alla i det jag just byggt

- **Nattgruppen lånade `mjau:fri`:s prioriteter** (12 och 15) med motiveringen
  att de aldrig är aktiva samtidigt. Strukturgrinden underkände det på alla tio
  katterna, och den hade rätt: exklusiviteten fanns bara i skriptets beteende,
  inte i datan. Egna prioriteter (19, 20) nu.
- **En sadlad katt behöll nattgruppen.** `mjau:on_sadel_*` tar bort de
  självgående grupperna så att katten inte går sin väg medan du rider — men
  inte den nya. Grinden namngav det exakt: "katten styr sig själv under
  ridning".
- **Testet tävlade mot kattens AI.** Två katter summonade ett block isär hann
  glida till mellan 2,5 och 3,0 block — nog för sovhögen, för långt för
  tvättningen. Testet flyttar dem nu till samma ruta först.
- **Testkroken mätte fel sak.** Loopen hade redan tvättat paret sekunden efter
  tämjningen, så paret satt på 45 sekunders paus när kroken kördes och
  `parTyst` växte inte. Testet rapporterade "inget par tvättade varandra" om en
  mekanik som fungerade. Kroken nollställer pauserna först.

