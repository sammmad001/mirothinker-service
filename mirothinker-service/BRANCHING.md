# MiroThinker - Git Branching Strategy

This document describes the Git branching model used for MiroThinker development.

## Branch Model

We follow **Git Flow** branching strategy with three main branches:

### Main Branches

| Branch | Purpose | Protection Rules | Deployment Target |
|--------|---------|------------------|-------------------|
| `main` | Production-ready code | - Force push disabled<br>- Requires PR approval<br>- All CI checks must pass | Production Environment |
| `develop` | Integration branch for features | - Force push disabled<br>- PR merge recommended | Staging Environment |

### Support Branches

| Branch Type | Created From | Merged To | Naming Convention | Lifetime |
|------------|--------------|-----------|-------------------|----------|
| Feature | `develop` | `develop` | `feature/<name>` | Temporary |
| Release | `develop` | `main` + `develop` | `release/v<version>` | Temporary |
| Hotfix | `main` | `main` + `develop` | `hotfix/<name>` | Temporary |

## Workflow

### Daily Development Flow

```bash
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/new-research-module

# 3. Make changes and commit
git add .
git commit -m "feat: add new research module with quality checks"

# 4. Push and create PR
git push origin feature/new-research-module
# Create PR on GitHub: feature/new-research-module → develop
# Wait for review and CI checks to pass
# Merge to develop

# 5. Automatic deployment to staging
# CI/CD automatically deploys to staging when develop is updated
```

### Release Flow

```bash
# 1. Create release branch from develop
git checkout develop
git checkout -b release/v1.8.0

# 2. Update version numbers and CHANGELOG
# Edit backend/src/core/config.py: APP_VERSION = "1.8.0"
# Edit CHANGELOG.md with all changes

# 3. Test release candidate
# CI/CD deploys to staging automatically
# Perform manual testing on staging environment

# 4. Merge to main and tag
git checkout main
git merge --no-ff release/v1.8.0
git tag -a v1.8.0 -m "Release v1.8.0: New research module and quality improvements"
git push origin main --tags

# 5. Automatic deployment to production
# CI/CD detects tag and deploys to production
# GitHub Release is created automatically

# 6. Merge back to develop
git checkout develop
git merge --no-ff release/v1.8.0
git push origin develop

# 7. Delete release branch
git branch -d release/v1.8.0
git push origin --delete release/v1.8.0
```

### Hotfix Flow

```bash
# 1. Create hotfix from main
git checkout main
git checkout -b hotfix/critical-bug-fix

# 2. Fix the bug
git add .
git commit -m "fix: resolve critical bug in research agent"

# 3. Tag and merge
git tag -a v1.8.1 -m "Hotfix v1.8.1: Critical bug fix"
git checkout main
git merge --no-ff hotfix/critical-bug-fix
git push origin main --tags

# 4. Merge to develop
git checkout develop
git merge --no-ff hotfix/critical-bug-fix
git push origin develop

# 5. Delete hotfix branch
git branch -d hotfix/critical-bug-fix
git push origin --delete hotfix/critical-bug-fix
```

## Commit Convention

We use **Conventional Commits** specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting, semicolons, etc.) |
| `refactor` | Code refactoring |
| `perf` | Performance improvements |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks, dependencies |

### Examples

```bash
feat: add quality enhancement module for research
fix: resolve call_llm response validation error
docs: update deployment guide with new steps
refactor: simplify agent state management
perf: optimize context window token usage
test: add unit tests for detect_domain function
chore: update dependencies to latest versions
```

## Version Management

### Semantic Versioning (SemVer)

Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

### Version Tags

- Production releases: `v1.8.0`, `v1.8.1`, etc.
- Pre-releases: `v1.8.0-rc.1`, `v1.8.0-beta.1`
- Development: `1.8.0-dev` (in config file only)

## Environment Branch Mapping

| Branch | Environment | Config File | Auto Deploy |
|--------|------------|-------------|-------------|
| `develop` | Staging | `.env.staging` | Yes (on push) |
| `main` + tag `v*` | Production | `.env.production` | Yes (on tag) |
| `main` (no tag) | - | - | No (requires tag) |
| Feature branches | Local dev | `.env.development` | No |

## Branch Protection Rules

### Main Branch

- ✅ Require pull request before merging
- ✅ Require 1 approving review
- ✅ Dismiss stale approvals on new commits
- ✅ Require status checks to pass
  - `Test Suite (Python 3.10)`
  - `Test Suite (Python 3.11)`
  - `Build Artifact`
- ✅ Include administrators
- ✅ Restrict who can push to matching branches

### Develop Branch

- ✅ Require pull request before merging
- ✅ Require 1 approving review
- ✅ Require status checks to pass
- ✅ Include administrators

## Quick Reference

```bash
# List all branches
git branch -a

# Create and switch to feature branch
git checkout -b feature/my-feature

# Push branch to remote
git push origin feature/my-feature

# Delete local branch
git branch -d feature/my-feature

# Delete remote branch
git push origin --delete feature/my-feature

# Create and push tag
git tag -a v1.8.0 -m "Release v1.8.0"
git push origin v1.8.0

# View tags
git tag -l

# View commit history
git log --oneline --graph --all --decorate
```
