$ErrorActionPreference = "Continue"
Add-Type -AssemblyName System.Drawing

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$assetRoot = Join-Path $root "assets\migrated"
$maxSide = 1000
$jpegQuality = 72L

if (!(Test-Path $assetRoot)) {
  Write-Output "No migrated images found."
  exit 0
}

$encoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" } | Select-Object -First 1
$params = New-Object System.Drawing.Imaging.EncoderParameters 1
$params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), $jpegQuality

$count = 0
$changed = 0

Get-ChildItem -LiteralPath $assetRoot -File -Include *.jpg,*.jpeg,*.png -Recurse | ForEach-Object {
  $count += 1
  try {
    $img = [System.Drawing.Image]::FromFile($_.FullName)
    $scale = [Math]::Min(1, $maxSide / [Math]::Max($img.Width, $img.Height))
    $shouldResize = $scale -lt 1
    $shouldCompressJpeg = $_.Extension -match "jpe?g" -and $_.Length -gt 80KB

    if ($shouldResize -or $shouldCompressJpeg) {
      $newWidth = [Math]::Max(1, [int]($img.Width * $scale))
      $newHeight = [Math]::Max(1, [int]($img.Height * $scale))
      $bitmap = New-Object System.Drawing.Bitmap $newWidth, $newHeight
      $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
      $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
      $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
      $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
      $graphics.DrawImage($img, 0, 0, $newWidth, $newHeight)
      $tmp = "$($_.FullName).tmp"
      if ($_.Extension -match "jpe?g") {
        $bitmap.Save($tmp, $encoder, $params)
      } else {
        $bitmap.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Png)
      }
      $graphics.Dispose()
      $bitmap.Dispose()
      $img.Dispose()
      Move-Item -LiteralPath $tmp -Destination $_.FullName -Force
      $changed += 1
    } else {
      $img.Dispose()
    }
  } catch {
    Write-Warning "Failed to optimize $($_.Name): $($_.Exception.Message)"
  }
  if ($count % 250 -eq 0) {
    Write-Output "optimized scan $count"
  }
}

Write-Output "Scanned $count images, optimized $changed."
