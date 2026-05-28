$ErrorActionPreference = "Continue"
Add-Type -AssemblyName System.Drawing

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$assetRoot = Join-Path $root "assets\migrated"
$maxSide = 1100
$jpegQuality = 76L

$encoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" } | Select-Object -First 1
$params = New-Object System.Drawing.Imaging.EncoderParameters 1
$params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), $jpegQuality

$replacements = @{}
$count = 0
$converted = 0

Get-ChildItem -LiteralPath $assetRoot -File -Filter *.png | ForEach-Object {
  $count += 1
  try {
    $img = [System.Drawing.Image]::FromFile($_.FullName)
    $scale = [Math]::Min(1, $maxSide / [Math]::Max($img.Width, $img.Height))
    $newWidth = [Math]::Max(1, [int]($img.Width * $scale))
    $newHeight = [Math]::Max(1, [int]($img.Height * $scale))
    $bitmap = New-Object System.Drawing.Bitmap $newWidth, $newHeight
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear([System.Drawing.Color]::White)
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.DrawImage($img, 0, 0, $newWidth, $newHeight)

    $jpgName = [System.IO.Path]::GetFileNameWithoutExtension($_.Name) + ".jpg"
    $jpgPath = Join-Path $_.DirectoryName $jpgName
    $bitmap.Save($jpgPath, $encoder, $params)
    $graphics.Dispose()
    $bitmap.Dispose()
    $img.Dispose()

    if ((Get-Item $jpgPath).Length -lt $_.Length) {
      Remove-Item -LiteralPath $_.FullName -Force
      $replacements[$_.Name] = $jpgName
      $converted += 1
    } else {
      Remove-Item -LiteralPath $jpgPath -Force
    }
  } catch {
    Write-Warning "Failed to convert $($_.Name): $($_.Exception.Message)"
  }
  if ($count % 200 -eq 0) {
    Write-Output "converted scan $count"
  }
}

if ($replacements.Count -gt 0) {
  $textFiles = Get-ChildItem -LiteralPath $root -Recurse -File -Include *.html,*.js,*.css,*.md
  foreach ($file in $textFiles) {
    $text = Get-Content -LiteralPath $file.FullName -Raw
    $updated = $text
    foreach ($key in $replacements.Keys) {
      $updated = $updated.Replace($key, $replacements[$key])
    }
    if ($updated -ne $text) {
      Set-Content -LiteralPath $file.FullName -Value $updated -Encoding UTF8
    }
  }
}

Write-Output "Scanned $count PNG files, converted $converted to JPG."
