function Get-VisualRegressionResumeKey {
    param(
        [Parameter(Mandatory)][Collections.Specialized.OrderedDictionary]$Request,
        [Parameter(Mandatory)][object[]]$SuiteRequest,
        [AllowEmptyCollection()][object[]]$OrdinaryInput = @()
    )

    $state = Get-VisualRegressionRepositoryState
    $generatedRequests = @($SuiteRequest | Where-Object Generated)
    $inputIdentity = @(
        $OrdinaryInput
        if ($generatedRequests.Count -gt 0) {
            $generatedInputs = @(
                Join-Path ([string]$state.Paths.resources) 'character_data.tsv'
                [string]$state.Paths.files.practice_movesets
                foreach ($generatedRequest in $generatedRequests) {
                    Get-VisualRegressionGeneratedInputPaths `
                        -RecordingRepository $state.RecordingRepository `
                        -Suite $generatedRequest.Suite
                }
            ) | Sort-Object -Unique
            foreach ($path in $generatedInputs) {
                [ordered]@{
                    path = [IO.Path]::GetRelativePath($state.Repository, $path).Replace('\', '/')
                    sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
                }
            }
        }
    )
    $Request['suite_requests'] = [object[]]@(
        $SuiteRequest |
            Sort-Object Suite |
            ForEach-Object {
                [ordered]@{
                    suite = [string]$_.Suite
                    arguments = [string[]]@($_.Arguments)
                }
            }
    )
    $Request['inputs'] = [object[]]@($inputIdentity | Sort-Object path)
    return $Request | ConvertTo-Json -Compress -Depth 6
}

function Test-VisualRegressionTransactionOwnerLive {
    param([Parameter(Mandatory)][string]$Transaction)

    $ownerPath = Join-Path $Transaction 'owner.json'
    if (-not (Test-Path -LiteralPath $ownerPath -PathType Leaf)) {
        return $false
    }
    try {
        $owner = Get-Content -Raw -LiteralPath $ownerPath | ConvertFrom-Json
        $ownerProcess = [Diagnostics.Process]::GetProcessById([int]$owner.pid)
        return (
            $ownerProcess.StartTime.ToFileTimeUtc() -eq
            [long]$owner.process_start_file_time_utc
        )
    }
    catch { return $false }
}

function Set-VisualRegressionTransactionOwner {
    param([Parameter(Mandatory)][string]$Transaction)

    Write-VisualRegressionJson -Path (Join-Path $Transaction 'owner.json') -Value ([ordered]@{
        pid = $PID
        process_start_file_time_utc = (Get-Process -Id $PID).StartTime.ToFileTimeUtc()
        created_utc = (Get-Date).ToUniversalTime().ToString('O')
    })
}

function Set-VisualRegressionTransactionRequest {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Prefix,
        [Parameter(Mandatory)][string]$ResumeKey,
        [Parameter(Mandatory)][int]$ResumeCount,
        [string]$CreatedUtc
    )

    if ([string]::IsNullOrWhiteSpace($CreatedUtc)) {
        $CreatedUtc = (Get-Date).ToUniversalTime().ToString('O')
    }
    Write-VisualRegressionJson -Path (Join-Path $Transaction 'request.json') -Value ([ordered]@{
        prefix = $Prefix
        resume_key = $ResumeKey
        resume_count = $ResumeCount
        created_utc = $CreatedUtc
        resumed_utc = if ($ResumeCount -gt 0) {
            (Get-Date).ToUniversalTime().ToString('O')
        }
        else { $null }
    })
}

function Test-VisualRegressionTransactionResumed {
    param([Parameter(Mandatory)][string]$Transaction)

    $requestPath = Join-Path $Transaction 'request.json'
    if (-not (Test-Path -LiteralPath $requestPath -PathType Leaf)) {
        return $false
    }
    $request = Get-Content -Raw -LiteralPath $requestPath | ConvertFrom-Json
    return [int]$request.resume_count -gt 0
}

