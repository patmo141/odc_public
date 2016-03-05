'''
Created on Nov 20, 2012
#test commit tracker
Implant functions and operators

Some License might be in the source directory. Summary: don't be an asshole, but do whatever you want with this code
Author: Patrick Moore:  patrick.moore.bu@gmail.com
'''
import bpy
import os

from mathutils import Vector, Matrix

#from . 
import odcutils
from odcutils import get_settings
#from . 
import implant_utils


#Global variables (should they be?)
global lib_imp
global lib_imp_enum
lib_implants = []
lib_imp_enum = []

class OPENDENTAL_OT_implant_slice_view(bpy.types.Operator):
    '''Gives 3 orthogonal slices and one obliqe slice'''
    bl_idname = "opendental.slice_view"
    bl_label = "Slice View"
    bl_options = {'REGISTER','UNDO'}
    
    thickness = bpy.props.FloatProperty(name="Slice Thickness", description="view slice thickenss", default=1, min=1, max=10, step=5, precision=2, options={'ANIMATABLE'})
    def execute(self,context):
        
        view = bpy.context.space_data
        
        view.clip_end = view.clip_start + self.thickness
        
        if not view.region_quadviews:
            bpy.ops.screen.region_quadview()
            view.lock_cursor = True
                           
        return{'FINISHED'}
  
class OPENDENTAL_OT_implant_normal_view(bpy.types.Operator):
    '''Returns view from quad view to normal'''
    bl_idname = "opendental.normal_view"
    bl_label = "Normal View"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self,context):
        
        view = bpy.context.space_data        
        view.clip_end = view.clip_start + 10000
        
        
        if view.region_quadviews:
            bpy.ops.screen.region_quadview()
            view.lock_cursor = False
                           
        return{'FINISHED'}
        
class OPENDENTAL_OT_implant_from_contour(bpy.types.Operator):
    '''
    Places an implant down the axis of a already planned crown..
    '''
    bl_idname = 'opendental.implant_from_crown'
    bl_label = "Place Implants from Crowns"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "imp"
    
    
    def item_cb(self, context):
        return [(obj.name, obj.name, '') for obj in self.objs]
 
    objs = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    imp = bpy.props.EnumProperty(name="Implant Library Objects", 
                                 description="A List of the tooth library", 
                                 items=item_cb)
    depth = bpy.props.IntProperty(name = 'Depth', description = "milimeters below CEJ to place implant", default = 5)
    hardware = bpy.props.BoolProperty(name="Include Hardware", default=True)
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        teeth = odcutils.tooth_selection(context) #TODO:...make this poll work for all selected teeth...
        condition = False
        if teeth and len(teeth)>0:
            condition = True
             
        return condition
    
    def invoke(self,context,event):
        self.objs.clear()
        #here we grab the asset library from the addon prefs
        settings = get_settings()
        libpath = settings.imp_lib
        assets = odcutils.obj_list_from_lib(libpath, exclude = '_')
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
        #context.window_manager.invoke_search_popup(self.ob_list)
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        #TODO: Scene Preservation recording
        teeth = odcutils.tooth_selection(context)
        sce = bpy.context.scene
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] 
        
        for tooth in teeth:
            
            #see if there is a corresponding implant
            if tooth.name in sce.odc_implants:
                contour = bpy.data.objects.get(tooth.contour)
                Z  = Vector((0,0,-1))
                if contour:
                    
                    if tooth.axis:
                        Axis = bpy.data.objects.get(tooth.axis)
                        if Axis:
                            neg_z = Axis.matrix_world.to_quaternion() * Z
                            rot_diff = odcutils.rot_between_vecs(Vector((0,0,1)), neg_z)
                        else:
                            neg_z = contour.matrix_world.to_quaternion() * Z
                            rot_diff = odcutils.rot_between_vecs(Vector((0,0,1)), neg_z)
                    else:
                        neg_z = contour.matrix_world.to_quaternion() * Z
                        rot_diff = odcutils.rot_between_vecs(Vector((0,0,1)), neg_z)
                    mx = contour.matrix_world
                    x = mx[0][3]
                    y = mx[1][3]
                    z = mx[2][3]
                    
                    #CEJ Location
                    new_loc = odcutils.box_feature_locations(contour, Vector((0,0,-1)))
                    
                    Imp = implant_utils.place_implant(context, sce.odc_implants[tooth.name], new_loc, rot_diff, self.imp, hardware = self.hardware)
                    
                    #reposition platform below CEJ
                    world_mx = Imp.matrix_world
                    delta =  Imp.dimensions[2] * world_mx.to_3x3() * Vector((0,0,1)) + self.depth * world_mx.to_3x3() * Vector((0,0,1))
                    
                    world_mx[0][3] += delta[0]
                    world_mx[1][3] += delta[1]
                    world_mx[2][3] += delta[2]
                    #odcutils.reorient_object(Imp, rot_diff)
        
        odcutils.layer_management(sce.odc_implants, debug = False)
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[11] = True
        
        return {'FINISHED'}
        
