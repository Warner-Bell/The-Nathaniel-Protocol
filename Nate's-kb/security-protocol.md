# Security Protocol

**Keywords**: security, git, credentials, PII, confidential, hardening, protection
**Purpose**: Comprehensive security practices for protecting sensitive data, credentials, and confidential content
**Last Updated**: 2026-02-11
**Trigger**: Any git operation, credential handling, PII exposure, or file operations on protected directories

---

## Protocol Scope

This protocol covers:
1. **Git Hardening** - Protocol-driven scanning and confidential content protection
2. **Credential Safety** - Never expose secrets, keys, or passwords
3. **PII Protection** - Mask account numbers, customer names, personal data
4. **File Protection** - Safeguard intelligence system and critical files
5. **Communication Security** - Sanitize outputs and responses
6. **Data Classification** - AWS data types, classification levels, and approved tools
7. **External Content Security** - Defense-in-depth for fetched/external content (always-on in kernel, see Nathaniel.md)

---

## 1. Git Hardening

### MANDATORY: Before ANY git stage, commit, or push

**Trigger keywords**: git add, git commit, git push, stage, commit, push

**Execution sequence**:

```
1. SCAN: Run git add --dry-run . and review output
2. CHECK: Scan for confidential patterns
3. VERIFY: No flagged content in staged files
4. CONFIRM: If anything flagged, STOP and ask before proceeding
```

### Confidential Patterns to Block

| Category | Patterns |
|----------|----------|
| **Customer Data** | Customer, Customer-Work/, client, account |
| **Internal Content** | internal/, Personal/, Feedback/, Daily-Tasks/ |
| **Secrets** | secret, credential, password, api_key, token |
| **Key Files** | .env, .pem, .key, .p12, .cert |
| **AWS Specific** | aws-exports, amplify-meta, .aws/, credentials.json |

### Verification Commands

```bash
# Check what will be staged
git add --dry-run .

# Scan for confidential patterns
git add --dry-run . 2>&1 | grep -iE "(customer|internal|personal|feedback|daily|secret|credential|password|\.env|\.pem|\.key)"
```

### If Confidential Content Detected

1. **STOP** - Do not proceed with commit
2. **IDENTIFY** - Which files contain sensitive content
3. **ASSESS** - Should this be in .gitignore?
4. **ASK** - Confirm with user before any action
5. **REMEDIATE** - Update .gitignore or remove sensitive content

### Common .gitignore Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Windows paths | `Blog\guidelines\` won't work | Use forward slashes: `Blog/guidelines/` |
| Including repo name | `RepoName/docs/` is wrong | Paths relative to root: `docs/` |
| Top-level only | `internal/` misses nested | Use `**/internal/` for all levels |
| Already tracked files | .gitignore doesn't affect tracked files | Run `git rm -r --cached path/` first |

### Local-Only Excludes

For rules you don't want in the repo's .gitignore, use `.git/info/exclude`:

```bash
# Add to .git/info/exclude (not shared with repo)
echo "local-notes.md" >> .git/info/exclude
echo "scratch/" >> .git/info/exclude
```

### Fresh Start Protocol

If repo has problematic git history with exposed secrets:

```bash
# Remove old git (CAUTION: loses all history)
rm -rf .git

# Initialize fresh
git init

# Verify .gitignore is working
git add --dry-run .

# Stage and commit
git add .
git commit -m "Initial commit"
```

### README Audit

Before publishing, check documentation for:
- [ ] Customer/client names
- [ ] Internal project codenames  
- [ ] Account IDs or identifiers
- [ ] Internal URLs or endpoints
- [ ] Employee names (other than yourself)
- [ ] References to directories that won't be public

### .gitignore Essentials

If no .gitignore exists, create one with this template:

```gitignore
# ===========================================
# Repository .gitignore
# Security-hardened for public publication
# ===========================================

# -------------------------------------------
# CONFIDENTIAL - Customer & Internal Data
# -------------------------------------------

# Customer-specific work (NEVER commit)
Customer-Work/
client-data/
accounts/

# Internal documentation
docs/internal/
internal/

# Personal and HR content
Personal/
Feedback/
performance/

# Daily operations
Daily-Tasks/
tasks/
agenda/

# -------------------------------------------
# SECRETS & CREDENTIALS
# -------------------------------------------

# Environment files
.env
.env.*
!.env.example
*.env

# AWS
.aws/
aws-exports.js
**/amplify-meta.json

# Keys and certs
*.pem
*.key
*.cert
*.p12

# Secret files
secrets.json
credentials.json
**/deployment.json

# -------------------------------------------
# ENVIRONMENT & DEPENDENCIES
# -------------------------------------------

# Python
venv/
.venv/
env/
__pycache__/
*.py[cod]
*.egg-info/

# Node
node_modules/
.pnpm-store/

# -------------------------------------------
# BUILD & OUTPUT
# -------------------------------------------

dist/
build/
out/
generated-*/
*.generated.*

# -------------------------------------------
# IDE & OS
# -------------------------------------------

.vscode/
.idea/
.DS_Store
Thumbs.db
desktop.ini

# -------------------------------------------
# TEMPORARY
# -------------------------------------------

*.tmp
*.temp
*.swp
*.bak
*.log
logs/
```

