[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.-]{1,48}[A-Za-z0-9]$')]
    [string]$IdentityName,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Publisher,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$PublisherDisplayName,

    [ValidatePattern('^\d+\.\d+\.\d+\.\d+$')]
    [string]$Version = '1.0.1.0',

    [string]$OutputPath,

    [switch]$RunAppCertKit
)

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '.'))
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'Run setup_windows.bat first so the project dependencies are available.'
}

function Remove-WorkspacePath([string]$TargetPath) {
    $absoluteTarget = [IO.Path]::GetFullPath($TargetPath)
    $absoluteRoot = [IO.Path]::GetFullPath($projectRoot).TrimEnd('\') + '\'
    if (-not $absoluteTarget.StartsWith($absoluteRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the project: $absoluteTarget"
    }
    if (Test-Path -LiteralPath $absoluteTarget) {
        Remove-Item -LiteralPath $absoluteTarget -Recurse -Force
    }
}

$storeDist = Join-Path $projectRoot 'dist\store'
$packageRoot = Join-Path $projectRoot 'build\store-package'
Remove-WorkspacePath $storeDist
Remove-WorkspacePath $packageRoot

$pyinstallerArguments = @(
    '-m', 'PyInstaller', '--noconfirm', '--clean', '--noconsole', '--onedir',
    '--name', 'WordSpring', '--distpath', $storeDist,
    '--workpath', (Join-Path $projectRoot 'build\store-work'),
    '--specpath', (Join-Path $projectRoot 'build\store-spec'),
    '--icon', (Join-Path $projectRoot 'store\Assets\WordSpring.ico'),
    '--collect-all', 'pyttsx3',
    '--exclude-module', 'edge_tts',
    '--exclude-module', 'PySide6.QtVirtualKeyboard',
    '--hidden-import', 'pyttsx3.drivers.sapi5',
    '--hidden-import', 'pythoncom',
    '--hidden-import', 'pywintypes',
    '--hidden-import', 'win32com.client',
    '--add-data', ((Join-Path $projectRoot 'THIRD_PARTY_NOTICES.md') + ';.'),
    (Join-Path $projectRoot 'main.py')
)
& $python @pyinstallerArguments
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE."
}

$appOutput = Join-Path $storeDist 'WordSpring'
if (-not (Test-Path -LiteralPath (Join-Path $appOutput 'WordSpring.exe') -PathType Leaf)) {
    throw 'The packaged WordSpring executable was not created.'
}

$unneededQtPayload = @(
    (Join-Path $appOutput '_internal\PySide6\Qt6VirtualKeyboard.dll'),
    (Join-Path $appOutput '_internal\PySide6\Qt6VirtualKeyboardQml.dll'),
    (Join-Path $appOutput '_internal\PySide6\Qt6VirtualKeyboardSettings.dll'),
    (Join-Path $appOutput '_internal\PySide6\plugins\platforminputcontexts\qtvirtualkeyboardplugin.dll'),
    (Join-Path $appOutput '_internal\PySide6\qml\QtQuick\VirtualKeyboard'),
    (Join-Path $appOutput '_internal\PySide6\metatypes\qt6virtualkeyboard_metatypes.json'),
    (Join-Path $appOutput '_internal\icuuc.dll'),
    (Join-Path $appOutput '_internal\icuin.dll')
)
foreach ($payloadPath in $unneededQtPayload) {
    Remove-WorkspacePath $payloadPath
}
$icuDataFiles = Get-ChildItem -LiteralPath (Join-Path $appOutput '_internal') -Recurse -File -Filter 'icudt*.dll' -ErrorAction SilentlyContinue
foreach ($payloadFile in $icuDataFiles) {
    Remove-WorkspacePath $payloadFile.FullName
}
$remainingIcuFiles = Get-ChildItem -LiteralPath (Join-Path $appOutput '_internal') -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^(icuuc|icuin|icudt\d*)\.dll$' }
if ($remainingIcuFiles) {
    throw "Unexpected bundled ICU DLL(s) remain: $($remainingIcuFiles.FullName -join ', ')"
}

$makeAppx = Get-ChildItem -Path (Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin') `
    -Filter 'MakeAppx.exe' -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '\\x64\\MakeAppx\.exe$' } |
    Sort-Object FullName -Descending |
    Select-Object -First 1
if (-not $makeAppx) {
    throw 'Windows SDK MakeAppx.exe was not found. Install the Windows 10/11 SDK and retry.'
}

New-Item -ItemType Directory -Path $packageRoot | Out-Null
Copy-Item -Path (Join-Path $appOutput '*') -Destination $packageRoot -Recurse -Force
$assetsTarget = Join-Path $packageRoot 'Assets'
New-Item -ItemType Directory -Path $assetsTarget | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot 'store\Assets\*') -Destination $assetsTarget -Force