function Move-VisualRegressionTransactionItemsToAttempt {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string[]]$RelativePath,
        [string]$Label = 'resume'
    )

    $transactionRoot = [IO.Path]::GetFullPath($Transaction).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    foreach ($relative in $RelativePath) {
        if ([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\\/])\.\.([\\/]|$)') {
            throw "Attempt artifact path must remain relative: $relative"
        }
        if (-not (Test-VisualRegressionPathWithin `
            -Path (Join-Path $transactionRoot $relative) `
            -Root $transactionRoot)) {
            throw "Attempt artifact path escapes its transaction: $relative"
        }
    }
    $existing = @(
        $RelativePath | Where-Object {
            Test-Path -LiteralPath (Join-Path $transactionRoot $_)
        }
    )
    if ($existing.Count -eq 0) {
        return $null
    }
    $attempt = Join-Path `
        (Join-Path $transactionRoot '.attempts') `
        ("$Label-$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfff'))-" +
            [guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $attempt -Force)
    foreach ($relative in $existing) {
        $source = Join-Path $transactionRoot $relative
        $destination = Join-Path $attempt $relative
        [void](New-Item `
            -ItemType Directory `
            -Path ([IO.Path]::GetDirectoryName($destination)) `
            -Force)
        if (Test-Path -LiteralPath $source -PathType Container) {
            [IO.Directory]::Move($source, $destination)
        }
        else {
            [IO.File]::Move($source, $destination)
        }
    }
    return $attempt
}

function New-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Prefix,
        [string]$ResumeKey
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    [void](New-Item -ItemType Directory -Path $transactions -Force)
    if (-not [string]::IsNullOrWhiteSpace($ResumeKey)) {
        $candidates = @(
            Get-ChildItem -LiteralPath $transactions -Directory -Force |
                Where-Object {
                    $_.Name.StartsWith("$Prefix-", [StringComparison]::Ordinal)
                } |
                Sort-Object LastWriteTimeUtc -Descending
        )
        foreach ($candidate in $candidates) {
            $retainedPath = Join-Path $candidate.FullName 'retained.json'
            $isRetained = Test-Path -LiteralPath $retainedPath -PathType Leaf
            if (-not $isRetained -and
                (Test-VisualRegressionTransactionOwnerLive -Transaction $candidate.FullName)) {
                continue
            }
            $claim = $null
            try {
                $claim = [IO.FileStream]::new(
                    (Join-Path $candidate.FullName '.resume-claim'),
                    [IO.FileMode]::CreateNew,
                    [IO.FileAccess]::ReadWrite,
                    [IO.FileShare]::None,
                    1,
                    [IO.FileOptions]::DeleteOnClose
                )
            }
            catch [IO.IOException] {
                continue
            }
            try {
                $isRetained = Test-Path -LiteralPath $retainedPath -PathType Leaf
                if (-not $isRetained -and
                    (Test-VisualRegressionTransactionOwnerLive -Transaction $candidate.FullName)) {
                    continue
                }
                $requestPath = Join-Path $candidate.FullName 'request.json'
                if (-not (Test-Path -LiteralPath $requestPath -PathType Leaf)) {
                    continue
                }
                try {
                    $request = Get-Content -Raw -LiteralPath $requestPath |
                        ConvertFrom-Json
                }
                catch {
                    continue
                }
                if ([string]$request.resume_key -cne $ResumeKey) {
                    continue
                }
                $resumeCount = [int]$request.resume_count + 1
                $createdUtc = [string]$request.created_utc
                Set-VisualRegressionTransactionOwner -Transaction $candidate.FullName
                Set-VisualRegressionTransactionRequest `
                    -Transaction $candidate.FullName `
                    -Prefix $Prefix `
                    -ResumeKey $ResumeKey `
                    -ResumeCount $resumeCount `
                    -CreatedUtc $createdUtc
                if ($isRetained) {
                    Remove-Item -LiteralPath $retainedPath -Force
                }
                Write-Host (
                    "Continuing failed E2E transaction: $($candidate.FullName)"
                ) -ForegroundColor Cyan
                return $candidate.FullName
            }
            finally {
                $claim.Dispose()
            }
        }
    }
    $transaction = Join-Path $transactions (
        $Prefix + '-' + [guid]::NewGuid().ToString('N')
    )
    [void](New-Item -ItemType Directory -Path $transaction)
    Set-VisualRegressionTransactionOwner -Transaction $transaction
    if (-not [string]::IsNullOrWhiteSpace($ResumeKey)) {
        Set-VisualRegressionTransactionRequest `
            -Transaction $transaction `
            -Prefix $Prefix `
            -ResumeKey $ResumeKey `
            -ResumeCount 0
    }
    return $transaction
}

function Set-VisualRegressionTransactionRetained {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Root
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    if (-not (Test-VisualRegressionPathWithin -Path $Transaction -Root $transactions)) {
        throw "Refusing to mark a transaction outside $transactions"
    }
    $resolvedTransaction = [IO.Path]::GetFullPath($Transaction)
    if (-not (Test-Path -LiteralPath $resolvedTransaction -PathType Container)) {
        throw "Transaction does not exist: $resolvedTransaction"
    }
    Write-VisualRegressionJson `
        -Path (Join-Path $resolvedTransaction 'retained.json') `
        -Value ([ordered]@{
            status = 'failed'
            completed_utc = (Get-Date).ToUniversalTime().ToString('O')
        })
}

