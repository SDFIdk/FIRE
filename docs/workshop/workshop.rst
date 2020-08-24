.. _workshop:



Præsentation af FIRE 
---------------------
FIRE indeholder alt den relevante information, som refgeo gør. Der er punktnumre,
identer, skitser, koordinater, tidsserier, beskrivelse, afmærkningstyper osv. osv.
Strukturen er dog en helt anden og meget mere overskuelig og vedligeholdelsesvenlig
nede i maven på databasen, hvilket gør FIRE til en markant forbedring af et af 
vores vigtigste dataarkiver. 

Dog er alt vores nuværende udjævnings- og datahåndteringssoftware (fx. ADJ, 
``valde`` og ``vedl.pl``) tilpasset refgeo og det famøse KSM-format, hvilket ikke kan
bruges i det nye setup. 
Derfor har vi udviklet adskillige kommandolinjekald, som har til formål at lade 
brugeren se ned i databasen, udtrække det data der er relevant, putte ny data 
ned i databasen osv. 
Det er en løbende opgave, hvor der bliver udviklet den funktionalitet, som viser 
sig nødvendig og brugbar til et gentagent formål.

Hvis nogen havde håbet på en lækkert designet brugergrænseflade med søgebokse og 
kasser, der kan hakkes af og en knap med *beregn* til til at lave en udjævning, 
som derefter bliver vist i QGIS, så må vi skuffe. 
Det er ikke der vi er; vi er slet ikke nok folk til at kunne retfærdiggøre at 
bruge tid og penge på at udvikle sådan noget, og desuden vil det være et hejs at 
vedligeholde og videudvikle kode til, hvilket vi helst vil gøre selv.
Derfor er det altså stadig kommandolinjekald, som er vejen frem! Men dermed bliver 
overgangen til ny database og beregningssoftware nok ikke så slem alligevel.

Nedenfor uddybes de funktionaliteter vi på nuværende tidspunkt har udviklet. Det er 
alle underprogrammer (og under-underprogrammer) under ``fire`` og køres derfor ved 
først at kalde ``fire`` efterfulgt af underkommandoens navn.

fire info
++++++++++++++++++++

En grundliggende funktionalitet er at kunne se hvilken data, der ligger i databasen, 
altså hvilken info man har i arkivet. Til det er der udviklet et kommandolinjeprogram 
kaldet ``fire info``. Man kan se hvad programmet indeholder ved at taste 

	> fire info --help

Herfra ses fem forskellige kommandoer man kan bruge:

- ``infotype`` 
- ``obstype``
- ``punkt``
- ``sag``
- ``srid``

Hvis man ønsker at fremsøge et punkt og se hvilke oplysninger, der knytter sig 
til det (som man før kunne med ``valde``, eller Valdemar i tjenesten), kan man 
fx taste:

	> fire info punkt g.i.2010

.. note:: Det er ligegyldet om der skrives med stort eller småt eller om der 
   benyttes punktummer eller ej i argumentet.

I udtrækket plottes diverse oplysninger om punktet direkte på skærmen, som set 
på billedet:

.. image:: fireinfopunkt.png
  :width: 800
  :alt: Udtræk fra databasen for punkt G.I.2010

Udtrækket viser den formodede relevante information, der ligger på punktet fra 
attribut-tabellerne og fra koordinattabellerne.
I eksemplet ses det fx, at punktet er oprettet i databasen 19/3 1985, at det også 
hedder K-11-09263, og i øvrigt er et jessenpunkt til en tidsserie, samt at det 
har en DVR90-kote fra 3. præc. indikeret ved EPSG-kode 5799 og beregningstidspunkt 
11/2-2000 kl. 13:30), en plankoordinat fra 2011 (med EPSG-koden 4258) og to andre 
koordinater i andre net. **Farven grøn indikerer at koordinaten er den gældende for 
det pågældende net.**

På samme måde kan andre elementer slås op i databasen, bl.a. oplysninger om historiske 
koter med parameteren *-K*, observationer med parameteren *-O* og andre detaljer med 
parameteren *-D*.

Øvelse
^^^^^^^^^^^^^^^^^^^^

Prøv selv at fremsøge mere info, fx:

1. alle observationer fra et givent punkt
2. alle historiske koordinater for et punkt
3. tekstbeskrivelsen på attributten AFM:2701
4. alle aktive sager i databasen




fire niv
++++++++++++++++++++++++++++++++
Der er blevet udviklet et kommandolinjeprogram til udjævningsberegning kaldet ``niv``. 
Læs om hvordan programmet kaldes :ref:`her <kommandolinjeprogrammer_niv>`

