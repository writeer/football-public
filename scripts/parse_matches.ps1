$content = Get-Content 'C:\Users\admin\AppData\Local\Temp\trae\toolcall-output\d132928c-5fab-4ba1-80ef-fb1dd5dbc92d.txt' -Raw
$jsonStart = $content.IndexOf('{')
$jsonEnd = $content.LastIndexOf('}')
$jsonStr = $content.Substring($jsonStart, $jsonEnd - $jsonStart + 1)
$data = $jsonStr | ConvertFrom-Json
$tuesdayMatches = $data.matches | Where-Object { $_.weekday -eq '周二' }
foreach ($m in $tuesdayMatches) {
    $had = $m.markets.had.outcomes
    $hhad = $m.markets.hhad.outcomes
    Write-Output "$($m.matchNumStr) | ID:$($m.matchId) | $($m.league.abbName) | $($m.home.abbName) vs $($m.away.abbName) | $($m.matchTime) | Single:$($m.bettingSingle) | HHAD_GL:$($m.markets.hhad.goalLine) | HAD:$($had[0].odds)/$($had[1].odds)/$($had[2].odds)"
}
