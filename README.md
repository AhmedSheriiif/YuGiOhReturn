# YuGiOh Return — developer guide

YuGiOh Return is a PC Yu-Gi-Oh! duel game built on the open-source EDOPro engine, with the graphics, music
and card pool of *Yu-Gi-Oh! Power of Chaos: Joey The Passion*, Joey as the computer opponent (WindBot),
LAN / Radmin VPN online play, spectating, banlists and an automatic updater. Developed by AhmedSherif.

This file is for **you, the developer**. Players only ever get the zip from the Releases page.

---

## 1. What is where

Everything lives in `D:\YugiohReturn`:

| Folder | What it is | On GitHub? |
|---|---|---|
| `game\` | The playable game (`YuGiOhReturn.exe`). Builds install into it; test here. | no |
| `edopro\` | The game engine source (EDOPro, branch `jtp`, with our changes). | no |
| `windbot\` | The computer-opponent source (WindBot, branch `jtp`, Joey's AI). | no |
| `dev\tools\` | All build / release scripts and the Banlist Editor. | **yes** |
| `dev\tools\banlists\` | Your banlists (`*.json`, written by the Banlist Editor). | **yes** |
| `dev\docs\` | Notes about the original game's data. | **yes** |
| `dev\edopro-pack\`, `dev\extracted\`, `dev\downloads\` | Cards, pictures, theme and sounds made from the original game. | no |
| `releases\<version>\` | Finished zips for each version. | no (zips go to GitHub *Releases*) |
| `updates\` | The update index the game reads on start (`<version>.json`). | **yes** |
| `vcpkg\`, `d3d9sdk\`, `dl\` | Libraries the engine needs to compile. | no |
| `_tests\` | Old test copies, build logs, a throwaway test database. Safe to delete. | no |

GitHub repo: <https://github.com/AhmedSheriiif/YuGiOhReturn> (must stay **public**: the game downloads
`updates/*.json` and the update zips from it without logging in).

Needed on this PC to build: Visual Studio 18 (C++ and .NET desktop workloads), Python 3.11, ffmpeg,
Git and the GitHub CLI (`gh`, logged in as AhmedSheriiif).

All commands below are typed in **PowerShell**.

---

## 2. Change a banlist and send it to players

1. **Edit the list.** Open the *YuGiOh Return Banlist Editor* shortcut on the Desktop
   (or double-click `D:\YugiohReturn\dev\tools\banlist_editor.pyw`).
   Pick the list (or **New**), search a card, choose Forbidden / Limited / Semi-Limited / Unlimited, then **Save**.
   Saving also installs it into `D:\YugiohReturn\game`, so you can try it right away (Host → banlist).
   New players start with the first list alphabetically.
2. **Raise the version.** Open `D:\YugiohReturn\edopro\gframe\config.h` and add 1 to `JTP_VERSION_PATCH`
   (1.0.0 → 1.0.1). That file is the only place the version number lives.
   * Use **PATCH** for banlists, card fixes and small changes. Players on different PATCH versions can still
     connect, but a room only lets in players whose card data and banlists are identical, so everyone needs the update.
   * Changing **MINOR** or **MAJOR** blocks old versions from connecting at all.
3. **Build** (close the game first):
   ```
   cd D:\YugiohReturn\dev\tools
   .\build_pc.ps1
   ```
   It ends with `OK: D:\YugiohReturn\game\YuGiOhReturn.exe`. Start the game and check the title shows the new version.
4. **Package the release:**
   ```
   python make_release.py 1.0.1 --base-url https://github.com/AhmedSheriiif/YuGiOhReturn/releases/download --notes "New banlist"
   ```
   This writes `D:\YugiohReturn\releases\1.0.1\` (`YuGiOhReturn-1.0.1-full.zip`, `YuGiOhReturn-1.0.1-update.zip`,
   `release.json`) and updates `D:\YugiohReturn\updates\` (one file per older version, listing what it must download).
5. **Publish on GitHub** (the tag must be exactly the version number):
   ```
   cd D:\YugiohReturn
   gh release create 1.0.1 releases\1.0.1\YuGiOhReturn-1.0.1-update.zip releases\1.0.1\YuGiOhReturn-1.0.1-full.zip --title "YuGiOh Return 1.0.1" --notes "New banlist"
   git add updates dev
   git commit -m "Release 1.0.1: new banlist"
   git push
   ```
   Upload the release **before** pushing `updates\`, otherwise players would be told to download a file that isn't there yet.
6. **Done.** Players see "Update available" the next time they start the game, click it, and the game downloads the
   small update zip, checks it, installs it and restarts. New players download the full zip from the Releases page
   (you can also put that same zip on MediaFire / Google Drive and link it on the website).

The updater can add and replace files but never deletes them. If you remove a file from the game, it stays on
players' PCs (harmless unless it's a banlist: to retire a banlist, keep its file but leave it empty, or tell players).

---

## 3. Change the game itself (code, graphics, AI)

* **Engine changes** are made by the `dev\tools\patch_*.py` scripts, which edit `D:\YugiohReturn\edopro`. Each can be
  run again safely. `build_pc.ps1` runs `patch_yugiohreturn.py` (name, version, update address, defaults) every time.
* **Graphics / sounds / cards** are generated from the original game by `build_theme.py`, `build_audio.py` and
  `build_edopro_pack.py` (all run by `build_pc.ps1`).
* **Only assets changed?** `.\build_pc.ps1 -AssetsOnly` skips compiling. **Added C++ files?** `.\build_pc.ps1 -Regenerate`.
* Then release it exactly like section 2, steps 2–6.

---

## 4. Test before releasing

* Start `D:\YugiohReturn\game\YuGiOhReturn.exe`, duel Joey (Single Player), host a LAN room.
* Online test: copy `game\` to a second folder, start both, host in one and join from the other with `127.0.0.1`.
  If the joiner is refused with a "different game files" message, the two copies don't match (that's the
  anti-tamper check working).
* To test the updater, keep a copy of the previous release's full zip, unzip it somewhere, publish the new release,
  then start the old copy: it should offer the update and restart on the new version.

---

## 5. Settings new players start with

Set in `dev\tools\make_release.py` → `DEFAULT_SETTINGS` (only used for the full zip):
nickname `Duelist`, theme `YuGiOh Return`, first banlist selected, best of 1, music 50 %, sound 60 %,
and **automatic monster and spell/trap placement turned on** (also the engine default in `game_config.inl`).

---

## 6. The website

The ladder website is a separate project: `D:\MyProjects\Active\YuGiOh Return`. How to change it and put it live
is in `D:\MyProjects\Active\YuGiOh Return\WEBSITE_UPDATE_STEPS.txt`. Short version: commit on a branch, merge into
`master`, `git push origin master` — Vercel builds it, applies database changes, and publishes it.