class OPENDENTAL_OT_place_implant(bpy.types.Operator):
    '''Places Implant or swaps existing implant with new implant of your choice'''
    bl_idname = "opendental.place_implant"
    bl_label = "Place Implant"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "imp"

    def item_cb(self, context):
        return [(obj.name, obj.name, '') for obj in self.objs]
 
    objs = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    
    imp = bpy.props.EnumProperty(name="Implant Library Objects", 
                                 description="A List of the tooth library", 
                                 items=item_cb)
    hardware = bpy.props.BoolProperty(name="Include Hardware", default=False)
    
    @classmethod
    def polls(cls, context):
        return len(context.scene.odc_implants) > 0
        
    def invoke(self, context, event): 
        self.objs.clear()
        settings = get_settings()
        libpath = settings.imp_lib
        assets = odcutils.obj_list_from_lib(libpath, exclude = '_')
       
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
           
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self, context):
        settings = get_settings()
        dbg = settings.debug
        #if bpy.context.mode != 'OBJECT':
        #    bpy.ops.object.mode_set(mode = 'OBJECT')
        
        sce = context.scene
        n = sce.odc_implant_index
        implant_space = sce.odc_implants[n]
        
        implants = odcutils.implant_selection(context)
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] 
        
        if implants != []:
        
            for implant_space in implants:
                #check if space already has an implant object.
                #if so, delete, replace, print warning
                if implant_space.implant and implant_space.implant in bpy.data.objects:
                    self.report({'WARNING'}, "replacing the existing implant with the one you chose")
                    Implant = bpy.data.objects[implant_space.implant]
                    
                    
                    #the origin/location of the implant is it's apex
                    L = Implant.location.copy()  

                    world_mx = Implant.matrix_world.copy()
                    
                    #the platorm is the length of the implant above the apex, in the local Z direction
                    #local Z positive is out the apex, soit's negative.
                    #Put the cursor there
                    sce.cursor_location = L - Implant.dimensions[2] * world_mx.to_3x3() *  Vector((0,0,1))
                                        
                    #first get rid of children...so we can use the
                    #parent to find out who the children are
                    if Implant.children:
                        for child in Implant.children:
                            sce.objects.unlink(child)
                            child.user_clear()
                            bpy.data.objects.remove(child)
                            
                    #unlink it from the scene, clear it's users, remove it.
                    sce.objects.unlink(Implant)
                    Implant.user_clear()
                    #remove the object
                    bpy.data.objects.remove(Implant)
                    
                    
                    
                #TDOD what about the children/hardwares?
                else:
                    world_mx = Matrix.Identity(4)
                    
                world_mx[0][3]=sce.cursor_location[0]
                world_mx[1][3]=sce.cursor_location[1]
                world_mx[2][3]=sce.cursor_location[2]
                                        
                #is this more memory friendly than listing all objects?
                current_obs = [ob.name for ob in bpy.data.objects]
                
                #link the new implant from the library
                odcutils.obj_from_lib(settings.imp_lib,self.imp)
                
                #this is slightly more robust than trusting we don't have duplicate names.
                for ob in bpy.data.objects:
                    if ob.name not in current_obs:
                        Implant = ob
                        
                sce.objects.link(Implant)
                
                #this relies on the associated hardware objects having the parent implant
                #name inside them
                if self.hardware:
                    current_obs = [ob.name for ob in bpy.data.objects]
                    
                    inc = self.imp + '_'
                    hardware_list = odcutils.obj_list_from_lib(settings.imp_lib, include = inc)
                    print(hardware_list)
                    for ob in hardware_list:
                        odcutils.obj_from_lib(settings.imp_lib,ob)
                
                    for ob in bpy.data.objects:
                        if ob.name not in current_obs:
                            sce.objects.link(ob)
                            ob.parent = Implant
                            ob.layers[11] = True
                

                delta =  Implant.dimensions[2] * world_mx.to_3x3() * Vector((0,0,1))
                print(delta.length)
                world_mx[0][3] += delta[0]
                world_mx[1][3] += delta[1]
                world_mx[2][3] += delta[2]
                    

                Implant.matrix_world = world_mx

                
                if sce.odc_props.master:
                    Master = bpy.data.objects[sce.odc_props.master]
                    odcutils.parent_in_place(Implant, Master)
                else:
                    self.report({'WARNING'}, 'No Master Model, placing implant anyway, moving objects may not preserve spatial relationships')
                
                #looks a little redundant, but it ensure if any
                #duplicates exist our referencing stays accurate
                Implant.name = implant_space.name + '_' + Implant.name
                implant_space.implant = Implant.name
                    
                odcutils.layer_management(sce.odc_implants, debug = dbg)
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[11] = True           
        return {'FINISHED'}

