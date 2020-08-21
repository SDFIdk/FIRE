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
alle underprogrammer (og under-underprogrammer) under ``fire`` og køres derfor ved først at kalde ``fire`` efterfulgt 
af underkommandoens navn.

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
til det (som man før kunne med ``valde``, eller Valdemar i tjenesten), kan man fx taste:

	> fire info g.i.2010

.. note:: Det er ligegyldet om der skrives med stort eller småt eller om der benyttes punktummer eller ej i argumentet.

I udtrækket plottes diverse oplysninger om punktet direkte på skærmen, som set på billedet:

.. image:: fireinfopunkt.png
  :width: 800
  :alt: Udtræk fra databasen for punkt G.I.2010

Udtrækket viser den formodede relevante information, der ligger på punktet fra attribut-tabellerne
og fra koordinattabellerne.
I eksemplet ses det fx, at punktet er oprettet i databasen 19/3 1985, at det også hedder K-11-09263,
og i øvrigt er et jessenpunkt til en tidsserie, samt at det har en DVR90-kote fra 3. præc. 
(indikeret ved EPSG-kode 5799 og beregningstidspunkt 11/2-2000 kl. 13:30), en plankoordinat 
fra 2011 (med EPSG-koden 4258) og to andre koordinater i andre net. Farven grøn indikerer at koordinaten
er den gældende for det pågældende net.

På samme måde kan andre elementer slås op i databasen, bl.a. 

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

Fra dette kald kan hele produktionslinjen køres; fra dataudtræk, revision, beregning, til 
ilægning af resultat og generering af afsluttende rapport til kunde.

Vi vil nedenfor gennemgå processen.

Revision
++++++++++++++++


Opdatering af database
++++++++++++++++++++++

Beregning
++++++++++++++++




Visualisering i QGIS
------------------------
