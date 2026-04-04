param(
    [Parameter(Mandatory = $true)]
    [string]$InputDir,

    [string]$OutputDir = '',

    [switch]$Recurse,

    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'

function Resolve-NormalizedPath {
    param([string]$PathValue)
    $resolved = (Resolve-Path -LiteralPath $PathValue).Path
    return $resolved
}

$inputRoot = Resolve-NormalizedPath -PathValue $InputDir
if (-not $OutputDir) {
    $OutputDir = Join-Path $inputRoot 'pdf-export'
}
if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}
$outputRoot = (Resolve-Path -LiteralPath $OutputDir).Path

if ($Recurse) {
    $files = Get-ChildItem -LiteralPath $inputRoot -File -Recurse | Where-Object { $_.Extension -in '.ppt', '.pptx' } | Sort-Object FullName
} else {
    $files = Get-ChildItem -LiteralPath $inputRoot -File | Where-Object { $_.Extension -in '.ppt', '.pptx' } | Sort-Object FullName
}
if (-not $files) {
    throw "No .ppt or .pptx files found under $inputRoot"
}

$ppt = $null
$results = New-Object System.Collections.Generic.List[object]
$ppSaveAsPDF = 32

try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue

    foreach ($file in $files) {
        $relativePart = $file.DirectoryName.Substring($inputRoot.Length).TrimStart('\\')
        $targetDir = if ([string]::IsNullOrWhiteSpace($relativePart)) { $outputRoot } else { Join-Path $outputRoot $relativePart }
        if (-not (Test-Path -LiteralPath $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }

        $pdfPath = Join-Path $targetDir ($file.BaseName + '.pdf')
        if ((-not $Overwrite) -and (Test-Path -LiteralPath $pdfPath)) {
            $results.Add([pscustomobject]@{
                source = $file.FullName
                pdf = $pdfPath
                status = 'skipped_exists'
            }) | Out-Null
            continue
        }

        $presentation = $null
        try {
            $presentation = $ppt.Presentations.Open($file.FullName, $false, $true, $false)
            $presentation.SaveAs($pdfPath, $ppSaveAsPDF)
            $results.Add([pscustomobject]@{
                source = $file.FullName
                pdf = $pdfPath
                status = 'exported'
            }) | Out-Null
        }
        finally {
            if ($presentation -ne $null) {
                $presentation.Close()
            }
        }
    }
}
finally {
    if ($ppt -ne $null) {
        $ppt.Quit()
    }
}

$results | ConvertTo-Json -Depth 4
