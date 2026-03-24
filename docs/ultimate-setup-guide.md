# Ultimate Setup Guide — Fintech AI Segmentation
## pyenv · Poetry · GitHub — Step by Step with Explanations

> This guide treats every command as a lesson. Every single line is explained.  
> Target: macOS, zsh shell, Python 3.12, Poetry 2.x.

---

## Part 1 — Machine Setup (one-time per computer)

### Step 1.1 — Install Homebrew

Homebrew is the macOS package manager. Almost everything else depends on it.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

> `curl -fsSL` downloads the install script silently.  
> `/bin/bash -c` runs it immediately.

Verify:

```bash
brew --version
```

---

### Step 1.2 — Install pyenv

`pyenv` lets you install and switch between multiple Python versions without touching the system Python. This is critical because macOS ships with Python 3 versions that are outdated and often cause conflicts.

```bash
brew install pyenv
```

> Homebrew downloads `pyenv` and its dependencies and adds it to `/opt/homebrew/bin/`.

Now add pyenv to your shell so it activates every time you open a terminal. Run all three lines in sequence:

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
```

> `echo '...' >> ~/.zshrc` appends a line to your shell config file.  
> `PYENV_ROOT` tells your shell where pyenv lives.  
> `eval "$(pyenv init --path)"` lets pyenv intercept `python` and `python3` calls and redirect them to the version you selected.

Apply changes immediately (without restarting the terminal):

```bash
source ~/.zshrc
```

> `source` re-reads and re-executes the config file in the current session.

Verify:

```bash
pyenv --version
```

---

### Step 1.3 — Install Python 3.12 via pyenv

```bash
pyenv install 3.12.9
```

> This downloads the CPython 3.12.9 source, compiles it, and stores it under `~/.pyenv/versions/3.12.9/`.  
> Use `pyenv install --list` to see all available versions if you want a different one.

Set it as the global default Python on this machine:

```bash
pyenv global 3.12.9
```

> `pyenv global` writes your choice to `~/.pyenv/version`.  
> From now on, `python3` resolves to 3.12.9 everywhere on this machine.

Verify:

```bash
python3 --version
which python3
```

> `which python3` should return something inside `~/.pyenv/shims/`, not `/usr/bin/python3`.

---

### Step 1.4 — Install Poetry via Homebrew

Poetry is the dependency manager and virtual environment handler for this project.

```bash
brew install poetry
```

> Homebrew installs the `poetry` CLI and manages its own Python interpreter internally.  
> Installing via Homebrew is preferred on macOS because it avoids PATH conflicts.

Verify:

```bash
poetry --version
```

> You should see `Poetry (version 2.x.x)`. If you see "command not found", see the troubleshooting section.

---

### Step 1.5 — Configure Poetry (one-time global settings)

Tell Poetry to always create the virtual environment **inside** the project folder as `.venv/`:

```bash
poetry config virtualenvs.in-project true
```

> Without this, Poetry stores venvs in `~/Library/Caches/...` which is hard to find, hard to delete, and IDEs like Cursor/VSCode sometimes fail to detect them automatically.  
> With this setting, every project gets its own `.venv/` folder at the root, making it easy to see and manage.

Tell Poetry to use whichever Python is active in your shell (i.e., the pyenv-managed one):

```bash
poetry config virtualenvs.prefer-active-python true
```

> Without this, Poetry might accidentally pick up the system Python instead of the pyenv one.

Confirm all settings look right:

```bash
poetry config --list
```

> This prints the full Poetry configuration. Check that `virtualenvs.in-project = true` and `virtualenvs.prefer-active-python = true` appear.

---

## Part 2 — GitHub Setup (one-time per machine)

### Step 2.1 — Configure Git identity

Git attaches your name and email to every commit. Set them once:

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

> `--global` writes to `~/.gitconfig`, which applies to all repositories on this machine.

Set the default branch name to `main` (GitHub's standard):

```bash
git config --global init.defaultBranch main
```

---

### Step 2.2 — Generate and register an SSH key

SSH keys let you push to GitHub without typing a password every time.

```bash
ssh-keygen -t ed25519 -C "your@email.com"
```

> `-t ed25519` generates a modern, secure key type.  
> `-C "your@email.com"` adds a comment so you know which key belongs to which account.  
> Press Enter to accept the default save location (`~/.ssh/id_ed25519`).  
> You may optionally set a passphrase for extra security.

Copy the public key to your clipboard:

```bash
cat ~/.ssh/id_ed25519.pub | pbcopy
```

> `cat` reads the file, `|` pipes it to `pbcopy`, which copies it to the macOS clipboard.

Now go to **GitHub → Settings → SSH and GPG keys → New SSH key**, paste, and save.

Test the connection:

```bash
ssh -T git@github.com
```

> You should see: `Hi YOUR_USERNAME! You've successfully authenticated...`

