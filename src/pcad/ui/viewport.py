"""3D CAD Viewport widget wrapping PyVistaQt."""

from pathlib import Path
from typing import Optional
import numpy as np
from PySide6 import QtCore, QtWidgets
import pyvista as pv
from pyvistaqt import QtInteractor

class CadViewport(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Top Mini-Toolbar for Camera Views
        view_bar = QtWidgets.QToolBar(self)
        view_bar.setIconSize(QtCore.QSize(16, 16))
        
        btn_iso = view_bar.addAction("Iso")
        btn_iso.triggered.connect(self.view_isometric)
        
        btn_top = view_bar.addAction("Top")
        btn_top.triggered.connect(self.view_top)
        
        btn_front = view_bar.addAction("Front")
        btn_front.triggered.connect(self.view_front)
        
        btn_right = view_bar.addAction("Right")
        btn_right.triggered.connect(self.view_right)
        
        view_bar.addSeparator()
        btn_fit = view_bar.addAction("Fit View")
        btn_fit.triggered.connect(self.fit_view)
        
        self.action_wireframe = view_bar.addAction("Wireframe")
        self.action_wireframe.setCheckable(True)
        self.action_wireframe.toggled.connect(self.toggle_wireframe)
        
        layout.addWidget(view_bar)
        
        # 2. Main 3D Interactor Canvas
        self.plotter = QtInteractor(self)
        self.plotter.set_background("#F8F9FA", top="#E2E8F0") # Subtle gradient
        self.plotter.add_axes()
        layout.addWidget(self.plotter)
        
        self._current_mesh_actor = None
        self._current_mesh = None

    def load_mesh_from_npz(self, npz_path: str):
        path = Path(npz_path)
        if not path.exists():
            return
            
        try:
            data = np.load(str(path))
            verts = data["verts"]
            faces = data["faces"]
            
            mesh = pv.PolyData(verts, faces)
            self._current_mesh = mesh
            
            # Remove old actor if present
            if self._current_mesh_actor is not None:
                try:
                    self.plotter.remove_actor(self._current_mesh_actor)
                except Exception:
                    pass
                
            style = "wireframe" if self.action_wireframe.isChecked() else "surface"
            self._current_mesh_actor = self.plotter.add_mesh(
                mesh,
                name="current_cad_mesh",
                color="#A0AEC0",
                style=style,
                show_edges=True,
                edge_color="#2D3748",
                line_width=1.0,
                smooth_shading=True,
                specular=0.3,
                specular_power=15,
                reset_camera=True
            )
            self.plotter.reset_camera()
            self.plotter.render()
            self.plotter.update()
        except Exception as e:
            import traceback
            traceback.print_exc()

    def view_isometric(self):
        self.plotter.camera_position = "iso"
        self.fit_view()

    def view_top(self):
        self.plotter.view_xy()
        self.fit_view()

    def view_front(self):
        self.plotter.view_xz()
        self.fit_view()

    def view_right(self):
        self.plotter.view_yz()
        self.fit_view()

    def fit_view(self):
        self.plotter.reset_camera()
        self.plotter.camera.zoom(1.1)
        self.plotter.render()

    def toggle_wireframe(self, enabled: bool):
        if self._current_mesh_actor:
            prop = self._current_mesh_actor.GetProperty()
            if enabled:
                prop.SetRepresentationToWireframe()
            else:
                prop.SetRepresentationToSurface()
            self.plotter.render()

    def close(self):
        if self.plotter:
            self.plotter.close()
        super().close()
