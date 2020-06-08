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

            #start = time.perf_counter()
            Fill_treshold = 500
            
            ####### Get model to clean ####### 

            Model = bpy.context.view_layer.objects.active
            Model_name = Model.name
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            
            #t1 = time.perf_counter()
            #print(f"step 1 Done in {t1-start}")

            ####### Clean borders #######
            
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.fill_holes(sides=Fill_treshold)
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.delete(type='FACE')
            
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.delete(type="VERT")
            
            #t2 = time.perf_counter()
            #print(f"step 2 Done in {t2-t1}")

            ####### Remove loose geometry #######
            
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
            
            #t3 = time.perf_counter()
            #print(f"step 3 Done in {t3-t2}")

            ####### Fill Holes #######

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.fill_holes(sides=Fill_treshold)
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

            #t4 = time.perf_counter()
            #print(f"step 4 Done in {t4-t3}")

            ####### Relax borders #######
            
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.looptools_relax(
                input="selected", interpolation="cubic", iterations="3", regular=True
            )

            #t5 = time.perf_counter()
            #print(f"step 5 Done in {t5-t4}")


            ####### Make mesh consistent (face normals) #######
            
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode="OBJECT")

            #t6 = time.perf_counter()
            #print(f"step 6 Done in {t6-t5}")

            #finish = time.perf_counter()
            #print(f"Clean Model Done in {finish-start}")
            
            return {"FINISHED"}


class OPENDENTAL_OT_model_base_type_select(bpy.types.Operator):
    """"""

    bl_idname = "opendental.model_base_type_select"
    bl_label = "Select model base type operator."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        Modelsprop = bpy.context.scene.BASE_props.Modelsprop
        if "Solid" in Modelsprop:
            bpy.ops.opendental.solid_model_base("INVOKE_DEFAULT")
        elif "Hollow" in Modelsprop:
            bpy.ops.opendental.hollow_model_base("INVOKE_DEFAULT")
        return {"FINISHED"}

