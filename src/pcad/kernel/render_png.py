"""Headless off-screen rendering for clean PNG screenshots and datasheet visuals."""

from pathlib import Path
import numpy as np
import pyvista as pv

def render_mesh_to_png(
    verts: np.ndarray,
    faces: np.ndarray,
    output_png_path: Path,
    image_size: tuple = (1200, 900),
    color: str = "#B0C4DE"
) -> Path:
    """Renders a 3D mesh off-screen and writes high-resolution PNG."""
    output_png_path = Path(output_png_path)
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    
    mesh = pv.PolyData(verts, faces)
    
    plotter = pv.Plotter(off_screen=True, window_size=image_size)
    plotter.set_background("#F8F9FA", top="#E9ECEF") # Subtle clean gradient
    
    # Add mesh with visible feature edges
    plotter.add_mesh(
        mesh,
        color=color,
        smooth_shading=True,
        show_edges=True,
        edge_color="#343A40",
        line_width=1.0,
        specular=0.4,
        specular_power=15
    )
    
    # Set isometric camera
    plotter.camera_position = "iso"
    plotter.reset_camera()
    plotter.camera.zoom(1.15)
    
    plotter.screenshot(str(output_png_path))
    plotter.close()
    
    return output_png_path
