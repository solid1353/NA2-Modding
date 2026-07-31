Set-StrictMode -Version Latest

function Get-Na228WatchTargetArguments {
    [CmdletBinding()]
    param(
        [string]$Target,
        [Parameter(Mandatory)]
        [psobject]$ProjectPaths
    )

    if (
        -not [string]::IsNullOrWhiteSpace($Target) -and
        (
            $Target.EndsWith('.json', [StringComparison]::OrdinalIgnoreCase) -or
            $Target.Contains([IO.Path]::DirectorySeparatorChar) -or
            $Target.Contains([IO.Path]::AltDirectorySeparatorChar)
        )
    ) {
        return @{ OverlayPlan = $Target }
    }

    $catalogPath = [string]$ProjectPaths.files.watch_catalog
    $catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json
    if ([int]$catalog.schema_version -ne 1) {
        throw "Unsupported watch-target catalog schema: $($catalog.schema_version)"
    }
    $targetsProperty = $catalog.PSObject.Properties['targets']
    if ($null -eq $targetsProperty) {
        throw 'Watch-target catalog has no targets object.'
    }

    $name = if ([string]::IsNullOrWhiteSpace($Target)) {
        $defaultProperty = $catalog.PSObject.Properties['default_target']
        if (
            $null -eq $defaultProperty -or
            [string]::IsNullOrWhiteSpace([string]$defaultProperty.Value)
        ) {
            throw 'Watch-target catalog has no default_target.'
        }
        ([string]$defaultProperty.Value).ToLowerInvariant()
    }
    else {
        $Target.ToLowerInvariant()
    }
    $targetProperty = $targetsProperty.Value.PSObject.Properties[$name]
    if ($null -eq $targetProperty) {
        $available = @($targetsProperty.Value.PSObject.Properties.Name)
        throw (
            "Unknown watch target '$Target'. Available targets: " +
            "$($available -join ', '). A task-owned overlay-plan path is also valid."
        )
    }

    $definition = $targetProperty.Value
    $allowed = @(
        'source_id',
        'entry',
        'source_path',
        'overlay_plan',
        'whole_source'
    )
    $extra = @(
        $definition.PSObject.Properties.Name |
            Where-Object { $_ -notin $allowed }
    )
    if ($extra.Count -gt 0) {
        throw "Watch target '$name' has unknown fields: $($extra -join ', ')."
    }

    $arguments = [ordered]@{}
    foreach ($mapping in @(
        @('source_id', 'SourceId'),
        @('entry', 'Entry'),
        @('source_path', 'SourcePath'),
        @('overlay_plan', 'OverlayPlan')
    )) {
        $property = $definition.PSObject.Properties[$mapping[0]]
        if ($null -ne $property) {
            $value = [string]$property.Value
            if ([string]::IsNullOrWhiteSpace($value)) {
                throw "Watch target '$name' has an empty $($mapping[0])."
            }
            $arguments[$mapping[1]] = $value
        }
    }
    $wholeSourceProperty = $definition.PSObject.Properties['whole_source']
    if ($null -ne $wholeSourceProperty) {
        if ($wholeSourceProperty.Value -isnot [bool]) {
            throw "Watch target '$name' has a non-boolean whole_source."
        }
        if ([bool]$wholeSourceProperty.Value) {
            $arguments['WholeSource'] = $true
        }
    }
    if (
        -not $arguments.Contains('OverlayPlan') -and
        (
            -not $arguments.Contains('SourceId') -or
            -not $arguments.Contains('Entry')
        )
    ) {
        throw (
            "Watch target '$name' must declare overlay_plan or both source_id " +
            'and entry.'
        )
    }
    return $arguments
}
