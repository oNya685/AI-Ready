"""
TEMPLATE: Scientific Data Parser
INSTRUCTION FOR AGENT:
1. Copy this code. DO NOT run in chunks.
2. Install necessary pip packages if needed before running.
3. Implement `parse_file`.
4. CRITICAL: Any unexpected metadata, unmapped keys, or unrecognized lines MUST be logged via `report_unparsed()`.
"""
import os
import json
import sys
# import h5py, netCDF4, etc. as needed

INPUT_PATH = "YOUR_INPUT_FILE"
OUTPUT_JSONL = "output_scientific.jsonl"
OUTPUT_MD = "output_scientific.md"

unparsed_warnings = []

def report_unparsed(location, content):
    """Call this when you find data/metadata that doesn't fit the expected schema."""
    warning_msg = f"[UNPARSED_WARNING] File: {INPUT_PATH}, Loc: {location}, Content: {content}"
    print(warning_msg, file=sys.stderr)
    unparsed_warnings.append(warning_msg)

def parse_file(filepath):
    """
    Agent: Implement your parsing logic here.
    Return a list of dictionary records.
    """
    records = []

    # EXAMPLE LOGIC FOR A CUSTOM TEXT FILE:
    # with open(filepath, 'r', encoding='utf-8') as f:
    #     for line_num, line in enumerate(f, 1):
    #         line = line.strip()
    #         if not line:
    #             continue
    #
    #         if line.startswith("DATA:"):
    #             # handle data
    #             pass
    #         elif line.startswith("META:"):
    #             # handle known metadata
    #             pass
    #         else:
    #             # Trigger warning for unknown lines!
    #             report_unparsed(f"Line {line_num}", line)

    return records

def generate_markdown(records):
    """Convert parsed records to AI-Ready Markdown format."""
    md_sections = [f"# Scientific Data Parsing Results\n**Source File**: {os.path.basename(INPUT_PATH)}\n---\n"]

    for i, rec in enumerate(records, 1):
        md_sections.append(f"## Record {i}\n")
        for key, value in rec.items():
            if key == "text":
                md_sections.append(f"{value}\n")
            elif isinstance(value, dict):
                md_sections.append(f"**{key}**:\n")
                for k, v in value.items():
                    md_sections.append(f"- {k}: {v}\n")
            else:
                md_sections.append(f"**{key}**: {value}\n")
        md_sections.append("---\n")

    return "".join(md_sections)

def main():
    print(f"[INFO] Starting to parse {INPUT_PATH}...")
    try:
        records = parse_file(INPUT_PATH)
    except Exception as e:
        print(f"[FATAL] Exception during parsing: {e}")
        sys.exit(1)

    if unparsed_warnings:
        print(f"\n[ATTENTION AGENT] Found {len(unparsed_warnings)} unparsed elements!")
        print("Please review the stderr output. If these elements contain valuable scientific context (like remarks, anomalous readings, or equipment settings), REWRITE the script to extract them properly.")
        sys.exit(2)  # Exit with error code to halt pipeline and force Agent to think

    # If successful and no warnings, save to JSONL
    print(f"[INFO] Parsing clean. Saving {len(records)} records...")

    # Save JSONL
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f"[SUCCESS] Saved JSONL to {OUTPUT_JSONL}")

    # Save Markdown
    md_content = generate_markdown(records)
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"[SUCCESS] Saved Markdown to {OUTPUT_MD}")

    print(f"[SUCCESS] AI-Ready data generated at {OUTPUT_JSONL} and {OUTPUT_MD}")

if __name__ == "__main__":
    main()