$licensesTarget = Join-Path $packageRoot 'Licenses'
New-Item -ItemType Directory -Path $licensesTarget | Out-Null
$sitePackages = Join-Path $projectRoot '.venv\Lib\site-packages'
function Copy-LicenseArtifact([string]$SourcePath, [string]$TargetName) {
    if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
        throw "Required third-party license file was not found: $SourcePath"
    }
    Copy-Item -LiteralPath $SourcePath -Destination (Join-Path $licensesTarget $TargetName) -Force
}

Copy-LicenseArtifact (Join-Path $PSScriptRoot 'store\Licenses\LGPL-3.0.txt') 'LGPL-3.0.txt'
$pyttsx3License = Get-ChildItem -Path (Join-Path $sitePackages 'pyttsx3-*.dist-info\licenses\LICENSE') -File | Select-Object -First 1
$pyinstallerLicense = Get-ChildItem -Path (Join-Path $sitePackages 'pyinstaller-*.dist-info\licenses\COPYING.txt') -File | Select-Object -First 1
$pywin32License = Get-ChildItem -Path (Join-Path $sitePackages 'pywin32-*.dist-info\licenses\win32\License.txt') -File | Select-Object -First 1
$comtypesLicense = Get-ChildItem -Path (Join-Path $sitePackages 'comtypes-*.dist-info\licenses\LICENSE.txt') -File | Select-Object -First 1
$pythonBasePrefix = & $python -c 'import sys; print(sys.base_prefix)'
Copy-LicenseArtifact $pyttsx3License.FullName 'pyttsx3-MPL-2.0.txt'
Copy-LicenseArtifact $pyinstallerLicense.FullName 'PyInstaller-COPYING.txt'
Copy-LicenseArtifact $pywin32License.FullName 'pywin32.txt'
Copy-LicenseArtifact $comtypesLicense.FullName 'comtypes-MIT.txt'
Copy-LicenseArtifact (Join-Path $pythonBasePrefix 'LICENSE.txt') 'Python-3.12.txt'

$templatePath = Join-Path $PSScriptRoot 'store\Package.appxmanifest.template'
$manifestPath = Join-Path $packageRoot 'AppxManifest.xml'
$manifest = Get-Content -LiteralPath $templatePath -Raw -Encoding UTF8
$replacements = @{
    '__IDENTITY_NAME__' = [System.Security.SecurityElement]::Escape($IdentityName)
    '__PUBLISHER__' = [System.Security.SecurityElement]::Escape($Publisher)
    '__PUBLISHER_DISPLAY_NAME__' = [System.Security.SecurityElement]::Escape($PublisherDisplayName)
    '__VERSION__' = $Version
}
foreach ($token in $replacements.Keys) {
    $manifest = $manifest.Replace($token, $replacements[$token])
}
[System.IO.File]::WriteAllText($manifestPath, $manifest, [System.Text.UTF8Encoding]::new($false))

$packagePath = if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    Join-Path $projectRoot "dist\WordSpring-$Version.msix"
} else {
    [IO.Path]::GetFullPath($OutputPath)
}
$projectPrefix = $projectRoot.TrimEnd('\') + '\'
if (-not $packagePath.StartsWith($projectPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "The output path must be inside the project folder: $packagePath"
}
New-Item -ItemType Directory -Path (Split-Path -Parent $packagePath) -Force | Out-Null
if (Test-Path -LiteralPath $packagePath -PathType Leaf) {
    Remove-Item -LiteralPath $packagePath -Force
}
& $makeAppx.FullName pack /d $packageRoot /p $packagePath /o
if ($LASTEXITCODE -ne 0) {
    throw "MakeAppx failed with exit code $LASTEXITCODE."
}
$verifyRoot = Join-Path $projectRoot 'build\store-verify'
Remove-WorkspacePath $verifyRoot
New-Item -ItemType Directory -Path $verifyRoot | Out-Null
& $makeAppx.FullName unpack /p $packagePath /d $verifyRoot /o
if ($LASTEXITCODE -ne 0) {
    throw "MakeAppx unpack validation failed with exit code $LASTEXITCODE."
}
if (-not (Test-Path -LiteralPath (Join-Path $verifyRoot 'AppxManifest.xml') -PathType Leaf)) {
    throw 'MakeAppx unpack validation did not produce AppxManifest.xml.'
}

if ($RunAppCertKit) {
    $appCert = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\App Certification Kit\appcert.exe'
    if (-not (Test-Path -LiteralPath $appCert -PathType Leaf)) {
        throw 'Windows App Certification Kit was not found.'
    }
    $reportPath = Join-Path $projectRoot 'build\WordSpring-appcert.xml'
    & $appCert reset
    & $appCert test -appxpackagepath $packagePath -reportoutputpath $reportPath
    if ($LASTEXITCODE -ne 0) {
        throw "Windows App Certification Kit returned exit code $LASTEXITCODE. Review $reportPath."
    }
}

Write-Host "Created and unpack-validated Store package: $packagePath"
Write-Host 'The Store will sign the package after certification; do not replace the reserved Partner Center identity.'