class OPENDENTAL_OT_hollow_model_base(bpy.types.Operator):
    """Make a hollow model base from top user view prspective"""

    bl_idname = "opendental.hollow_model_base"
    bl_label = "Create a hollow base and remesh model to solid."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

        else:
            
            # Get area and space "VIEW_3D" :

            for area in bpy.context.screen.areas:
                if area.type == "VIEW_3D":
                    my_area = area

            for space in my_area.spaces:
                if space.type == "VIEW_3D":
                    my_space = space

            # Context override: (Need it Only if we run this script in text editor)

            context = bpy.context.copy()
            context["area"] = my_area
            context["space_data"] = my_space

            #start = time.perf_counter()

            # Prepare scene settings :

            bpy.ops.view3d.snap_cursor_to_center(context)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            bpy.ops.transform.select_orientation(context, orientation="GLOBAL")
            bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'

            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.scene.tool_settings.use_proportional_edit_objects = False
            bpy.ops.object.mode_set(mode="OBJECT")


            ####### Duplicate Model #######

            # Get active Object :

            Model = bpy.context.view_layer.objects.active

            # Duplicate Model :

            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model
            bpy.ops.object.duplicate_move()

            # Rename Model_hollow....

            Model_hollow = bpy.context.view_layer.objects.active
            Model_hollow.name = f"{Model.name}_hollow"
            mesh_hollow = Model_hollow.data
            mesh_hollow.name = f"{Model.name}_hollow_mesh"

            # Get Model_hollow :

            bpy.ops.object.select_all(action="DESELECT")
            Model_hollow.select_set(True)
            bpy.context.view_layer.objects.active = Model_hollow

            # store model hollow location :

            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            hollow_location = Model_hollow.location.copy()

            # center model new model hollow to world origin :

            bpy.ops.view3d.snap_selected_to_cursor(context, use_offset=False) 



            ####### Flip Model_hollow to top view #######
            view_rotation = my_space.region_3d.view_rotation
            view3d_rot_matrix = view_rotation.to_matrix().to_4x4()

            flip_matrix = view3d_rot_matrix.inverted()
            unflip_matrix = view3d_rot_matrix

            Model_hollow.matrix_world = flip_matrix @ Model_hollow.matrix_world
            
            # Make duplicate :
            bpy.ops.object.mode_set(mode="OBJECT")

            bpy.ops.object.select_all(action="DESELECT")
            Model_hollow.select_set(True)
            bpy.context.view_layer.objects.active = Model_hollow
            bpy.ops.object.duplicate_move()

            # get model hollow dup_1 and Make vertex groups :

            dup_1 = bpy.context.view_layer.objects.active
            dup_1.name = 'hollow dup_1'
            bpy.ops.object.select_all(action="DESELECT")
            dup_1.select_set(True)
            bpy.context.view_layer.objects.active = dup_1

            # remesh dup_1 1mm :

            bpy.context.object.data.use_remesh_smooth_normals = True
            bpy.context.object.data.use_remesh_preserve_volume = True
            bpy.context.object.data.use_remesh_fix_poles = True
            bpy.context.object.data.remesh_voxel_size = 1
            bpy.ops.object.voxel_remesh()

            #t1 = time.perf_counter()
            #print(f"before modifiers Done in {t1-start}")
            
            # modifiers :
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            dup_1.select_set(True)
            bpy.context.view_layer.objects.active = dup_1

            # Remesh modifier :

            bpy.ops.object.modifier_add(type='REMESH')

            bpy.context.object.modifiers["Remesh"].octree_depth = 6
            bpy.context.object.modifiers["Remesh"].mode = 'SMOOTH'
            bpy.context.object.modifiers["Remesh"].scale = 0.6
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Remesh")

            #smooth modifier :

            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].iterations = 200
            bpy.context.object.modifiers["Smooth"].factor = 1


            # subdiv modifier :

            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.object.modifiers["Subdivision"].levels = 3


            # Shrinkwrap modifier :

            bpy.ops.object.modifier_add(type='SHRINKWRAP')

            bpy.context.object.modifiers["Shrinkwrap"].target = Model_hollow
            bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].offset = -2.8


            # Corrective smooth modifier :

            bpy.ops.object.modifier_add(type='CORRECTIVE_SMOOTH')
            bpy.context.object.modifiers["CorrectiveSmooth"].iterations = 100
            bpy.context.object.modifiers["CorrectiveSmooth"].use_only_smooth = True
            bpy.context.object.modifiers["CorrectiveSmooth"].factor = 1


            #apply modifiers :

            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Smooth")


            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Subdivision")
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Shrinkwrap")
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="CorrectiveSmooth") 


            # remesh dup_1 1mm :

            bpy.context.object.data.use_remesh_smooth_normals = True
            bpy.context.object.data.use_remesh_preserve_volume = True
            bpy.context.object.data.use_remesh_fix_poles = True
            bpy.context.object.data.remesh_voxel_size = 0.1
            bpy.ops.object.voxel_remesh()

            #t2 = time.perf_counter()
            #print(f"modifiers Done in {t2-t1}")


            # join the 2 meshes :

            bpy.ops.object.mode_set(mode="OBJECT")
            Model_hollow.select_set(True)
            bpy.context.view_layer.objects.active = Model_hollow
            bpy.ops.object.join()
            Model_hollow = bpy.context.view_layer.objects.active
            Model_hollow.name = f"{Model.name}_hollow"
            mesh_hollow = Model_hollow.data
            mesh_hollow.name = f"{Model.name}_hollow_mesh"

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bisect(plane_co=(0, 0, -6), plane_no=(0, 0, 1), use_fill=True, clear_inner=True, xstart=100, xend=1600, ystart=400, yend=400)
            bpy.ops.object.mode_set(mode="OBJECT")


            # Model_base matrix_world reset :

            Model_hollow.matrix_world = unflip_matrix @ Model_hollow.matrix_world

            # Restore new Model hollow location :

            Model_hollow.location = hollow_location
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            """
            # Hide everything but hollow model :

            bpy.ops.object.select_all(action="DESELECT")
            Model_hollow.select_set(True)
            bpy.context.view_layer.objects.active = Model_hollow

            bpy.ops.object.shade_flat()

            bpy.ops.object.hide_view_set(context,unselected=True)

            finish = time.perf_counter()
            print(f"total time Done in {finish-start}")
            """
            
        return {"FINISHED"}

class OPENDENTAL_OT_solid_model_base(bpy.types.Operator):
    """Make a model base from top user view prspective"""

    bl_idname = "opendental.solid_model_base"
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
    bpy.utils.register_class(OPENDENTAL_OT_model_base_type_select)
    bpy.utils.register_class(OPENDENTAL_OT_solid_model_base)
    bpy.utils.register_class(OPENDENTAL_OT_remesh_model)
    bpy.utils.register_class(OPENDENTAL_OT_hollow_model_base)

    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_decimate_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_clean_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_model_base_type_select)
    bpy.utils.unregister_class(OPENDENTAL_OT_solid_model_base)
    bpy.utils.unregister_class(OPENDENTAL_OT_remesh_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_hollow_model_base)
