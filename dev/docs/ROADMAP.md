# Yu-Gi-Oh! Joey The Passion: game + ladder site roadmap

Draft for discussion, 2026-11-26. Covers the new PC game (EDOPro fork, `D:\JTP`) and the ladder site
(`D:\MyProjects\Active\YuGiOh Return`, live at yugioh-jtp-ladder.vercel.app).

## Where things stand
- **Game**: rebranded EDOPro fork, JTP card pool (1,098 cards, all with art), classic Master Rule 1,
  WindBot with Joey's 58 decks, original music/SFX, spectate (Watch), simplified host + settings.
  Multiplayer today = LAN host/join over Radmin/Hamachi.
- **Site**: Next.js 16 + Prisma + Supabase on Vercel. Elo (Skill Points), seasonal Duel Points, Gold/EXP/levels,
  Appeals, admin panel, news, Arabic/RTL, banlist page. Results are **self-reported**; banlist is honor system;
  disconnects are unhandled (BUILD_PLAN §18).
- **Constraint**: Vercel cannot host a game server (no long-lived TCP). The game server needs a small VPS.
- **Data gap**: site card list = ~380 cards with custom IDs; the game uses real passcodes (full list of 1,098
  in `edopro-pack/jtp_cards.csv`, with images).

## Architecture
```
 JTP.exe (PC, later Android)
   ├─ HTTPS: login, profile, banlist, updates ──► Site API (Vercel) ──► Supabase
   └─ TCP: duels ──► Game server (VPS, Multirole: runs ocgcore + JTP scripts)
                        └─ duel end → signed result + replay ──► Site API → applyDuelResult()
```
The server runs every ranked duel, so results are trusted (no claims, no "who won" disputes).

## Phases
1. **Updates + version lock**: content updates via a git repo the game pulls on start; exe updates via
   EDOPro's client updater + GitHub Releases; game refuses ranked/online with a different JTP version.
2. **Online server**: Multirole on a VPS, "Online" button with a room list (no VPN). LAN stays for friends.
3. **Site accounts in game**: new `/api/game/*` routes (login → game token, me, banlist). Game shows
   avatar, Skill Points/tier, level, gold.
4. **Ranked duels**: site challenge → "Play" in game → server room → server posts result + replay →
   `applyDuelResult` (new source: `server`). Disconnect rule enforced by the server.
5. **Real banlist**: site `CardLimit` switches to game passcodes and the full card list; site serves the
   lflist, and game + server enforce it. Site card pages get all 1,098 cards with images.
6. **Matchmaking**: in-game ranked queue by Elo (alternative to challenges).
7. **Tournaments**: site brackets → server matches; Watch mode (with optional delay) for finals.
8. **Progression in game**: shop cosmetics (avatars, card backs, field skins, titles) shown in duels;
   quests using server data (deck/card based).
9. **Arabic game**, then **Android** (same server + accounts).

## Open decisions (owner)
1. VPS for the game server (~€4-5/month)?
2. Transition: keep self-report for original-game duels + auto "Verified" for new-game duels (recommended),
   or new-game-only ranked?
3. Rules parity check: EDOPro engine vs original JTP engine for meta cards before ranked launch?
4. Disconnect rule (auto-loss after a grace period vs Judge review)?
5. Site workflow: changes on a branch + test DB, owner deploys?
