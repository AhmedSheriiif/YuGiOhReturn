# Rebuild YuGiOh Return (PC) end to end and install into D:\YugiohReturn\game.
#
#   .\tools\build_pc.ps1               build client + WindBot, regenerate assets, install
#   .\tools\build_pc.ps1 -Regenerate   also re-run premake (after adding/removing C++ files)
#   .\tools\build_pc.ps1 -AssetsOnly   skip compiling; only regenerate + install assets
#
# Layout (on D: because C: is full):
#   D:\YugiohReturn\edopro   client source (edo9300/edopro, our branch "jtp") + ocgcore submodule
#   D:\YugiohReturn\windbot  AI source (ProjectIgnis/windbot, our branch "jtp", JoeyExecutor)
#   D:\YugiohReturn\vcpkg    prebuilt deps (edopro-vcpkg-cache). git2.lib was REBUILT locally
#                   (libgit2 1.8.5, WinHTTP, /MT) because the cached one is LTCG from VS2022
#                   and won't link with VS18/v145; original kept as git2.lib.vs2022-orig.
#   D:\YugiohReturn\d3d9sdk  DirectX 9 SDK headers
#   D:\YugiohReturn\game     the playable game (ProjectIgnis/Distribution + our files) -> YuGiOhReturn.exe
param([switch]$Regenerate, [switch]$AssetsOnly)
$ErrorActionPreference = 'Continue'   # native tools write warnings to stderr; failures are checked via $LASTEXITCODE
$tools = $PSScriptRoot
$msb = 'C:\Program Files\Microsoft Visual Studio\18\Insiders\MSBuild\Current\Bin\MSBuild.exe'

if (Get-Process YuGiOhReturn,JTP -ErrorAction SilentlyContinue) { throw 'Close the game (YuGiOhReturn.exe) first.' }

if (-not $AssetsOnly) {
    # --- client
    $env:DXSDK_DIR = 'D:\YugiohReturn\d3d9sdk\'
    $env:VCPKG_ROOT = 'D:\YugiohReturn\vcpkg'
    $env:LINK = 'winhttp.lib crypt32.lib rpcrt4.lib secur32.lib ole32.lib advapi32.lib'
    python "$tools\patch_yugiohreturn.py"; if ($LASTEXITCODE) { throw 'rename patch failed' }
    Push-Location D:\YugiohReturn\edopro
    if ($Regenerate) {
        .\premake5.exe vs2022 --bundled-font=NotoSansJP-Regular.otf --sound=miniaudio --vcpkg-root=D:/YugiohReturn/vcpkg --no-joystick=true
    }
    & $msb build\ygo.sln -m -t:ygopro -p:Configuration=Release -p:Platform=Win32 -p:PlatformToolset=v145 `
        "-p:ForceImportBeforeCppTargets=D:\YugiohReturn\vcpkg\scripts\buildsystems\msbuild\vcpkg.targets" `
        -p:VcpkgRoot=D:\YugiohReturn\vcpkg\ -p:VcpkgEnableManifest=false -verbosity:minimal
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "client build failed ($LASTEXITCODE)" }
    Pop-Location
    Copy-Item D:\YugiohReturn\edopro\bin\release\ygopro.exe D:\YugiohReturn\game\YuGiOhReturn.exe -Force
    Remove-Item D:\YugiohReturn\game\JTP.exe -ErrorAction SilentlyContinue   # old name

    # --- WindBot (AI)
    & $msb D:\YugiohReturn\windbot\WindBot.csproj -p:Configuration=Release -p:TargetFrameworkVersion=v4.8 -verbosity:minimal
    if ($LASTEXITCODE -ne 0) { throw "WindBot build failed ($LASTEXITCODE)" }
}

# --- assets (cards, decks, theme, audio) and install
python "$tools\build_edopro_pack.py";  if ($LASTEXITCODE) { throw 'pack failed' }
# art for cards from the other Power of Chaos games (downloads only what is missing), then rebuild pics
python "$tools\fetch_missing_art.py";  if ($LASTEXITCODE) { throw 'art download failed' }
python "$tools\build_edopro_pack.py";  if ($LASTEXITCODE) { throw 'pack failed' }
python "$tools\build_theme.py";        if ($LASTEXITCODE) { throw 'theme failed' }
python -W ignore "$tools\build_audio.py" 2>$null; if ($LASTEXITCODE) { throw 'audio failed' }
$pack = Join-Path $tools '..\edopro-pack'
Copy-Item "$pack\pics\*" D:\YugiohReturn\game\pics\ -Force
# banlists come from tools/banlists/*.json (Banlist Editor); replace the installed set with exactly those
Remove-Item D:\YugiohReturn\game\lflists\*.lflist.conf -ErrorAction SilentlyContinue
Copy-Item "$pack\lflists\*.lflist.conf" D:\YugiohReturn\game\lflists\ -Force
Copy-Item "$pack\deck\*.ydk" D:\YugiohReturn\game\deck\ -Force
python "$tools\install_theme.py";      if ($LASTEXITCODE) { throw 'theme install failed' }
python "$tools\install_windbot.py";    if ($LASTEXITCODE) { throw 'windbot install failed' }
Write-Host 'OK: D:\YugiohReturn\game\YuGiOhReturn.exe'