---

## 1b. Memory Sanitization Filter

### Purpose

Automatically sanitize customer names and account IDs in `Nate's-kb/Memory/` files during git commit. Local files remain intact with real customer names for operational use; pushed versions are sanitized.

### How It Works

Git clean/smudge filter configured in `.gitattributes`:
- **Clean filter** (commit): Replaces customer names with placeholders
- **Smudge filter** (checkout): Passes through unchanged

### Customer Mappings

| Real Name | Placeholder |
|-----------|-------------|
| *(add customer names here)* | [CUSTOMER-A] |
| *(add account IDs here)* | [ACCOUNT-A] |

### Files Involved

| File | Purpose |
|------|---------|
| `scripts/git-filter-clean.py` | Sanitizes on commit |
| `scripts/git-filter-smudge.py` | Passthrough on checkout |
| `.gitattributes` | Defines which files use filter |

### Verification

```bash
# Check local file (should have real names)
grep -i "[customer-name]" Nate\'s-kb/Memory/memory.json

# Check what git would commit (should be sanitized)
git add Nate\'s-kb/Memory/memory.json
git show :Nate\'s-kb/Memory/memory.json | grep -i "\[CUSTOMER"
git reset HEAD Nate\'s-kb/Memory/memory.json
```

### Adding New Customers

Edit `scripts/git-filter-clean.py` and add to REPLACEMENTS list:
```python
(r"(?i)NewCustomer", "[CUSTOMER-X]"),
```

### Troubleshooting

If filter not working:
```bash
# Verify filter is configured
git config --get-regexp filter.sanitize

# Re-configure if needed
git config filter.sanitize-memory.clean "python3 scripts/git-filter-clean.py"
git config filter.sanitize-memory.smudge "python3 scripts/git-filter-smudge.py"
git config filter.sanitize-memory.required true
```

---

## 2. Credential Safety

### NEVER Include in Code or Output

- API keys
- Access tokens
- Passwords
- Secret keys
- Connection strings with credentials
- AWS access key IDs or secret access keys
- Private keys (RSA, SSH, etc.)

### Safe Credential Patterns

| Instead of... | Use... |
|---------------|--------|
| Hardcoded API key | Environment variable reference |
| Password in config | `<PASSWORD>` placeholder |
| AWS keys in code | IAM roles or credential provider |
| Connection string | Secrets manager reference |

### Code Review Checklist

Before committing any code:
- [ ] No hardcoded credentials
- [ ] No API keys in source files
- [ ] No passwords in configuration
- [ ] Environment variables used for secrets
- [ ] .env files are gitignored

---

## 3. PII Protection

### Data Requiring Masking

| Data Type | Masking Pattern | Example |
|-----------|-----------------|---------|
| AWS Account ID | `*******[last5]` | Account ending in *******12345 |
| Customer Name | `[Customer]` or anonymize | "Customer A" not "Acme Corp" |
| Email Address | `<email>` | user@<email> |
| Phone Number | `<phone>` | Contact: <phone> |
| IP Address | `<ip>` or partial | 192.168.x.x |
| Personal Names | `[Name]` | Employee [Name] reported... |

### When to Mask

- Session logs that might be shared
- Documentation with real examples
- Error messages in responses
- Any output that could be committed to git
- Customer-facing communications being drafted

### Masking in Practice

```
❌ "Account 123456789012 has an issue"
✅ "Account ending in *******89012 has an issue"

❌ "Contact John Smith at john.smith@company.com"
✅ "Contact [Name] at <email>"

❌ "Customer Acme Corp requested..."
✅ "Customer requested..." or "[Customer] requested..."
```

---

## 4. File Protection

### Critical Directories - Extra Caution Required

| Directory | Contains | Protection Level |
|-----------|----------|------------------|
| `/Intelligence/` | Learning database, patterns | 🔴 CRITICAL |
| `/Memory/` | Session memory, logs | 🔴 CRITICAL |
| `/.steering-files/steering/` | Core personality | 🔴 CRITICAL |
| `/Nate's-kb/` root | Protocols | 🟡 IMPORTANT |