---

## Part 3 — Project Setup from Scratch

### Step 3.1 — Create the project folder and initialize Git

```bash
mkdir -p ~/Documents/GitHub/Fintech_AI_Segmentation
cd ~/Documents/GitHub/Fintech_AI_Segmentation
git init
```

> `mkdir -p` creates the full path, including parent folders, without error if they already exist.  
> `cd` moves you inside it.  
> `git init` creates the hidden `.git/` folder that tracks all history for this repository.

---

### Step 3.2 — Create the .gitignore immediately

This must happen before any `git add`, to prevent accidental commits of secrets, environments, and OS junk.

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd

# Virtual environment (Poetry puts it here with in-project=true)
.venv/

# Environment variables — NEVER commit secrets
.env
.envrc

# Jupyter checkpoints
.ipynb_checkpoints/

# OS
.DS_Store
Thumbs.db

# Editors
.vscode/
.idea/

# Distribution / packaging
dist/
build/
*.egg-info/
EOF
```

> `cat > .gitignore << 'EOF' ... EOF` is a heredoc — it writes multi-line text directly into a file from the terminal.  
> Each line pattern tells Git to ignore files matching that pattern.  
> `.env` is the most critical: your API keys and database passwords live there and must never reach GitHub.

---

### Step 3.3 — Pin the Python version for this project

Tell pyenv which Python version to use specifically in this folder:

```bash
pyenv local 3.12.9
```

> `pyenv local` creates a `.python-version` file in the current directory.  
> Any time someone `cd`s into this folder, pyenv automatically activates Python 3.12.9, even if their global default is different.  
> This makes the project reproducible across machines.

Verify:

```bash
python3 --version
```

---

### Step 3.4 — Initialize Poetry in the existing folder

```bash
poetry init
```

> `poetry init` runs an interactive wizard that creates `pyproject.toml`.  
> Answer the prompts:
> - **Package name**: `fintech-ai-segmentation`
> - **Version**: `0.1.0`
> - **Description**: `AI-powered customer segmentation dashboard for SynaptiqPay`
> - **Author**: your name and email
> - **License**: `MIT`
> - **Compatible Python versions**: `^3.12`
> - **Define dependencies interactively?**: `no` (we'll add them properly next)

---

### Step 3.5 — Create the package directory

Poetry needs a Python package folder to install your project as a module:

```bash
mkdir -p src/fintech_ai_segmentation
touch src/fintech_ai_segmentation/__init__.py
```

> `mkdir -p src/fintech_ai_segmentation` creates the nested directory structure.  
> `touch __init__.py` creates an empty file that tells Python "this folder is a package".  
> Without this, `poetry install` fails with "No file/folder found for package fintech-ai-segmentation".

Now add the `src` layout to `pyproject.toml` so Poetry knows where to find the package. Open the file and add this section:

```toml
[tool.poetry]
packages = [{include = "fintech_ai_segmentation", from = "src"}]
```

> This tells Poetry: "the installable package lives inside `src/`".  
> The `src` layout is a best practice that prevents accidental imports of local files instead of the installed package.

---

### Step 3.6 — Tell Poetry which Python to use for this project

```bash
poetry env use python3
```

> This reads the active Python from pyenv (3.12.9) and creates a `.venv/` folder at the project root with that interpreter.  
> If a broken venv exists from previous attempts, remove it first:

```bash
poetry env remove python
poetry env use python3
```

> `poetry env remove python` deletes the existing virtual environment so it can be recreated cleanly.

Verify the environment:

```bash
poetry env info
```

> Shows the path to the venv, the Python version being used, and whether it's valid.

---

### Step 3.7 — Add runtime dependencies (including OpenAI API)

These are the packages required for the application to run in production and Docker, including the OpenAI API client:

```bash
poetry add pandas scikit-learn faker fastapi "uvicorn[standard]" sqlalchemy pydantic psycopg2-binary asyncpg langgraph openai
```

> **What each package does in this project:**
>
> | Package | Role in this project |
> |---|---|
> | `pandas` | EDA, RFM scoring, cohort analysis, unit economics pipeline |
> | `scikit-learn` | K-Means clustering + Logistic Regression churn model |
> | `faker` | Generates the 8,000 synthetic SynaptiqPay customer dataset |
> | `fastapi` | REST API serving `/dashboard`, `/customers`, `/customers/{id}/analyze` |
> | `uvicorn[standard]` | ASGI server that runs FastAPI; `[standard]` includes performance extras |
> | `sqlalchemy` | ORM for all Supabase (PostgreSQL) interactions |
> | `pydantic` | Request/response validation + LangGraph agent output schema |
> | `psycopg2-binary` | PostgreSQL adapter for synchronous SQLAlchemy connections |
> | `asyncpg` | PostgreSQL adapter for async connections |
> | `langgraph` | Orchestrates the AI agent pipeline (fetch → analyze → recommend) |
> | `openai` | OpenAI API client (e.g. `gpt-4.1`, `gpt-4.1-mini`) for personalized recommendations and explanations |
>
> Poetry resolves all version conflicts, updates `pyproject.toml`, and installs everything into `.venv/` in one command.

---

### Step 3.8 — Add development dependencies

These packages are only needed during development — they are NOT installed in production or Docker:

```bash
poetry add --group dev ruff black ipykernel jupyter pytest pytest-cov httpx matplotlib seaborn
```

> `--group dev` adds packages to the dev dependency group in `pyproject.toml` (Poetry 2 uses `[dependency-groups]` / PEP 735).  
> This group is excluded when you run `poetry install --without dev` (e.g. in Docker).
>
> **What each dev package does:**
>
> | Package | Role |
> |---|---|
> | `ruff` | Extremely fast Python linter and formatter (replaces flake8 + isort) |
> | `black` | Opinionated code formatter — enforces consistent style |
> | `ipykernel` | Registers the Poetry venv as a Jupyter kernel so notebooks use the right packages |
> | `jupyter` | Runs the EDA notebook locally |
> | `pytest` | Test runner for unit and integration tests |
> | `pytest-cov` | Measures how much of the code is covered by tests |
> | `httpx` | Async HTTP client — required to test FastAPI endpoints with `TestClient` |
> | `matplotlib` | Plotting library for EDA charts and visualizations in notebooks |
> | `seaborn` | Statistical plots on top of matplotlib — used alongside pandas in EDA |

---

### Step 3.9 — Install everything

```bash
poetry install
```

> This reads `pyproject.toml` and `poetry.lock`, installs all dependencies and your own package into `.venv/`, and pins exact versions.  
> After this, your environment is fully reproducible.
>
> If you only want dependencies without installing the project itself (for CI tools):
> ```bash
> poetry install --no-root
> ```
> But for normal development and Docker, always use plain `poetry install`.

Verify the installation worked:

```bash
poetry run python -c "import pandas; import sklearn; import fastapi; print('All imports OK')"
```

> `poetry run` executes a command inside the `.venv/` environment without needing to activate it first.  
> If this prints `All imports OK`, the environment is correctly set up.

---

### Step 3.10 — Register the Jupyter kernel

So that Jupyter notebooks use the Poetry venv (and can import all the project packages):

```bash
poetry run python -m ipykernel install --user --name fintech-ai-segmentation --display-name "Fintech AI Segmentation"
```

> `--user` installs the kernel for your user account (no sudo needed).  
> `--name` is the internal ID used by Jupyter.  
> `--display-name` is what you see in the "Select Kernel" dropdown in Cursor or JupyterLab.
>
> After this, open any notebook and select **"Fintech AI Segmentation"** as the kernel.

---

## Part 4 — Push to GitHub

### Step 4.1 — Create the repository on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `Fintech_AI_Segmentation`
3. Set to **Public**
4. **Do NOT** add a README, `.gitignore`, or license — you already have them locally
5. Click **Create repository**

---

### Step 4.2 — Create the initial project structure files

Before committing, create the minimal folders:

```bash
mkdir -p notebooks
touch notebooks/EDA.ipynb
touch README.md
touch .env
```

> `touch .env` creates an empty file so the `.gitignore` entry takes effect and nobody gets confused about where to put secrets.  
> The `.env` file will **not** be committed because it's in `.gitignore`.

---

### Step 4.3 — Connect local to GitHub

```bash
git remote add origin git@github.com:YOUR_USERNAME/Fintech_AI_Segmentation.git
```

> `git remote add` registers the GitHub repository URL under the alias `origin`.  
> `origin` is the conventional name for the main remote.  
> We use the SSH format (`git@github.com:...`) so pushes use your SSH key — no password prompts.

Verify:

```bash
git remote -v
```

> Should show two lines: `fetch` and `push`, both pointing to your GitHub repo.

---

### Step 4.4 — Stage, commit, and push

```bash
git add .
```

> `git add .` stages every file in the current directory for the next commit — except files matched by `.gitignore` (so `.env` and `.venv/` are automatically excluded).

```bash
git status
```

> Always run `git status` before committing to review exactly which files are staged.  
> Verify `.env` and `.venv/` do NOT appear in the list.

```bash
git commit -m "chore: initial project setup with poetry, pyenv, and src layout"
```

> `git commit -m` creates a snapshot of all staged files with the provided message.  
> A good commit message starts with a type: `chore` (setup/tooling), `feat` (new feature), `fix` (bug fix), `docs` (documentation).

```bash
git branch -M main
git push -u origin main
```

> `git branch -M main` renames the default branch from `master` to `main` (matches GitHub's default).  
> `git push -u origin main` pushes your commits to GitHub and sets `origin/main` as the upstream, so future pushes only need `git push`.

---

## Part 5 — Cloning on a New Machine (Reproducibility)

If you switch machines or a collaborator joins, they only need to run:

```bash
git clone git@github.com:YOUR_USERNAME/Fintech_AI_Segmentation.git
cd Fintech_AI_Segmentation
pyenv local 3.12.9      # activates the correct Python
poetry install           # recreates the exact environment from poetry.lock
```

> `poetry.lock` pins every package to its exact version.  
> `poetry install` on a different machine reads `poetry.lock` and installs **exactly the same versions**.  
> This is what makes Poetry superior to plain `pip` — no "works on my machine" problem.

---

## Part 6 — Daily Workflow

### Run the FastAPI backend

```bash
poetry run uvicorn src.fintech_ai_segmentation.main:app --reload
```

> `--reload` watches for file changes and restarts the server automatically — essential during development.

### Run the linter

```bash
poetry run ruff check .
```

> Checks all Python files for style issues, unused imports, and common bugs.

### Auto-fix linting issues

```bash
poetry run ruff check . --fix
```

### Format all code

```bash
poetry run black .
```

### Run tests

```bash
poetry run pytest
```

### Open a shell with the venv activated

```bash
poetry shell
# now you can run python, uvicorn, pytest etc. directly
exit   # to leave the poetry shell
```

---

## Part 7 — Troubleshooting

### `poetry: command not found`

```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.zshrc
```

If installed via Homebrew, check:

```bash
brew doctor
brew link poetry
```

---

### `poetry install` fails with "No file/folder found for package"

Your `src/fintech_ai_segmentation/__init__.py` is missing, or `pyproject.toml` is missing the `packages` entry:

```bash
mkdir -p src/fintech_ai_segmentation
touch src/fintech_ai_segmentation/__init__.py
```

And confirm `pyproject.toml` contains:

```toml
[tool.poetry]
packages = [{include = "fintech_ai_segmentation", from = "src"}]
```

---

### Wrong Python in the venv

```bash
poetry env remove python
pyenv local 3.12.9
poetry env use python3
poetry install
```

---

### Notebook imports fail (ModuleNotFoundError)

The notebook is using the system kernel, not the Poetry one:

```bash
poetry run python -m ipykernel install --user --name fintech-ai-segmentation --display-name "Fintech AI Segmentation"
```

Then in Cursor/JupyterLab, select kernel → **"Fintech AI Segmentation"**.

---

### SSH push rejected

```bash
ssh -T git@github.com
```

If it fails, re-run Step 2.2 to regenerate and register the SSH key.

---

## Quick Reference Card

```bash
# Machine setup (one-time)
brew install pyenv poetry
pyenv install 3.12.9
pyenv global 3.12.9
poetry config virtualenvs.in-project true
poetry config virtualenvs.prefer-active-python true

# New project (with OpenAI)
mkdir MyProject && cd MyProject
git init
pyenv local 3.12.9
poetry init
mkdir -p src/my_package && touch src/my_package/__init__.py
poetry env use python3
poetry add pandas scikit-learn faker fastapi "uvicorn[standard]" sqlalchemy pydantic psycopg2-binary asyncpg langgraph openai
poetry add --group dev ruff black ipykernel jupyter pytest pytest-cov httpx matplotlib seaborn
poetry install

# GitHub
git remote add origin git@github.com:USER/REPO.git
git add . && git status
git commit -m "chore: initial setup"
git branch -M main && git push -u origin main

# Daily
poetry run uvicorn src.fintech_ai_segmentation.main:app --reload
poetry run ruff check . --fix
poetry run pytest
```
