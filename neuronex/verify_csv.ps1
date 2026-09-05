$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$csvFiles = Get-ChildItem "$scriptDir\backend\data\synthetic\*.csv"
$errorCount = 0

foreach ($f in $csvFiles) {
    $rows = Import-Csv $f.FullName
    Write-Host "$($f.Name): $($rows.Count) rows"
    
    # Check each row for null or empty header names
    $rowIdx = 0
    foreach ($r in $rows) {
        foreach ($p in $r.PSObject.Properties) {
            if ([string]::IsNullOrWhiteSpace($p.Name)) {
                Write-Host "  [MALFORMED] File $($f.Name) row $rowIdx has null/empty property with value '$($p.Value)'"
                $errorCount++
            }
        }
        $rowIdx++
    }
}

if ($errorCount -eq 0) {
    Write-Host "`nSUCCESS: All synthetic CSV files verified clean. Zero phantom/null properties."
    
    $p011 = (Import-Csv "$scriptDir\backend\data\synthetic\criminal_history.csv") | Where-Object { $_.person_id -eq 'P011' }
    Write-Host "`n[P011 Check] Person: $($p011.name), Case: $($p011.case_ref), Address: '$($p011.last_known_address)'"
} else {
    Write-Host "`nFAILURE: Found $errorCount malformed CSV properties!"
    exit 1
}
