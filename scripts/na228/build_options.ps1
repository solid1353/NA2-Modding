Set-StrictMode -Version Latest

function Get-Na2BuildOptions {
    [CmdletBinding()]
    param([Parameter(Mandatory)][object[]]$Tokens)

    $remaining = [Collections.Generic.List[string]]::new()
    $postfix = $null
    $overridesJson = $null
    for ($index = 0; $index -lt $Tokens.Count; $index++) {
        $token = [string]$Tokens[$index]
        if ($token -ieq '-postfix' -or $token -ieq '-overrides') {
            if ($index + 1 -ge $Tokens.Count) {
                throw "$token requires a value."
            }
            $index++
            $value = $Tokens[$index]
            if ($token -ieq '-postfix') {
                if ($null -ne $postfix) { throw '-postfix may be specified only once.' }
                if ($value -isnot [string]) { throw '-postfix requires text.' }
                $postfix = [string]$value
                if (-not $postfix -or $postfix -ne $postfix.Trim(' ', '.') -or
                    $postfix.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0) {
                    throw 'Invalid ISO filename postfix.'
                }
            }
            else {
                if ($null -ne $overridesJson) { throw '-overrides may be specified only once.' }
                if ($value -isnot [Collections.IDictionary]) {
                    throw '-overrides requires a PowerShell hashtable.'
                }
                $overridesJson = ConvertTo-Json -InputObject $value -Depth 100 -Compress
            }
            continue
        }
        $remaining.Add($token)
    }
    return [pscustomobject]@{
        Tokens = [string[]]$remaining.ToArray()
        Postfix = $postfix
        OverridesJson = $overridesJson
    }
}
