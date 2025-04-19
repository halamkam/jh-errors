Errory vyvolavaj bud cez formu (urob si tam rozne policka cez ktore budes konfigurovat cokolvek na hocjaku hodnotu) alebo budes musiet vo values stale pre singleuser (ako pre ten uzivatelsky notebook) menit zadane hodnoty. Podla mna je lepsie sa bavit s tou formou. Myslim si, ze eventuelne budes musiet pridat vlastne tie kusy kodu, ktore mame my v nasom  produkcnom hube aby si vedel vlastne kazdu jednu cast tej formy otestovat, ale s tym imagom, zdrojmi a neexistujucim beznym pvc vies zacat hned. Taktiez vies naimplementovat to zrusenie spawnovania a aj kontaktovanie AI. A nakonec mozme pridat tie storae-related errory (alebo predtym nez budes robit na tom AI, nech mas jeden “logicky” celok ukonceny.

Z hlavy mi napada:
-	image pre notebook neexistuje – si proste vymysli daco co das jak image a neni – pozoruj aky error je a ci ho vies jednoznacne zachytit
-	K notebooku sa ma pripojit PVC, ktore neexistuje
o	K notebookom sa vedia pripojit aj 2 “specialne” typy PVC – sshfs a s3
o	Sshfs sluzi na pripojenie metacentrum home, pri sshfs pripojeni najcastejsie zlyha, ze dany clovek nema home alebo ze je nejaky sietovy problem. Errory co sa vypisuju maju zopar verzi ale nejake z nich (mozno najcastejsi su)
	
2025-02-21T07:31:06Z [Warning] AttachVolume.Attach failed for volume
"jupyterhub-dklement-prod-ns-brno12-cerit-data-sshfs" : timed out
waiting for external-attacher of csi-sshfs CSI driver to attach volume
jupyterhub-dklement-prod-ns-brno12-cerit-data-sshfs
•	Tento error nemas jak osetrit, na to sa musim kuknut jak my admini (napr sa resetli stroje, je zaseknuty nejaky controller, dakde blikla siet) - preto by bolo najlepsie napisat uzivatelovi ze je nejaky problem s tym sshfs driverom prip pripajani volume [meno] a ze nec napise na k8s@ics.muni.cz
	2025-01-23T09:47:30Z [Warning] (combined from similar events): MountVolume.SetUp failed for volume "ondryx-brno12-cerit-data-sshfs" : rpc error: code = Internal desc = mounting failed: exit status 1 cmd: 'sshfs ondryx@storage-brno12-cerit.metacentrum.cz:/nfs4/home/ondryx /var/lib/kubelet/pods/817dd1b0-7697-440b-abf2-49cb1025186e/volumes/kubernetes.io~csi/ondryx-brno12-cerit-data-sshfs/mount -o port=22 -o IdentityFile=/tmp/pk-904049267 -o reconnect -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o uid=1000,gid=100,allow_other,follow_symlinks' output: "read: Connection reset by peer\n"

MountVolume.SetUp failed for volume "vvlcek-plzen4-ntis-data-sshfs" : rpc error: code = Internal desc = mounting failed: exit status 1 cmd: 'sshfs vvlcek_@storage-plzen4-ntis.metacentrum.cz:/home/vvlcek_ /var/lib/kubelet/pods/5aad1c55-b443-495e-bccb-b4961b65a229/volumes/kubernetes.io~csi/vvlcek-plzen4-ntis-data-sshfs/mount -o port=22 -o IdentityFile=/tmp/pk-3947173871 -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o uid=1000,gid=100,allow_other,follow_symlinks' output: "read: Connection reset by peer\n"	

•	Tento error nemas jak osetrit (oba priklady su ten isty error, len ukazujem ze dvaja rozni ludia ho mali), na to sa musim kuknut jak my admini (zvycajne je daco s tym home, ma zle prava nebo tak) - preto by bolo najlepsie napisat uzivatelovi ze je nejaky  problem s tym pripajanim jeho home z daneho storage servru [meno] a  nehc napise na k8s@ics.muni.cz


o	Pri S3 nema velmi uz co zlyhat – tam je urobeny dopredny check, ze si zadal spravne udaje cize tam nemusis asi riesit nic, alebo mi to nenapada teraz

-	Pohraj sa s tymi zdrojmi, skus priradit take, ktore nesu splnitelne na 1 stroji




K jednotlivym errorom si namysli nejake fixy – ci budes cakat dalej, ci vypises nejaku vhodnejsiu hlasku a ukoncis spawnovanie (a zmazes vsetky eventy tykajuce sa toho notebooku). Tych errorov tu ocividne neni vela ale je fakt podstatne aby si mal tieto dve veci hotove:
-	Moznost (abo defaultne) ze sa to spawnovanie okamzite zastavi ak je error “unrecoverable”
-	Napojenie na to AI v pripade neuskutocnitelnych zdrojov -> poradi to, co by si tak mohol skusit. 
Nejdeme to smerovat na mnozstvo osetrenych errorov – ked jeden uz bude namysleny, ako ho osetrovat a vypisat vlastne lepsie hlasky, zrobit to pre zvysne nebude tak problem. Gro tvojej prace spociva v tychto dvoch veciach bo tie su naozaj nove a zaujimave.

VYKOPIROVANE Z NASHO CHATU
Upravena reakcia na chyby zahrna: 
•	Implementaciu reakcie na chyby v JupyterHube:
o	1. pripad - notebook je pending lebo nesu zdroje - volitelne na strane uzivatela 
	zabit alebo pockat hoc i nekonecne dlho, az sa raz notebook spusti  -> toto sme uz zmenili na to, ze sa spawn zastavi a potom kontajtuje AI a nejak ti poradi ze co je k dispozicii
o	2. pripad - Image je prilis velky a musi sa stiahnut - malo by to ist poznat dakde v systeme, (ze sa stahuje image) a teda je spravne pockat
o	vo vsetkych ostatnych pripadoch chyby notebook proste zabit. Vhodne informovat uzivatela o chybe (daco vhodne sa mu vypise, ukaze sa mu cute obrazok a neco jak "jejda neco se pokazilo" a do logov (normalne log.print sa zapisu chyby)

a este par technickych veci nam napadlo, to tu zatial odlozim ale neskor pri impl sa to zide. Minimalne to tu necham ako myslienky, nad ktorymi sa da konceptualne premyslat
•	ked sa dany notebook ma zmazat (napr. pri neopravitelnej chybe), pomazu sa s nim i jeho eventy. Vytvorenie ntb je sprevadzane kopu eventami a ked v rychlom slede za sebou vytvoris novy ntb s tym istym nazvom, tak ti v tej pending page vypisuje este eventy stareho ntb (kubectl get events –n [namespace] ti ukaze tie eventy)
•	error handling ako volitelne funkcionalita: default implementacia error handlingu pre kubernetes napr. preformatuje error, aby daval vacsi zmysel pre citatela, nebol tak skaredy a ponukal funkcionalitu ze ak je error neopravitelny, ten notebook (Pod=kontajer) sa rovno zmaze
•	ku tejto default funkcionalite ale moze existovat extra funkcionalita - volitelny callback - ktory moze implementovat co sa ma stat pri erroroch. To je vlastne scasti to, co pisem v sprave vyssue (ze by bolo pekne aby to bola volitelna funkcionalita) a callback by mohol napr.byt dobry na to, ze ako sme sa bavili - ak mas error , ktory vravi o tom, ze v neni dostatok zdrojov, tak napr. u nas by sme urobili volanie na promethea, zistili ake su zdroje a potom volanie na nejake AI a spytali sa, co navrhuje za mozne kombinacie. ... toto cele je volitelne, isto to tak nebude mat kazdy system ktory kedy deployoval jupyterhub , preto to tam nemozeme natvrdo nakodit ale zaorven je vysoko pravdepodobne ze pri error si mozes chciet nieco custom pridat. Tak na to by bol taky callback. - 
o	Pri tomto ale plati, ze sa proste zamysli nad tym, ako je ten jupyterhub naimplementovany a ked usudis ze toto neni lahko implementovatelne, tak si to len zapamataj a dakde bokom napis ze preco – bude sa ti to hodit jednak do bakalarky a jednak to povies i mne, ze preco to neslo tak 

Errory vyvolavaj bud cez formu (urob si tam rozne policka cez ktore budes konfigurovat cokolvek na hocjaku hodnotu) alebo budes musiet vo values stale pre singleuser (ako pre ten uzivatelsky notebook) menit zadane hodnoty. Podla mna je lepsie sa bavit s tou formou. Myslim si, ze eventuelne budes musiet pridat vlastne tie kusy kodu, ktore mame my v nasom  produkcnom hube aby si vedel vlastne kazdu jednu cast tej formy otestovat, ale s tym imagom, zdrojmi a neexistujucim beznym pvc vies zacat hned. Taktiez vies naimplementovat to zrusenie spawnovania a aj kontaktovanie AI. A nakonec mozme pridat tie storae-related errory (alebo predtym nez budes robit na tom AI, nech mas jeden “logicky” celok ukonceny.

Z hlavy mi napada:
-	image pre notebook neexistuje – si proste vymysli daco co das jak image a neni – pozoruj aky error je a ci ho vies jednoznacne zachytit
-	K notebooku sa ma pripojit PVC, ktore neexistuje
o	K notebookom sa vedia pripojit aj 2 “specialne” typy PVC – sshfs a s3
o	Sshfs sluzi na pripojenie metacentrum home, pri sshfs pripojeni najcastejsie zlyha, ze dany clovek nema home alebo ze je nejaky sietovy problem. Errory co sa vypisuju maju zopar verzi ale nejake z nich (mozno najcastejsi su)
	
2025-02-21T07:31:06Z [Warning] AttachVolume.Attach failed for volume
"jupyterhub-dklement-prod-ns-brno12-cerit-data-sshfs" : timed out
waiting for external-attacher of csi-sshfs CSI driver to attach volume
jupyterhub-dklement-prod-ns-brno12-cerit-data-sshfs
•	Tento error nemas jak osetrit, na to sa musim kuknut jak my admini (napr sa resetli stroje, je zaseknuty nejaky controller, dakde blikla siet) - preto by bolo najlepsie napisat uzivatelovi ze je nejaky problem s tym sshfs driverom prip pripajani volume [meno] a ze nec napise na k8s@ics.muni.cz
	2025-01-23T09:47:30Z [Warning] (combined from similar events): MountVolume.SetUp failed for volume "ondryx-brno12-cerit-data-sshfs" : rpc error: code = Internal desc = mounting failed: exit status 1 cmd: 'sshfs ondryx@storage-brno12-cerit.metacentrum.cz:/nfs4/home/ondryx /var/lib/kubelet/pods/817dd1b0-7697-440b-abf2-49cb1025186e/volumes/kubernetes.io~csi/ondryx-brno12-cerit-data-sshfs/mount -o port=22 -o IdentityFile=/tmp/pk-904049267 -o reconnect -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o uid=1000,gid=100,allow_other,follow_symlinks' output: "read: Connection reset by peer\n"

MountVolume.SetUp failed for volume "vvlcek-plzen4-ntis-data-sshfs" : rpc error: code = Internal desc = mounting failed: exit status 1 cmd: 'sshfs vvlcek_@storage-plzen4-ntis.metacentrum.cz:/home/vvlcek_ /var/lib/kubelet/pods/5aad1c55-b443-495e-bccb-b4961b65a229/volumes/kubernetes.io~csi/vvlcek-plzen4-ntis-data-sshfs/mount -o port=22 -o IdentityFile=/tmp/pk-3947173871 -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o uid=1000,gid=100,allow_other,follow_symlinks' output: "read: Connection reset by peer\n"	

•	Tento error nemas jak osetrit (oba priklady su ten isty error, len ukazujem ze dvaja rozni ludia ho mali), na to sa musim kuknut jak my admini (zvycajne je daco s tym home, ma zle prava nebo tak) - preto by bolo najlepsie napisat uzivatelovi ze je nejaky  problem s tym pripajanim jeho home z daneho storage servru [meno] a  nehc napise na k8s@ics.muni.cz


o	Pri S3 nema velmi uz co zlyhat – tam je urobeny dopredny check, ze si zadal spravne udaje cize tam nemusis asi riesit nic, alebo mi to nenapada teraz

-	Pohraj sa s tymi zdrojmi, skus priradit take, ktore nesu splnitelne na 1 stroji




K jednotlivym errorom si namysli nejake fixy – ci budes cakat dalej, ci vypises nejaku vhodnejsiu hlasku a ukoncis spawnovanie (a zmazes vsetky eventy tykajuce sa toho notebooku). Tych errorov tu ocividne neni vela ale je fakt podstatne aby si mal tieto dve veci hotove:
-	Moznost (abo defaultne) ze sa to spawnovanie okamzite zastavi ak je error “unrecoverable”
-	Napojenie na to AI v pripade neuskutocnitelnych zdrojov -> poradi to, co by si tak mohol skusit. 
Nejdeme to smerovat na mnozstvo osetrenych errorov – ked jeden uz bude namysleny, ako ho osetrovat a vypisat vlastne lepsie hlasky, zrobit to pre zvysne nebude tak problem. Gro tvojej prace spociva v tychto dvoch veciach bo tie su naozaj nove a zaujimave.

VYKOPIROVANE Z NASHO CHATU
Upravena reakcia na chyby zahrna: 
•	Implementaciu reakcie na chyby v JupyterHube:
- 1. pripad - notebook je pending lebo nesu zdroje - volitelne na strane uzivatela 
	zabit alebo pockat hoc i nekonecne dlho, az sa raz notebook spusti  -> toto sme uz zmenili na to, ze sa spawn zastavi a potom kontajtuje AI a nejak ti poradi ze co je k dispozicii
- 2. pripad - Image je prilis velky a musi sa stiahnut - malo by to ist poznat dakde v systeme, (ze sa stahuje image) a teda je spravne pockat
- 	vo vsetkych ostatnych pripadoch chyby notebook proste zabit. Vhodne informovat uzivatela o chybe (daco vhodne sa mu vypise, ukaze sa mu cute obrazok a neco jak "jejda neco se pokazilo" a do logov (normalne log.print sa zapisu chyby)

a este par technickych veci nam napadlo, to tu zatial odlozim ale neskor pri impl sa to zide. Minimalne to tu necham ako myslienky, nad ktorymi sa da konceptualne premyslat
•	ked sa dany notebook ma zmazat (napr. pri neopravitelnej chybe), pomazu sa s nim i jeho eventy. Vytvorenie ntb je sprevadzane kopu eventami a ked v rychlom slede za sebou vytvoris novy ntb s tym istym nazvom, tak ti v tej pending page vypisuje este eventy stareho ntb (kubectl get events –n [namespace] ti ukaze tie eventy)
•	error handling ako volitelne funkcionalita: default implementacia error handlingu pre kubernetes napr. preformatuje error, aby daval vacsi zmysel pre citatela, nebol tak skaredy a ponukal funkcionalitu ze ak je error neopravitelny, ten notebook (Pod=kontajer) sa rovno zmaze
•	ku tejto default funkcionalite ale moze existovat extra funkcionalita - volitelny callback - ktory moze implementovat co sa ma stat pri erroroch. To je vlastne scasti to, co pisem v sprave vyssue (ze by bolo pekne aby to bola volitelna funkcionalita) a callback by mohol napr.byt dobry na to, ze ako sme sa bavili - ak mas error , ktory vravi o tom, ze v neni dostatok zdrojov, tak napr. u nas by sme urobili volanie na promethea, zistili ake su zdroje a potom volanie na nejake AI a spytali sa, co navrhuje za mozne kombinacie. ... toto cele je volitelne, isto to tak nebude mat kazdy system ktory kedy deployoval jupyterhub , preto to tam nemozeme natvrdo nakodit ale zaorven je vysoko pravdepodobne ze pri error si mozes chciet nieco custom pridat. Tak na to by bol taky callback. - 
o	Pri tomto ale plati, ze sa proste zamysli nad tym, ako je ten jupyterhub naimplementovany a ked usudis ze toto neni lahko implementovatelne, tak si to len zapamataj a dakde bokom napis ze preco – bude sa ti to hodit jednak do bakalarky a jednak to povies i mne, ze preco to neslo tak 

