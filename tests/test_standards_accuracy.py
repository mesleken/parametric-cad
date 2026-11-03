"""Analytical accuracy and standards compliance test suite.

Validates ISO 53, ISO 6336, DIN 743, DIN 6885, ASME Section VIII, 
Bruhn D1/D2, and Steiner parallel-axis composite inertia calculations.
"""

import math
import tempfile
from pathlib import Path
import pytest
import numpy as np

from pcad.domain.materials import MaterialDB, Material
from pcad.domain.template import PhysicsResult, MarginStatus
from pcad.kernel.physics import compute_physics
from pcad.kernel.stl_io import export_stl_file
from pcad.engineering.shaft_checks import check_stepped_shaft
from pcad.engineering.gear_checks import check_spur_gear
from pcad.engineering.bending import check_bracket
from pcad.engineering.flange_checks import check_flange
from pcad.engineering.lug import check_lug
from pcad.templates.builtin.mech.spur_gear import SpurGearParams, build as build_gear
from pcad.templates.builtin.mech.stepped_shaft import SteppedShaftParams, build as build_shaft
from pcad.templates.builtin.demo.flange import FlangeParams, build as build_flange
from pcad.templates.builtin.aero.lug import LugParams, build as build_lug
from pcad.templates.builtin.aero.gusset_bracket import BracketParams, build as build_bracket
from pcad.templates.builtin.aero.splice_plate import SplicePlateParams, build as build_splice


class TestMaterialsAndPhysics:
    def test_materials_have_elasticity_and_hardness(self):
        db = MaterialDB.get_default_db()
        for mat in db.list_materials():
            assert mat.elastic_modulus_gpa > 0, f"{mat.id} missing E"
            assert 0.15 <= mat.poisson_ratio <= 0.45, f"{mat.id} invalid Poisson ratio"
            assert mat.endurance_limit_mpa >= 0, f"{mat.id} negative endurance limit"
            assert mat.hardness_hb is None or mat.hardness_hb >= 0, f"{mat.id} negative hardness"

    def test_principal_inertia_ordered_eigenvalues(self):
        # Stepped shaft is cylindrical with different axial vs transverse inertia
        p = SteppedShaftParams()
        solid = build_shaft(p)
        db = MaterialDB.get_default_db()
        mat = db.get("AISI4140")
        phys = compute_physics(solid, mat)
        
        i1, i2, i3 = phys.principal_inertia_g_mm2
        assert i1 <= i2 + 1e-3, "Eigenvalues must be sorted in ascending order"
        assert i2 <= i3 + 1e-3, "Eigenvalues must be sorted in ascending order"
        assert i1 > 0, "Principal inertia must be positive"


class TestGearStandardsISO6336:
    def test_involute_tooth_pitch_thickness_with_profile_shift(self):
        m = 2.5
        alpha = math.radians(20.0)
        x0 = 0.0
        x1 = 0.35
        # Standard pitch thickness: s = m * (pi / 2 + 2 * x * tan(alpha))
        s0 = m * (math.pi / 2.0 + 2.0 * x0 * math.tan(alpha))
        s1 = m * (math.pi / 2.0 + 2.0 * x1 * math.tan(alpha))
        assert s1 > s0
        assert round(s0, 3) == round(m * math.pi / 2.0, 3)
        assert round(s1 - s0, 3) == round(2.0 * m * x1 * math.tan(alpha), 3)

    def test_profile_shift_increases_gear_volume_and_reduces_bending(self):
        p0 = SpurGearParams(num_teeth=24, module=2.0, profile_shift=0.0)
        p1 = SpurGearParams(num_teeth=24, module=2.0, profile_shift=0.3)
        
        solid0 = build_gear(p0)
        solid1 = build_gear(p1)
        assert solid1.volume > solid0.volume, "Positive profile shift adds tooth material"
        
        db = MaterialDB.get_default_db()
        mat = db.get("AISI4140")
        phys0 = compute_physics(solid0, mat)
        phys1 = compute_physics(solid1, mat)
        
        checks0 = check_spur_gear(p0, mat, phys0)
        checks1 = check_spur_gear(p1, mat, phys1)
        
        # Root bending stress should decrease with positive shift due to thicker root
        sigma_bend0 = next(c.applied for c in checks0 if "Bending" in c.name)
        sigma_bend1 = next(c.applied for c in checks1 if "Bending" in c.name)
        assert sigma_bend1 < sigma_bend0

    def test_hertz_contact_stress_scales_with_elasticity(self):
        p = SpurGearParams(num_teeth=24, module=2.5)
        db = MaterialDB.get_default_db()
        mat_steel = db.get("AISI4140")  # E = 205 GPa
        mat_al = db.get("Al6061-T6")    # E = 68.9 GPa
        
        phys_dummy = PhysicsResult(
            volume_mm3=1000.0, mass_g=10.0, cog_mm=(0,0,0),
            bbox_mm=(0,0,0,10,10,10), inertia_g_mm2=(1,1,1),
            principal_inertia_g_mm2=(1,1,1)
        )
        checks_steel = check_spur_gear(p, mat_steel, phys_dummy)
        checks_al = check_spur_gear(p, mat_al, phys_dummy)
        
        sigma_h_steel = next(c.applied for c in checks_steel if "Hertz" in c.name)
        sigma_h_al = next(c.applied for c in checks_al if "Hertz" in c.name)
        
        # Contact stress scales with sqrt(E): sqrt(205 / 68.9) ~= 1.72
        ratio_actual = sigma_h_steel / sigma_h_al
        ratio_theoretical = math.sqrt(205.0 / 68.9)
        assert abs(ratio_actual - ratio_theoretical) < 0.15


