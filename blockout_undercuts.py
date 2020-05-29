#Python Imports
import math
from math import degrees, radians, pi


#Blender Imports
import bpy
from mathutils import Vector


#Addon Imports
import odcutils


class OPENDENTAL_OT_survey_model(bpy.types.Operator):
    """Calculates silhouette of object which surveys convexities AND concavities from the current view axis"""

    bl_idname = "opendental.view_silhouette_survey"
    bl_label = "Survey Model From View"
    bl_options = {"REGISTER", "UNDO"}

    world = bpy.props.BoolProperty(
        default=True,
        name="Use world coordinate for calculation...almost always should be true.",
    )
    smooth = bpy.props.BoolProperty(
        default=True,
        name="Smooth the outline.  Slightly less acuurate in some situations but more accurate in others.  Default True for best results",
    )

    @classmethod
    def poll(cls, context):
        # restoration exists and is in scene
        C0 = context.space_data.type == "VIEW_3D"
        C1 = context.object != None
        if C1:
            C2 = context.object.type == "MESH"
        else:
            C2 = False
        return C0 and C1 and C2

    def execute(self, context):
        #settings = get_settings()
        #dbg = settings.debug
        ob = context.object
        view = context.space_data.region_3d.view_rotation @ Vector((0, 0, 1))
        odcutils.silouette_brute_force(
            context, ob, view, self.world, self.smooth #, debug=dbg
        )
        return {"FINISHED"}

class OPENDENTAL_OT_blockout_model(bpy.types.Operator):
    """Calculates silhouette of object which surveys convexities AND concavities from the current view axis"""

    bl_idname = "opendental.view_blockout_undercuts"
    bl_label = "Blockout Model From View"
    bl_options = {"REGISTER", "UNDO"}

    world = bpy.props.BoolProperty(
        default=True,
        name="Use world coordinate for calculation...almost always should be true.",
    )
    smooth = bpy.props.BoolProperty(
        default=True,
        name="Smooth the outline.  Slightly less acuurate in some situations but more accurate in others.  Default True for best results",
    )

    @classmethod
    def poll(cls, context):
        # restoration exists and is in scene
        C0 = context.space_data.type == "VIEW_3D"
        C1 = context.object != None
        if C1:
            C2 = context.object.type == "MESH"
        else:
            C2 = False
        return C0 and C1 and C2

    def execute(self, context):
        # settings = get_settings()
        # dbg = settings.debug
        ob = context.object
        view = context.space_data.region_3d.view_rotation @ Vector((0, 0, 1))

        Modelsprop = bpy.context.scene.UNDERCUTS_props.Modelsprop
        if "Preview" in Modelsprop:
            bmesh_fns.remove_undercuts(context, ob, view, self.world, self.smooth)
        elif "Solid" in Modelsprop:
            bpy.ops.opendental.view_blockout_undercuts_solid("INVOKE_DEFAULT")
        return {"FINISHED"}


