# Repository Reorganization Prompt

Copy and paste this into Copilot Chat in any repository that needs reorganization:

---

## PROMPT:

I need help reorganizing my repository to clean up the root directory and create a logical folder structure. **IMPORTANT: I need this done safely with full rollback capability in case something breaks.**

### Requirements:

1. **Analyze Current Structure**
   - Count how many files are in the root directory
   - Identify what types of scripts/files exist
   - Find all path dependencies (grep for imports, subprocess calls, workflow references)

2. **Create Reorganization Proposal**
   - Propose a new folder structure organized by function
   - Show me what files would go where
   - Identify which files should stay in root (like main entry points)
   - List all files/paths that need updating
   - Wait for my approval before proceeding

3. **Safe Migration Process** (Option A approach)
   - Create new directory structure
   - COPY files to new locations (don't move yet)
   - Update all path references in:
     - Main scripts that call other scripts
     - GitHub workflows (.github/workflows/*.yml)
     - Any internal script dependencies
   - Test/validate syntax of updated files
   - Commit changes with originals still intact

4. **Archive for Rollback**
   - Move (don't delete) old files to `archive/legacy-root-scripts/`
   - Create a detailed README in archive with restoration instructions
   - Use git rename tracking so history is preserved
   - Final commit and push

5. **Safety Checks**
   - Verify all workflows only reference paths that still exist
   - Check that main entry points work with new structure
   - Ensure data paths are unchanged (no risk to actual data)
   - Confirm easy rollback is possible

### Things NOT to Change:
- Data directory paths
- Any directories that are already well-organized
- Main entry point files (they can stay in root)
- .gitignore patterns (but work around them if needed)

### Output I Need:
1. Initial analysis and proposal (for my review)
2. Step-by-step progress updates
3. Clear summary of what changed
4. Verification that all workflows/scripts will work
5. Instructions for monitoring after deployment

### Note on .gitignore:
If you encounter directories that are ignored by .gitignore (like `build/`), rename them (e.g., `builders/`) to avoid conflicts.

Please start by analyzing my repository structure and creating a proposal for me to review before making any changes.

---

## Alternative: Quick Start for Simple Repos

If you have a simpler repository and want faster results, use this shorter version:

---

I have too many files in my root directory. Please:

1. **Analyze** - Show me how many files are in root and what types
2. **Propose** - Suggest organized folders (by function: scripts/utils/, scripts/etl/, etc.)
3. **List dependencies** - Find all path references in workflows and scripts
4. **Execute safely**:
   - Create new folders
   - Copy (not move) files to new locations  
   - Update all path references
   - Move originals to `archive/` (not delete)
   - Commit in 2 phases: (1) with originals intact, (2) after moving to archive

Use the "Option A - Safe & Comprehensive" approach. Don't delete anything - I want the ability to rollback if needed.

---

