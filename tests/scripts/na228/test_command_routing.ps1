[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$workshopRepository = [IO.Path]::GetFullPath((
    Join-Path $sourceRepository '..\UN Workshop'
))
$testRoot = Join-Path $env:TEMP ('na228-command-routing-' + [Guid]::NewGuid().ToString('N'))
$repository = Join-Path $testRoot 'repository'
$powershell = if ([string]::IsNullOrWhiteSpace($env:NA228_TEST_POWERSHELL)) {
    (Get-Process -Id $PID).Path
}
else { $env:NA228_TEST_POWERSHELL }

function Assert-CommandRouting {
    param([Parameter(Mandatory)][bool]$Condition, [Parameter(Mandatory)][string]$Message)
    if (-not $Condition) { throw $Message }
}

function Invoke-FakeNa228 {
    param([string[]]$ArgumentList, [switch]$Failure)

    foreach ($name in 'build.json', 'launch.json', 'watch.json', 'tests.txt') {
        $path = Join-Path $repository $name
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
    }
    $output = @(& $powershell -NoProfile -File (Join-Path $repository 'na228.ps1') @ArgumentList 2>&1)
    $exitCode = $LASTEXITCODE
    if ($Failure) {
        Assert-CommandRouting ($exitCode -ne 0) "Command unexpectedly succeeded: $ArgumentList"
    }
    else {
        Assert-CommandRouting ($exitCode -eq 0) "Command failed: $ArgumentList`n$($output -join "`n")"
    }
    return [pscustomobject]@{ Output = [string[]]$output; ExitCode = $exitCode }
}

try {
    foreach ($directory in @(
        'build', 'logs', 'recordings', 'scripts\lib', 'scripts\na228',
        'scripts\injection', 'tests', 'workshop\scripts\lib',
        'workshop\scripts\pcsx2',
        'na228_builder\configurations'
    )) {
        [void](New-Item -ItemType Directory -Path (Join-Path $repository $directory) -Force)
    }
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'na228.ps1') -Destination $repository
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'CLI.txt') -Destination $repository
    Copy-Item `
        -LiteralPath (Join-Path $workshopRepository 'scripts\lib\console_help.ps1') `
        -Destination (Join-Path $repository 'workshop\scripts\lib\console_help.ps1')
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\na228\build_configurations.ps1') `
        -Destination (Join-Path $repository 'scripts\na228\build_configurations.ps1')

    [IO.File]::WriteAllText((Join-Path $repository 'game.json'), @'
{
  "title": "Synthetic",
  "serial": "TEST",
  "output_boot_path": "TEST",
  "launch_settings": {
    "default": {
      "startup_fast_forward_frames": 120,
      "speed_after_startup": "turbo"
    },
    "practice": {
      "startup_fast_forward_frames": 180,
      "speed_after_startup": "normal"
    }
  },
  "configurations": { "base": "b", "test": "t", "release": "r", "e2e": "e" }
}
'@)
    foreach ($configuration in 'base', 'test', 'release', 'e2e', 'foo') {
        [IO.File]::WriteAllText(
            (Join-Path $repository "na228_builder\configurations\$configuration.jsonc"),
            '{}'
        )
        [IO.File]::WriteAllText((Join-Path $repository "build\$configuration.iso"), $configuration)
    }

    [IO.File]::WriteAllText((Join-Path $repository 'scripts\lib\paths.ps1'), @'
function Get-Na2Paths {
    $repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
    [pscustomobject]@{
        repository = $repository
        scripts = Join-Path $repository 'scripts'
        builder = Join-Path $repository 'na228_builder'
        build = Join-Path $repository 'build'
        logs = Join-Path $repository 'logs'
        work = Join-Path $repository 'work'
        workshop = Join-Path $repository 'workshop'
        pcsx2_scripts = Join-Path $repository 'workshop\scripts\pcsx2'
        pcsx2_input_recordings = Join-Path $repository 'recordings'
        settings = Get-Content -Raw -LiteralPath (Join-Path $repository 'game.json') | ConvertFrom-Json
        games = [pscustomobject]@{
            Names = @('NA2')
            Aliases = [pscustomobject]@{ NA2 = 'NA2' }
            Entries = [pscustomobject]@{}
        }
        files = [pscustomobject]@{
            pcsx2_game_launch_command = Join-Path $repository 'fake_launch.ps1'
            publish_release_command = Join-Path $repository 'fake_release.ps1'
        }
    }
}
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\na228\task_paths.ps1'), @'
function Get-Na2TaskContext { throw 'Task context was not expected.' }
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\na228\launch_settings.ps1'), @'
function Get-Na2LaunchSettings {
    param([string]$Configuration, [psobject]$Paths, [string]$LaunchProfile)
    if ($LaunchProfile -ceq 'practice') {
        return [pscustomobject]@{
            StartupFastForwardFrames = [UInt64]180
            SpeedAfterStartup = 'normal'
        }
    }
    [pscustomobject]@{
        StartupFastForwardFrames = [UInt64]120
        SpeedAfterStartup = 'turbo'
    }
}
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\na228\launch_profile.ps1'), @'
function Resolve-Na2LaunchProfile {
    param([string]$Name, [psobject]$Paths)
    [pscustomobject]@{ Name = $Name }
}
function Invoke-Na2LaunchProfile {}
function Merge-Na2LaunchProfileParameters { throw 'No profile result was expected.' }
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\na228\build_registry.ps1'), @'
function Resolve-Na2CachedBuild {
    param([string]$Configuration, [psobject]$Paths)
    [pscustomobject]@{ image = Join-Path $Paths.build "$Configuration.iso" }
}
'@)
[IO.File]::WriteAllText((Join-Path $repository 'workshop\scripts\pcsx2\launch_arguments.ps1'), @'
function Test-UnWorkshopLaunchOption {
    param([string]$Token)
    return $false
}
function ConvertFrom-UnWorkshopLaunchArguments {
    param([string[]]$Tokens, [switch]$OptionsOnly)
    [pscustomobject]@{ LaunchParameters = @{} }
}
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\na228\run.ps1'), @'
param([string]$Action, [string]$Configuration, [string]$LogDirectory)
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$image = Join-Path $repository "build\$Configuration.iso"
[IO.File]::WriteAllText($image, "built-$Configuration")
[IO.File]::WriteAllText(
    (Join-Path $repository 'build.json'),
    ([ordered]@{ action = $Action; configuration = $Configuration } | ConvertTo-Json -Compress)
)
[pscustomobject]@{ OutputIso = $image }
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'fake_launch.ps1'), @'
param(
    [string[]]$Games,
    [string]$ProjectRoot,
    [string]$InputRecordingsRoot,
    [UInt64]$UnlimitedForFrames,
    [switch]$Turbo,
    [switch]$Unlimited
)
[IO.File]::WriteAllText(
    (Join-Path $ProjectRoot 'launch.json'),
    ([ordered]@{
        games = $Games
        frames = $UnlimitedForFrames
        turbo = $Turbo.IsPresent
        unlimited = $Unlimited.IsPresent
    } | ConvertTo-Json -Compress)
)
foreach ($game in $Games) { [pscustomobject]@{ Game = $game; PinePort = 28011 } }
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\injection\watch.ps1'), @'
param([string]$SourcePath, [string]$OverlayPlan, [int]$PinePort)
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
[IO.File]::WriteAllText(
    (Join-Path $repository 'watch.json'),
    ([ordered]@{ source = $SourcePath; plan = $OverlayPlan; port = $PinePort } | ConvertTo-Json -Compress)
)
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'tests\run.ps1'), @'
[IO.File]::WriteAllText((Join-Path $PSScriptRoot '..\tests.txt'), 'ran')
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'fake_release.ps1'), "throw 'Release was not expected.'")

    $originalTaskRoot = $env:NA228_TASK_WORK_ROOT
    Remove-Item Env:NA228_TASK_WORK_ROOT -ErrorAction SilentlyContinue
    try {
        $help = Invoke-FakeNa228 -ArgumentList @('help')
        $helpText = $help.Output -join "`n"
        Assert-CommandRouting ($helpText -match 'token: <source>\[w\] \| \[b\]<config>\[w\]') `
            'Help omitted the accepted token grammar.'
        Assert-CommandRouting ($helpText -match 'b=base, t=test, r=release, e=e2e, foo') `
            'Help did not list discovered configurations and aliases.'
        Assert-CommandRouting ($helpText -match 'profiles: practice') `
            'Help did not list configured launch profiles.'

        $null = Invoke-FakeNa228 -ArgumentList @('build', 'b')
        $build = Get-Content -Raw -LiteralPath (Join-Path $repository 'build.json') | ConvertFrom-Json
        Assert-CommandRouting ($build.configuration -ceq 'base') 'Build alias did not resolve to base.'
        Assert-CommandRouting (-not (Test-Path -LiteralPath (Join-Path $repository 'launch.json'))) `
            'Build-only command launched a game.'

        $null = Invoke-FakeNa228 -ArgumentList @('build', 'foo')
        $build = Get-Content -Raw -LiteralPath (Join-Path $repository 'build.json') | ConvertFrom-Json
        Assert-CommandRouting ($build.configuration -ceq 'foo') `
            'Alias-free configuration name did not build.'
        $rejected = Invoke-FakeNa228 -ArgumentList @('build', 'base') -Failure
        Assert-CommandRouting (($rejected.Output -join "`n") -match 'Unknown build configuration: base') `
            'Aliased configuration was accepted by its full name.'

        $null = Invoke-FakeNa228 -ArgumentList @('b')
        $launch = Get-Content -Raw -LiteralPath (Join-Path $repository 'launch.json') | ConvertFrom-Json
        Assert-CommandRouting (
            $launch.games[0] -like '*\build\base.iso' -and
            $launch.frames -eq 120 -and
            $launch.turbo
        ) 'Configuration alias did not launch with its configured Turbo fallback.'

        $null = Invoke-FakeNa228 -ArgumentList @('b', '-l', 'practice')
        $launch = Get-Content -Raw -LiteralPath (Join-Path $repository 'launch.json') | ConvertFrom-Json
        Assert-CommandRouting (
            $launch.frames -eq 180 -and
            -not $launch.turbo
        ) 'Practice profile did not retain Normal after timed Unlimited.'

        $null = Invoke-FakeNa228 -ArgumentList @('b', '-l', 'practice', '-t')
        $launch = Get-Content -Raw -LiteralPath (Join-Path $repository 'launch.json') | ConvertFrom-Json
        Assert-CommandRouting ($launch.turbo) `
            'Explicit Turbo did not override the practice profile fallback.'

        $null = Invoke-FakeNa228 -ArgumentList @('bb')
        $build = Get-Content -Raw -LiteralPath (Join-Path $repository 'build.json') | ConvertFrom-Json
        Assert-CommandRouting ($build.configuration -ceq 'base') `
            'Build-and-launch alias did not build base.'

        $null = Invoke-FakeNa228 -ArgumentList @('foo')
        $launch = Get-Content -Raw -LiteralPath (Join-Path $repository 'launch.json') | ConvertFrom-Json
        Assert-CommandRouting ($launch.games[0] -like '*\build\foo.iso') `
            'Alias-free configuration did not launch.'

        $null = Invoke-FakeNa228 -ArgumentList @('bew', 'src\candidate.c')
        $build = Get-Content -Raw -LiteralPath (Join-Path $repository 'build.json') | ConvertFrom-Json
        $watch = Get-Content -Raw -LiteralPath (Join-Path $repository 'watch.json') | ConvertFrom-Json
        Assert-CommandRouting (
            $build.configuration -ceq 'e2e' -and
            $watch.source -ceq 'src\candidate.c' -and
            $watch.port -eq 28011
        ) 'Combined build/watch selector did not route configuration, target, and PINE port.'

        $null = Invoke-FakeNa228 -ArgumentList @('b', 'foo', '-t')
        $launch = Get-Content -Raw -LiteralPath (Join-Path $repository 'launch.json') | ConvertFrom-Json
        Assert-CommandRouting (
            $launch.games.Count -eq 2 -and
            $launch.turbo -and
            $launch.frames -eq 120
        ) 'Two-game configuration launch did not preserve turbo startup routing.'

        $null = Invoke-FakeNa228 -ArgumentList @('test')
        Assert-CommandRouting (Test-Path -LiteralPath (Join-Path $repository 'tests.txt')) `
            'Unit-test command did not retain precedence over the test configuration name.'

        [IO.File]::WriteAllText(
            (Join-Path $repository 'na228_builder\configurations\bfoo.jsonc'),
            '{}'
        )
        $conflict = Invoke-FakeNa228 -ArgumentList @('help') -Failure
        Assert-CommandRouting (($conflict.Output -join "`n") -match 'Conflicting build configuration selectors') `
            'Ambiguous derived selector was not rejected.'
    }
    finally {
        if ($null -eq $originalTaskRoot) {
            Remove-Item Env:NA228_TASK_WORK_ROOT -ErrorAction SilentlyContinue
        }
        else { $env:NA228_TASK_WORK_ROOT = $originalTaskRoot }
    }

    Write-Host 'NA228 command-routing tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
