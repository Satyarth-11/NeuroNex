$path = "C:\Users\satya\.gemini\antigravity-ide\brain\273dd972-f645-4159-9a59-d13c5bf4315b\.system_generated\logs\transcript_full.jsonl"
$reader = [System.IO.File]::OpenText($path)
$fullPrompt = ""
while ($null -ne ($line = $reader.ReadLine())) {
    if ($line.Contains('"step_index":1067')) {
        $fullPrompt = $line
        break
    }
}
$reader.Close()
if ($fullPrompt -ne "") {
    $j = ConvertFrom-Json $fullPrompt
    [System.IO.File]::WriteAllText("C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\full_step1067.txt", $j.content)
    Write-Host "Wrote full step 1067, length: $($j.content.Length)"
} else {
    Write-Host "Step 1067 not found in transcript_full.jsonl"
}
