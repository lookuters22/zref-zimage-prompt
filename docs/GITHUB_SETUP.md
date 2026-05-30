# Create the GitHub repository (no `gh` CLI required)

Target for this project: **`lookuters22/zref-zimage-prompt`**  
→ **https://github.com/lookuters22/zref-zimage-prompt**

## Fast path: GitHub API + `scripts/publish_github.ps1`

1. GitHub → **Settings → Developer settings → Personal access tokens**  
   Create a **classic** token with **`repo`** scope (or fine-grained access to create repos under `lookuters22`).

2. In **PowerShell** (repo root):

```powershell
cd "E:\NODE SAMPLING"   # or your clone path
$env:GITHUB_TOKEN = "ghp_...."   # do not commit; clear after: Remove-Item Env:GITHUB_TOKEN
.\scripts\publish_github.ps1 -Owner lookuters22
```

The script calls **`POST https://api.github.com/user/repos`** (repo is created under the **authenticated user**).  
Your PAT must be for the **`lookuters22`** GitHub account.

If **`lookuters22`** is an **organization** and your token belongs to your personal user, run:

```powershell
.\scripts\publish_github.ps1 -Owner lookuters22 -IsOrg
```

That uses **`POST https://api.github.com/orgs/lookuters22/repos`** (needs org permission to create repos).

## Manual: empty repo on the website

1. **https://github.com/new** — Owner **lookuters22**, name **`zref-zimage-prompt`**
2. Public or Private. **No** README / `.gitignore` / license.
3. Then:

```bash
git branch -M main
git remote add origin https://github.com/lookuters22/zref-zimage-prompt.git
git push -u origin main
```

## On RunPod — clone and install

```bash
git clone https://github.com/lookuters22/zref-zimage-prompt.git
cd zref-zimage-prompt
pip install -e .
cp -r comfy/zref_prompt /workspace/ComfyUI/custom_nodes/
```

## Optional: GitHub CLI

```bash
gh auth login
gh repo create lookuters22/zref-zimage-prompt --public --source=. --remote=origin --push
```
