#Python Imports
import math
from math import degrees, radians, pi


#Blender Imports
import bpy
import bmesh
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

            return {"CANCELLED"}

        else:

            bpy.ops.opendental.solid_model_base("INVOKE_DEFAULT")
            bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")

            # Prepare scene settings :
            bpy.ops.view3d.snap_cursor_to_center()
            bpy.ops.transform.select_orientation(orientation="GLOBAL")
            bpy.context.scene.tool_settings.transform_pivot_point = "INDIVIDUAL_ORIGINS"
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.scene.tool_settings.use_proportional_edit_objects = False
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')


            ####### Duplicate Model #######
                    
            # Get active Object :

            Model = bpy.context.view_layer.objects.active

            # Duplicate Model to Model_hollow:

            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model
            bpy.ops.object.duplicate_move()

            # Rename Model_hollow....

            Model_hollow = bpy.context.view_layer.objects.active
            Model_hollow.name = f"{Model.name}_hollow"
            mesh_hollow = Model_hollow.data
            mesh_hollow.name = f"{Model.name}_hollow_mesh"


            # Duplicate Model_hollow and make a low resolution duplicate :

            bpy.ops.object.duplicate_move()

            # Rename Model_lowres :

            Model_lowres = bpy.context.view_layer.objects.active
            Model_lowres.name = "Model_lowres"
            mesh_lowres = Model_lowres.data
            mesh_lowres.name = "Model_lowres_mesh"

            # Get Model_lowres :

            bpy.ops.object.select_all(action="DESELECT")
            Model_lowres.select_set(True)
            bpy.context.view_layer.objects.active = Model_lowres

            # remesh Model_lowres 1.0 mm :

            bpy.context.object.data.use_remesh_smooth_normals = True
            bpy.context.object.data.use_remesh_preserve_volume = True
            bpy.context.object.data.use_remesh_fix_poles = True
            bpy.context.object.data.remesh_voxel_size = 1.0
            bpy.ops.object.voxel_remesh()

            # Add Metaballs :

            obj = bpy.context.view_layer.objects.active

            loc, rot, scale = obj.matrix_world.decompose()

            verts = obj.data.vertices
            vcords = [ rot  @ v.co + loc for v in verts]
            mball_elements_cords = [ vco - vcords[0] for vco in vcords[1:]]

            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")

            bpy.ops.object.metaball_add(type='BALL', radius=1.7, enter_editmode=False, location= vcords[0])

            Mball_object = bpy.context.view_layer.objects.active
            Mball_object.name = "Mball_object"
            mball = Mball_object.data
            mball.resolution = 0.6
            bpy.context.object.data.update_method = 'FAST'

            for i in range(len(mball_elements_cords)) :
                element = mball.elements.new()
                element.co = mball_elements_cords[i]
                element.radius = 3.4

            bpy.ops.object.convert(target='MESH')

            Mball_object = bpy.context.view_layer.objects.active
            Mball_object.name = "Mball_object"
            mball_mesh = Mball_object.data
            mball_mesh.name = "Mball_object_mesh"

            # Make boolean intersect operation :

            bpy.ops.object.select_all(action="DESELECT")
            Model_hollow.select_set(True)
            bpy.context.view_layer.objects.active = Model_hollow

            bpy.ops.object.modifier_add(type='BOOLEAN')
            bpy.context.object.modifiers["Boolean"].show_viewport = False
            bpy.context.object.modifiers["Boolean"].operation = 'INTERSECT'
            bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["Mball_object"]
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

            # Delet Model_lowres and Mball_object:

            bpy.ops.object.select_all(action="DESELECT")
            Model_lowres.select_set(True)
            bpy.context.view_layer.objects.active = Model_lowres
            Mball_object.select_set(True)

            bpy.ops.object.delete(use_global=False, confirm=False)
            

            # Hide everything but hollow model :

            bpy.ops.object.select_all(action="DESELECT")
            Model_hollow.select_set(True)
            bpy.context.view_layer.objects.active = Model_hollow

            bpy.ops.object.shade_flat()
            #bpy.ops.object.hide_view_set(unselected=True)

            #bpy.ops.view3d.view_all(center=True)
            """

            act_obj = Model_hollow
            if act_obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(act_obj.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(act_obj.data)
            new_mesh = bmesh.new()

            onm = {} # old index to new vert map
            for v in [v for v in bm.verts if v.select]:
                #norm_trans = v.co + v.normal * 0.3
                nv = new_mesh.verts.new(v.co)
                onm[v.index] = nv

            for f in [f for f in bm.faces if f.select]:
                nfverts = [onm[v.index] for v in f.verts]
                new_mesh.faces.new(nfverts)

            #bpy.ops.object.editmode_toggle()
            scene = bpy.context.scene

            new_data = bpy.data.meshes.new("mymesh2")
            new_mesh.to_mesh(new_data)
            obj = bpy.data.objects.new("SplitObj2", new_data)
            bpy.context.scene.collection.objects.link(obj)
            bpy.data.objects["SplitObj2"].location = bpy.data.objects[act_obj.name].location
            #bpy.context.scene.update()
            #bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)
            


            bm.free()
            new_mesh.free()
            
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['SplitObj2'].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects['SplitObj2']
            #return {"FINISHED"}
            #bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            
            #view_rotation = bpy.context.space_data.region_3d.view_rotation
            #view3d_rot_matrix = view_rotation.to_matrix().to_3x3()

            world_view = bpy.context.space_data.region_3d.view_rotation #@ Vector((0,0,1))
            local_view = act_obj.matrix_world.inverted().to_quaternion() @ world_view
            view3d_rot_matrix = local_view.to_matrix().to_3x3()

            #bpy.ops.transform.resize(value=(1.1, 1.1, 1), orient_type='LOCAL', orient_matrix=view3d_rot_matrix, orient_matrix_type='LOCAL', constraint_axis=(True, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, release_confirm=True)
            #return {"FINISHED"}
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.context.tool_settings.mesh_select_mode = (False, False, True)
            bpy.ops.mesh.select_all(action='SELECT')

            #bpy.ops.mesh.extrude_region_shrink_fatten(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_shrink_fatten={"value":1, "use_even_offset":True, "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "release_confirm":False, "use_accurate":False})
            #return {"FINISHED"}
            bpy.ops.mesh.extrude_region_move()
            bpy.ops.transform.translate(value=(0,0,5), constraint_axis=(False, False, True), orient_matrix=view3d_rot_matrix)

            bpy.ops.object.editmode_toggle()
            bpy.ops.transform.translate(value=(0, 0, -1), orient_type='LOCAL', orient_matrix=view3d_rot_matrix, orient_matrix_type='LOCAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, release_confirm=True)
            #return {"FINISHED"}
            bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')

            act_obj = bpy.data.objects['SplitObj2']
            if act_obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(act_obj.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(act_obj.data)
            for v in bm.verts:
                v.co += v.normal * 0.3
            bm.free()
            #return {"FINISHED"}

            
            bpy.context.tool_settings.mesh_select_mode = (False, False, True)
            #bpy.ops.mesh.extrude_region_shrink_fatten(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_shrink_fatten={"value":-1, "use_even_offset":True, "mirror":False, "use_proportional_edit":True, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":True, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "release_confirm":False, "use_accurate":False})
            
            
            
            bpy.ops.object.editmode_toggle()
            bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")
            bpy.ops.object.select_all(action='DESELECT')
            """

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')

            #calculate bounding box center of original mesh
            #o = bpy.context.object
            local_bbox_center = 0.125 * sum((Vector(b) for b in Model_hollow.bound_box), Vector())
            global_bbox_center = Model_hollow.matrix_world @ local_bbox_center

            cut_plane_pos = global_bbox_center + 7*(context.space_data.region_3d.view_rotation @ Vector((0,0,-1)))

            bpy.ops.mesh.bisect(plane_co=tuple(cut_plane_pos), plane_no=tuple(context.space_data.region_3d.view_rotation @ Vector((0,0,-1))), use_fill=True, clear_inner=False, clear_outer=True)
            bpy.ops.object.editmode_toggle()

            return {"FINISHED"}

            act_obj = Model_hollow
            bpy.data.objects[act_obj.name].select_set(True)
            bpy.context.view_layer.objects.active = act_obj
            #bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")
            bool_base_cut = bpy.data.objects[act_obj.name].modifiers.new(type="BOOLEAN", name="bool_base_cut")
            bool_base_cut.object = bpy.data.objects["SplitObj2"]
            bool_base_cut.operation = 'DIFFERENCE'
            #bpy.ops.object.modifier_apply(modifier="bool_base_cut")
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects["SplitObj2"]
            bpy.data.objects["SplitObj2"].select_set(True)
            #bpy.ops.object.delete() 


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

            # Prepare scene settings :

            bpy.ops.view3d.snap_cursor_to_center(context)
            bpy.ops.transform.select_orientation(context, orientation="GLOBAL")
            bpy.context.scene.tool_settings.transform_pivot_point = "INDIVIDUAL_ORIGINS"
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.scene.tool_settings.use_proportional_edit_objects = False
            bpy.ops.object.mode_set(mode="OBJECT")


            ####### Duplicate Model #######
                        
            # Get active Object :

            Model = bpy.context.view_layer.objects.active

            # Duplicate Model to Model_Base :

            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model
            bpy.ops.object.duplicate_move()

            # Rename Model_Base :

            Model_base = bpy.context.view_layer.objects.active
            Model_base.name = f"{Model.name}_base"
            mesh_base = Model_base.data
            mesh_base.name = f"{Model.name}_base_mesh"

            bpy.ops.object.select_all(action="DESELECT")
            Model_base.select_set(True)
            bpy.context.view_layer.objects.active = Model_base


            ####### Flip Model_Base to top view #######

            view_rotation = my_space.region_3d.view_rotation
            view3d_rot_matrix = view_rotation.to_matrix().to_4x4()

            flip_matrix = view3d_rot_matrix.inverted()
            unflip_matrix = view3d_rot_matrix

            Model_base.matrix_world = flip_matrix @ Model_base.matrix_world

            # Select base boarder :
                        
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            # Make some calcul of average z_cordinate of border vertices :

            bpy.ops.object.mode_set(mode="OBJECT") 
            obj = bpy.context.view_layer.objects.active
            obj_mx = obj.matrix_world.copy()
            verts = obj.data.vertices           
            global_z_cords = [(obj_mx @ v.co)[2] for v in verts if v.select]

            max_z = max(global_z_cords)
            min_z = min(global_z_cords)
            offset = max_z - min_z

            bpy.ops.object.mode_set(mode="EDIT")

            # Border_2 = Extrude 1st border loop by offset/2 + 1 :

            extrude_value = (0, 0, -(offset/2 + 1.5))

            bpy.ops.mesh.extrude_region_move()
            bpy.ops.transform.translate(value=extrude_value, constraint_axis=(False, False, True))

            # Relax border loop :

            bpy.ops.mesh.looptools_relax(input="selected", interpolation="cubic",
            iterations="10", regular=True)

            # Scale Border_2 vertices to zero :

            bpy.ops.transform.resize(value=(1, 1, 0), constraint_axis=(False, False, True))

            # Border_3 = Extrude Border_2 by -10 :

            extrude_value = (0, 0, -6)

            bpy.ops.mesh.extrude_region_move()
            bpy.ops.transform.translate(value=extrude_value, constraint_axis=(False, False, True))

            # fill base :

            bpy.ops.mesh.fill()

            # Remove extra edges from Base face :

            bpy.ops.mesh.dissolve_limited()

            # Add vertex group Border_3 vertices :

            Model_base.vertex_groups.clear()
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)

            Model_base.vertex_groups.new(name=f"base_border_vgroup")
            bpy.ops.object.vertex_group_assign()

            # Repare geometry resuting from precedent operation :

            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.mesh.select_all(action="DESELECT")
            Model_base.vertex_groups.active_index = 0
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.mode_set(mode="OBJECT")

            # Hide everything but Model_base :

            bpy.ops.object.mode_set(mode="OBJECT")

            bpy.ops.object.shade_flat()

            bpy.ops.object.hide_view_set(context, unselected=True)

            # Model_base matrix_world reset :

            Model_base.matrix_world = unflip_matrix @ Model_base.matrix_world



            return {"FINISHED"}

