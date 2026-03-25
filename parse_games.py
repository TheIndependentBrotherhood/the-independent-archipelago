import json
import re

# Parse the game list
game_list_text = """A Dance of Fire and Ice(PC): <#1194141971644682412>
A Difficult Game About Climbing(PC): <#1336857648464920586>
A Hat in Time(PC): <#1257453386073374842>
A Short Hike(PC): <#1224389725922787389>
ActRaiser(SNES): <#1113529234800005181>
Adventure(2600): <#1090814076378153111>
Against the Storm(PC): <#1250491355290140672>
Age of Empires II: Definitive Edition(PC): <#1364201827113107526>
Air Delivery(PICO-8): <#1252453771661803523>
An Untitled Story(PC): <#1194062970230165554>
ANIMAL WELL(PC): <#1238463626344665119>
Anodyne(PC): <#1121290232688545792>
Another Crab's Treasure (PC): <#1239467743116525688>
APQuest (PC): <#1450659987331481610>
Ape Escape (PSX): <#1168645708103028856>
Ape Escape 3 (PS2): <#1336332485788831825>
Aquaria (PC): <#1257452465272389687>
Archipeladoku (PC): <#1451642525726150677>
Archipela-Go! (Android): <#1203890996794884126>
Armored Core (PSX): <#1393754231214837861>
Astalon: Tears of the Earth (PC): <#1211521722881286164>
Autopelago (PC): <#1307517897194868768>
Axiom Verge (PC): <#1032831597583536208>
Balatro (PC): <#1424479033261031474>
Banjo-Tooie (N64): <#1380609128753532948>
Blasphemous (PC): <#1090815418731597884>
Blasphemous 2 (PC): <#1399145913649467524>
Bloons Tower Defense 6 (PC): <#1465832575359516970>
Bomberman Quest (GB): <#1409932342017134655>
Bomberman 64 (N64): <#1326400868773400677>
Bomberman 64: The Second Attack! (N64): <#1064213698861879459>
Bomberman Hero (N64): <#1330612852867858505>
Bomb Rush Cyberfunk (PC): <#1257453065083031642>
Brave Fencer Musashi (PSX): <#1291453297370337351>
Brotato (PC): <#1154944430097313803>
Buckshot Roulette (PC): <#1234399148665737237>
Bumper Stickers (PC): <#1148330200891932742>
Candy Box 2 (PC): <#1351112920398037015>
Castlevania 64 (N64): <#1224387731782893731>
Castlevania: Circle of the Moon (GBA): <#1356647822803603536>
Castlevania: Dawn of Sorrow (NDS): <#1441671319690412052>
Castlevania: Harmony of Dissonance (GBA): <#1356897465046929498>
Castlevania: Legacy of Darkness (N64): <#1178601625078738985>
Castlevania: Symphony of the Night (PSX): <#1462294492752380167>
Cat Quest (PC): <#1319965826601844736>
Cavern of Dreams (PC): <#1189647737210286080>
Cave Story (PC): <#1083474864150695956>
Celeste (PC): <#1367624611256205443>
Celeste (Open World) (PC): <#1408557298946670835>
Celeste 64 (PC): <#1224388599160635552>
Chained Echoes (PC): <#1306059155899154493>
ChecksFinder (PC): <#959282474746282014>
ChecksMate (PC): <#1033159819114319892>
Chrono Trigger (SNES): <#1063559984148906035>
Choo-Choo Charles (PC): <#1436453823928598679>
Clique (Web): <#1090815835825774683>
ClusterTruck (PC): <#1344157838578290792>
Cobalt Core (PC): <#1190007746641272912>
Corn Kidz 64 (PC): <#1282470024560508990>
CrossCode (PC): <#1128180904926396437>
CrosswordAP (PC): <#1433538371031924798>
Crypt of the NecroDancer (PC): <#1192775219740422176>
Crystal Project (PC): <#1193008693827076106>
Crystalis (NES): <#1041412559460389017>
Cuphead (PC): <#1050929729844297789>
Dark Souls: Remastered (PC): <#1367143578576621670>
Dark Souls II (PC): <#1124935172287123466>
Dark Souls III (PC): <#1005246392329052220>
Deadlock (PC): <#1476976528171597875>
Death's Door (PC): <#1126418897827020800>
Deep Rock Galactic (PC): <#1195162433292087358>
Delivering HOPE (PC): <#1435067745476546600>
Deltarune (PC): <#1481971897024516250>
Devil May Cry 3 (PC): <#1255822049163612271>
Dicey Dungeons (PC): <#1172783536474947595>
Diddy Kong Racing (N64): <#1057754627795337387>
Digimon World (PSX): <#1224418923861118977>
DLC Quest (PC): <#1109178880838868992>
Dome Keeper (PC): <#1195385214877306921>
Don't Starve Together (PC): <#1149971904447385751>
Donkey Kong 64 (N64): <#1409624528912650360>
Donkey Kong Country (SNES): <#1364840991755997244>
Donkey Kong Country 2: Diddy's Kong Quest (SNES): <#1023381145565548646>
Donkey Kong Country 3: Dixie Kong's Double Trouble! (SNES): <#1005246223277641809>
DOOM 1993 (PC): <#1148329739996643348>
DOOM II (PC): <#1192236810487738510>
DORONKO WANKO (PC): <#1325915019313152097>
Dracomino (PC): <#1458225573552848908>
Dragon Warrior 1 (NES): <#1132150057852997733>
DREDGE (PC): <#1323663496566542336>
Duke Nukem 3D: Atomic Edition (PC): <#1223230842130796544>
Dungeon Clawler (PC): <#1339622918774067220>
EarthBound (SNES): <#1077266688657068032>
Ender Lilies: Quietus of the Knights (PC): <#1093030832886792242>
Enter the Gungeon (PC): <#1191767250257055785>
Everhood 2 (PC): <#1365278588219424828>
Factorio (PC): <#827139809763262525>
Factorio Space Age Without Space (PC): <#1311946326040383589>
Fakutori (PC): <#1480232889659559966>
Faxanadu (NES): <#1356649072462659716>
Final Fantasy (NES): <#917510025461776445>
Final Fantasy IV (SNES): <#1170144930610557008>
Final Fantasy VI (SNES): <#1022545979146252288>
Final Fantasy X HD Remaster (PC): <#1304953414148554824>
Final Fantasy XII: Open World (PC): <#1229091295465570456>
Final Fantasy XII: Trial Mode (PC): <#1177092493981007922>
Final Fantasy: Mystic Quest (SNES): <#1192237281298362539>
Final Fantasy Tactics Advance (GBA): <#1100823015819837449>
Final Fantasy Tactics: Ivalice Island (PC): <#1451730887136903240>
Final Fantasy Pixel Remaster (PC): <#1195372952166879262>
Final Fantasy Tactics A2: Grimoire of the Rift (DS): <#1296095764518277143>
Fire Emblem: The Sacred Stones (GBA): <#1098762105445953546>
FNaF World (PC): <#1104088448127729704>
Freddy Fazbear's Pizzeria Simulator (PC): <#1078423429310582806>
Freedom Planet 2 (PC): <#1204965442494660608>
Friday Night Funkin' (PC): <#1142560423594430576>
Frogmonster (PC): <#1271323478779363398>
Garfield Kart - Furious Racing (PC): <#1315673680155639848>
Gato Roboto (PC): <#1205195046689841217>
Gato Roboto B-Side (PC): <#1466872819433607248>
Gauntlet Legends (N64): <#1195336830258778183>
Getting Over It with Bennett Foddy (PC): <#1123510506884444250>
GLYPHS (PC): <#1401434680808575017>
Golden Sun: The Lost Age (GBA): <#1055515261270241320>
Grim Dawn (PC): <#1114646643225137224>
Guild Wars 2 (PC): <#1247738360160587787>
gzDoom (PC): <#1344142763842601090>
Hades (PC): <#1367914798519550024>
Hammerwatch (PC): <#1072687192360624218>
Haste: Broken Worlds (PC): <#1356638437872111687>
Hatsune Miku: Project Diva Mega Mix+ (PC): <#1241134454391443580>
Here Comes Niko! (PC): <#1289974001434886287>
Heretic (PC): <#1192236842515439627>
Hero Core (PC): <#1019382284878622790>
Hexcells Infinite (PC): <#1398578301081223260>
High Roller (PC): <#1470104360682917961>
Hi-Fi RUSH (PC): <#1223862313145073674>
Hollow Knight (PC): <#959203442570715176>
holo8 (PC): <#1368677346869252228>
Hololive Treasure Mountain (PC): <#1435070203460583445>
Hylics 2 (PC): <#1043593298247417929>
Iji (PC): <#1335786670641123400>
Isles of Sea and Sky (PC): <#1253182614441951282>
Inscryption (PC): <#1356651394320437469>
Into the Breach (PC): <#1127025077196701828>
Ittle Dew 2+ (PC): <#1260030530217574500>
Jak and Daxter: The Precursor Legacy (PS2): <#1394026388683755613>
Jak 2 (PC): <#1369067607290024056>
Jet Island (VR): <#1370901827826094192>
Jigsaw (Web): <#1409148531637489775>
JS Paint (PC): <#1404622196567048253>
K-On! After School Live!! (PSP) : <#1388861873025323059>
Kabuto Park DEMO (PC): <#1356738429139816680>
Keep Talking and Nobody Explodes (PC): <#1058549067107532840>
Keymaster's Keep (PC): <#1321323711676284939>
KINGDOM HEARTS FINAL MIX (PC): <#1311061458662199357>
KINGDOM HEARTS Chain of Memories (GBA): <#1074710550384234587>
KINGDOM HEARTS Birth by Sleep FINAL MIX (PC): <#1158149027385319434>
KINGDOM HEARTS Re:Chain of Memories (PC): <#1074710550384234587>
KINGDOM HEARTS II FINAL MIX (PC): <#1090817012416118815>
Kirby 64: The Crystal Shards (N64): <#1175344681928904806>
Kirby Air Ride (GC): <#1291501105389502554>
Kirby's Dream Land 3 (SNES): <#1224389195485806703>
Kirby Super Star (SNES): <#1455078199611490384>
Landstalker - The Treasures of King Nole (GEN): <#1192237232069808238>
League of Legends (PC): <#1184691812099686492>
Legend of Dragoon (PSX): <#1334988609249345567>
Lego Batman: The Video Game (PC): <#1182049227145232474>
Lego Star Wars: The Complete Saga (PC): <#1110760232763801711>
Lethal Company (PC): <#1183860023147896942>
Lil Gator Game (PC): <#1084922067469734039>
Lingo (PC): <#1192233449868767362>
Lingo 2 (PC): <#1351182605655080970>
Little Witch Nobeta (PC): <#1170655339323080796>
Loonyland: Halloween Hill (PC/Web): <#1314639182655656016>
Lufia II: Rise of the Sinistrals (SNES): <#1055241755383046154>
Luigi's Mansion (GC): <#1378465872917827614>
Lunacid (PC): <#1176614031067455528>
Mario & Luigi: Superstar Saga (GBA): <#1257453738612756632>
Mario is Missing! (SNES): <#1188695271941603348>
Mario Kart 64 (N64): <#1124649084544876615>
Mario Kart: Double Dash (GC): <#1257102472967884882>
Mario Kart Wii (Wii): <#1204920631351713823>
Mario Super Sluggers (Wii): <#1238777175033909318>
MediEvil (1998) (PSX): <#1282755532515709048>
Mega Man 2 (NES): <#1311061171192729690>
Mega Man 3 (NES): <#1250369456048177152>
Mega Man X (SNES): <#1134349743984742520>
Mega Man X2 (SNES): <#1232388647127613490>
Mega Man X3 (SNES): <#1209396673755746324>
Mega Man Battle Network 3 Blue (GBA): <#1148331400542568558>
Meritous (PC): <#959202754188963880>
MetroCUBEvania (PICO-8): <#1259263968245977128>
Metroid Fusion (GBA): <#1161319361345232946>
Metroid: Zero Mission (GBA): <#1106280250528235620>
Metroid Prime (GC): <#1425600401733980301>
Mindustry (PC): <#1160797230161211472>
Minecraft (PC): <#837136185662111746>
Minecraft Dig (PC): <#837136185662111746>
Minishoot' Adventures (PC): <#1307687662798508113>
Minit (PC): <#1167463223528787998>
Momodora: Moonlit Farewell (PC): <#1351406749315240007>
Monster Sanctuary (PC): <#1096278752142577684>
Muse Dash (PC): <#1148331097705414796>
Mystical Ninja Starring Goemon (N64): <#1176230651352068226>
Nine Sols (PC): <#1291949699150123048>
Noita (PC): <#1109174779619057795>
Nodebuster (PC): <#1354141892434067476>
Nonogram (Picross) (PC/Mobile): <#1454544116711952384>
Old School Runescape (PC): <#1311060866598178866>
OpenRCT2 (PC): <#1095746758774108240>
OpenTTD (PC): <#1475251506381979970>
Ori and the Blind Forest (PC): <#1036405779726610452>
Ori and the Will of the Wisps (PC): <#1272952565843103765>
Osu! (PC): <#1195040661171355730>
Our Ascent (PC): <#1358525617234252130>
Outer Wilds (PC): <#1178700404637311086>
Overcooked! 2 (PC): <#1043593072174440448>
Oxygen Not Included (PC): <#1446597534847074416>
Panel De Pon/Tetris Attack (SNES): <#1207963109990596669>
Paper Mario (N64): <#1369329691076329582>
Paper Mario: The Thousand Year Door (GC): <#1388344505446432789>
Parkitect (PC): <#1417531615956963439>
Peaks of Yore (PC): <#1332506808182378677>
Peggle Deluxe (PC): <#1470246861557334016>
Peggle Nights (PC): <#1470912354941141156>
Pikmin 2 (GC): <#1062964930174779452>
Pinball FX3 (PC): <#1465211526141972684>
PixelDraw (PC): <#1483851572340457604>
Pizza Tower (PC): <#1079671816257277972>
Placid Plastic Duck Simulator (PC): <#1104785671262056559>
Plants vs Zombies: Replanted/GOTY (PC): <#1437352496455483413>
Plateup! (PC): <#1159168584505901106>
Plok (SNES): <#1353834617433755688>
Pokémon Red and Blue (GB): <#1043592720603693167>
Pokémon Pinball (GB): <#1358934774647095447>
Pokémon Crystal (GBC): <#1365127145709502575>
Pokémon FireRed and LeafGreen (GBA): <#1365127226533871718>
Pokémon Emerald (GBA): <#1192236871468711966>
Pokémon Black and White (DS): <#1414928022854696991>
Pokémon Platinum (DS): <#1414786317014929418>
Pokémon Ranger (Quest) (DS): <#1476751710801362995>
Pokémon Mystery Dungeon Explorers of Sky (DS): <#1408865961385267260>
PokéPark Wii: Pikachu's Adventure (Wii): <#1365710916011819088>
Poképelago - Pokémon Guessing Game (PC): <#1474030797811093514>
Powerwash Simulator (PC): <#1158367507703410739>
Prodigal (PC): <#1140678965422465115>
Pseudoregalia (PC): <#1147564210436452393>
Psychonauts (PC): <#1191273397976584212>
Rabi-Ribi (PC): <#1183337635805138994>
Raft (PC): <#937206960472883243>
Rain World (PC): <#1136042293162418176>
Rachet & Clank (PS3): <#1146024297324879872>
Ratchet & Clank: Going Commando (PS2): <#1325015730218860554>
Ratchet & Clank 3: Up Your Arsenal (PS2): <#1357102103054651622>
Rayman 2: The Great Escape (PC): <#1151502935667257386>
Refunct (PC): <#1273001824919617577>
R.E.P.O. (PC): <#1345146101094678639>
Reventure (PC): <#1200081144629174363>
Rift of the NecroDancer (PC): <#1337112354130759757>
Rift Wizard (PC): <#1097001818564853770>
Risk of Rain (PC): <#1193665646467231764>
Risk of Rain 2 (PC): <#884926818480705586>
Risk of Rain Returns (PC): <#1172336306890747984>
Rogue Legacy (PC): <#929585237695029268>
Rusted Moss (PC): <#1239286100472758302>
Satisfactory (PC): <#1454822629423841442>
Saving Princess (PC): <#1356647146484666439>
Scooby-Doo! Night of 100 Frights (GC): <#1188152412498829352>
Secret of Evermore (SNES): <#909605724190019645>
Secret of Mana (SNES): <#1228235556589146193>
Sentinels of the Multiverse (PC / Physical): <#1241869295848521730>
Severed Soul (PC): <#1400131509569978478>
Shadow the Hedgehog (GC): <#1142558464242094200>
Shadowgate 64 (N64): <#1295834685548658819>
Shapez (PC): <#1394026826782740601>
Shapez 2 (PC): <#1278481415830245427>
Shivers (PC): <#1192237130005610586>
Sid Meier's Civilization V (PC): <#1342924294757552229>
Sid Meier's Civilization VI (PC): <#1356645390497222887>
Simon Tatham's Portable Puzzle Collection (Web): <#1278733078516207719>
Slay the Spire (PC): <#884926940182609920>
Slime Rancher (PC): <#1108426937409486909>
Sly Cooper and the Thievius Raccoonus (PS2): <#1170557242660093952>
Sly 2: Band of Thieves (PS2): <#1359447263981600788>
Smushi Come Home (PC): <#1443621717552402535>
SMW: Spicy Mycena Waffles (SNES): <#1435322478024200202>
SMZ3 (SNES): <#959203096142184458>
Sonic the Hedgehog (GEN): <#1212629606608408576>
Sonic Adventure DX (PC): <#1420425220858056874>
Sonic Adventure 2: Battle (PC): <#980554290798145566>
Sonic Heroes (PC): <#1234592520403423352>
Sonic Riders (GC): <#1292128680046235739>
Sonic Rush (DS): <#1280648306124394567>
Soulblazer (SNES): <#1209689725057761310>
Spelunker (NES): <#1237999589907234938>
Spelunky 2 (PC): <#1142626744629735555>
Spinball (Web): <#1325257989891952742>
SpongeBob SquarePants: Battle For Bikini Bottom (GC): <#1098766534035386458>
Spyro 2 (PSX): <#1281660590431015046>
Spyro 3 (PSX): <#1018847303722872843>
Stacklands (PC): <#1151149079238299719>
Star Wars: Episode I - Racer (PC): <#1207274588120158269>
StarCraft II (PC): <#980554570075873300>
Stardew Valley (PC): <#1090823633099833464>
Starfox 64 (N64): <#1024876649151475732>
Stick Ranger (PC): <#1368511758662373517>
Streets of Rage (GEN): <#1421815799504437409>
Subnautica (PC): <#868938368346628096>
Super Cat Planet (PC): <#1338978189682409473>
Super Junkoid (SNES): <#1196920710724071555>
Super Mario Land 2: 6 Golden Coins (GB): <#1394026996325158982>
Super Mario Sunshine (GC): <#1383204057514250300>
Super Mario Sunshine Arcade 2 (GC): <#1399897298301096048>
Super Mario World (SNES): <#1043593173089398846>
Super Mario World 2: Yoshi's Island (SNES): <#1224389973336133743>
Super Mario 64 (N64/PC): <#937206798014898186>
Super Mario RPG (SNES): <#1091478379963883651>
Super Metroid (SNES): <#909599727341928538>
Super Metroid Map Rando (SNES): <#1156395911874875473>
Super Smash Bros. Melee (GC): <#1179050965802942474>
System Shock 2 (PC): <#1340419754200010915>
Talos Principle Reawakened (PC): <#1473070314165633215>
TCG Card Shop Simulator (PC): <#1302063649812250665>
Terraria (PC): <#1148330488482767008>
Tetris (GB): <#1477485575937331281>
TEVI (PC): <#1320015979736203304>
The Binding of Isaac: Repentance (PC): <#1454262765047775326>
The Forged Curse (PICO-8): <#1411846246271815850>
The Grinch (PSX): <#1279837475338190999>
The Legend of Heroes: Trails in the Sky the 3rd (PC): <#1217595862872490065>
The Legend of Zelda (NES): <#1090821869340467332>
The Legend of Zelda II: The Adventure of Link (NES): <#1239454398367924325>
The Legend of Zelda: A Link to the Past (SNES): <#827141303330406408>
The Legend of Zelda: Link's Awakening DX (GBC): <#1090819435893362768>
The Legend of Zelda: Ocarina of Time (N64): <#884928390421938206>
The Legend of Zelda: Ocarina of Time (Ship of Harkinian) (PC): <#1434235335625281707>
The Legend of Zelda: Ocarina of Time but it's just Master Quest Water Temple (N64): <#1211745516807782410>
The Legend of Zelda: Majora's Mask (N64/PC): <#1368653154241089546>
The Legend of Zelda: Oracle of Ages (GBC): <#1279722186601750>
The Legend of Zelda: Oracle of Seasons (GBC): <#1439343546615206019>
The Legend of Zelda: The Wind Waker (GC): <#1356643332754768044>
The Legend of Zelda: The Minish Cap (GBA): <#1419820477404418140>
The Legend of Zelda: Twilight Princess (GC): <#1369050080887312506>
The Legend of Zelda: Skyward Sword (Wii): <#1469917221068214444>
The Legend of Zelda: Phantom Hourglass (DS): <#1256012365049233438>
The Legend of Zelda: Spirit Tracks (DS): <#1358582876085682417>
The Legend of Zelda: A Link Between Worlds (3DS): <#1434699603843874846>
The Messenger (PC): <#1090822939697500243>
The Simpsons: Hit and Run (PC): <#1158211913495359548>
The Sims 4 (PC): <#1079002955262480424>
The Witness (PC): <#980554001231786014>
Timespinner (PC): <#893636303630000169>
Toejam & Earl (GEN): <#1204326236415856671>
TOEM (PC): <#1255989734497587241>
Tombola (PC): <#1475176727235002571>
Total War Warhammer 3: Immortal Empires (PC): <#1136329107370684538>
Totally Accurate Battle Simulator (PC): <#1348142956682547230>
Touhou 18.5 (PC): <#1346288808512983040>
Trackmania Random Campaign (PC): <#1368696493904625785>
TUNIC (PC): <#1224388891948093540>
Turnip Boy Commits Tax Evasion (PC): <#1297617351977734214>
Twisty Cube (PC/Mobile): <#1420821472057757716>
Tyrian (PC): <#1224498137570349076>
Ty the Tasmanian Tiger (PC): <#1111533202184613991>
UFO 50 (PC): <#1286076770445164575>
Undertale (PC): <#1148330675452264499>
Unfair Flips (PC): <#1443942587974029322>
Vacation Simulator (VR): <#1204935955580985414>
Voltorb Flip (HGSS) (DS): <#1419104603126890506>
Void Sols (PC): <#1448045030777421844>
Void Stranger (PC): <#1231073014439743528>
VVVVVV (PC): <#937206899949076540>
Wargroove (PC): <#1090824439710625822>
Wargroove 2 (PC): <#1159482310652076082>
Wario Land: Super Mario Land 3 (GB): <#1173641836502454303>
Wario Land 4 (GBA): <#1079899101732290620>
Wario World (GC): <#1257377358269251666>
Watery Words (Web): <#1292965246847418388>
WEBFISHING (PC): <#1299564055597416449>
West of Loathing (PC): <#1273856413327822950>
Wordipelago (Web): <#1336387000928047186>
XCOM 2: War of the Chosen (PC): <#1037751568700805141>
Xenoblade Chronicles X (Wii U): <#1333863771868762265>
Yacht Dice (Web): <#1311061580645142578>
YARG (Yet Another Rhythm Game) (PC): <#1451771538943508490>
YARG (Guitar Hero 1/Rock Band 3/Combined) (PC): <#1454538103933898752>
(SENS) yrtnuoC gnoK yeknoD (N64): <#1395482597710106694>
Yoku's Island Express (PC): <#1225283906333446245>
Yooka-Laylee (PC): <#1103936661156536330>
Yu-Gi-Oh! Dungeon Dice Monsters (GBA): <#1298768685510561842>
Yu-Gi-Oh! Ultimate Masters: WCT 2006 (GBA): <#1257454640950149151>
Yu-Gi-Oh! Forbidden Memories (PSX): <#1210743818564149288>
Yu-Gi-Oh GX Duel Academy (GBA): <#1345884440571678862>
Zillion (SMS): <#1043593966131613736>
Zork: Grand Inquisitor (PC): <#1224389493289648218>"""

