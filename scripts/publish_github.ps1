<#
.SYNOPSIS
  Create GitHub repo via REST API and push this repo to github.com/OWNER/REPO.

.DESCRIPTION
  Requires a Personal Access Token with `repo` scope (classic) or fine-grained
  "Contents" + "Metadata" on the target repo (and org permission if OWNER is an org).

  Set the token in the environment (do not commit it):

    $env:GITHUB_TOKEN = "ghp_...."

  Then:

    .\scripts\publish_github.ps1 -Owner lookuters22

  If OWNER is a GitHub *organization* (not your user login), pass -IsOrg.
#>
param(
  [Parameter(Mandatory = $false)]
  [string] $Owner = "lookuters22",

  [Parameter(Mandatory = $false)]
  [string] $RepoName = "zref-zimage-prompt",

  [switch] $IsOrg
)

$ErrorActionPreference = "Stop"

if (-not $env:GITHUB_TOKEN) {
  Write-Error "Set GITHUB_TOKEN first (GitHub Settings → Developer settings → PAT, `repo` scope)."
}

$headers = @{
  Authorization  = "Bearer $($env:GITHUB_TOKEN)"
  Accept         = "application/vnd.github+json"
  "X-GitHub-Api-Version" = "2022-11-28"
}

# Verify token and (for user repos) login matches Owner
$me = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers -Method Get
if (-not $IsOrg -and $me.login -ne $Owner) {
  Write-Warning "Authenticated as '$($me.login)' but -Owner is '$Owner'. Repos created with /user/repos go under $($me.login). Use -Owner $($me.login) or an org token with -IsOrg."
}

$bodyObj = @{
  name        = $RepoName
  description = "Reference image to Z-Image (Qwen3-4B) prompts; ComfyUI custom node"
  private     = $false
  auto_init   = $false
}
$body = $bodyObj | ConvertTo-Json

$createUri = if ($IsOrg) {
  "https://api.github.com/orgs/$Owner/repos"
} else {
  "https://api.github.com/user/repos"
}

try {
  $null = Invoke-RestMethod -Uri $createUri -Headers $headers -Method Post -Body $body -ContentType "application/json"
  Write-Host "Created: https://github.com/$Owner/$RepoName"
} catch {
  if ($_.Exception.Response.StatusCode.value__ -eq 422) {
    Write-Host "Repo may already exist (422). Continuing with remote + push."
  } else {
    throw
  }
}

$remoteUrl = "https://github.com/$Owner/$RepoName.git"
git remote remove origin 2>$null
git remote add origin $remoteUrl
Write-Host "Remote origin -> $remoteUrl"

$branch = git branch --show-current
if (-not $branch) { $branch = "main" }

git push -u origin $branch
Write-Host "Done. Open: https://github.com/$Owner/$RepoName"
