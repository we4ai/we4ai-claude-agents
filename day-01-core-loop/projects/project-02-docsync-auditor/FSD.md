# 📐 Functional Specification Document (FSD)
## DocSync Auditor

---

## 1. Dynamic Sizing & Discovery Algorithm

```python
def calculate_docsync_budget(target_dir: str) -> tuple[int, float, str]:
    """
    Computes dynamic turns and budget ceiling based on document & code density.
    """
    md_files = glob.glob(os.path.join(target_dir, "**/*.md"), recursive=True)
    py_files = glob.glob(os.path.join(target_dir, "**/*.py"), recursive=True)
    total_files = len(md_files) + len(py_files)

    if total_files <= 5:
        return (8, 0.15, "TIER 1 (Focused Package)")
    elif total_files <= 20:
        return (18, 0.50, "TIER 2 (Standard Repository)")
    else:
        return (30, 2.00, "TIER 3 (Monorepo / Multi-Package)")
```

---

## 2. Parity Scorecard Schema

The agent yields findings structured into a Drift Scorecard:

```markdown
### 📚 DocSync Parity Scorecard

| Documentation File | Source Code File | Symbol / Function | Drift Classification | Actionable Recommendation |
|---|---|---|---|---|
| `README.md` | `testing.py` | `calculate_average` | Verified ✅ | Document matches implementation. |
| `API_GUIDE.md` | `testing.py` | `get_user_name` | Stale Parameter ⚠️ | Doc mentions string input; implementation expects user dict. |
```
