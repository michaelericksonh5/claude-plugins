@echo off
setlocal EnableDelayedExpansion
title slot-art-creator-node installer
cd /d "%~dp0"
echo.
echo  slot-art-creator-node ^| High 5 Games
echo  ========================================
echo  Node.js edition. No Python required.
echo.
:: -----------------------------------------------------------------------
:: Check Node.js
:: -----------------------------------------------------------------------
where node >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Node.js not found.
    echo.
    echo  Install Node.js 20 or later from:
    echo    https://nodejs.org/en/download
    echo.
    echo  Then re-run this installer.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>nul') do set NODE_VER=%%v
echo  Found Node.js %NODE_VER%
for /f "tokens=1 delims=." %%m in ("%NODE_VER:v=%") do set NODE_MAJOR=%%m
if !NODE_MAJOR! LSS 20 (
    echo  ERROR: Node.js 20 or later required. You have %NODE_VER%.
    echo  Download from https://nodejs.org/en/download
    pause
    exit /b 1
)
:: -----------------------------------------------------------------------
:: Install npm dependencies
:: -----------------------------------------------------------------------
echo.
echo  Installing dependencies (this takes about 10 seconds)...
cd nb2-mcp-server
:: Use npm ci if package-lock.json exists for reproducible installs.
:: --no-audit / --no-fund suppress audit + funding noise (audit is already
:: run + cleaned at build time; coworkers don't need it again).
::
:: The deprecated `node-domexception` polyfill is replaced at install time
:: with a local shim (see nb2-mcp-server/shims/node-domexception/) wired
:: in via the npm `overrides` block in package.json. The shim re-exports
:: globalThis.DOMException, which is native on Node >=20 (our minimum).
:: Result: no deprecation warning at install time, no functional change.
if exist package-lock.json (
    call npm ci --prefer-offline --no-audit --no-fund 2>&1
    if errorlevel 1 (
        echo  Offline install failed, trying online...
        call npm ci --no-audit --no-fund 2>&1
    )
) else (
    call npm install --no-audit --no-fund 2>&1
)
if errorlevel 1 (
    echo.
    echo  ERROR: npm install failed. Check your internet connection and try again.
    pause
    exit /b 1
)
:: Bundle the MCP server into a single self-contained file at dist/index.mjs.
:: Marketplace cloners (Claude Code, Cowork) don't run npm install on the
:: cached plugin, so the cached install can't reach node_modules. plugin.json
:: points at the bundle, which has zero runtime deps.
echo  Building MCP server bundle...
call npm run build --silent 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: npm run build failed.
    pause
    exit /b 1
)
cd ..
echo  Dependencies installed and bundle built.
:: -----------------------------------------------------------------------
:: API key setup
:: -----------------------------------------------------------------------
echo.
echo  This plugin needs an API key to generate images.
echo  EITHER KEY ALONE is fully sufficient for all 4 tools — both providers can do everything.
echo  Setting BOTH only matters because each tool gets routed to its strongest backend.
echo.
echo    Option 1 - Google Gemini   https://aistudio.google.com/apikey
echo    Option 2 - fal.ai          https://fal.ai/dashboard
echo.
set /p RUN_SETUP="  Set up API key(s) now? [Y/n] "
if /i "!RUN_SETUP!"=="n" goto skip_keys
node setup-keys.js
goto done_keys
:skip_keys
echo.
echo  Skipped. Run later:  node setup-keys.js
:done_keys
:: -----------------------------------------------------------------------
:: Prepare Claude Code marketplace / legacy Cowork upload ZIP
:: -----------------------------------------------------------------------
echo.
echo  Where do you want to install this plugin?
echo    [1] Claude Code only (this machine)   [RECOMMENDED]
echo    [2] Claude Code + legacy/admin Cowork ZIP
echo    [3] Legacy/admin Cowork ZIP only
echo    [4] Skip (I will install manually)
echo.
echo  Note: Claude Code and Claude Cowork are SEPARATE plugin systems even though
echo        they both live inside the Claude desktop app. Cowork's normal path is
echo        the H5G marketplace URL. The ZIP option is only for legacy/admin cases
echo        where GitHub-synced marketplaces are blocked.
echo.
set /p INSTALL_TARGET="  Choice [1]: "
if "!INSTALL_TARGET!"=="" set INSTALL_TARGET=1
:: Resolve source path WITHOUT trailing backslash so we can compare directly
:: with the destination path. (%~dp0 always ends in \, the targets do not.)
set "SOURCE_DIR=%~dp0"
if "!SOURCE_DIR:~-1!"=="\" set "SOURCE_DIR=!SOURCE_DIR:~0,-1!"
if "!INSTALL_TARGET!"=="1" goto install_code
if "!INSTALL_TARGET!"=="2" goto install_both
if "!INSTALL_TARGET!"=="3" goto package_cowork
goto done_install
:install_code
echo.
echo  Preparing Claude Code local marketplace source...
set "CODE_MARKETPLACE_PLUGIN=%USERPROFILE%\Documents\Claude_Plugins\slot-art-creator-node"
call :copy_plugin "!SOURCE_DIR!" "!CODE_MARKETPLACE_PLUGIN!"
if errorlevel 1 goto done_install
echo  Marketplace source ready at: !CODE_MARKETPLACE_PLUGIN!
goto done_install
:package_cowork
echo.
echo  Building legacy/admin Claude Cowork upload ZIP...
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\package-cowork-zip.ps1"
if errorlevel 1 (
    echo.
    echo  ERROR: Cowork ZIP packaging failed.
    pause
    exit /b 1
)
goto done_install
:install_both
echo.
echo  Preparing Claude Code marketplace and legacy/admin Cowork ZIP...
set "CODE_MARKETPLACE_PLUGIN=%USERPROFILE%\Documents\Claude_Plugins\slot-art-creator-node"
call :copy_plugin "!SOURCE_DIR!" "!CODE_MARKETPLACE_PLUGIN!"
if errorlevel 1 goto done_install
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\package-cowork-zip.ps1"
if errorlevel 1 (
    echo.
    echo  ERROR: Cowork ZIP packaging failed.
    pause
    exit /b 1
)
echo  Marketplace source ready at: !CODE_MARKETPLACE_PLUGIN!
goto done_install
:: ---------------------------------------------------------------
:: Helper: copy_plugin <source> <dest>
:: Idempotent. Refuses to delete the destination when source==dest
:: (which would be self-destructive when the user runs install.bat
:: from inside the local marketplace source folder).
:: ---------------------------------------------------------------
:copy_plugin
setlocal
set "SRC=%~1"
set "DST=%~2"
:: Strip any trailing backslash from both for comparison
if "!SRC:~-1!"=="\" set "SRC=!SRC:~0,-1!"
if "!DST:~-1!"=="\" set "DST=!DST:~0,-1!"
:: Case-insensitive compare via /i
if /i "!SRC!"=="!DST!" (
    echo  Skipping copy — source and destination are the same path:
    echo    !SRC!
    echo  ^(the plugin is already at the target. No files to copy.^)
    endlocal
    exit /b 0
)
set "STAGE_ROOT=%TEMP%\slot-art-creator-node-%RANDOM%-%RANDOM%"
set "STAGE=!STAGE_ROOT!\slot-art-creator-node"
if exist "!STAGE_ROOT!" rmdir /s /q "!STAGE_ROOT!"
mkdir "!STAGE!" >nul 2>&1
for %%I in (.claude-plugin skills agents hooks nb2-mcp-server shared) do (
    if exist "!SRC!\%%I\" (
        robocopy "!SRC!\%%I" "!STAGE!\%%I" /E /XD node_modules generated logs .git .cache cache caches __pycache__ /XF .env .env.* *.zip *.7z *.tar *.tgz *.tar.gz *.rar *.log npm-debug.log* yarn-debug.log* yarn-error.log* pnpm-debug.log* *.pem *credentials* id_rsa* id_ed25519* >nul
        if !ERRORLEVEL! GEQ 8 (
            echo  ERROR: failed to stage %%I for marketplace copy.
            if exist "!STAGE_ROOT!" rmdir /s /q "!STAGE_ROOT!"
            endlocal
            exit /b 1
        )
    )
)
for %%I in (package.json README.md setup-keys.js setup-keys.bat setup-keys.ps1 setup-keys.sh .env.example) do (
    if exist "!SRC!\%%I" copy /y "!SRC!\%%I" "!STAGE!\%%I" >nul
)
if exist "!DST!" rmdir /s /q "!DST!"
for %%P in ("!DST!") do set "DST_PARENT=%%~dpP"
if not exist "!DST_PARENT!" mkdir "!DST_PARENT!" >nul 2>&1
move /y "!STAGE!" "!DST!" >nul
if exist "!STAGE_ROOT!" rmdir /s /q "!STAGE_ROOT!"
endlocal
exit /b 0
:done_install
:: -----------------------------------------------------------------------
:: Register the marketplace + plugin with Claude Code
:: -----------------------------------------------------------------------
:: Idempotent — adds h5g-plugins to settings.json's extraKnownMarketplaces
:: and writes a local marketplace manifest so the plugin shows up in the
:: documented Claude Code plugin marketplace flow.
:: Registration runs for options [1] and [2] - both prepare the
:: Code marketplace. Option [3] is ZIP-only so it skips registration.
if "!INSTALL_TARGET!"=="1" goto register_code
if "!INSTALL_TARGET!"=="2" goto register_code
goto skip_register
:register_code
    echo.
    echo  Registering plugin with Claude Code...
    set /p ENABLE_NOW="  Enable plugin automatically? [Y/n] "
    if /i "!ENABLE_NOW!"=="n" (
        call node "%~dp0tools\register-marketplace.js" 2>&1
    ) else (
        call node "%~dp0tools\register-marketplace.js" --enable 2>&1
    )
    if errorlevel 1 (
        echo.
        echo  WARNING: marketplace registration script failed.
        echo  You can re-run it later with:
        echo    node "%~dp0tools\register-marketplace.js" --enable
    )