Fra dette kald kan hele produktionslinjen køres; fra dataudtræk, revision, beregning, 
til ilægning af resultat og generering af afsluttende rapport til kunde. Se mere ved 
at køre kaldet::

	> fire niv --help

Alt datahåndtering foregår på Windows og i Excelregneark med diverse faneblade. 
Vi vil nedenfor gennemgå processen.

Step 1) opret-sag
^^^^^^^^^^^^^^^^^^^^^^^^

I ``fire`` har vi valgt at knytte al beregning og punkthpndtering op på såkaldte 
*sagsevents*. Det vil sige at når man går igang med et nyt projekt, fx. en opgave 
omhandlende opmåling og beregning af lokal vandstand i Havnebyen, så opretter man 
en sag til denne opgave, hvori alt ens dataudtræk, observationer, beregninger og 
endelige resultater bliver registreret på. Kaldet, der skal køres under ``fire niv`` 
for at oprette en ny sag, hedder, passende nok, ``opret-sag``. Lad os prøve at få 
mere hjælp::

	> fire niv opret-sag --help

Her kommer en beskrivelse af hvad der forventes af input:

- Options: Valgfrit. Valgmuligheder ses i hjælpeteksten.
- Projektnavn: Obligatorisk. Kan fx være *Fjernkontrol af SULD*. Dette bliver navnet 
  på dit regneark. 
- Sagsbehandler: Obligatorisk. Skal være opretters FULDE NAVN.
- Beskrivelse: Valgfrit, men en god idé at beskrive nærmere hvad sagen indeholder, 
  fx "Nivellement af skruepløkke samt lodrette bolte ved SULD samt fjernkontrol til 
  5D-punktet GRAV. Antenne IKKE opført." 

I terminalen vil det se ud som dette, når der oprettes en sag:

.. image:: firenivopretsag.png
  :width: 800
  :alt: Opret sag, step 1
  
Det ses, at der kommer en advarsel op. Da alt hvad der oprettes i databasen ikke 
kan slettes, er det en god idé at dobbelttjekke alt info man skriver til databasen.
Hvis man er sikker på sit input, kan man svare *"ja"* til spørgsmålet. Hvis der svares
alt andet, vil der ikke blive oprettet en sag i databasen.

.. image:: firenivopretsag2.png
  :width: 800
  :alt: Opret sag, step 2


Skrives der alt andet end *"ja"*, får man valget om der alligevel skal oprettes 
sagsregneark. Hertil kan der svares *"ja"*, og et excel-ark med filnavn som projektnavn 
oprettes i den mappe man kører kaldet i.

.. image:: firenivopretsag3.png
  :width: 800
  :alt: Opret sag, step 3

Excel-arket åbnes, og der ses seks faneblade:

- Projektside: Her kan man løbende indtaste relevant info for projektet.
- Sagsgang: Her vil sagens hændelser fremgå, efterhånden som de forekommer.
- Nyetablerede punkter: Her kan man indtaste de nye punkter, som er oprettet til 
  projektet.
- Notater
- Filoversigt: Her kan man indtaste filnavnene på opmålingsfilerne.
- Parametre

Hvert faneblad kan nu redigeres til det formål man ønsker.

Step 2) udtræk-revision
^^^^^^^^^^^^^^^^^^^^^^^^

Ved de kommunale opgaver starter vi normalt med at lave et udtræk fra databasen for 
et specifikt område, hvor tekstbeskrivelsen for hvert relevant fikspunkt fremgår i en 
såkaldt *rev-fil*. Med "relevant fikspunkt" menes fikspunkter, som vi tilser og som 
vises i webtjenesten Valdemar. Altså ikke restrictede punkter, kendingspunkter, som 
skorstene og fyr, jernrør i støbning, og lignende punkter irrelevant for kunden.
Det script som lavede udtræk hed i det gamle system ``bsk_ud``. 
I dag kan det gøres via et underkald i ``fire niv``, som hedder ``udtræk-revision``

	> fire niv udtræk-revision
	
Step 3) udtræk-revision
^^^^^^^^^^^^^^^^^^^^^^^^

Step 4) ilæg-revision
^^^^^^^^^^^^^^^^^^^^^^^^

Step 5) ilæg-nye-punkter
^^^^^^^^^^^^^^^^^^^^^^^^

Step 6) læs-observationer
^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 7) beregn-nye-koter (eller adj)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 8) ilæg-observationer
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 9) ilæg-nye-koter 
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 10) luk-sag
^^^^^^^^^^^^^^^^^^^^^^^^^^^



Visualisering i QGIS
------------------------