function Remove-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Root
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    if (-not (Test-VisualRegressionPathWithin -Path $Transaction -Root $transactions)) {
        throw "Refusing to remove a transaction outside $transactions"
    }
    $resolvedTransaction = [IO.Path]::GetFullPath($Transaction)
    if (Test-Path -LiteralPath $resolvedTransaction) {
        Remove-Item -LiteralPath $resolvedTransaction -Recurse -Force
    }
    if ((Test-Path -LiteralPath $transactions -PathType Container) -and
        @(Get-ChildItem -LiteralPath $transactions -Force).Count -eq 0) {
        Remove-Item -LiteralPath $transactions -Force
    }
}

function Complete-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][bool]$Succeeded,
        [Parameter(Mandatory)][string]$Command
    )

    if ($Succeeded) {
        Remove-VisualRegressionTransaction -Transaction $Transaction -Root $Root
        return
    }
    try {
        Set-VisualRegressionTransactionRetained -Transaction $Transaction -Root $Root
    }
    catch {
        Write-Warning "Failed to mark the retained $Command transaction inactive: $($_.Exception.Message)"
    }
    Write-Warning "Failed $Command transaction retained for continuation: $Transaction"
    Write-Warning "Rerun the same $($Command.ToLowerInvariant()) command to continue completed suites."
}

