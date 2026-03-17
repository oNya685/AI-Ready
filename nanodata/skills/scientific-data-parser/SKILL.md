---
name: scientific-data-parser
description: Parse specialized scientific data formats (e.g., HDF5, NetCDF, FITS, mzML, CIF, PDB) or unfamiliar raw data files. Use when the user wants to process complex scientific files into AI-Ready formats.
---

# Scientific Data Parsing SOP

Scientific data often contains a mix of structured numerical arrays and unstructured metadata/remarks. Follow this workflow to ensure ZERO data loss.

## Phase 1: Exploration & Dependency Management
1. **Never use `read_file` on raw data.**
2. **Text vs Binary**:
   - For text-based formats (CIF, PDB, XML, JSON, CSV, unfamiliar txt): Use the `read_file_lines` tool (e.g., lines 1-100) to understand the schema and locate metadata blocks.
   - For binary formats (HDF5 `.h5`, NetCDF `.nc`, FITS `.fits`), do NOT read them as text.
3. **Install Dependencies**: If the format requires a specific library, use `python_exec` to install it first.
   - HDF5 -> `!pip install h5py`
   - NetCDF -> `!pip install netCDF4`
   - FITS/Astronomy -> `!pip install astropy`
   - Crystallography (CIF) -> `!pip install pymatgen`

## Phase 2: Parser Script Generation with Strict Feedback Loop
When writing the Python parsing script (via `python_exec`), you must adhere to the **Zero Data Loss Rule**:
1. Read `skills/scientific-data-parser/scripts/template_science.py` for the standard architecture.
2. Your script must proactively catch any unparsed items, unmatched regex groups, or trailing metadata/remarks.
3. **Raise Warnings**: If the script finds extra columns, floating text, or undocumented metadata, it MUST print a warning to `stderr` or `stdout` in this format:
   `[UNPARSED_WARNING] File: <path>, Line/Key: <location>, Content: <content>`

## Phase 3: Evaluate & Iterate
1. After running the script, carefully read the output from `python_exec`.
2. If you see `[UNPARSED_WARNING]`, it means your script missed valuable scientific context.
3. **Self-Correction**: Rewrite the script to explicitly extract those missed items, map them to appropriate JSON fields (like `metadata` or `operator_notes`), and run it again until no warnings are generated.
4. Output the final data using the standard dual-output format (.md and .jsonl).