class OPENDENTAL_OT_place_sleeve(bpy.types.Operator):
    '''Places or replace guide sleeve at specified depth'''
    bl_idname = "opendental.place_guide_sleeve"
    bl_label = "Place Sleeve"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "drill"

    def item_cb(self, context):
        return [(obj.name, obj.name, '') for obj in self.objs]
 
    objs = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    
    drill = bpy.props.EnumProperty(name="Drill/Sleeve Library", 
                                 description="A List of the items library", 
                                 items=item_cb)
    
    depth = bpy.props.FloatProperty(name="Depth", description="Top edge to apex of implant", default=20, min=0, max=30, step=5, precision=2, options={'ANIMATABLE'}) 
    
    @classmethod
    def polls(cls, context):
        return len(context.scene.odc_implants) > 0
        
    def invoke(self, context, event): 
        self.objs.clear()
        settings = get_settings()
        libpath = settings.drill_lib
        assets = odcutils.obj_list_from_lib(libpath, exclude = 'Drill')
       
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
           
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self, context):
        settings = get_settings()
        dbg = settings.debug
        #if bpy.context.mode != 'OBJECT':
        #    bpy.ops.object.mode_set(mode = 'OBJECT')
        
        sce = context.scene
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        implants = odcutils.implant_selection(context)
        
        if implants != []:
        
            for implant_space in implants:
                #check if space already has an implant object.
                #if so, delete, replace, print warning
                Implant = bpy.data.objects[implant_space.implant]
                if Implant.rotation_mode != 'QUATERNION':
                    Implant.rotation_mode = 'QUATERNION'
                    Implant.update_tag()
                    sce.update()
                    
                if bpy.data.objects.get(implant_space.sleeve):
                    self.report({'WARNING'}, "replacing the existing sleeve with the one you chose")
                    Sleeve = bpy.data.objects[implant_space.sleeve]
                    #unlink it from the scene, clear it's users, remove it.
                    sce.objects.unlink(Sleeve)
                    Implant.user_clear()
                    #remove the object
                    bpy.data.objects.remove(Sleeve)
                    
                current_obs = [ob.name for ob in bpy.data.objects]
                
                #link the new implant from the library
                odcutils.obj_from_lib(settings.drill_lib,self.drill)
                
                #this is slightly more robust than trusting we don't have duplicate names.
                for ob in bpy.data.objects:
                    if ob.name not in current_obs:
                        Sleeve = ob
                        
                sce.objects.link(Sleeve)
                
                mx_w = Implant.matrix_world.copy()
                #point the right direction
                Sleeve.rotation_mode = 'QUATERNION'
                Sleeve.rotation_quaternion = mx_w.to_quaternion()          
                Sleeve.update_tag()
                context.scene.update()   
                Trans = Sleeve.rotation_quaternion * Vector((0,0,-self.depth))
                Sleeve.matrix_world[0][3] = mx_w[0][3] + Trans[0]
                Sleeve.matrix_world[1][3] = mx_w[1][3] + Trans[1]
                Sleeve.matrix_world[2][3] = mx_w[2][3] + Trans[2]
                
                Sleeve.name = implant_space.name + '_' + 'Sleeve'
                implant_space.sleeve = Sleeve.name
                Sleeve.update_tag()
                context.scene.update()    
                odcutils.parent_in_place(Sleeve, Implant)
                odcutils.layer_management(sce.odc_implants, debug = dbg)
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[19] = True
                        
        return {'FINISHED'}
    