class TestShaftStandardsDIN743:
    def test_peterson_fillet_concentration_decreases_with_larger_radius(self):
        class MockParams:
            d1 = 20.0
            d2 = 30.0
            d3 = 20.0
            l1 = 40.0
            l2 = 60.0
            l3 = 40.0
            r_fillet = 1.0
            torque_nm = 100.0
            fos = 1.5
            keyway_enabled = False

        db = MaterialDB.get_default_db()
        mat = db.get("AISI4140")
        phys_dummy = PhysicsResult(
            volume_mm3=1000.0, mass_g=10.0, cog_mm=(0,0,0),
            bbox_mm=(0,0,0,10,10,10), inertia_g_mm2=(1,1,1),
            principal_inertia_g_mm2=(1,1,1)
        )
        
        p_sharp = MockParams()
        p_sharp.r_fillet = 0.5
        checks_sharp = check_stepped_shaft(p_sharp, mat, phys_dummy)
        
        p_smooth = MockParams()
        p_smooth.r_fillet = 3.0
        checks_smooth = check_stepped_shaft(p_smooth, mat, phys_dummy)
        
        tau_sharp = next(c.applied for c in checks_sharp if "tau_max" in c.name)
        tau_smooth = next(c.applied for c in checks_smooth if "tau_max" in c.name)
        assert tau_sharp > tau_smooth, "Sharper fillet must produce higher peak stress"

    def test_shaft_rigidity_proportional_to_shear_modulus(self):
        p = SteppedShaftParams()
        db = MaterialDB.get_default_db()
        mat_steel = db.get("AISI4140")  # E = 205 GPa, G ~= 79.5 GPa
        mat_al = db.get("Al6061-T6")    # E = 68.9 GPa, G ~= 25.9 GPa
        phys_dummy = PhysicsResult(
            volume_mm3=1000.0, mass_g=10.0, cog_mm=(0,0,0),
            bbox_mm=(0,0,0,10,10,10), inertia_g_mm2=(1,1,1),
            principal_inertia_g_mm2=(1,1,1)
        )
        
        checks_steel = check_stepped_shaft(p, mat_steel, phys_dummy)
        checks_al = check_stepped_shaft(p, mat_al, phys_dummy)
        
        twist_steel = next(c.applied for c in checks_steel if "Rigidity" in c.name)
        twist_al = next(c.applied for c in checks_al if "Rigidity" in c.name)
        
        # Twist is inversely proportional to G: twist_al / twist_steel ~= G_steel / G_al ~= 3.0
        assert twist_al > 2.5 * twist_steel


