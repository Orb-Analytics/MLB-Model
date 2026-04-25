# Legacy Root Scripts Archive

This folder contains the original Python scripts that were previously located in the repository root directory.

## Purpose

These scripts have been **moved** (not deleted) to the new organized structure under `scripts/` but are kept here temporarily as a safety net during the transition.

## Current Organization

All scripts have been organized into:
- `scripts/etl/fetch/` - API fetching scripts
- `scripts/etl/compute/` - Data computation scripts
- `scripts/etl/consolidate/` - Data consolidation scripts
- `scripts/etl/join/` - Data joining/merging scripts
- `scripts/etl/builders/` - Dataset building scripts
- `scripts/etl/alignment/` - Data alignment scripts
- `scripts/etl/rebuild/` - Dataset rebuild scripts
- `scripts/exploration/` - Testing/exploration scripts
- `scripts/utilities/` - Utility scripts

## How to Restore (If Needed)

If you need to restore the old structure:

```bash
# Move all scripts back to root
cd /workspaces/MLB-Model
cp archive/legacy-root-scripts/*.py .

# Revert etl.py to use old paths
git checkout HEAD~1 etl.py
```

## When to Delete This Folder

Once we've confirmed that:
1. The daily ETL pipeline runs successfully with the new structure
2. All prediction workflows work correctly
3. No path errors occur

Then this archive can be safely deleted.

**Do not delete before confirming everything works!**

---

📅 Archived: April 25, 2026
📦 Contains: 81 Python scripts
