# Ej publicerat på CurseForge ännu

Posten nedan är FÄRDIG BUTIKSTEXT och ligger kvar här, inte i publish/, tills
den dagen den faktiskt släpps. publish_site.sh globbar ut publish/*.md på
purrfect.pelleops.se, och en changelog på sajten som CurseForge inte har är en
mismatch. Vid släpp: flytta blocket mellan strecken överst i
publish/changelog.md, kör `tools/purrfect-ship --curseforge` och sedan
`./publish_site.sh`.

---

## 3.32.0 — A colony, not nine copies of the same cat

Until now every cat related only to you. Nine cats in a base behaved like nine
copies of one cat: they walked around separately and never took the slightest
notice of each other. That is the thing this release fixes.

**They groom each other.** Two tame cats standing close together will wash one
another now and then — hearts, a purr, and a little healing for both. Kittens
play instead, with a lighter meow and their own particles. Neither of them says
a word about it on your screen. The pack already learned that lesson the hard
way with the warning system; grooming is something you see, not something you
need to be told.

**They sleep in a pile.** At night the flock stops wandering and gathers on cat
beds and cardboard boxes. Before, a cat looking for somewhere to be would pick
the nearest of eight pieces of furniture — the food bowl, the cat flap, the fish
pond — so a house full of cats scattered instead of settling. After dark they
only look for places to sleep.

**And the pile actually looks like one.** The curled-up sleeping pose has been
in the pack all along, but it hung on a vanilla query that is never true for a
cat, so the game could never reach it. It has its own trigger now, and the cats
lie curled up together for real.

A saddled cat still goes where you steer her, night or not.

---

<!-- ALLT NEDANFÖR ÄR PROJEKTETS EGEN LOGG och ska INTE med till butiken. -->

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

