#Python Imports
import math
from math import degrees, radians, pi


#Blender Imports
import bpy
from mathutils import Vector


#Addon Imports



class OPENDENTAL_OT_decimate_model(bpy.types.Operator):
    """ Decimate Model to ratio """  # TODO ratio poperty

    bl_idname = "opendental.decimate_model"
    bl_label = "Decimate Model"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        ratio = 0.5

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:

            # get model to clean :

            Model = bpy.context.view_layer.objects.active
            mesh = Model.data
            Faces = len(mesh.polygons)
            if Faces >= 300000:

                ratio = 300000 / Faces
                bpy.ops.object.select_all(action="DESELECT")
                Model.select_set(True)
                bpy.ops.object.mode_set(mode="OBJECT")

                ###............... Decimate Model ....................###

                bpy.ops.object.modifier_add(type="DECIMATE")
                bpy.context.object.modifiers["Decimate"].ratio = ratio
                bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Decimate")

            return {"FINISHED"}


class OPENDENTAL_OT_clean_model(bpy.types.Operator):
    """ Fill small and medium holes and remove small parts"""

    bl_idname = "opendental.clean_model"
    bl_label = "Clean Model"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:

            Fill_treshold = 400
            # get model to clean :

            Model = bpy.context.view_layer.objects.active
            Model_name = Model.name
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)

            ##### 1st step #########

            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.tris_convert_to_quads(shape_threshold=1.0472, sharp=True)
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.remove_doubles(threshold=0.16)
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.delete(type="FACE")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.delete(type="VERT")

            ##### 2nd step : Fill Holes #########

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.fill_holes(sides=Fill_treshold)

            ##### 3rd step : Remove weird boders : ######

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()

            bpy.ops.mesh.delete(type="FACE")
            ###............5th step Remove separated parts : ............###

            # Separate parts :

            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.separate(type="LOOSE")
            bpy.ops.object.mode_set(mode="OBJECT")

            # Calculate parts volumes and deslect the big volume :

            list_vol = []
            for obj in bpy.context.selected_objects:
                obj_dim = obj.dimensions
                obj_vol = obj_dim[0] * obj_dim[1] * obj_dim[2]
                list_vol.append(obj_vol)

            for obj in bpy.context.selected_objects:
                obj_dim = obj.dimensions
                obj_vol = obj_dim[0] * obj_dim[1] * obj_dim[2]
                if obj_vol > max(list_vol) - 1:
                    obj.select_set(False)

            # Delete small parts :

            bpy.ops.object.delete(use_global=False, confirm=False)
            Model = bpy.data.objects[Model_name]
            Model.select_set(True)

            ###### 4th step : space up and smooth borders : ##############
            """
            # Give it some space :

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()

            bpy.ops.mesh.remove_doubles(threshold=0.2)
            """
            # Smooth mesh borders and Select Non-Manifold :
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()

            bpy.ops.mesh.delete(type="FACE")
  
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.vertices_smooth(factor=0.5)

            bpy.ops.mesh.remove_doubles(threshold=0.2)

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.delete(type="FACE")

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.looptools_relax(
                input="selected", interpolation="cubic", iterations="10", regular=True
            )
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.delete_loose()

            # Repair geometry resuting from precedent operation :

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.remove_doubles(threshold=0.1)

            # Repair geometry resuting from precedent operation :

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.delete(type="VERT")

            # Make mesh consistent (face normals) :

            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode="OBJECT")

            print("Clean Model Done")

            return {"FINISHED"}


class OPENDENTAL_OT_project_model_base(bpy.types.Operator):
    """Make a model base from top user view prspective"""

    bl_idname = "opendental.project_model_base"
    bl_label = "Create a base and remesh model to solid."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:

            extrude_value = (0, 0, -15)

            # Get area and space "VIEW_3D" :...........................

            for area in bpy.context.screen.areas:
                if area.type == "VIEW_3D":
                    my_area = area

            for space in my_area.spaces:
                if space.type == "VIEW_3D":
                    my_space = space

            # [DEBUG] Context override: Need it Only if we run this script in text editor
            #context = bpy.context.copy()
            #context["area"] = my_area
            #context["space_data"] = my_space

            # Prepare scene settings :

            bpy.ops.view3d.snap_cursor_to_center()
            bpy.ops.transform.select_orientation(orientation="GLOBAL")
            bpy.context.scene.tool_settings.transform_pivot_point = "INDIVIDUAL_ORIGINS"
            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.scene.tool_settings.use_proportional_edit_objects = False
            bpy.ops.object.mode_set(mode="OBJECT")

            # Get active Object :

            Model = bpy.context.view_layer.objects.active

            # Duplicate Model :

            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model
            bpy.ops.object.duplicate_move()

            # ....Rename Model_base....

            Model_base = bpy.context.view_layer.objects.active
            Model_base.name = f"{Model.name}_base"
            mesh_base = Model_base.data
            mesh_base.name = f"{Model.name}_base_mesh"

            # Get Model_base :

            Model = Model_base

            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model
            bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")

            # Select border :
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.mesh.select_non_manifold()

            ###......... Get View values : ............###

            view3d = my_space.region_3d
            view_matrix = view3d.view_matrix

            view_matrix_3 = view_matrix.to_3x3()

            ###............. Project Base Operation...............###

            # Extrude selected vertices :

            bpy.ops.mesh.extrude_region_move()
            bpy.ops.transform.translate(
                value=extrude_value,
                orient_type="VIEW",
                orient_matrix_type="VIEW",
                constraint_axis=(False, False, True),
            )

            # Scale border vertices to zero :

            bpy.ops.transform.resize(
                value=(1, 1, 0),
                orient_type="VIEW",
                orient_matrix=view_matrix_3.transposed(),
                orient_matrix_type="VIEW",
                constraint_axis=(False, False, True),
            )

            # and fill base :

            bpy.ops.mesh.fill()

            # Remove extra edges from Base face :

            bpy.ops.mesh.dissolve_limited()

            # Repare geometry resuting from precedent operation :

            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.delete(type="FACE")
            bpy.ops.object.mode_set(mode="OBJECT")

            return {"FINISHED"}


class OPENDENTAL_OT_remesh_model(bpy.types.Operator):
    """ Rmesh Model - remesh alogorythm remove any internal intersecting topology and make quad polygons """

    bl_idname = "opendental.remesh_model"
    bl_label = "Remesh Model"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:

            # get model to clean :
            bpy.ops.object.mode_set(mode="OBJECT")
            Model = bpy.context.view_layer.objects.active
            mesh = Model.data
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            Model.data.use_auto_smooth = True
            bpy.data.meshes[mesh.name].remesh_voxel_size = 0.147
            bpy.context.object.data.use_remesh_smooth_normals = True
            bpy.ops.object.voxel_remesh()
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")

            return {"FINISHED"}


def register():
    bpy.utils.register_class(OPENDENTAL_OT_decimate_model)
    bpy.utils.register_class(OPENDENTAL_OT_clean_model)
    bpy.utils.register_class(OPENDENTAL_OT_project_model_base)
    bpy.utils.register_class(OPENDENTAL_OT_remesh_model)

    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_decimate_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_clean_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_project_model_base)
    bpy.utils.unregister_class(OPENDENTAL_OT_remesh_model)
