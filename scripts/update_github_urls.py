import json
import re

# Read the existing games.json
with open('../data/games.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

games_by_id = {game['id']: game for game in data['games']}

# Parse GitHub URLs
github_data = """A Dance of Fire and Ice (PC): https://github.com/ClaudeChibout/ADOFAI_AP-Mod/releases
A Difficult Game About Climbing (PC): https://github.com/BlastSlimey/GrabbingChecks/releases
ActRaiser (SNES): https://github.com/Happyhappyism/Archipelago/releases
Against the Storm (PC): https://github.com/Ryguy-9999/ArchipelagoATS/releases
Age of Empires II: Definitive Edition (PC): https://github.com/dmwever/Ageipelago/releases
Air Delivery (PICO-8): https://github.com/qwint/ap-air-delivery/releases
An Untitled Story (PC): https://github.com/ThatOneGuy27/Archipelago-aus/releases
ANIMAL WELL (PC): https://github.com/ScipioWright/Archipelago-SW/releases
Anodyne (PC): https://github.com/PixieCatSupreme/ArchipelagoAno/releases
Another Crab's Treasure (PC): https://github.com/Automagic00/ACT-AP-Client-Plugin/releases
Ape Escape (PSX): https://github.com/Thedragon005/Archipelago-Ape-Escape/releases
Ape Escape 3 (PS2): https://github.com/aidanii24/ae3-archipelago/releases
Archipeladoku (PC): https://github.com/galdiuz/archipeladoku/
Archipela-Go! (Android): https://github.com/aki665/react-native-archipelago/releases
Armored Core (PSX): https://github.com/JustinMarshall98/Armored-Core-PSX-Archipelago/releases
Astalon: Tears of the Earth (PC): https://github.com/drtchops/Archipelago-Astalon/releases
Autopelago (PC): https://github.com/airbreather/Autopelago/releases
Axiom Verge (PC): https://github.com/mail-liam/Archipelago/releases/latest
Balatro (PC): https://github.com/BurndiL/BalatroAP/releases
Banjo-Tooie (N64): https://github.com/jjjj12212/Archipelago-BanjoTooie/releases
Bloons TD 6 (PC): https://github.com/GamingInfinite/Archipelago/releases
Bomberman Quest (GB): https://github.com/Happyhappyism/Archipelago/releases?q=bomberman&expanded=true
Bomberman 64 (N64): https://github.com/Happyhappyism/Archipelago/releases?q=093058ece14c8cc1a887b2087eb5cfe9&expanded=true
Bomberman 64: The Second Attack! (N64): https://github.com/Happyhappyism/Archipelago/releases
Brave Fencer Musashi (PSX): https://github.com/AegeusEvander/Brave-Fencer-Musashi-AP-World/releases
Brotato (PC): https://github.com/SpenserHaddad/Brotato-ArchipelagoClient/releases
Buckshot Roulette (PC): https://github.com/asdfwyay/APBuckshot/releases
Candy Box 2 (PC): https://github.com/vicr123/Archipelago/releases
Castlevania: Dawn of Sorrow (NDS): https://github.com/PinkSwitch/Archipelago/releases?q=castlevania:%20dawn%20of%20sorrow&expanded=true
Castlevania: Harmony of Dissonance (GBA): https://github.com/LiquidCat64/LiquidCatipelago/releases
Castlevania: Legacy of Darkness (N64): https://github.com/LiquidCat64/LiquidCatipelago/releases
Castlevania: Symphony of the Night (PSX): https://github.com/Darvitz/Archipelago-Crystal/releases
Cat Quest (PC): https://github.com/Nikkilites/Archipelago-CatQuest/releases
Cavern of Dreams (PC): https://github.com/wu4/Archipelago/releases
Cave Story (PC): https://github.com/kl3cks7r/Archipelago/releases
Chained Echoes (PC): https://github.com/Samupo/ChainedEchoesRandomizer/releases/
ChecksMate (PC): https://github.com/chesslogic/chessv/releases
Chrono Trigger (SNES): https://www.wiki.ctjot.com/doku.php?id=multiworld
Clique (Web): https://pharware.com/git/Phar/Clique/releases/latest
ClusterTruck (PC): https://github.com/Nullctipus/ArchipelagoClusterTruck/releases
Cobalt Core (PC): https://github.com/Isaac-SOL/CobaltCoreArchipelagoMod/releases
Corn Kidz 64 (PC): https://github.com/Cyb3RGER/cornkidz64_apworld/releases
CrossCode (PC): https://github.com/CodeTriangle/CCMultiworldRandomizer/releases
CrosswordAP (PC): https://github.com/densebamboo/CrosswordAP/releases
Crypt of the NecroDancer (PC): https://github.com/lastingParadox/Archipelago-CotND/releases
Crystal Project (PC): https://github.com/Emerassi/CrystalProjectAPWorld/releases
Crystalis (NES): https://github.com/Ars-Ignis/Archipelago/releases
Cuphead (PC): https://github.com/JKLeckr/Archipelago-cuphead/releases
Dark Souls: Remastered (PC): https://github.com/ArsonAssassin/DSAP/releases
Dark Souls II (PC): https://github.com/WildBunnie/DarkSoulsII-Archipelago/releases
Deadlock (PC): https://github.com/ArchipelagoBrad/deadlockipelago/releases
Death's Door (PC): https://github.com/roseasromeo/DeathsDoorAPWorld/releases
Delivering HOPE (PC): https://github.com/StellatedCUBE/Delivering-Hope-Archipelago/releases
Deltarune (PC): https://github.com/theemeraldsword85/DELTARUNEAP/releases/
Devil May Cry 3 (PC): https://github.com/AshIndigo/DMC3ArchipelagoClient/releases
Dicey Dungeons (PC): https://github.com/Fylcoast/AP_diceydungeons/releases
Diddy Kong Racing (N64): https://github.com/zakwiz/DiddyKongRacingAP/releases
Digimon World (PSX): https://github.com/ArsonAssassin/DWAP/releases
Dome Keeper (PC): https://github.com/Arrcival/ArchipelagoDK/releases
Don't Starve Together (PC): https://github.com/DragonWolfLeo/Archipelago-DST/releases
Donkey Kong 64 (N64): https://dev.dk64randomizer.com/wiki/index.html?title=Archipelago-Dev-Setup-Guide
Donkey Kong Country (SNES): https://github.com/TheLX5/Archipelago/releases?q="Donkey+Kong+Country+1"&expanded=true
Donkey Kong Country 2: Diddy's Kong Quest (SNES): https://github.com/TheLX5/Archipelago/releases?q=country+2&expanded=true
DORONKO WANKO (PC): https://github.com/Vendily/DoronkoWankoArchipelago/releases
Dracomino (PC): https://github.com/DragonWolfLeo/DracominoAPWorld/releases
Dragon Warrior 1 (NES): https://github.com/Serpikmin/Archipelago-DragonWarrior/releases
DREDGE (PC): https://github.com/alextric234/ArchipelagoDredge/releases
Duke Nukem 3D: Atomic Edition (PC): https://github.com/LLCoolDave/Duke3DAP/releases
Dungeon Clawler (PC): https://github.com/agilbert1412/Clawrchipelago/releases
EarthBound (SNES): https://github.com/PinkSwitch/Archipelago/releases?q=earthbound&expanded=true
Ender Lilies: Quietus of the Knights (PC): https://github.com/Trexounay/EnderLilies.Archipelago/releases
Enter the Gungeon (PC): https://github.com/MaoBoulve/ArchipelaGunAPWorld/releases
Everhood 2 (PC): https://github.com/DeamonHunter/ArchipelagoEverhood2/releases
Fakutori (PC): https://github.com/chickentuna/Archipelago-Fakutori/releases/tag/apworld
Final Fantasy IV (SNES): https://github.com/Rosalie-A/Archipelago/releases?q=FF4&expanded=true
Final Fantasy VI (SNES): https://docs.google.com/document/d/1ZN-eO3ZasTEAReGCRP7l9tgI-kEh0GG4gJxVv7JOlyk/edit?tab=t.0
Final Fantasy X HD Remaster (PC): https://github.com/FFX-AP/Archipelago/releases
Final Fantasy XII: Open World (PC): https://github.com/Bartz24/Archipelago/releases
Final Fantasy XII: Trial Mode (PC): https://github.com/silasary/Archipelago/releases?q="FFXII+Trial+Mode"&expanded=true
Final Fantasy Tactics Advance (GBA): https://github.com/spicynun/Archipelago/releases
Final Fantasy Tactics: Ivalice Island (PC): https://github.com/Rosalie-A/Archipelago/releases?q=Tactics&expanded=true
Final Fantasy Tactics A2: Grimoire of the Rift (DS): https://github.com/Rurusachi/Archipelago/releases
Final Fantasy Pixel Remaster (PC): https://github.com/wildham0/FF1PRAP/releases/latest
Fire Emblem: The Sacred Stones (GBA): https://github.com/CT075/Archipelago/releases
Freedom Planet 2 (PC): https://github.com/Knuxfan24/Freedom-Planet-2-Archipelago/releases
Friday Night Funkin' (PC): https://github.com/Z11Coding/Mixtape-Engine-Rework/releases
Frogmonster (PC): https://github.com/Rooby-Roo/FrogmonsterAPWorld/releases
Garfield Kart - Furious Racing (PC): https://github.com/FeluciaPS/Archipelago/releases
Gato Roboto (PC): https://github.com/Ravenmist-Games/Gato-Roboto-AP-Tracker/releases
Gato Roboto B-Side (PC): https://github.com/Nitroxyz/Gato-Roboto-B-Side-Archipelago/releases
Gauntlet Legends (N64): https://github.com/jamesbrq/GauntletLegendsAP/releases
Getting Over It with Bennett Foddy (PC): https://github.com/BlastSlimey/CheckingOverIt/releases
GLYPHS (PC): https://github.com/BuffYoda21/ap-glyphs/releases/
Golden Sun: The Lost Age (GBA): https://github.com/cjmang/Archipelago/releases
Grim Dawn (PC): https://github.com/routhken/Archipelago/releases
Guild Wars 2 (PC): https://github.com/Feldar99/Archipelago/releases
gzDoom (PC): https://github.com/ToxicFrog/doom-mods/blob/main/release/gzdoom.apworld
Hades (PC): https://github.com/NaixGames/Polycosmos/releases
Hammerwatch (PC): https://github.com/Parcosmic/Hammerwatch-Archipelago/releases
HASTE: Broken Worlds (PC): https://github.com/WritingHusky/haste_apworld/releases
Hatsune Miku: Project Diva Mega Mix+ (PC): https://github.com/Cynichill/DivaAPworld/releases
Here Comes Niko! (PC): https://github.com/niieli/Niko-Archipelago/releases
Hero Core (PC): https://github.com/Minish-Link/HeroCore-Archipelago/releases
Hexcells Infinite (PC): https://github.com/Heaxeus/Archipelago/releases/
High Roller (PC): https://github.com/ElireFeltores/High-Roller/releases
Hi-Fi RUSH (PC): https://github.com/TRPG0/HbkArchipelago/releases
holo8 (PC): https://github.com/KitLemonfoot/ArchipelagoHolo8/releases/latest
Hololive Treasure Mountain (PC): https://github.com/StellatedCUBE/Treasure-Mountain-Archipelago/releases
Iji (PC): https://github.com/Minish-Link/Iji-Archipelago/releases
Into the Breach (PC): https://github.com/Ishigh1/ITB-randomizer-for-AP/releases
Ittle Dew 2+ (PC): https://github.com/Extra-2-Dew/ArchipelagoRandomizer/releases
Isles of Sea and Sky (PC): https://github.com/Kim-Delicious/Archipelago_IslesOfSeaAndSky/releases
Jak 2 (PC): https://github.com/narramoment/Archipelago/releases
Jet Island (VR): https://github.com/Nullctipus/JetIslandArchipelago/releases
Jigsaw (Web): https://github.com/spineraks-org/ArchipelagoJigsaw/releases
K-On! After School Live!! (PSP): https://github.com/dannybonz/k-on_archipelago/releases
Keep Talking and Nobody Explodes (PC): https://github.com/GreenPower713/Archipelago/releases
Keymaster's Keep (PC): https://github.com/SerpentAI/Archipelago/releases
KINGDOM HEARTS Chain of Memories (GBA): https://github.com/gaithernOrg/ArchipelagoKHCOM/releases
KINGDOM HEARTS Re:Chain of Memories (PC): https://github.com/gaithernOrg/ArchipelagoKHRECOM/releases
KINGDOM HEARTS Birth by Sleep FINAL MIX (PC): https://github.com/gaithernOrg/ArchipelagoKHBBS/releases/
Kirby 64: The Crystal Shards (N64): https://github.com/Silvris/Archipelago/releases?q=tag%3Ak64_0&expanded=true
Kirby Air Ride (GC): https://github.com/DeDeDeK/KARchipelago/releases/latest
Kirby Super Star (SNES): https://github.com/Silvris/Archipelago/releases?q=tag%3Akss_0&expanded=true
League of Legends (PC): https://github.com/gaithernOrg/LoLAP/releases
Lego Batman: The Video Game (PC): https://github.com/ZAPaDASH04/LEGO-Batman-Archipelago-Mod/releases/latest
Legend of Dragoon (PSX): https://github.com/pkolb-dev/Archipelago/releases
Lego Star Wars: The Complete Saga (PC): https://github.com/Mysteryem/Archipelago-TCS/releases
Lethal Company (PC): https://github.com/T0r1nn/APLC/releases
Lil Gator Game (PC): https://github.com/natronium/GatorArchipelago/releases
Lingo 2 (PC): https://code.fourisland.com/lingo2-archipelago/about/
Little Witch Nobeta (PC): https://github.com/danielgruethling/RandomizedWitchNobeta/releases
Loonyland: Halloween Hill (PC/Web): https://github.com/AutomaticFrenzy/HamSandwich/releases
Luigi's Mansion (GC): https://github.com/BootsinSoots/Archipelago/releases
Lunacid (PC): https://github.com/Witchybun/LunacidAPClient/releases/
Mario is Missing! (SNES): https://github.com/TheRealSolidusSnake/Mario-Is-Missing/releases
Mario Kart 64 (N64): https://github.com/Edsploration/MK64-Archipelago/releases
Mario Kart: Double Dash (GC): https://github.com/aXu-AP/archipelago-double-dash/releases
Mario Kart Wii (Wii): https://github.com/toent/Archipelago-MKWii/releases
Mario Super Sluggers (Wii): https://github.com/MarioManTAW/Archipelago/releases
MediEvil (1998) (PSX): https://github.com/riezahughes/MedievilAPWorld/releases
Mega Man 3 (NES): https://github.com/Silvris/Archipelago/releases?q=tag%3Amm3_0&expanded=true
Mega Man X (SNES): https://github.com/TheLX5/Archipelago/releases?q="Mega+Man+X"&expanded=true
Mega Man X2 (SNES): https://github.com/TheLX5/Archipelago/releases?q="Mega+Man+X2"&expanded=true
Mega Man X3 (SNES): https://github.com/TheLX5/Archipelago/releases?q="Mega+Man+X3"&expanded=true
MetroCUBEvania (PICO-8): https://github.com/ap-metrocubevania/ap-metrocubevania/releases
Metroid Fusion (GBA): https://github.com/Rosalie-A/Archipelago/releases?q=Metroid+Fusion&expanded=true
Metroid: Zero Mission (GBA): https://github.com/lilDavid/Archipelago-Metroid-Zero-Mission/releases
Metroid Prime (GC): https://github.com/UltiNaruto/MetroidAPrime/releases
Mindustry (PC): https://github.com/JohnMahglass/Archipelago-Mindustry/releases
Minecraft (NeoForge) (PC): https://github.com/qixils/NeoForgeAP/releases
Minecraft Dig (PC): https://github.com/jacobmix/Minecraft_AP_Randomizer/releases/
Minishoot' Adventures (PC): https://github.com/TheNooodle/MinishootRandomizer/releases
Minit (PC): https://github.com/qwint/APMinit/releases
Momodora: Moonlit Farewell (PC): https://github.com/alditoOt/Momodora-Moonlit-Farewell-Randomizer/releases
Monster Sanctuary (PC): https://github.com/Gtaray/archipelago-monstersanctuary/releases
Mystical Ninja Starring Goemon (N64): https://github.com/Killklli/MNSGRecompRando/releases
Nine Sols (PC): https://github.com/Ixrec/NineSolsArchipelagoRandomizer/releases
Nodebuster (PC): https://github.com/josephwhite/Emerlads-Nodebuster_AP_Mod/releases/
Nonogram (Picross) (PC/Mobile): https://github.com/spineraks-org/ArchipelagoNonogram/releases
OpenRCT2 (PC): https://github.com/Crazycolbster/rollercoaster-tycoon-randomizer/releases
OpenTTD (PC): https://github.com/solida1987/openttd-archipelago/releases
Ori and the Blind Forest (PC): https://github.com/c-ostic/Archipelago/releases
Ori and the Will of the Wisps (PC): https://github.com/Satisha10/APwotw_release/releases
Osu! (PC): https://github.com/lilymnky-F/Archipelago-Osu/releases
Our Ascent (PC): https://github.com/AzuriCaelum/OurAscentAPWorld/releases
Outer Wilds (PC): https://github.com/Ixrec/OuterWildsArchipelagoRandomizer/releases
Oxygen Not Included (PC): https://github.com/ShadowKitty42/ONI-Archipelago/releases
Panel De Pon/Tetris Attack (SNES): https://github.com/AgStarRay/TetrisAttackAP/releases
Paper Mario (N64): https://github.com/JKBSunshine/PMR_APWorld/releases
Paper Mario: The Thousand Year Door (GC): https://github.com/jamesbrq/ArchipelagoTTYD/releases
Parkitect (PC): https://github.com/CrusherRL/AP_Parkitect_World/releases
Peggle Deluxe (PC): https://github.com/SerpentAI/Archipelago/releases?q="peggle+deluxe"&expanded=true
Peggle Nights (PC): https://github.com/SerpentAI/Archipelago/releases?q="peggle+nights"&expanded=true
Pikmin 2 (GC): https://github.com/chpas0/Pikmin2Archipelago
Pinball FX3 (PC): https://github.com/SerpentAI/Archipelago/releases?q="pinball+fx3"&expanded=true
PixelDraw (PC): https://interestedsc2.itch.io/pixel-draw
Pizza Tower (PC): https://github.com/unsafetyskizzers/Archipelago/releases/latest/
Placid Plastic Duck Simulator (PC): https://github.com/SWCreeperKing/PPDSArchipelago/releases
Plants vs Zombies: Replanted/GOTY (PC): https://github.com/dannybonz/replanted_archipelago/releases
Plateup! (PC): https://github.com/CazIsABoi/Archipelago/releases
Plok (SNES): https://github.com/Happyhappyism/Archipelago/releases
Pokémon Pinball (GB): https://github.com/Happyhappyism/Archipelago/releases?q=pokemon&expanded=true
Pokémon Crystal (GBC): https://github.com/gerbiljames/Archipelago-Crystal/releases
Pokémon FireRed and LeafGreen (GBA): https://github.com/vyneras/Archipelago/releases
Pokémon Black and White (DS): https://github.com/BlastSlimey/PokemonBWAP/releases
Pokémon Platinum (DS): https://github.com/ljtpetersen/platinum_archipelago?tab=readme-ov-file
Pokémon Ranger (Quest) (DS): https://github.com/BlastSlimey/Archipelago/releases?q=Pokémon+Ranger+(Quest)&expanded=true
Pokémon Mystery Dungeon Explorers of Sky (DS): https://github.com/CrypticMonkey33/ArchipelagoExplorersOfSky/releases
PokéPark Wii: Pikachu's Adventure (Wii): https://github.com/Mekurushi/Archipelago_Pokepark/releases
Poképelago - Pokémon Guessing Game (PC): https://github.com/dowlle/PokepelagoClient/releases
Powerwash Simulator (PC): https://github.com/SWCreeperKing/PowerwashSimAP/releases
Prodigal (PC): https://github.com/randomsalience/ProdigalArchipelago/releases
Pseudoregalia (PC): https://github.com/pseudoregalia-modding/pseudoregalia-archipelago/releases
Psychonauts (PC): https://github.com/Akashortstack/Psychonauts-AP-Integration/releases
Rabi-Ribi (PC): https://github.com/tdkollins/Archipelago-Rabi-Ribi/releases
Rain World (PC): https://github.com/alphappy/ArchipelagoRW/releases
Ratchet & Clank (PS3): https://github.com/Panda291/Archipelago/releases
Ratchet & Clank: Going Commando (PS2): https://github.com/evilwb/APRac2/releases
Ratchet & Clank 3: Up Your Arsenal (PS2): https://github.com/Taoshix/Archipelago-RaC3/releases
Rayman 2: The Great Escape (PC): https://github.com/Aeltumn/Rayman2AP/releases
Refunct (PC): https://github.com/spinerak/refunct-tas-archipelago/releases/latest
R.E.P.O. (PC): https://github.com/Automagic00/R.E.P.O.-Archipelago-Client-Mod/releases
Reventure (PC): https://github.com/Droppel/ReventureEndingRando/releases
Rift of the NecroDancer (PC): https://github.com/studkid/RiftArchipelago/releases
Rift Wizard (PC): https://github.com/TheBigSalarius/Archipelago/releases
Risk of Rain (PC): https://github.com/studkid/RoR_Archipelago/releases
Risk of Rain Returns (PC): https://github.com/studkid/RoR_Archipelago/releases
Rusted Moss (PC): https://github.com/dgrossmann144/Archipelago/releases
Satisfactory (PC): https://github.com/Jarno458/SatisfactoryArchipelagoMod/releases
Scooby-Doo! Night of 100 Frights (GC): https://github.com/vgm5/Night_Of_100_Frights_ap_world/releases
Secret of Mana (SNES): https://github.com/black-sliver/som-apworld/releases
Sentinels of the Multiverse (PC / Physical): https://github.com/Totox00/Archipelago-sotm/releases
Severed Soul (PC): https://github.com/Grenhunterr/Archipelago/releases
Shadow the Hedgehog (GC): https://github.com/choatix/Archipelago/releases
Shadowgate 64 (N64): https://github.com/jjjj12212/Archipelago-Shadowgate64/releases
Shapez (PC): https://github.com/BlastSlimey/shapezipelago/releases
Shapez 2 (PC): https://github.com/BlastSlimey/2hapezipelago/releases
Sid Meier's Civilization V (PC): https://github.com/1313e/Civ-V-AP-World/releases
Simon Tatham's Portable Puzzle Collection (Web): https://github.com/ishanpm/ap-sgtpuzzles-web/releases
Slay the Spire (PC): https://github.com/cjmang/StS-AP-World/releases
Slime Rancher (PC): https://github.com/SWCreeperKing/Slimipelago/releases
Sly Cooper and the Thievius Raccoonus (PS2): https://github.com/hoppel16/ArchipelagoBranchSly1/releases
Sly 2: Band of Thieves (PS2): https://github.com/NikolajDanger/APSly2/releases
Smushi Come Home (PC): https://github.com/xMcacutt-Archipelago/Archipelago-SmushiComeHome/releases/latest
SMW: Spicy Mycena Waffles (SNES): https://github.com/TheLX5/Archipelago/releases?q=Spicy&expanded=true
Sonic the Hedgehog (GEN): https://github.com/kaithar/Archipelago/releases
Sonic Adventure DX (PC): https://github.com/ClassicSpeed/sadx-classic-randomizer/releases
Sonic Heroes (PC): https://github.com/Ethicallogic-Archipelago/SonicHeroesArchipelago/releases
Sonic Riders (GC): https://github.com/Ninjakakes/Archipelago/releases?q=Sonic+Riders&expanded=true
Sonic Rush (DS): https://github.com/BlastSlimey/SonicRushAP/releases
Soul Blazer (SNES): https://github.com/Tranquilite0/Archipelago-SoulBlazer/releases
Spelunky 2 (PC): https://github.com/DDR-Khat/Spelunky2-Archipelago/releases
Spinball (Web): https://github.com/spineraks-org/ArchipelagoSpinball/releases
SpongeBob SquarePants: Battle For Bikini Bottom (GC): https://github.com/Cyb3RGER/bfbb_ap_world/releases
Spyro 2 (PSX): https://github.com/Uroogla/S2AP/releases
Spyro 3 (PSX): https://github.com/Uroogla/S3AP/releases
Stacklands (PC): https://github.com/JammyGeeza/Stacklands-Randomizer/releases
Star Wars: Episode I - Racer (PC): https://github.com/wcolding/SWR_AP_Client/releases
Starfox 64 (N64): https://github.com/Auztin/AP-Star-Fox-64/releases
Stick Ranger (PC): https://github.com/Kryen112/AP_Stick_Ranger/releases
Streets of Rage (GEN): https://github.com/UltiNaruto/SOR_AP_Randomizer/releases
Super Cat Planet (PC): https://github.com/lone01/scp/releases
Super Junkoid (SNES): https://github.com/Ninjakakes/Archipelago/releases
Super Mario Sunshine (GC): https://github.com/Joshark/archipelago-sms/releases
Super Mario Sunshine Arcade 2 (GC): https://github.com/Jorbori/SMSA2AP/releases
Super Mario RPG (SNES): https://github.com/TheRealSolidusSnake/SMRPG_apworld/releases
Super Smash Bros. Melee: https://github.com/PinkSwitch/Archipelago/releases?q=melee&expanded=true
System Shock 2 (PC): https://github.com/Partatio/SS2-Apworld/releases
Talos Principle Reawakened (PC): https://github.com/johnso48/TalosPrincipleArchipelago/releases
TCG Card Shop Simulator (PC): https://github.com/FyreDay/Archipelago-TCGCardShopSimulator/releases
Tetris (GB): https://github.com/Alchav/Archipelago/releases?q=Tetris&expanded=true
TEVI (PC): https://github.com/BlackSoulKnight/Tevi_Archipelago/releases
The Binding of Isaac: Repentance (PC): https://github.com/NaveTK/Archipelago/releases
The Forged Curse (PICO-8): https://github.com/cheesepak/ap-forged-curse/releases
The Grinch (PSX): https://github.com/MarioSpore/Grinch-AP/releases
The Legend of Heroes: Trails in the Sky the 3rd (PC): https://github.com/Archipelago-Trails-in-the-Sky-the-3rd/Archipelago-Trails-in-the-Sky-the-3rd/releases
The Legend of Zelda II: The Adventure of Link (NES): https://github.com/PinkSwitch/Archipelago/releases?q=zelda&expanded=true
The Legend of Zelda: Ocarina of Time (Ship of Harkinian) (PC): https://github.com/HarbourMasters/Archipelago-SoH?tab=readme-ov-file#ship-of-harkinian--archipelago
The Legend of Zelda: Ocarina of Time but it's just Master Quest Water Temple (N64): https://github.com/Alchav/Archipelago/releases?q=Water&expanded=true
The Legend of Zelda: Majora's Mask (N64/PC): https://github.com/RecompRando/MMRecompRando/releases
The Legend of Zelda: Oracle of Ages (GBC): https://github.com/SenPierre/ArchipelagoOoA/releases
The Legend of Zelda: Oracle of Seasons (GBC): https://github.com/Dinopony/ArchipelagoOoS/releases
The Legend of Zelda: The Minish Cap (GBA): https://github.com/eternalcode0/Archipelago/releases/
The Legend of Zelda: Twilight Princess (GC): https://github.com/WritingHusky/Twilight_Princess_apworld/releases
The Legend of Zelda: Skyward Sword (Wii): https://github.com/Battlecats59/SS_APWorld/releases
The Legend of Zelda: Phantom Hourglass (DS): https://github.com/carrotinator/Archipelago/releases
The Legend of Zelda: Spirit Tracks (DS): https://github.com/DayKat/spirit-tracks/releases
The Legend of Zelda: A Link Between Worlds (3DS): https://github.com/randomsalience/albw-archipelago/releases
The Simpsons: Hit and Run (PC): https://github.com/nmize1/Archipelago/releases
The Sims 4 (PC): https://github.com/benny-dreamly/Archipelago/releases/latest
Toejam & Earl (GEN): https://github.com/IgnisUmbrae/TJE-Archipelago/releases
TOEM (PC): https://github.com/bbernardoni/Archipelago.TOEM/releases
Tombola (PC): https://github.com/Arenes214/APWorld-Tombola/releases
Total War Warhammer 3: Immortal Empires (PC): https://github.com/jordansds/Archipelago_TWW3_Alt/releases
Totally Accurate Battle Simulator (PC): https://github.com/duckboycool/TABS-Archipelago/releases
Touhou 18.5 (PC): https://github.com/furret78/Archipelago/releases
Trackmania Random Campaign (PC): https://github.com/SerialBoxes/ArchipelagoTrackmania/releases
Turnip Boy Commits Tax Evasion (PC): https://github.com/pointfivetee/TurnipBoyRandomizer/releases
Twisty Cube (PC/Mobile): https://github.com/spineraks-org/ArchipelagoTwistyCube/releases/latest
Tyrian (PC): https://github.com/KScl/TyrianArchipelago/releases
Ty the Tasmanian Tiger (PC): https://github.com/xMcacutt/Archipelago-TyTheTasmanianTiger/releases
Unfair Flips (PC): https://github.com/xMcacutt-Archipelago/Archipelago-UnfairFlips/releases
UFO 50 (PC): https://github.com/UFO-50-Archipelago/Archipelago/releases
Voltorb Flip (HGSS) (DS): https://github.com/BlastSlimey/Archipelago/releases?q=Voltorb+Flip&expanded=true
Void Sols (PC): https://github.com/cookie966507/Archipelago/releases
Void Stranger (PC): https://github.com/CriminalPancake/void-stranger-ap/releases
Wargroove 2 (PC): https://github.com/FlySniper/Archipelago/releases?q=Wargroove+2&expanded=true
Wario Land: Super Mario Land 3 (GB): https://github.com/randomcodegen/Archipelago/releases
Wario Land 4 (GBA): https://github.com/lilDavid/Archipelago-Wario-Land-4/releases
Wario World (GC): https://github.com/m0ester/WarioworldAP/releases
Watery Words (Web): https://github.com/spineraks-org/ArchipelagoWateryWords/releases
WEBFISHING (PC): https://github.com/mwoiii/webfishing-ap/releases
West of Loathing (PC): https://github.com/Lucasvdm/WOLAP/releases
Wordipelago (Web): https://github.com/ProfDeCube/Archipelago/releases
XCOM 2: War of the Chosen (PC): https://github.com/MaxReinstadler/X2WOTCArchipelago/releases
Xenoblade Chronicles X (Wii U): https://github.com/MaragonMH/Archipelago/releases
YARG (Yet Another Rhythm Game) (PC): https://github.com/energymaster22/YARGArchipelago/releases
YARG (Guitar Hero 1/Rock Band 3/Combined) (PC): https://github.com/GirlWithoutAFairy/YARGArchipelago-GH-and-RB-forks/releases
Donkey Kong Country (Mirror Hack) (SNES): https://github.com/TheLX5/Archipelago/releases?q=yeknoD&expanded=true
Yoku's Island Express (PC): https://git.makuluni.com/Archipelago/YokuAPWorld/releases
Yooka-Laylee (PC): https://github.com/Awareqwx/Archipelago/releases
Yu-Gi-Oh! Dungeon Dice Monsters (GBA): https://github.com/JustinMarshall98/Archipelago/releases
Yu-Gi-Oh! Forbidden Memories (PSX): https://github.com/sg4e/Archipelago/releases
Zork: Grand Inquisitor (PC): https://github.com/SerpentAI/Archipelago/releases?q=zork&expanded=true"""

new_games_count = 0
updated_games_count = 0

for line in github_data.strip().split('\n'):
    if not line.strip():
        continue

    # Parser: "Name (Platform): URL"
    match = re.match(r'^(.+?)\s+\(([^)]+)\):\s+(.+)$', line.strip())
    if match:
        name = match.group(1).strip()
        platform = match.group(2).strip()
        github_url = match.group(3).strip()

        # Create game ID
        game_id = name.lower().replace(' ', '-').replace(':', '').replace("'",
                                                                          '').replace('!', '').replace('&', 'and').replace('/', '-')

        if game_id in games_by_id:
            # Update existing game
            games_by_id[game_id]['githubUrl'] = github_url
            updated_games_count += 1
        else:
            # Add new game
            game = {
                "id": game_id,
                "name": name,
                "platform": platform,
                "url": f"https://archipelago.gg/games/{name.replace(' ', '%20')}/info/en",
                "description": f"Archipelago randomizer for {name} ({platform})",
                "githubUrl": github_url,
                "completed": [],
                "todo": []
            }
            games_by_id[game_id] = game
            new_games_count += 1

# Convert back to list and save
updated_games = list(games_by_id.values())
result = {"games": updated_games}

with open('../data/games.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Updated {updated_games_count} games with GitHub URLs")
print(f"Added {new_games_count} new games")
print(f"Total games: {len(updated_games)}")
