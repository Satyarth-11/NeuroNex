$path = "C:\Users\satya\.gemini\antigravity-ide\brain\273dd972-f645-4159-9a59-d13c5bf4315b\.system_generated\logs\transcript.jsonl"
$reader = [System.IO.File]::OpenText($path)
$lastUserPrompt = ""
while ($null -ne ($line = $reader.ReadLine())) {
    if ($line.Contains('"type":"USER_INPUT"')) {
        $lastUserPrompt = $line
    }
}
$reader.Close()
[System.IO.File]::WriteAllText("C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\last_prompt.json", $lastUserPrompt)
