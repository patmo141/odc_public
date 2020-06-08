# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
bl_info = {
    "name": "Lina_Model_Trim",
    "author": "Dr_Issam_Dakir",
    "description": "Dental Model Trim Tool",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "view-3d/UI panel/Lina Dental Align",
    "warning": "",
    "category": "Dental",
}

"""
import bpy
import mathutils
import os
from os import path
from math import sqrt
from bpy_extras import view3d_utils
from bpy.props import IntProperty, FloatProperty, StringProperty

trim_model_prop = str()
trim_tool_prop = str()
preview_collections = {}
override = {}

initial_matrix = mathutils.Matrix.Identity(4)


for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == "VIEW_3D":
            my_area = area

            for space in my_area.spaces:
                if space.type == "VIEW_3D":
                    my_space = space

                    override = {
                        "window": window,
                        "screen": screen,
                        "area": my_area,
                        "space_data": my_space,
                    }


def ShowMessageBox(message="", title="INFO", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def add_curve():

    global trim_model_prop
    global trim_tool_prop
    global initial_matrix

    bpy.ops.transform.select_orientation(orientation="GLOBAL")
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {"FACE"}
    bpy.context.scene.tool_settings.transform_pivot_point = "INDIVIDUAL_ORIGINS"

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    Model = bpy.context.view_layer.objects.active

    # Duplicate Model :

    bpy.ops.object.select_all(action="DESELECT")
    Model.select_set(True)
    bpy.context.view_layer.objects.active = Model
    bpy.ops.object.duplicate_move()

    # ....set Model_Trim name... :

    Model_Trim = bpy.context.view_layer.objects.active

    Model_Trim_list = []

    for ob in bpy.data.objects:
        if ob.name.startswith("Model_Trimed"):
            Model_Trim_list.append(ob.name)

    n = len(Model_Trim_list)
    if n == 0:
        Model_Trim.name = "Model_Trimed"
        mesh_Trim = Model_Trim.data
        mesh_Trim.name = "Model_Trimed_mesh"
        trim_model_prop = Model_Trim.name

    else:
        Model_Trim.name = f"Model_Trimed_0{n}"
        mesh_Trim = Model_Trim.data
        mesh_Trim.name = f"Model_Trimed_mesh_0{n}"
        trim_model_prop = Model_Trim.name

    # .... Get Model_Trim..... :

    bpy.ops.object.select_all(action="DESELECT")
    Model_Trim.select_set(True)
    bpy.context.view_layer.objects.active = Model_Trim
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    bpy.ops.object.hide_view_set(unselected=True)

    # 1_# Get rotation matrix before applying Transf_rotation:

    initial_matrix = Model_Trim.matrix_world.copy()

    # 2_# Apply Transf_rotation :

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)

    # ....Add Curve ....... :

    bpy.context.scene.tool_settings.use_snap = True
    bpy.ops.curve.primitive_bezier_curve_add(
        radius=1, enter_editmode=True, align="CURSOR"
    )  # ....EDIT mode is tuggled

    bpy.ops.object.mode_set(mode="OBJECT")
    trim_tool = bpy.context.view_layer.objects.active

    # ....set trim_tool name....(control of doubles names) :

    trim_tool_list = []
    for ob in bpy.data.objects:
        if ob.name.startswith("Trim_tool"):
            trim_tool_list.append(ob.name)

    n = len(trim_tool_list)
    if n == 0:
        trim_tool.name = "Trim_tool"
        curve = trim_tool.data
        curve.name = "Trim_tool_mesh"
        trim_tool_prop = trim_tool.name

    else:
        trim_tool.name = f"Trim_tool_0{n}"
        curve = trim_tool.data
        curve.name = f"Trim_tool_mesh_0{n}"
        trim_tool_prop = trim_tool.name

    # ....Curve settings.... :
    bpy.ops.object.select_all(action="DESELECT")
    trim_tool.select_set(True)
    bpy.context.view_layer.objects.active = trim_tool

    bpy.ops.object.mode_set(mode="EDIT")

    bpy.ops.curve.select_all(action="DESELECT")
    curve.splines[0].bezier_points[0].select_control_point = True
    bpy.ops.curve.dissolve_verts()
    bpy.ops.curve.select_all(action="SELECT")
    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
    bpy.context.object.data.dimensions = "3D"
    bpy.context.object.data.twist_smooth = 3
    bpy.ops.curve.handle_type_set(type="AUTOMATIC")

    bpy.context.object.data.bevel_depth = 0.5
    bpy.context.object.data.extrude = 0

    bpy.context.object.data.bevel_resolution = 2

    bpy.context.scene.tool_settings.curve_paint_settings.error_threshold = 1
    bpy.context.scene.tool_settings.curve_paint_settings.corner_angle = 1.5708

    bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = "SURFACE"
    bpy.context.scene.tool_settings.curve_paint_settings.surface_offset = 0
    bpy.context.scene.tool_settings.curve_paint_settings.use_offset_absolute = True
    mat = bpy.data.materials.new("Blue_Metalica")
    mat.diffuse_color = [0.3, 0.6, 1.0, 1.0]
    mat.metallic = 1.0
    mat.roughness = 0.1

    curve.materials.append(mat)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.wm.tool_set_by_id(name="builtin.cursor")
    bpy.context.space_data.overlay.show_outline_selected = False



def delete_last_point():

    global trim_tool_prop

    trim_tool = bpy.data.objects[trim_tool_prop]
    curve = trim_tool.data
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.curve.dissolve_verts()
    curve.splines[0].bezier_points[0].select_control_point = True
    bpy.ops.object.mode_set(mode="OBJECT")

def extrude_to_cursor(context, event):
    
    global trim_tool_prop
    
    trim_tool = bpy.data.objects[trim_tool_prop]
    
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    trim_tool.select_set(True)
    bpy.context.view_layer.objects.active = trim_tool

    bpy.ops.object.mode_set(mode="EDIT")
    # bpy.ops.curve.select_all(action='DESELECT')
    # curve.splines[0].bezier_points[0].select_control_point = True

    bpy.ops.curve.extrude(mode="INIT")

    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    
    
class OBJECT_OT_start_trim(bpy.types.Operator):
    """start trim tool"""

    bl_idname = "object.start_trim"
    bl_label = "START tool"
    bl_options = {"REGISTER", "UNDO"}

    global trim_model_prop
    global trim_tool_prop

    def modal(self, context, event):

        if event.type in {
            "MIDDLEMOUSE",
            "WHEELUPMOUSE",
            "WHEELDOWNMOUSE",
            "TAB",
        }:
            # allow navigation
            
            return {"PASS_THROUGH"}

        elif event.type == ("DEL"):

            if event.value == ("PRESS"):

                delete_last_point()
                return {"RUNNING_MODAL"}

        elif event.type == ("LEFTMOUSE"):

            if event.value == ("PRESS"):

                return {"PASS_THROUGH"}
            
            if event.value == ("RELEASE"):
                
                extrude_to_cursor(context, event)

        elif event.type == "RET":

            global trim_tool_prop
            
            trim_tool = bpy.data.objects[trim_tool_prop]
            bpy.ops.object.mode_set(mode="OBJECT")

            bpy.ops.object.select_all(action="DESELECT")
            trim_tool.select_set(True)
            bpy.context.view_layer.objects.active = trim_tool
            
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.curve.cyclic_toggle()
            """
            bpy.context.object.data.bevel_depth = 0.1
            bpy.context.object.data.extrude = 3
            """
            bpy.ops.object.mode_set(mode="OBJECT")
            
            return {"FINISHED"}
        
        elif event.type == ("RIGHTMOUSE"):
            
            return {"PASS_THROUGH"}
        
        
        elif event.type == ("ESC"):
            
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context, event):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:

            if context.space_data.type == "VIEW_3D":

                add_curve()

                context.window_manager.modal_handler_add(self)

                return {"RUNNING_MODAL"}

            else:

                self.report({"WARNING"}, "Active space must be a View3d")

                return {"CANCELLED"}


class OBJECT_OT_cut_model(bpy.types.Operator):
    " Cut model and separate parts"

    bl_idname = "object.cut_model"
    bl_label = "Cut Model"

    def execute(self, context):

        global trim_model_prop
        global trim_tool_prop
        global initial_matrix

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:
            
            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)

            Model = bpy.data.objects[trim_model_prop]
            trim_tool = bpy.data.objects[trim_tool_prop]

            

            # ....Get Trim_tool:.....

            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            trim_tool.select_set(True)
            bpy.context.view_layer.objects.active = trim_tool

            # ....Add modifiers...:

            bpy.context.object.data.bevel_depth = 0
            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["Model_Trimed"]
            bpy.context.object.modifiers["Shrinkwrap"].offset = 2
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].use_apply_on_spline = True

            
            # ....Add undo history point...:
            bpy.ops.ed.undo_push()

            # ....Duplicate curve...:
            
            bpy.ops.object.duplicate_move()
            trim_tool_inner = bpy.context.view_layer.objects.active
            bpy.context.object.modifiers["Shrinkwrap"].offset = -2
            bpy.ops.object.convert(target='MESH')
            trim_tool_inner = bpy.context.view_layer.objects.active

            # ....join curve meshes...:
            bpy.ops.object.select_all(action="DESELECT")
            trim_tool.select_set(True)
            bpy.context.view_layer.objects.active = trim_tool
            bpy.ops.object.convert(target='MESH')
            trim_tool = bpy.context.view_layer.objects.active

            bpy.ops.object.select_all(action="DESELECT")
            trim_tool_inner.select_set(True)
            trim_tool.select_set(True)
            bpy.context.view_layer.objects.active = trim_tool
            bpy.ops.object.join()
            trim_tool = bpy.context.view_layer.objects.active

            # ....Solidify curve.... :

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bridge_edge_loops()
            bpy.ops.mesh.subdivide(number_cuts=5)
            
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            trim_tool.select_set(True)
            
            # ....Add undo history point...:
            bpy.ops.ed.undo_push()

            bpy.ops.object.modifier_add(type='SOLIDIFY')
            bpy.context.object.modifiers["Solidify"].thickness = 0.2
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Solidify")
            bpy.context.object.data.remesh_voxel_size = 0.1
            bpy.context.object.data.use_remesh_smooth_normals = True
            bpy.ops.object.voxel_remesh()
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='SELECT')

            # ....Add undo history point...:
            bpy.ops.ed.undo_push()

            # ....Make boolean union , select less and delete curve.... :
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode="OBJECT")

            
            bpy.ops.object.modifier_add(type='BOOLEAN')
            bpy.context.object.modifiers["Boolean"].show_viewport = False
            bpy.context.object.modifiers["Boolean"].operation = 'UNION'
            bpy.context.object.modifiers["Boolean"].object = trim_tool
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.delete(type='VERT')

            # ....Separate by loose parts.... :

            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.separate(type="LOOSE")
            bpy.ops.object.mode_set(mode="OBJECT")

            # .... Hide trim_tool... :

            bpy.ops.object.hide_view_set(unselected=True)

            bpy.ops.object.select_all(action="DESELECT")
            bpy.ops.wm.tool_set_by_id(name="builtin.select")
            bpy.ops.view3d.snap_cursor_to_center()
            bpy.context.space_data.overlay.show_outline_selected = True
            
            # ....info popup message.... :

            message = " the model was successfully cuted. Please select the part to keep and click on Trim Model!"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"FINISHED"}

class OBJECT_OT_trim_model(bpy.types.Operator):
    " keep selected part and remove inselected"

    bl_idname = "object.trim_model"
    bl_label = "Trim Model"

    def execute(self, context):

        global trim_model_prop
        global trim_tool_prop
        global initial_matrix

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:

            Model = bpy.context.view_layer.objects.active
            Model.name = trim_model_prop
            Model.data.name = f'{trim_model_prop}_mesh'
            bpy.ops.object.select_all(action='INVERT')
            bpy.ops.object.delete(use_global=False, confirm=False)

            return {"FINISHED"}



class OBJECT_PT_trim_tool(bpy.types.Panel):
    """Creates a Panel in Lina Dental Align addon panel"""

    bl_label = "Model Trim"
    bl_idname = "OBJECT_PT_trim_tool"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Open Dental CAD"

    def draw(self, context):
        layout = self.layout

        icon_coll = preview_collections["main"]
        start_ico = icon_coll["start_ico"].icon_id
        cut_ico = icon_coll["cut_ico"].icon_id
        Trim_ico = icon_coll["Trim_ico"].icon_id
        # Create a simple row.

        row = layout.row()
        row.operator("object.start_trim", text="Start tracing", icon_value=start_ico)
        row.operator("object.cut_model", text="Cut Model", icon_value=cut_ico)
        #row = layout.row()
        #row.operator("object.trim_model", text="Trim Model", icon_value=Trim_ico)



classes = (
    OBJECT_OT_start_trim,
    OBJECT_OT_trim_model,
    OBJECT_PT_trim_tool,
    OBJECT_OT_cut_model,
)



def register():

    import bpy.utils.previews

    icons_dict = bpy.utils.previews.new()

    # path to the folder where the icon is
    # the path is calculated relative to this py file inside the addon folder
    dirpath = path.dirname(path.abspath(__file__))
    my_icons_dir = os.path.join(dirpath, "icons")

    # load a preview thumbnail of a file and store in the previews collection
    icons_dict.load(
        "start_ico",
        os.path.join(my_icons_dir, "start_ico.png"),
        "IMAGE",
        force_reload=True,
    )
    icons_dict.load(
        "cut_ico",
        os.path.join(my_icons_dir, "cut_ico.png"),
        "IMAGE",
        force_reload=True,
    )

    icons_dict.load(
        "Trim_ico",
        os.path.join(my_icons_dir, "Trim_ico.png"),
        "IMAGE",
        force_reload=True,
    )
    
    preview_collections["main"] = icons_dict


    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
