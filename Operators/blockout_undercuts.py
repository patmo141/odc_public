#Python Imports
import math
from math import degrees, radians, pi

#Blender Imports
import bpy
from mathutils import Vector

#Addon Imports
from Addon_utils import odcutils

#Popup message box function :

def ShowMessageBox(message="", title="INFO", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


color = {
    "No color selected": [1.0, 0.9, 0.8, 1],
    "Green": [0, 1.0, 0.0, 1],
    "Blue": [0.0, 0.02, 0.19, 1],
    "Violet": [0.16, 0.0, 0.19, 1],
    "Pink": [1.0, 0.3, 1.0, 1],
}


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

        colorprop = context.scene.UNDERCUTS_view_props.colorprop

        context.scene.UNDERCUTS_view_props.survey_quaternion = context.space_data.region_3d.view_rotation

        bpy.types.Scene.pre_surveyed = True
        
        
        if bpy.context.selected_objects == []:

            message = " Please select the Model to survey !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        elif colorprop == "No color selected" :

            message = " Please select a color for the survey zone !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:

            # ...........................Prepare scene settings : ..............................................

            # bpy.ops.view3d.snap_cursor_to_center()
            bpy.context.scene.transform_orientation_slots[0].type = "GLOBAL"
            bpy.context.scene.tool_settings.transform_pivot_point = "ACTIVE_ELEMENT"
            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.tool_settings.mesh_select_mode = (False, False, True)
            bpy.ops.object.mode_set(mode = 'OBJECT')

            # Get active Object :..........................................................

            Model = bpy.context.view_layer.objects.active
            Model_name = Model.name

            if not f"_survey({colorprop})" in Model_name : 

                # Remove old survey model and silhouette :
                for obj in bpy.data.objects :

                    if obj.name.endswith((f"_survey({colorprop})", f"_survey({colorprop})_silhouette"))  :
                        
                        bpy.ops.object.hide_view_clear()
                        bpy.ops.object.select_all(action="DESELECT")
                        obj.select_set(True)
                        bpy.context.view_layer.objects.active = obj

                        bpy.ops.object.delete(use_global=False, confirm=False)
            
                # duplicate Model :

                bpy.ops.object.select_all(action="DESELECT")
                Model.select_set(True)
                bpy.context.view_layer.objects.active = Model
                bpy.ops.object.duplicate_move()
                Model_Survey = bpy.context.view_layer.objects.active
                mesh_Survey = Model_Survey.data 
                bpy.ops.object.select_all(action="DESELECT")
                Model_Survey.select_set(True)

                # Rename Model_Survey :
            
                if "_solid_base" in Model_name :
                    Model_Survey.name = Model_name.replace("_solid_base", "_")

                Model_Survey.name += f"survey({colorprop})"
                mesh_Survey.name = f"{Model_Survey.name}_mesh"
                
            else :

                Model_Survey = Model
                mesh_Survey = Model_Survey.data
                # Remove old silhouette :
                for obj in bpy.data.objects :

                    if obj.name.endswith(f"_survey({colorprop})_silhouette")  :
                        
                        bpy.ops.object.hide_view_clear()
                        bpy.ops.object.select_all(action="DESELECT")
                        obj.select_set(True)
                        bpy.context.view_layer.objects.active = obj

                        bpy.ops.object.delete(use_global=False, confirm=False)
            
                
            # Model_Survey add material :

            bpy.ops.object.select_all(action="DESELECT")
            Model_Survey.select_set(True)
            bpy.context.view_layer.objects.active = Model_Survey

            for _ in range(len(Model_Survey.material_slots)) :
                
                bpy.ops.object.material_slot_remove()


            mat_list = []

            for mat in bpy.data.materials:

                mat_list.append(mat.name)


            if not "my_Neutral" in mat_list:

                Model_mat = bpy.data.materials.new("my_Neutral")
                Model_mat.diffuse_color = [0.8, 0.8, 0.8, 1]

            else:

                Model_mat = bpy.data.materials["my_Neutral"]

            mesh_Survey.materials.append(Model_mat)

            

            survey_matname = f"survey_materiel({colorprop})"
            survey_matcolor = color[colorprop]

            if not survey_matname in mat_list:

                Survey_mat = bpy.data.materials.new(survey_matname)
                Survey_mat.diffuse_color = survey_matcolor
                Survey_mat.roughness = 0.4

            else:

                Survey_mat = bpy.data.materials[survey_matname]

            mesh_Survey.materials.append(Survey_mat)
            Model_Survey.active_material_index = 1


            
            # #############################____Surveying____###############################

            global survey_faces_index_list
            
            survey_faces_index_list = []
            

            bpy.ops.object.select_all(action="DESELECT")
            Model_Survey.select_set(True)
            bpy.context.view_layer.objects.active = Model_Survey

            ob = Model_Survey
            world_view = context.space_data.region_3d.view_rotation @ Vector((0,0,1))
            local_view = ob.matrix_world.inverted().to_quaternion() @ world_view

            bpy.context.tool_settings.mesh_select_mode = (False, False, True)

            for f in ob.data.polygons:

                if f.normal.dot(local_view) < -0.000001:
                    survey_faces_index_list.append(f.index)

            
            # 4_# select survey faces :

            # ....Deselect everything first
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")

            # ....it seems we can only select faces during object mode
            bpy.ops.object.mode_set(mode="OBJECT")

            for i in survey_faces_index_list:
                face = ob.data.polygons[i]
                face.select = True

            # Remove old vertex groups :

            ob.vertex_groups.clear()
            
            # Add vertex group :

            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            Model_Survey.vertex_groups.new(name=f"my_survey_vgroup({colorprop})")
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.material_slot_assign()
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
            bpy.ops.object.select_all(action="DESELECT")
            Model_Survey.select_set(True)


            ob = Model_Survey
            view = context.space_data.region_3d.view_rotation @ Vector((0, 0, 1))
            odcutils.silouette_brute_force(
                context, ob, view, self.world, self.smooth #, debug=dbg
            )
            silhouette = bpy.context.view_layer.objects.active
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
            silhouette.select_set(True)
            Model_Survey.select_set(True)
            bpy.context.view_layer.objects.active = Model_Survey
            bpy.ops.object.hide_view_set(unselected=True)
            silhouette.select_set(False)
            
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
        ob = context.active_object
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

            message = " Please select the Model to Blockout !"
            ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"CANCELLED"}

        else:

            # ...........................Prepare scene settings : ..............................................

            # bpy.ops.view3d.snap_cursor_to_center()
            bpy.context.scene.transform_orientation_slots[0].type = "GLOBAL"
            bpy.context.scene.tool_settings.transform_pivot_point = "ACTIVE_ELEMENT"
            bpy.context.scene.tool_settings.use_snap = False

            # Get active Object :..........................................................

            ob = bpy.context.view_layer.objects.active

            ###  PATRICKS TEST ###############################
            ##################################################
            if bpy.types.Scene.pre_surveyed == True:
                world_view = context.scene.UNDERCUTS_view_props.survey_quaternion @ Vector((0,0,1))
            else:
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

            bpy.types.Scene.pre_surveyed = False

            # Rename Model_Survey :
            
            colorprop = context.scene.UNDERCUTS_view_props.colorprop

            if "_solid_base" in ob.name :
                ob_name = ob.name
                ob.name = ob_name.replace("_solid_base", "_")

            if f"_survey({colorprop})" in ob.name :
                ob_name = ob.name
                ob.name = ob_name.replace(f"_survey({colorprop})", "_")

            ob.name += "blocked"
            ob.data.name = f"{ob.name}_mesh"


        
        return {'FINISHED'}
        ### END PATRICK"S TEST   #########################
        ###################################################
    
def register():
    bpy.utils.register_class(OPENDENTAL_OT_survey_model)
    bpy.utils.register_class(OPENDENTAL_OT_blockout_model)
    bpy.utils.register_class(OPENDENTAL_OT_blockout_model_solid)

    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_survey_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_blockout_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_blockout_model_solid)