class OPENDENTAL_OT_place_drill(bpy.types.Operator):
    '''Places or replaces drill at specified depth'''
    bl_idname = "opendental.place_drill"
    bl_label = "Place Drill"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "drill"

    def item_cb(self, context):
        return [(obj.name, obj.name, '') for obj in self.objs]
 
    objs = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    
    drill = bpy.props.EnumProperty(name="Drill Library", 
                                 description="A List of the items library", 
                                 items=item_cb)
    
    depth = bpy.props.FloatProperty(name="Depth", description="Distance tip of drill to implant apex", default=0, min=-4, max=10, step=5, precision=2, options={'ANIMATABLE'}) 
    
    @classmethod
    def polls(cls, context):
        return len(context.scene.odc_implants) > 0
        
    def invoke(self, context, event): 
        self.objs.clear()
        settings = get_settings()
        libpath = settings.drill_lib
        assets = odcutils.obj_list_from_lib(libpath, include = 'Drill', exclude = 'Sleeve')
       
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
           
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self, context):
        settings = get_settings()
        dbg = settings.debug
        #if bpy.context.mode != 'OBJECT':
        #    bpy.ops.object.mode_set(mode = 'OBJECT')
        
        sce = context.scene
        implants = odcutils.implant_selection(context)
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        if implants != []:
        
            for implant_space in implants:
                #check if space already has an implant object.
                #if so, delete, replace, print warning
                Implant = bpy.data.objects[implant_space.implant]
                
                if Implant.rotation_mode != 'QUATERNION':
                    Implant.rotation_mode = 'QUATERNION'
                    Implant.update_tag()
                    sce.update()
                    
                if bpy.data.objects.get(implant_space.drill):
                    self.report({'WARNING'}, "replacing the existing drill with the one you chose")
                    Sleeve = bpy.data.objects[implant_space.drill]
                    #unlink it from the scene, clear it's users, remove it.
                    sce.objects.unlink(Sleeve)
                    Implant.user_clear()
                    #remove the object
                    bpy.data.objects.remove(Sleeve)
                    
                current_obs = [ob.name for ob in bpy.data.objects]
                
                #link the new implant from the library
                settings = get_settings()
                odcutils.obj_from_lib(settings.drill_lib,self.drill)
                
                #this is slightly more robust than trusting we don't have duplicate names.
                for ob in bpy.data.objects:
                    if ob.name not in current_obs:
                        Sleeve = ob
                        
                sce.objects.link(Sleeve)
                Sleeve.layers[19] = True
                mx_w = Implant.matrix_world.copy()
                #point the right direction
                Sleeve.rotation_mode = 'QUATERNION'
                Sleeve.rotation_quaternion = mx_w.to_quaternion()          
                Sleeve.update_tag()
                context.scene.update()   
                Trans = Sleeve.rotation_quaternion * Vector((0,0,-self.depth))
                Sleeve.matrix_world[0][3] = mx_w[0][3] + Trans[0]
                Sleeve.matrix_world[1][3] = mx_w[1][3] + Trans[1]
                Sleeve.matrix_world[2][3] = mx_w[2][3] + Trans[2]
                
                Sleeve.name = implant_space.name + '_' + Sleeve.name
                implant_space.drill = Sleeve.name
                Sleeve.update_tag()
                context.scene.update()    
                odcutils.parent_in_place(Sleeve, Implant)
                odcutils.layer_management(sce.odc_implants, debug = dbg)
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[19] = True                
        return {'FINISHED'}
    
class OPENDENTAL_OT_implant_guide_cylinder(bpy.types.Operator):
    '''Implant Guide Cylinder'''
    bl_idname = "opendental.implant_guide_cylinder"
    bl_label = "Guide Cylinder"
    bl_options = {'REGISTER','UNDO'}
    

    #inner = bpy.props.FloatProperty(name="Slice Thickness", description="view slice thickenss", default=1, min=1, max=10, step=5, precision=2, options={'ANIMATABLE'})
    width = bpy.props.FloatProperty(name="Width", description="Width of Support", default=6, min=1, max=10, step=5, precision=2, options={'ANIMATABLE'})
    depth = bpy.props.FloatProperty(name="Top Edge to Apex of Implant", description="", default=20, min=10, max=30, step=5, precision=2, options={'ANIMATABLE'})
    trim_width = bpy.props.FloatProperty(name="Trim Width", description="Amount to shave off sides", default=0, min=0, max=4, step=5, precision=2, options={'ANIMATABLE'})
    use_wedge = bpy.props.BoolProperty(name = 'Use Wedge', description = "Make a fraction of a full circle", default = False)
    pctg = bpy.props.FloatProperty(name="Wedge pctg", description="Fraction of full circle to make", default=.65, min=0, max=1, step=5, precision=2, options={'ANIMATABLE'})
    
    
    def invoke(self, context, event): 
               
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}
    
    def execute(self,context):
        settings = get_settings()
        dbg  = settings.debug
        odcutils.scene_verification(context.scene, debug = dbg)
        spaces = odcutils.implant_selection(context)
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        for space in spaces:
            if not space.implant:
                self.report({'WARNING'}, "It seems you have not yet placed an implant for %s" % space.name)
            else:
                implant_utils.implant_outer_cylinder(context, space, 
                           self.width, self.depth, 
                           trim = self.trim_width, 
                           wedge = self.use_wedge, 
                           wedge_pct = self.pctg,
                           debug = dbg)    
        
            
        
        odcutils.material_management(context, context.scene.odc_implants)
        odcutils.layer_management(context.scene.odc_implants, debug = dbg)
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[19] = True
        return {'FINISHED'}
 