class OPENDENTAL_OT_blockout_model_solid(bpy.types.Operator): #produces watertight blockout mesh when supplied watertight mesh
    bl_idname = 'opendental.view_blockout_undercuts_solid'
    bl_label = "Blockout Model From Z-axis"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):

        extrude_z = -10
        
        if bpy.context.selected_objects == []:

            message = " Please select the Model to survey !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        #else:

        # Get area and space "VIEW_3D" :...........................

        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                my_area = area

        for space in my_area.spaces:
            if space.type == "VIEW_3D":
                my_space = space

        # ...........................Prepare scene settings : ..............................................

        # bpy.ops.view3d.snap_cursor_to_center()
        bpy.context.scene.transform_orientation_slots[0].type = "GLOBAL"
        bpy.context.scene.tool_settings.transform_pivot_point = "ACTIVE_ELEMENT"
        bpy.context.scene.tool_settings.use_snap = False

        # Get active Object :..........................................................

        ob = bpy.context.view_layer.objects.active

        # Get avtive Object mode :.....................................................

        mode = ob.mode

        # Get VIEW_matrix and extract euler angles :
        #my_space = context.space_data #PRM
        view3d_matrix = my_space.region_3d.view_matrix
        
        
        
        ###  PATRICKS TEST ###############################
        ##################################################
        world_view = context.space_data.region_3d.view_rotation @ Vector((0,0,1))
        local_view = ob.matrix_world.inverted().to_quaternion() @ world_view
        
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        for v in ob.data.vertices:
            v.select = False
        for ed in ob.data.edges:
            ed.select = False
            
        for f in ob.data.polygons:
            if f.normal.dot(local_view) < -0.000001:
                f.select = True
            else:
                f.select = False
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        bpy.context.scene.transform_orientation_slots[0].type = "LOCAL"
        extrude_vec = extrude_z * local_view
        bpy.ops.mesh.extrude_region_move()
        bpy.ops.transform.translate(
            value=(extrude_vec[0], extrude_vec[1], extrude_vec[2]), constraint_axis=(False, False, False)
        )
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")
        
        return {'FINISHED'}
        ### END PATRICK"S TEST   #########################
        ###################################################
        """

        # duplcate Model and name it Model_undercut :

        Model = ob
        bpy.ops.object.select_all(action="DESELECT")
        Model.select_set(True)
        bpy.context.view_layer.objects.active = Model
        bpy.ops.object.duplicate_move()
        Model_undercut = bpy.context.view_layer.objects.active
        Model_undercut.name = f"{Model.name}_undercut"
        mesh_undercut = Model_undercut.data
        mesh_undercut.name = f"{Model.name}_undercut_mesh"
        bpy.ops.object.select_all(action="DESELECT")

        # #############################____Making undercuts____###############################

        # ...........................Flip Model undercut to top view........................:

        Model_undercut.matrix_world = view3d_matrix @ Model_undercut.matrix_world

        # ..................Model undercut surveing (srvey axis = Z_UP(0, 0, 1)............:

        # 1_# Get rotation matrix before applying Transf_rotation:

        ob = Model_undercut
        initial_matrix = ob.matrix_world
        iloc, irot, iscale = initial_matrix.decompose()
        initial_rot_matrix = irot.to_matrix().to_4x4()

        # 2_# Apply Transf_rotation :

        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        # 3_# Get a list of  mesh_faces :

        survey_faces_index_list = []

        for i in range(0, len(ob.data.polygons)):

            face = ob.data.polygons[i]
            if Vector((0, 0, 1)).angle(face.normal) >= pi / 2:
                survey_faces_index_list.append(i)

        print(survey_faces_index_list[0])

        # 4_# select survey faces :

        # ....Deselect everything first
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")

        # ....it seems we can only select faces during object mode
        bpy.ops.object.mode_set(mode="OBJECT")

        for i in survey_faces_index_list:
            face = ob.data.polygons[i]
            face.select = True

        # ....Add vertex group
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)

        Model_undercut.vertex_groups.new(name="my_survey")
        bpy.ops.object.vertex_group_assign()

        print("#" * 20)
        print("Model Surveying done, Vertex Group my_survey created")

        # 5_# Reset Model_undercut Transf_rotation :

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        Model_undercut.select_set(True)
        bpy.context.view_layer.objects.active = Model_undercut
        ob = Model_undercut

        inv_rot_matrix = initial_rot_matrix.transposed()

        ob.matrix_world = inv_rot_matrix @ ob.matrix_world
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        ob = Model_undercut

        # bpy.context.view_layer.objects.active = ob
        ob.matrix_world = initial_rot_matrix @ ob.matrix_world
        if ob.matrix_world == initial_matrix:
            print("object matrix reset DONE")

        else:
            print("Error : reset not done!")

        # ..................Extrude survey Faces : axis = (0, 0, -1)......................:

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        Model_undercut.select_set(True)
        bpy.context.view_layer.objects.active = Model_undercut

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.vertex_group_set_active(group="my_survey")
        bpy.ops.object.vertex_group_select()

        bpy.ops.mesh.extrude_region_move()
        bpy.ops.transform.translate(
            value=(0, 0, extrude_z), constraint_axis=(False, False, True)
        )

        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.mode_set(mode="OBJECT")

        #return {"FINISHED"}
    
        print("Extrude DONE")

        # ....................................Unflip Model undercut.............................
        # Model undercut matrix_world rest :

        Model_undercut.matrix_world = (
            view3d_matrix.inverted() @ Model_undercut.matrix_world
        )

        # ...........clean Model_undercut mesh :........................................

        bpy.ops.object.select_all(action="DESELECT")
        Model_undercut.select_set(True)
        bpy.context.view_layer.objects.active = Model_undercut
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode="OBJECT")

        # .......................Model_undercut Remesh voxels :.............................

        Model_undercut.data.use_auto_smooth = True
        bpy.ops.object.select_all(action="DESELECT")
        Model_undercut.select_set(True)
        bpy.context.view_layer.objects.active = Model_undercut
        bpy.data.meshes[mesh_undercut.name].remesh_voxel_size = 0.2
        bpy.context.object.data.use_remesh_smooth_normals = True
        bpy.ops.object.voxel_remesh()

        # Finish ...........................................................

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")
        #bpy.ops.object.select_all(action="DESELECT")

        return {"FINISHED"}
        """
    
def register():
    bpy.utils.register_class(OPENDENTAL_OT_survey_model)
    bpy.utils.register_class(OPENDENTAL_OT_blockout_model)
    bpy.utils.register_class(OPENDENTAL_OT_blockout_model_solid)

    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_survey_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_blockout_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_blockout_model_solid)
