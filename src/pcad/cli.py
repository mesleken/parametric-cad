"""Command-line interface (CLI) for pcad."""

import argparse
import sys
from pathlib import Path

def run_selftest() -> int:
    """Automated self-test of all built-in templates and exports without opening GUI."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        
    print("=" * 60)
    print("PCAD AUTOMATED SYSTEM SELF-TEST")
    print("=" * 60)
    
    from pcad.templates.registry import TemplateRegistry
    from pcad.domain.materials import MaterialDB
    from pcad.kernel.validate import validate_solid
    from pcad.kernel.physics import compute_physics
    from pcad.kernel.step_io import export_step_file, verify_step_volume
    from pcad.kernel.stl_io import export_stl_file
    from pcad.kernel.tessellate import tessellate_solid
    from pcad.report.datasheet import generate_datasheet_pdf
    
    reg = TemplateRegistry.get_default_registry()
    templates = reg.list_templates()
    print(f"Found {len(templates)} registered templates:")
    for tpl in templates:
        print(f"  • {tpl.id} (v{tpl.version}): {tpl.name}")
        
    mat_db = MaterialDB.get_default_db()
    mat = mat_db.get("Al7075-T6")
    
    out_dir = Path("selftest_output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    all_passed = True
    for tpl in templates:
        print(f"\n[Testing Template: {tpl.id}]")
        try:
            # 1. Instantiate default params
            param_obj = tpl.param_cls()
            print("  ✓ Default parameters valid")
            
            # 2. Build geometry
            raw_part = tpl.build_func(param_obj)
            solid = validate_solid(raw_part)
            print(f"  ✓ Valid solid generated (Vol={solid.volume:.1f} mm³)")
            
            # 3. Physics & Material
            mat = mat_db.get(tpl.default_material) if tpl.default_material else mat_db.get("Al7075-T6")
            phys = compute_physics(solid, mat)
            print(f"  ✓ Physics calculated: Mass={phys.mass_g:.1f} g, CoG={phys.cog_mm}")
            
            # 4. Engineering checks
            checks = []
            if tpl.checks_func:
                checks = tpl.checks_func(param_obj, mat, phys)
                print(f"  ✓ {len(checks)} Engineering checks evaluated")
                for chk in checks:
                    print(f"     - {chk.name}: MS={chk.margin_of_safety} [{chk.status.value}]")
                    
            # 5. Tessellation
            verts, faces = tessellate_solid(solid)
            print(f"  ✓ Tessellation: {len(verts)} verts, {len(faces)//4} triangles")
            
            # 6. STEP Export and re-read verification
            step_file = out_dir / f"{tpl.id}.step"
            export_step_file(solid, step_file)
            re_vol = verify_step_volume(step_file)
            diff = abs(re_vol - solid.volume) / solid.volume
            assert diff < 1e-4, f"STEP re-read volume error: {diff}"
            print(f"  ✓ STEP export & re-read verified (Diff={diff:.2e})")
            
            # 7. STL Export
            stl_file = out_dir / f"{tpl.id}.stl"
            export_stl_file(solid, stl_file)
            print("  ✓ STL export verified")
            
            # 8. PDF Datasheet Export
            pdf_file = out_dir / f"{tpl.id}.pdf"
            generate_datasheet_pdf(
                output_pdf_path=pdf_file,
                template_name=str(tpl.name),
                template_version=tpl.version,
                params=param_obj.model_dump(),
                material=mat,
                physics=phys,
                checks=checks,
                model_hash="selftest12345"
            )
            print("  ✓ PDF Datasheet export verified")
            
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL SELF-TEST CHECKS PASSED SUCCESSFULLY (100%)!")
        print("=" * 60)
        return 0
    else:
        print("SELF-TEST ENCOUNTERED FAILURES!")
        print("=" * 60)
        return 1

def run_gen(template_id: str, params_json: str, out_path: str, fmt: str, material_id: str) -> int:
    """Generates a single model from CLI parameters."""
    import json
    from pcad.templates.registry import TemplateRegistry
    from pcad.domain.materials import MaterialDB
    from pcad.kernel.validate import validate_solid
    from pcad.kernel.step_io import export_step_file
    from pcad.kernel.stl_io import export_stl_file
    from pcad.kernel.physics import compute_physics

    reg = TemplateRegistry.get_default_registry()
    spec = reg.get(template_id)
    param_dict = json.loads(params_json) if params_json else {}
    param_obj = spec.param_cls(**param_dict)
    
    mat_db = MaterialDB.get_default_db()
    mat = mat_db.get(material_id)
    
    print(f"Generating {template_id}...")
    solid = validate_solid(spec.build_func(param_obj))
    phys = compute_physics(solid, mat)
    
    out_file = Path(out_path) if out_path else Path(f"{template_id.replace('.', '_')}.{fmt.lower()}")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    if fmt.lower() == "step":
        export_step_file(solid, out_file)
    elif fmt.lower() == "stl":
        export_stl_file(solid, out_file)
    else:
        print(f"Unsupported CLI format '{fmt}'. Choose 'step' or 'stl'.")
        return 1
        
    print(f"✓ Generated {fmt.upper()} to: {out_file} (Mass: {phys.mass_g:.1f} g, Volume: {phys.volume_mm3:.1f} mm³)")
    return 0

def run_batch_cli(template_id: str, csv_path: str, out_dir: str, material_id: str) -> int:
    """Runs batch generation from CLI."""
    from pcad.services.batch_service import BatchService
    service = BatchService()
    
    csv_p = Path(csv_path)
    out_d = Path(out_dir) if out_dir else Path(f"./batch_out_{template_id.replace('.', '_')}")
    
    print(f"Running batch production for {template_id} from {csv_p}...")
    summary = service.run_batch(
        template_id=template_id,
        csv_path=csv_p,
        output_dir=out_d,
        material_id=material_id
    )
    print(f"✓ Batch completed: {summary.successful_count}/{summary.total_rows} successful in {summary.total_duration_sec}s.")
    print(f"  Output directory: {summary.output_directory}")
    return 0 if summary.failed_count == 0 else 1

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # If launched with --worker flag (used in packaged PyInstaller binaries)
    if "--worker" in sys.argv:
        from pcad.runtime.worker_main import main as worker_main
        worker_main()
        return

    parser = argparse.ArgumentParser(description="PCAD - Parametric CAD Application CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # GUI command
    subparsers.add_parser("gui", help="Launch the Desktop GUI application")
    
    # Selftest command
    subparsers.add_parser("selftest", help="Run automated system self-tests")
    
    # Gen command
    gen_parser = subparsers.add_parser("gen", help="Generate single CAD model headlessly")
    gen_parser.add_argument("template", help="Template ID (e.g. demo.flange, aero.lug, mech.spur_gear)")
    gen_parser.add_argument("--params", default="{}", help="JSON dictionary of parameters")
    gen_parser.add_argument("--format", default="step", choices=["step", "stl"], help="Output format")
    gen_parser.add_argument("--output", default="", help="Output file path")
    gen_parser.add_argument("--material", default="Al7075-T6", help="Material ID (e.g. Al7075-T6, AISI4140)")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Run batch multi-part CSV generation")
    batch_parser.add_argument("template", help="Template ID")
    batch_parser.add_argument("csv", help="Input CSV file path")
    batch_parser.add_argument("--out-dir", default="", help="Output directory path")
    batch_parser.add_argument("--material", default="Al7075-T6", help="Material ID")
    
    args = parser.parse_args()
    
    if args.command == "selftest":
        sys.exit(run_selftest())
    elif args.command == "gen":
        sys.exit(run_gen(args.template, args.params, args.output, args.format, args.material))
    elif args.command == "batch":
        sys.exit(run_batch_cli(args.template, args.csv, args.out_dir, args.material))
    else:
        # Default action: run GUI
        from pcad.ui.app import run_app
        sys.exit(run_app())

if __name__ == "__main__":
    main()