class OPENDENTAL_OT_implant_inner_cylinder(bpy.types.Operator):
    '''
    Makes a cylinder the same diameter as the implant unless
    override thickness is used in which case it uses the
    user specified diameter
    '''
    bl_idname = "opendental.implant_inner_cylinder"
    bl_label = "Inner Cylinder"
    bl_options = {'REGISTER','UNDO'}
    
    use_thickness = bpy.props.BoolProperty(name="Manual Diameter", default=True)
    thickness = bpy.props.FloatProperty(name="Cylinder Diameter", description="diameter of the hole", default=5, min=1, max=7, step=5, precision=1, options={'ANIMATABLE'})

    def execute(self,context):
        settings = get_settings()
        dbg  = settings.debug
        odcutils.scene_verification(context.scene, debug = dbg)
        spaces = odcutils.implant_selection(context)
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        for space in spaces: 
            if not space.implant:
                self.report({'WARNING'}, "It seems you have not yet placed an implant for %s" % space.name)
        
            else:
                if self.use_thickness:
                    thickness = self.thickness
                else:
                    thickness = None
                
                implant_utils.implant_inner_cylinder(context, space, thickness = thickness, debug = dbg)
        
        
        odcutils.material_management(context, context.scene.odc_implants) 
        odcutils.layer_management(context.scene.odc_implants, debug = dbg)
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[9] = True
        return {'FINISHED'}   
            
def post_register2():
    print('not needed')

def update_link_operators():
    #unregister get crown
    bpy.utils.unregister_class(OPENDENTAL_OT_place_implant)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_from_contour)
    #redefinte list from user prefs prop
    global lib_teeth_enum
    global lib_teeth
    lib_teeth_enum = []
    lib_teeth = []
    settings = get_settings()
    dbg = settings.debug
    lib_teeth = odcutils.obj_list_from_lib(settings.tooth_lib, exclude = '_', debug = dbg)
    for ind, obj in enumerate(lib_teeth):
        lib_teeth_enum.append((str(ind), obj, str(ind)))
    
    #reregister.
    bpy.utils.register_class(OPENDENTAL_OT_place_implant)
    bpy.utils.register_class(OPENDENTAL_OT_implant_from_contour)

           
def register():
    
    bpy.utils.register_class(OPENDENTAL_OT_implant_guide_cylinder)
    bpy.utils.register_class(OPENDENTAL_OT_implant_inner_cylinder)
    bpy.utils.register_class(OPENDENTAL_OT_implant_slice_view)
    bpy.utils.register_class(OPENDENTAL_OT_implant_normal_view)
    bpy.utils.register_class(OPENDENTAL_OT_implant_from_contour)
    bpy.utils.register_class(OPENDENTAL_OT_place_implant)
    bpy.utils.register_class(OPENDENTAL_OT_place_sleeve)
    bpy.utils.register_class(OPENDENTAL_OT_place_drill)
    #bpy.utils.register_module(__name__)

def unregister():

    bpy.utils.unregister_class(OPENDENTAL_OT_implant_guide_cylinder)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_inner_cylinder)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_slice_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_normal_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_place_implant)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_from_contour)
    bpy.utils.unregister_class(OPENDENTAL_OT_place_sleeve)
    bpy.utils.unregister_class(OPENDENTAL_OT_place_drill)
    
#    bpy.utils.unregister_class(SetMaster)

if __name__ == "__main__":
    register()