### Before Modifying Protected Files

1. **READ** the file first - understand its purpose
2. **ASSESS** - Is this intelligence data? User preferences?
3. **CONFIRM** - Ask before overwriting or deleting
4. **BACKUP** - Consider backup before major changes

### Files That Are IRREPLACEABLE

```
memory.json      - Weeks of learned preferences
patterns.json    - Intelligence database
knowledge.json   - Factual knowledge
Nathaniel.md     - Core personality definition
session-*.md     - Historical context
```

### Safe File Operations

```
✅ Create new files with unique names
✅ Append to existing files
✅ Read before write
✅ Ask before overwrite

❌ Overwrite without reading
❌ Delete without confirmation
❌ Move files blindly
❌ Assume file purpose from name
```

---

## 5. Communication Security

### Sanitize Before Sharing

When drafting emails, documents, or any shareable content:

- [ ] No internal account numbers
- [ ] No customer names (unless appropriate)
- [ ] No internal URLs or endpoints
- [ ] No credential references
- [ ] No internal project codenames

### Response Hygiene

When responding with examples or code:

- [ ] Use placeholder values for sensitive data
- [ ] Anonymize real customer scenarios
- [ ] Remove internal references
- [ ] Check for accidental PII inclusion

---

## Quick Reference

### Git Commit Security Checklist

```
[ ] git add --dry-run shows only safe files
[ ] No Customer-Work/ or internal/ directories
[ ] No .env, .pem, .key files
[ ] No credentials in staged files
[ ] No customer names in documentation
[ ] .gitignore is comprehensive
```

### Security Triggers

| Trigger | Action |
|---------|--------|
| "git add/commit/push" | Execute Git Hardening scan |
| Credential in code | Flag and remove |
| Account number | Mask with *******[last5] |
| Customer name in output | Anonymize or confirm |
| Modifying /Intelligence/ | Read first, confirm before write |

### Emergency Response

If sensitive data was committed:

1. **Don't push** if not already pushed
2. **git reset** to remove from staging
3. **Update .gitignore** to prevent recurrence
4. **If pushed**: Consider git history rewrite (consult user)
5. **Rotate credentials** if any were exposed

---

## Integration with Nathaniel.md

This protocol is triggered by:
- Git operation keywords (stage, commit, push)
- Credential-related discussions
- File operations on protected directories
- PII appearing in context

**Reference**: Nathaniel.md → Git Hardening Protocol section

---

## 6. Data Classification Awareness

Customize this section with your organization's data classification policy.

### Classification Levels

Define sensitivity tiers appropriate to your context. A common framework:

| Level | Name | Impact if Exposed | Example |
|-------|------|-------------------|---------|
| 1 | Public | Little to none | Published docs, marketing materials |
| 2 | Internal | Limited, reversible | Internal wikis, non-sensitive policies |
| 3 | Confidential | Moderate, contained | Architecture diagrams, internal tools |
| 4 | Restricted | Severe | Credentials, PII, financial data |

### Combined Sensitivity Rule

When multiple data elements are combined, overall sensitivity can increase beyond individual elements. A name + an account number = higher classification than either alone. Always assess the *combined* sensitivity, not just individual pieces.

### Nate-Actionable Rules

1. **Before suggesting where to store/share data**: Check your classification limits
2. **When handling sensitive info**: Identify which data type it is, apply corresponding handling rules
3. **When combining data points**: Assess combined sensitivity, not just individual elements
4. **When in doubt**: Treat as one level higher than your best guess

---

*Security is not optional. These practices protect user data, trust, and system integrity.*

---

## 7. External Content Security

**Location**: Always-on behavioral rules in `Nathaniel.md` (kernel), not this protocol.

This protocol is keyword-triggered (loads on "security", "git", "credentials"). External content threats occur during any fetch/research workflow regardless of keywords. Therefore, external content defenses are embedded directly in the kernel as always-on rules.

**What the kernel covers**:
- Detection triggers for prompt injection in fetched content (11 patterns)
- Context compartmentalization (external content = reference data only)
- Bash command restrictions (env/printenv, base64 decode, interpreter one-liners)
- Save hygiene (don't persist preferences derived from external content)
- Markdown image exfiltration prevention

**Fetch proxy**: `scripts/secure-fetch.py` filters URLs at the JSON-RPC protocol level before they reach `mcp-server-fetch`. Blocks private IPs, metadata endpoints, URL shorteners, dangerous ports, and userinfo bypass attempts.

**Full spec**: `Nate's-kb/Growth/defense-in-depth.md`
