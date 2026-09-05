$json = Get-Content -Raw "C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\last_prompt.json" | ConvertFrom-Json
[System.IO.File]::WriteAllText("C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\full_prompt10.txt", $json.content)
