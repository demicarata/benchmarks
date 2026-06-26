import json, re, sys
from pathlib import Path
from collections import OrderedDict

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

def _strip_header_macros(text, keep):
    out = []
    i = 0
    pat = re.compile(
        r"(?P<lead>(?:^[ \t]*//[^\n]*\n)*)"                       
        r"(?P<macro>^[ \t]*macro\s+(?P<name>\w+)\s*\([^)]*\).*?\{.*?\})",
        re.DOTALL | re.MULTILINE,
    )
    for m in pat.finditer(text):
        out.append(text[i:m.start()])
        if m.group("name") in keep:
            out.append(m.group("lead"))    
            out.append(m.group("macro"))
        i = m.end()
    out.append(text[i:])                    
    return "".join(out)
  


def _pip_section(detected_variants):
    sections = ["// ── pip_reg_overwrite ──"]

    if not _PIP_HEADER_PATH.exists():
        sections.append(f"// WARNING: pipeline header not found at {_PIP_HEADER_PATH}")
        return sections
    
    header = _strip_header_macros(_PIP_HEADER_PATH.read_text(), keep={"advance_pipeline"})
    sections.append(header.strip())
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

_MACRO_RE = re.compile(
    r"macro\s+(?P<name>\w+)\s*"          # macro name
    r"\((?P<params>[^)]*)\)"             # (params)
    r"(?P<decls>.*?)"                    # optional pre-brace declarations
    r"\{(?P<body>.*?)\}",               # { body }
    re.DOTALL,
)
 
 
def _render_macro(mac):
    header = f"macro {mac['name']}({mac['params']})"
    if mac["decls"]:
        header += f"\n    {mac['decls']}"
    inner = "\n".join(b.strip("\n") for b in mac["bodies"])
    return f"{header}\n{{\n{inner}\n}}"
 
 
def _merge_into(registry, text):
    
    for m in _MACRO_RE.finditer(text):
        name = m.group("name")
        if name in registry:
            registry[name]["bodies"].append(m.group("body"))
        else:
            registry[name] = {
                "name": name,
                "params": m.group("params").strip(),
                "decls": m.group("decls").strip(),
                "bodies": [m.group("body")],
            }


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
    macro_registry = OrderedDict()  # shared across templates; same names get merged
 
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
        _merge_into(macro_registry, path.read_text())
        included.append(key)
 
    # Emit merged macros (same-named macros from multiple templates combined)
    for mac in macro_registry.values():
        sections.append(_render_macro(mac))
        sections.append("")
 
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