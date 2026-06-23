import json, sys
from pathlib import Path

_SCRIPTS       = Path(__file__).resolve().parent
_SCVERIF_MODELS = _SCRIPTS.parent.parent / "scVerifModels"
_PIP_HEADER_PATH = _SCVERIF_MODELS / "pipelineRegisterOverwrite" / "leakage_model_pipRegOver.il"

def _parse_pip_variant(variant):
    left, right = variant.split("x")
    return left[2:], right[2:]  # strip 'op'

def _pip_variant_macro(variant):
    op1, op2 = _parse_pip_variant(variant)
    macro_name = f"pip_{variant}"
    return (
        f"macro {macro_name}(w32 dst, w32 src)\n"
        f"{{\n"
        f"    advance_pipeline(dst, src);\n"
        f"    leak pip({op1} ^w32 {op2});\n"
        f"}}"
    )
def _pip_section(detected_variants):
    sections = ["// ── pip_reg_overwrite ──"]
 
    if not _PIP_HEADER_PATH.exists():
        sections.append(f"// WARNING: pipeline header not found at {_PIP_HEADER_PATH}")
        return sections
 
    sections.append(_PIP_HEADER_PATH.read_text().strip())
    sections.append("")
 
    for variant in detected_variants:
        sections.append(_pip_variant_macro(variant))
        sections.append("")
 
    # eors2_leak calls all detected variants
    calls = "\n".join(f"    pip_{v}(dst, src);" for v in detected_variants)
    sections.append(
        f"macro eors2_leak(w32 dst, w32 src)\n"
        f"{{\n"
        f"{calls}\n"
        f"}}"
    )
    sections.append("")
 
    return sections

def _leakage_detected(entry):
    cpa = entry.get("cpa", {}).get("leakage_detected", False)
    tvla = entry.get("tvla", {}).get("leakage_detected", False)

    return cpa or tvla

def generate_il(report):
    device  = report.get("device", "unknown")
    effects = report.get("effects", {})
 
    sections = [
        f"// scVerif leakage model — device: {device}",
        "",
    ]
 
    included = []
    skipped  = []
    pip_variants = []
 
    for key, entry in effects.items():
        if not _leakage_detected(entry):
            skipped.append(key)
            continue

        if key.startswith("pip_reg_overwrite/"):
            variant = key.split("/", 1)[1]
            pip_variants.append(variant)
            included.append(key)
            continue
 
        if key == "mem_remnant":
            path = _SCVERIF_MODELS / "memoryRemnant" / "leakage_model_memRem.il"
        elif key == "reg_overwrite":
            path = _SCVERIF_MODELS / "registerOverwrite" / "leakage_model_regOver.il"
        else:
            sections.append(f"// WARNING: unknown effect '{key}', skipping")
            skipped.append(key)
            continue

        if not path.exists():
            sections.append(f"// WARNING: template not found for '{key}': {path}")
            skipped.append(key)
            continue

 
        sections.append(f"// ── {key} ──")
        sections.append(path.read_text().strip())
        sections.append("")
        included.append(key)

    if pip_variants:
        sections.extend(_pip_section(pip_variants))

 
    if not included:
        sections.append("// No leakage detected for any effect — model is empty.")
 
    if skipped:
        sections.append("// Effects skipped (no leakage detected or template missing):")
        for k in skipped:
            sections.append(f"// {k}")
 
    return "\n".join(sections)


def main():
    if len(sys.argv) < 2:
        print("Usage: python leakage_model.py <report.json> [output.il]")
        sys.exit(1)

    report_path = Path(sys.argv[1])
    report      = json.loads(report_path.read_text())
    il          = generate_il(report)
 
    if len(sys.argv) >= 3:
        out = Path(sys.argv[2])
        out.write_text(il)
        print(f"Written to {out}")
    else:
        print(il)


if __name__ == "__main__":
   main()