function Publish-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][Collections.IDictionary]$Replacements,
        [Parameter(Mandatory)][string]$TransactionRoot,
        [scriptblock]$AfterPublish
    )

    function Clear-PublishedFiles {
        param([Parameter(Mandatory)][string]$Root)

        if (Test-Path -LiteralPath $Root -PathType Container) {
            foreach ($file in Get-ChildItem -LiteralPath $Root -Recurse -File -Force) {
                $path = $file.FullName
                Invoke-VisualRegressionFileOperation `
                    -Description "Removing published file '$path'" `
                    -Operation {
                        Remove-Item -LiteralPath $path -Force -ErrorAction Stop
                    }.GetNewClosure()
            }
        }
    }

    function Copy-PublishedFiles {
        param(
            [Parameter(Mandatory)][string]$Source,
            [Parameter(Mandatory)][string]$Destination
        )

        [void](New-Item -ItemType Directory -Path $Destination -Force)
        foreach ($file in Get-ChildItem -LiteralPath $Source -Recurse -File -Force) {
            $relative = [IO.Path]::GetRelativePath($Source, $file.FullName)
            $target = Join-Path $Destination $relative
            [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force)
            $temporary = "$target.publishing-$([guid]::NewGuid().ToString('N'))"
            try {
                $sourcePath = $file.FullName
                Invoke-VisualRegressionFileOperation `
                    -Description "Copying staged file '$sourcePath'" `
                    -Operation {
                        [IO.File]::Copy($sourcePath, $temporary, $true)
                    }.GetNewClosure()
                Invoke-VisualRegressionFileOperation `
                    -Description "Publishing file '$target'" `
                    -Operation {
                        [IO.File]::Move($temporary, $target, $true)
                    }.GetNewClosure()
            }
            finally {
                if (Test-Path -LiteralPath $temporary -PathType Leaf) {
                    Invoke-VisualRegressionFileOperation `
                        -Description "Removing temporary publication file '$temporary'" `
                        -Operation {
                            Remove-Item -LiteralPath $temporary -Force -ErrorAction Stop
                        }.GetNewClosure()
                }
            }
        }
    }

    function Link-PublishedFiles {
        param(
            [Parameter(Mandatory)][string]$Source,
            [Parameter(Mandatory)][string]$Destination
        )

        [void](New-Item -ItemType Directory -Path $Destination -Force)
        foreach ($file in Get-ChildItem -LiteralPath $Source -Recurse -File -Force) {
            $relative = [IO.Path]::GetRelativePath($Source, $file.FullName)
            $target = Join-Path $Destination $relative
            [void](New-Item `
                -ItemType Directory `
                -Path ([IO.Path]::GetDirectoryName($target)) `
                -Force)
            $linkPath = ConvertTo-VisualRegressionLongPath -Path $target
            $sourcePath = ConvertTo-VisualRegressionLongPath -Path $file.FullName
            Invoke-VisualRegressionFileOperation `
                -Description "Hardlinking staged file '$($file.FullName)'" `
                -Operation {
                    [void](New-Item `
                        -ItemType HardLink `
                        -Path $linkPath `
                        -Target $sourcePath `
                        -ErrorAction Stop)
                }.GetNewClosure()
        }
    }

    function Sync-PublishedFiles {
        param(
            [Parameter(Mandatory)][string]$Source,
            [Parameter(Mandatory)][string]$Destination
        )

        Copy-PublishedFiles -Source $Source -Destination $Destination
        $relativePaths = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($file in Get-ChildItem -LiteralPath $Source -Recurse -File -Force) {
            [void]$relativePaths.Add([IO.Path]::GetRelativePath($Source, $file.FullName))
        }
        foreach ($file in @(Get-ChildItem -LiteralPath $Destination -Recurse -File -Force)) {
            $relative = [IO.Path]::GetRelativePath($Destination, $file.FullName)
            if (-not $relativePaths.Contains($relative)) {
                $path = $file.FullName
                Invoke-VisualRegressionFileOperation `
                    -Description "Removing stale published file '$path'" `
                    -Operation {
                        Remove-Item -LiteralPath $path -Force -ErrorAction Stop
                    }.GetNewClosure()
            }
        }
    }

    function Remove-EmptyPublishedDirectories {
        param([Parameter(Mandatory)][string]$Root)

        if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return }
        foreach ($directory in @(
            Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force |
                Sort-Object { $_.FullName.Length } -Descending
        )) {
            if (@(Get-ChildItem -LiteralPath $directory.FullName -Force).Count -ne 0) {
                continue
            }
            try {
                [IO.Directory]::Delete($directory.FullName)
            }
            catch [IO.IOException] {}
            catch [UnauthorizedAccessException] {}
        }
    }

    $published = [Collections.Generic.List[object]]::new()
    $backupRoot = Join-Path `
        (Join-Path $TransactionRoot '.backups') `
        ('publish-' + [guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $backupRoot -Force)
    $backupIndex = 0
    try {
        foreach ($destination in $Replacements.Keys) {
            $source = $Replacements[$destination]
            $backup = Join-Path $backupRoot ('{0:D4}' -f $backupIndex)
            $backupIndex++
            if ($script:E2eStableCaptureDirectories -ccontains
                [IO.Path]::GetFileName($destination)) {
                if (Test-Path -LiteralPath $destination -PathType Container) {
                    Copy-PublishedFiles -Source $destination -Destination $backup
                }
                try {
                    Sync-PublishedFiles -Source $source -Destination $destination
                    Remove-EmptyPublishedDirectories -Root $destination
                    $published.Add([pscustomobject]@{
                        Destination = $destination
                        Backup = $backup
                        Stable = $true
                    })
                }
                catch {
                    Clear-PublishedFiles -Root $destination
                    if (Test-Path -LiteralPath $backup -PathType Container) {
                        Copy-PublishedFiles -Source $backup -Destination $destination
                    }
                    throw
                }
                continue
            }
            if (-not (Test-Path -LiteralPath $source -PathType Container)) {
                throw "Staged publication directory does not exist: $source"
            }
            $destinationParent = [IO.Path]::GetDirectoryName($destination)
            [void](New-Item -ItemType Directory -Path $destinationParent -Force)
            if (Test-Path -LiteralPath $destination) {
                [IO.Directory]::Move($destination, $backup)
            }
            $temporaryDestination = Join-Path `
                $destinationParent `
                ('.' + [IO.Path]::GetFileName($destination) +
                    '.publishing-' + [guid]::NewGuid().ToString('N'))
            try {
                Link-PublishedFiles `
                    -Source $source `
                    -Destination $temporaryDestination
                [IO.Directory]::Move($temporaryDestination, $destination)
                $published.Add([pscustomobject]@{
                    Destination = $destination
                    Backup = $backup
                    Stable = $false
                })
            }
            catch {
                if (Test-Path -LiteralPath $temporaryDestination) {
                    Remove-Item -LiteralPath $temporaryDestination -Recurse -Force
                }
                if (Test-Path -LiteralPath $backup) {
                    [IO.Directory]::Move($backup, $destination)
                }
                throw
            }
        }
        if ($null -ne $AfterPublish) {
            & $AfterPublish
        }
    }
    catch {
        for ($index = $published.Count - 1; $index -ge 0; $index--) {
            $item = $published[$index]
            if ($item.Stable) {
                Clear-PublishedFiles -Root $item.Destination
                if (Test-Path -LiteralPath $item.Backup -PathType Container) {
                    Copy-PublishedFiles -Source $item.Backup -Destination $item.Destination
                }
                Remove-EmptyPublishedDirectories -Root $item.Destination
                continue
            }
            if (Test-Path -LiteralPath $item.Destination) {
                Remove-Item -LiteralPath $item.Destination -Recurse -Force
            }
            if (Test-Path -LiteralPath $item.Backup) {
                [IO.Directory]::Move($item.Backup, $item.Destination)
            }
        }
        throw
    }
    foreach ($item in $published) {
        if (Test-Path -LiteralPath $item.Backup) {
            Remove-Item -LiteralPath $item.Backup -Recurse -Force
        }
    }
    if (Test-Path -LiteralPath $backupRoot) {
        Remove-Item -LiteralPath $backupRoot -Recurse -Force
    }
}