class OPENDENTAL_OT_trim_base(bpy.types.Operator):
    """Dental Model base triming tool"""

    bl_idname = "opendental.trim_base"
    bl_label = "Trim Base"
    bl_options = {"REGISTER", "UNDO"}


    def modal(self, context, event):

        if event.type == "RET":

            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            Model = bpy.context.view_layer.objects.active
            loc = Model.location.copy()# get model location
            view_rotation = context.space_data.region_3d.view_rotation

            view3d_rot_matrix = view_rotation.to_matrix().to_4x4()# get v3d rotation matrix 4x4

            # Add cube :
            bpy.ops.mesh.primitive_cube_add(size=120, enter_editmode=False )

            frame = bpy.context.view_layer.objects.active
            frame.name = "my_frame_cutter"


            # Reshape and align cube :

            frame.matrix_world = view3d_rot_matrix 

            frame.location = loc
            frame.location[1] += 30

            bpy.context.object.display_type = 'WIRE'
            bpy.context.object.scale[1] = 0.5
            bpy.context.object.scale[2] = 2
            

            # Boolean :

            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model

            bpy.ops.object.modifier_add(type='BOOLEAN')
            bpy.context.object.modifiers["Boolean"].show_viewport = False
            bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
            bpy.context.object.modifiers["Boolean"].object = frame
            #bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

            # Select frame :

            bpy.ops.object.select_all(action="DESELECT")
            frame.select_set(True)
            bpy.context.view_layer.objects.active = frame

            bpy.context.scene.transform_orientation_slots[0].type = 'VIEW'
            
            message = " Move the frame (G + Y) and press confirm button ! Please make part to remove inside the frame "
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            bpy.types.Scene.base_trim_mode = True

            return {"FINISHED"}

        elif event.type == ("ESC"):
            bpy.types.Scene.base_trim_mode = False

            return {"CANCELLED"}


        else :

            # allow navigation
            return {"PASS_THROUGH"}

        

        return {"RUNNING_MODAL"}


    def invoke(self, context, event):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")
            bpy.types.Scene.base_trim_mode = False
            return {"CANCELLED"}

        else:

            if context.space_data.type == "VIEW_3D":

                # Hide everything but model :

                bpy.ops.object.mode_set(mode="OBJECT")

                Model = bpy.context.view_layer.objects.active
                bpy.ops.object.select_all(action="DESELECT")
                Model.select_set(True)

                #bpy.ops.object.hide_view_set(unselected=True)

                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

                message = " Please align View to Model and click 'ENTER' or 'Confirm' !"
                ShowMessageBox(message=message, icon="COLORSET_02_VEC")
                
                context.window_manager.modal_handler_add(self)

                bpy.types.Scene.base_trim_mode = True

                return {"RUNNING_MODAL"}

            else:

                self.report({"WARNING"}, "Active space must be a View3d")

                return {"CANCELLED"}