games = []
for line in game_list_text.strip().split('\n'):
    if not line.strip():
        continue

    # Parse: "Game Name(Platform): <#ChannelID>"
    match = re.match(r'^(.+?)\(([^)]+)\):\s*<#(\d+)>$', line.strip())
    if match:
        name = match.group(1).strip()
        platform = match.group(2).strip()
        channel_id = match.group(3)

        # Create game object
        game_id = name.lower().replace(' ', '-').replace(':',
                                                         '').replace("'", '').replace('!', '')

        game = {
            "id": game_id,
            "name": name,
            "platform": platform,
            "url": f"https://archipelago.gg/games/{name.replace(' ', '%20')}/info/en",
            "description": f"Archipelago randomizer for {name} ({platform})",
            "discordUrl": f"https://discord.com/channels/731205301247803413/{channel_id}",
            "completed": [],
            "todo": []
        }
        games.append(game)

# Add the existing games at the beginning
existing_games = [
    {
        "id": "elden-ring",
        "name": "Elden Ring",
        "platform": "PC",
        "url": "https://archipelago.gg/games/Elden%20Ring/info/en",
        "description": "A masterpiece of action RPG gameplay. Explore the Lands Between with randomized bosses and loot.",
        "completed": ["minipomme"],
        "todo": []
    },
    {
        "id": "ocarina-of-time",
        "name": "The Legend of Zelda: Ocarina of Time",
        "platform": "N64",
        "url": "https://archipelago.gg/games/Ocarina%20of%20Time/info/en",
        "description": "Classic N64 Zelda adventure with randomized dungeons and items.",
        "completed": [],
        "todo": ["minipomme"]
    },
    {
        "id": "super-metroid",
        "name": "Super Metroid",
        "platform": "SNES",
        "url": "https://archipelago.gg/games/Super%20Metroid/info/en",
        "description": "Space exploration action-adventure with randomized power-ups and routes.",
        "completed": ["minipomme"],
        "todo": []
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "platform": "PC",
        "url": "https://archipelago.gg/games/Minecraft/info/en",
        "description": "Sandbox adventure with randomized progression and linked worlds.",
        "completed": [],
        "todo": ["minipomme", "todiun"]
    },
    {
        "id": "stardew-valley",
        "name": "Stardew Valley",
        "platform": "PC",
        "url": "https://archipelago.gg/games/Stardew%20Valley/info/en",
        "description": "Farming life simulation with randomized relationships and objectives.",
        "completed": ["minipomme"],
        "todo": []
    },
    {
        "id": "dark-souls-3",
        "name": "Dark Souls III",
        "platform": "PC",
        "url": "https://archipelago.gg/games/Dark%20Souls%20III/info/en",
        "description": "Challenging action RPG with randomized bosses and loot progression.",
        "completed": [],
        "todo": ["todiun"]
    }
]

# Combine and deduplicate by ID
all_games_dict = {game["id"]: game for game in games}
for game in existing_games:
    if game["id"] not in all_games_dict:
        all_games_dict[game["id"]] = game

final_games = list(all_games_dict.values())

# Create the final JSON
result = {"games": final_games}

# Write to file
with open("games_output.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Generated {len(final_games)} games")
print("File saved to games_output.json")