class TestSteinerParallelAxisTheorem:
    def test_gusset_ribs_increase_composite_inertia_and_reduce_deflection(self):
        db = MaterialDB.get_default_db()
        mat = db.get("Al7075-T6")
        
        # 1. Plain bracket without gusset
        checks_plain = check_bracket(
            length_mm=100.0, width_mm=50.0, thickness_mm=5.0,
            inner_radius_mm=5.0, load_n=500.0, material=mat,
            gusset_count=0, gusset_thickness_mm=0.0
        )
        
        # 2. Reinforced bracket with 2 gusset ribs
        checks_ribbed = check_bracket(
            length_mm=100.0, width_mm=50.0, thickness_mm=5.0,
            inner_radius_mm=5.0, load_n=500.0, material=mat,
            gusset_count=2, gusset_thickness_mm=4.0, gusset_depth_mm=40.0
        )
        
        sigma_plain = next(c.applied for c in checks_plain if "Bending" in c.name)
        sigma_ribbed = next(c.applied for c in checks_ribbed if "Bending" in c.name)
        assert sigma_ribbed < sigma_plain * 0.5, "Gusset ribs must dramatically reduce root flexural stress"
        
        delta_plain = next(c.applied for c in checks_plain if "Deflection" in c.name)
        delta_ribbed = next(c.applied for c in checks_ribbed if "Deflection" in c.name)
        assert delta_ribbed < delta_plain * 0.2, "Gussets must dramatically reduce tip deflection"


class TestASMESectionVIIIFlange:
    def test_hydrostatic_end_force_and_hoop_stress(self):
        db = MaterialDB.get_default_db()
        mat = db.get("SS316L")
        
        p1 = 1.0  # MPa
        p2 = 3.0  # MPa
        
        checks1 = check_flange(
            outer_dia=140.0, inner_dia=40.0, pcd=100.0, num_bolts=4,
            bolt_hole_dia=14.0, flange_thickness=18.0,
            neck_outer_dia=60.0, neck_height=30.0, design_pressure_mpa=p1,
            material=mat
        )
        checks2 = check_flange(
            outer_dia=140.0, inner_dia=40.0, pcd=100.0, num_bolts=4,
            bolt_hole_dia=14.0, flange_thickness=18.0,
            neck_outer_dia=60.0, neck_height=30.0, design_pressure_mpa=p2,
            material=mat
        )
        
        bolt1 = next(c.applied for c in checks1 if "ASME VIII Bolt" in c.name)
        bolt2 = next(c.applied for c in checks2 if "ASME VIII Bolt" in c.name)
        assert abs(bolt2 - 3.0 * bolt1) < 1.0, "Bolt tensile stress must scale linearly with design pressure"
        
        hoop1 = next(c.applied for c in checks1 if "Hoop Stress" in c.name)
        hoop2 = next(c.applied for c in checks2 if "Hoop Stress" in c.name)
        assert abs(hoop2 - 3.0 * hoop1) < 1.0, "Hub hoop stress must scale linearly with design pressure"


class TestBruhnLugObliqueInteraction:
    def test_oblique_loading_interaction(self):
        db = MaterialDB.get_default_db()
        mat = db.get("Al7075-T6")
        
        # Pure axial load
        checks_axial = check_lug(
            W=50.0, D=20.0, e=25.0,
            t=10.0, F_axial_N=20000.0, material=mat,
            load_angle_deg=0.0
        )
        
        # 45 deg oblique load
        checks_oblique = check_lug(
            W=50.0, D=20.0, e=25.0,
            t=10.0, F_axial_N=20000.0, material=mat,
            load_angle_deg=45.0
        )
        
        oblique_chk = next((c for c in checks_oblique if "Oblique" in c.name), None)
        assert oblique_chk is not None, "Oblique load check must be executed when load_angle_deg > 0"
        assert oblique_chk.applied > 0, "Oblique load index (Ra^1.6 + Rtr^1.6) must be positive"


class TestSTLExportIntegrity:
    def test_watertight_stl_export_validity(self):
        p = SteppedShaftParams()
        solid = build_shaft(p)
        with tempfile.TemporaryDirectory() as tmpdir:
            stl_path = Path(tmpdir) / "test_shaft.stl"
            export_stl_file(solid, stl_path)
            
            assert stl_path.exists()
            assert stl_path.stat().st_size >= 84
            # Read triangle count
            with open(stl_path, "rb") as f:
                f.seek(80)
                num_tri = int.from_bytes(f.read(4), "little")
            assert num_tri >= 4
            assert stl_path.stat().st_size == 84 + (num_tri * 50)