class OPENDENTAL_OT_trim_base_confirm(bpy.types.Operator):
    """confirm model trim base operation"""

    bl_idname = "opendental.trim_base_confirm"
    bl_label = "confirm"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context) :

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")
            bpy.types.Scene.base_trim_mode = False

            return {"CANCELLED"}

        else:
            
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.object.mode_set(mode="OBJECT")
            frame = bpy.data.objects["my_frame_cutter"]
            
            bpy.ops.object.select_all(action="DESELECT")
            frame.select_set(True)
            bpy.context.view_layer.objects.active = frame
            bpy.ops.object.select_all(action='INVERT')
            Model = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = Model

            bpy.context.scene.transform_orientation_slots[0].type = "GLOBAL"
            bpy.ops.wm.tool_set_by_id(name="builtin.select")

            # get initial location :

            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            loc_initial = Model.location.copy() 

            # get initial state :

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.object.mode_set(mode="OBJECT")
            verts_initial = Model.data.vertices
            selected_verts_initial =  [v for v in verts_initial if v.select]  

            # ....Add undo history point...:
            bpy.ops.ed.undo_push()

            # Subdivide cube 10 iterations 3 times :

            bpy.ops.object.select_all(action="DESELECT")
            frame.select_set(True)
            bpy.context.view_layer.objects.active = frame

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.subdivide(number_cuts=10)
            #bpy.ops.mesh.subdivide(number_cuts=9)
            bpy.ops.object.mode_set(mode="OBJECT")

            # ....Add undo history point...:
            bpy.ops.ed.undo_push()

            # Apply boolean modifier :

            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model

            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            
            # Result Check :

            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            loc_current = Model.location.copy()

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.object.mode_set(mode="OBJECT")
            verts_current = Model.data.vertices
            
            selected_verts =  [v for v in verts_current if v.select]         

            if selected_verts_initial == [] : #closed mesh

                if selected_verts == [] and loc_current != loc_initial:

                    # Delete frame :
                    frame = bpy.data.objects["my_frame_cutter"]
                    bpy.ops.object.select_all(action="DESELECT")
                    frame.select_set(True)
                    bpy.context.view_layer.objects.active = frame
                    bpy.ops.object.delete(use_global=False, confirm=False)

                    bpy.ops.object.select_all(action="DESELECT")
                    Model.select_set(True)
                    bpy.context.view_layer.objects.active = Model

                    message = " Model is succeffuly trimed !"
                    ShowMessageBox(message=message, icon="COLORSET_03_VEC")

                    print("operation done in 1st check")
                
                    return {"FINISHED"}

                else :

                    bpy.ops.ed.undo()
                    frame = bpy.data.objects["my_frame_cutter"]
                    bpy.ops.object.select_all(action="DESELECT")
                    frame.select_set(True)
                    bpy.context.view_layer.objects.active = frame

                    frame.location[1] += 1

                    bpy.ops.object.mode_set(mode="EDIT")
                    bpy.ops.mesh.subdivide(number_cuts=10)
                    bpy.ops.object.mode_set(mode="OBJECT")

                    bpy.ops.object.select_all(action="DESELECT")
                    Model.select_set(True)
                    bpy.context.view_layer.objects.active = Model

                    ###............... Decimate Model ....................###

                    bpy.ops.object.mode_set(mode="OBJECT")
                    bpy.ops.object.modifier_add(type="DECIMATE")
                    bpy.context.object.modifiers["Decimate"].ratio = 0.7
                    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Decimate")
                    
                    # Apply boolean modifier :

                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

                    # recheck :

                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    loc_current = Model.location.copy()

                    bpy.ops.object.mode_set(mode="EDIT")
                    bpy.ops.mesh.select_all(action="DESELECT")
                    bpy.ops.mesh.select_non_manifold()

                    bpy.ops.object.mode_set(mode="OBJECT")
                    verts_current = Model.data.vertices
                    selected_verts =  [v for v in verts_current if v.select]         
                    

                    if selected_verts == [] and loc_current != loc_initial:

                        # Delete frame :
                        frame = bpy.data.objects["my_frame_cutter"]
                        bpy.ops.object.select_all(action="DESELECT")
                        frame.select_set(True)
                        bpy.context.view_layer.objects.active = frame
                        bpy.ops.object.delete(use_global=False, confirm=False)

                        bpy.ops.object.select_all(action="DESELECT")
                        Model.select_set(True)
                        bpy.context.view_layer.objects.active = Model

                        message = " Model is succeffuly trimed !"
                        ShowMessageBox(message=message, icon="COLORSET_03_VEC")

                        print("operation done in 2nd check")
                    
                        return {"FINISHED"}

                    else :
                        bpy.ops.ed.undo()

                        # Delete frame :
                        frame = bpy.data.objects["my_frame_cutter"]
                        bpy.ops.object.select_all(action="DESELECT")
                        frame.select_set(True)
                        bpy.context.view_layer.objects.active = frame
                        bpy.ops.object.delete(use_global=False, confirm=False)

                        # remove boolean modifier :

                        bpy.ops.object.select_all(action="DESELECT")
                        Model.select_set(True)
                        bpy.context.view_layer.objects.active = Model
                        bpy.ops.object.modifier_remove(modifier="Boolean")

                        bpy.ops.object.select_all(action="DESELECT")
                        Model.select_set(True)
                        bpy.context.view_layer.objects.active = Model

                        message = " Model trim operation failed please try to trim model manualy !"
                        ShowMessageBox(message=message, icon="COLORSET_01_VEC")

                        bpy.types.Scene.base_trim_mode = False

                        return {"CANCELLED"}

            else : # Open mesh

                if loc_current != loc_initial:

                    # Delete frame :
                    frame = bpy.data.objects["my_frame_cutter"]
                    bpy.ops.object.select_all(action="DESELECT")
                    frame.select_set(True)
                    bpy.context.view_layer.objects.active = frame
                    bpy.ops.object.delete(use_global=False, confirm=False)

                    bpy.ops.object.select_all(action="DESELECT")
                    Model.select_set(True)
                    bpy.context.view_layer.objects.active = Model

                    message = " Model is succeffuly trimed !"
                    ShowMessageBox(message=message, icon="COLORSET_03_VEC")

                    print("operation done in 1st check")

                    bpy.types.Scene.base_trim_mode = False
                
                    return {"FINISHED"}

                else :

                    bpy.ops.ed.undo()
                    frame = bpy.data.objects["my_frame_cutter"]
                    bpy.ops.object.select_all(action="DESELECT")
                    frame.select_set(True)
                    bpy.context.view_layer.objects.active = frame

                    frame.location[1] += 1

                    bpy.ops.object.mode_set(mode="EDIT")
                    bpy.ops.mesh.subdivide(number_cuts=10)
                    bpy.ops.object.mode_set(mode="OBJECT")

                    bpy.ops.object.select_all(action="DESELECT")
                    Model.select_set(True)
                    bpy.context.view_layer.objects.active = Model

                    ###............... Decimate Model ....................###

                    bpy.ops.object.mode_set(mode="OBJECT")
                    bpy.ops.object.modifier_add(type="DECIMATE")
                    bpy.context.object.modifiers["Decimate"].ratio = 0.7
                    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Decimate")
                    
                    # Apply boolean modifier :

                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

                    # recheck :

                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    loc_current = Model.location.copy()

                    if loc_current != loc_initial:

                        # Delete frame :
                        frame = bpy.data.objects["my_frame_cutter"]
                        bpy.ops.object.select_all(action="DESELECT")
                        frame.select_set(True)
                        bpy.context.view_layer.objects.active = frame
                        bpy.ops.object.delete(use_global=False, confirm=False)

                        bpy.ops.object.select_all(action="DESELECT")
                        Model.select_set(True)
                        bpy.context.view_layer.objects.active = Model

                        message = " Model is succeffuly trimed !"
                        ShowMessageBox(message=message, icon="COLORSET_03_VEC")

                        print("operation done in 2nd check")

                        bpy.types.Scene.base_trim_mode = False
                    
                        return {"FINISHED"}

                    else :
                        bpy.ops.ed.undo()

                        # Delete frame :
                        frame = bpy.data.objects["my_frame_cutter"]
                        bpy.ops.object.select_all(action="DESELECT")
                        frame.select_set(True)
                        bpy.context.view_layer.objects.active = frame
                        bpy.ops.object.delete(use_global=False, confirm=False)

                        # remove boolean modifier :

                        bpy.ops.object.select_all(action="DESELECT")
                        Model.select_set(True)
                        bpy.context.view_layer.objects.active = Model
                        bpy.ops.object.modifier_remove(modifier="Boolean")

                        bpy.ops.object.select_all(action="DESELECT")
                        Model.select_set(True)
                        bpy.context.view_layer.objects.active = Model

                        message = " Model trim operation failed please try to trim model manualy !"
                        ShowMessageBox(message=message, icon="COLORSET_01_VEC")

                        bpy.types.Scene.base_trim_mode = False

                        return {"CANCELLED"}



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
            #bpy.ops.object.select_all(action="DESELECT")

            return {"FINISHED"}

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def register():
    bpy.utils.register_class(OPENDENTAL_OT_decimate_model)
    bpy.utils.register_class(OPENDENTAL_OT_clean_model)
    bpy.utils.register_class(OPENDENTAL_OT_model_base_type_select)
    bpy.utils.register_class(OPENDENTAL_OT_solid_model_base)
    bpy.utils.register_class(OPENDENTAL_OT_trim_base)
    bpy.utils.register_class(OPENDENTAL_OT_trim_base_confirm)
    bpy.utils.register_class(OPENDENTAL_OT_remesh_model)
    bpy.utils.register_class(OPENDENTAL_OT_hollow_model_base)

    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_decimate_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_clean_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_model_base_type_select)
    bpy.utils.unregister_class(OPENDENTAL_OT_solid_model_base)
    bpy.utils.unregister_class(OPENDENTAL_OT_trim_base)
    bpy.utils.unregister_class(OPENDENTAL_OT_trim_base_confirm)
    bpy.utils.unregister_class(OPENDENTAL_OT_remesh_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_hollow_model_base)
