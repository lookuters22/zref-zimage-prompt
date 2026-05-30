# Create the GitHub repository (no `gh` CLI required)

`gh` is optional. Use the website + `git` if you do not have GitHub CLI installed.

## 1. Create an empty repo on GitHub

1. Open **https://github.com/new**
2. **Repository name:** e.g. `zref-zimage-prompt`
3. **Public** (or Private)
4. **Do not** add a README, `.gitignore`, or license (this folder already has them).
5. Click **Create repository**.

## 2. Point this project at GitHub and push

In **this** project directory (`E:\NODE SAMPLING` or your clone path), run (replace `YOUR_USER`):

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USER/zref-zimage-prompt.git
git push -u origin main
```

If GitHub shows **SSH** instead:

```bash
git remote add origin git@github.com:YOUR_USER/zref-zimage-prompt.git
git push -u origin main
```

## 3. On RunPod — clone and install

```bash
git clone https://github.com/YOUR_USER/zref-zimage-prompt.git
cd zref-zimage-prompt
pip install -e .
cp -r comfy/zref_prompt /workspace/ComfyUI/custom_nodes/
```

(Adjust `ComfyUI` path to match your template.)

## Optional: GitHub CLI later

Install [GitHub CLI](https://cli.github.com/), then from the repo root:

```bash
gh auth login
gh repo create zref-zimage-prompt --public --source=. --remote=origin --push
```
