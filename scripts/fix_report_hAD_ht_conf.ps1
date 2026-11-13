# Fix HAD row, half-time score row, and confidence paragraph for all 27 matches
$file = "e:\VibeCoding\football\reports\html\20260816_sunday_analysis_zhihu.md"
$lines = Get-Content -Path $file -Encoding UTF8

# Step 1: Build confidence map from 总览 table
$confMap = @{}
foreach ($line in $lines) {
    if ($line -match '^\| (\d{3}) \| .+ \| .+ \| .+ \| (★+) \|') {
        $confMap[$matches[1]] = $matches[2]
    }
}
Write-Host "Confidence map entries: $($confMap.Count)"
foreach ($k in ($confMap.Keys | Sort-Object)) { Write-Host "  $k -> $($confMap[$k])" }

# Factorial function
function Get-Factorial([int]$n) {
    $r = 1.0
    for ($i = 2; $i -le $n; $i++) { $r *= $i }
    return $r
}

# Poisson PMF
function Get-PoissonPmf([int]$k, [double]$lambda) {
    return [Math]::Pow($lambda, $k) * [Math]::Exp(-$lambda) / (Get-Factorial $k)
}

# Generate top 3 half-time scores from lambda
function Get-HalfTimeScores([double]$lh, [double]$la) {
    $htHome = $lh * 0.45
    $htAway = $la * 0.45
    $scores = @()
    for ($h = 0; $h -le 3; $h++) {
        for ($a = 0; $a -le 3; $a++) {
            $p = (Get-PoissonPmf $h $htHome) * (Get-PoissonPmf $a $htAway)
            $scores += [PSCustomObject]@{ Score = "$h-$a"; Prob = $p }
        }
    }
    $top3 = $scores | Sort-Object Prob -Descending | Select-Object -First 3
    $result = @()
    foreach ($s in $top3) {
        $pct = [Math]::Round($s.Prob * 100)
        $result += "$($s.Score)($pct%)"
    }
    return ($result -join ' > ')
}

# Direction name mapping
function Get-DirName([string]$key) {
    switch ($key) {
        'home' { return '主胜' }
        'draw' { return '平局' }
        'away' { return '客胜' }
    }
    return $key
}

$output = @()
$currentMatch = $null
$modelHome = 0
$modelDraw = 0
$modelAway = 0
$lambdaH = 0.0
$lambdaA = 0.0
$inRecommendTable = $false

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]

    # Detect match section start
    if ($line -match '^## (\d{3}) ') {
        $currentMatch = $matches[1]
        $modelHome = 0; $modelDraw = 0; $modelAway = 0
        $lambdaH = 0.0; $lambdaA = 0.0
        $inRecommendTable = $false
    }

    # Extract model probabilities from "融合概率" line
    if ($line -match '融合概率.*主胜\s*(\d+)%.*平\s*(\d+)%.*客\s*(\d+)%') {
        $modelHome = [int]$matches[1]
        $modelDraw = [int]$matches[2]
        $modelAway = [int]$matches[3]
    }

    # Extract lambda values
    if ($line -match 'λ：主\s*([\d.]+).*客\s*([\d.]+)') {
        $lambdaH = [double]$matches[1]
        $lambdaA = [double]$matches[2]
    }

    # Track if we're inside the recommendation table
    if ($line -match '^\*\*推荐：\*\*') { $inRecommendTable = $true }
    if ($line -match '^---') { $inRecommendTable = $false }

    # Skip the misplaced 置信度 line that appears before the rule trigger note
    # (i.e., between 伤停 and the > 规则触发 blockquote)
    # Pattern: **置信度：**  — ...  followed by an empty line then > 规则
    if ($line -match '^\*\*置信度：\*\*\s+—' -and -not $inRecommendTable) {
        # Check if next non-empty line is a > blockquote (rule trigger) or model line
        $nextIdx = $i + 1
        while ($nextIdx -lt $lines.Count -and $lines[$nextIdx] -match '^\s*$') { $nextIdx++ }
        if ($nextIdx -lt $lines.Count -and ($lines[$nextIdx] -match '^>' -or $lines[$nextIdx] -match '^\*\*模型')) {
            # This is the misplaced 置信度 before the table - skip it
            Write-Host "  Skipping misplaced 置信度 at line $($i+1) for match $currentMatch"
            continue
        }
    }

    # Fix HAD row: "| **HAD** | 首选 (%) / 次选 (%) |"
    if ($line -match '\| \*\*HAD\*\* \| 首选 \(%\) / 次选 \(%\)') {
        if ($modelHome -gt 0 -or $modelDraw -gt 0 -or $modelAway -gt 0) {
            $probs = @(
                [PSCustomObject]@{ Dir = 'home'; Name = '主胜'; Prob = $modelHome }
                [PSCustomObject]@{ Dir = 'draw'; Name = '平局'; Prob = $modelDraw }
                [PSCustomObject]@{ Dir = 'away'; Name = '客胜'; Prob = $modelAway }
            )
            $sorted = $probs | Sort-Object Prob -Descending
            $first = $sorted[0]
            $second = $sorted[1]
            $line = "| **HAD** | 首选 $($first.Name)($($first.Prob)%) / 次选 $($second.Name)($($second.Prob)%) |"
            Write-Host "  Fixed HAD for $currentMatch : $($first.Name)($($first.Prob)%) / $($second.Name)($($second.Prob)%)"
        }
    }

    # Fix 半场比分 row with placeholder values
    if ($line -match '\| \*\*半场比分\*\* \| 0-0\(100%\)|\| \*\*半场比分\*\* \| 0-0\(0%\)') {
        if ($lambdaH -gt 0 -and $lambdaA -gt 0) {
            $htScores = Get-HalfTimeScores $lambdaH $lambdaA
            $line = "| **半场比分** | $htScores |"
            Write-Host "  Fixed 半场比分 for $currentMatch : $htScores"
        }
    }

    # Fix the 置信度 paragraph after the recommendation table
    # Pattern: **置信度：**  — reason  (missing the star level)
    if ($line -match '^\*\*置信度：\*\*\s+—' -and $inRecommendTable) {
        if ($currentMatch -and $confMap.ContainsKey($currentMatch)) {
            $conf = $confMap[$currentMatch]
            $reason = $line -replace '^\*\*置信度：\*\*\s+—\s*', ''
            $line = "**置信度：** $conf — $reason"
            Write-Host "  Fixed 置信度 for $currentMatch : $conf"
        }
    }

    $output += $line
}

# Write output
$output | Set-Content -Path $file -Encoding UTF8
Write-Host "`nDone! Total lines: $($output.Count)"