:skip_register
echo.
:: -----------------------------------------------------------------------
:: H drive detection (shared asset folder)
:: -----------------------------------------------------------------------
echo.
set "H_DRIVE_PATH=H:\Shared drives\Content Management - AI\Production_AI 2\Asset_Creation_Suite"
if exist "%H_DRIVE_PATH%" (
    echo  [OK] Asset suite detected at: %H_DRIVE_PATH%
    echo       Projects will be saved in {GameID}_%USERNAME% folders here.
) else (
    echo  [!] Asset suite folder not found at H:\
    echo      Make sure Google Drive for Desktop is running and the H: drive is mounted.
    echo      Expected path: %H_DRIVE_PATH%
)
echo.
:: -----------------------------------------------------------------------
:: Final verification — read the installed state and confirm everything
:: is wired correctly. This is what tells the user (or a coworker) whether
:: the install actually succeeded end-to-end, vs. a half-finished state.
:: -----------------------------------------------------------------------
call node "%~dp0tools\verify-install.js"
set VERIFY_RC=!ERRORLEVEL!
echo.
if !VERIFY_RC! NEQ 0 (
    echo  Verification reported a failure above. Address the items marked [FAIL]
    echo  before reloading Claude Code, otherwise the slot- commands will not appear.
    pause
    exit /b !VERIFY_RC!
)
:: If a Cowork ZIP was built, surface it as a legacy/admin escape hatch.
:: The normal Cowork path is the H5G marketplace URL.
set "COWORK_ZIP=%~dp0dist\slot-art-creator-node-cowork-upload.zip"
if exist "!COWORK_ZIP!" (
    echo.
    echo  ========================================================================
    echo   LEGACY/ADMIN COWORK ZIP
    echo  ========================================================================
    echo.
    echo   The optional Cowork upload ZIP is built at:
    echo     !COWORK_ZIP!
    echo.
    echo   Use it only if GitHub-synced marketplaces are blocked by org policy.
    echo   Otherwise use the H5G marketplace install path in Claude Desktop.
    echo.
    echo.
)
echo  ----------------------------------------------------------
echo   CLAUDE CODE — already installed and registered automatically
echo  ----------------------------------------------------------
echo   Reload Claude Code (Ctrl+Shift+P ^> Developer: Reload Window) to activate.
echo   Then type /slot-step- to see the 11 numbered workflow commands.
echo.
echo  Press any key to exit.
pause
exit /b 0
