'''
This module handles operators for the bridge functionality of ODC
The "meat" of the more complicated operator functions is in crown_methods.py
Some License might be in the source directory. Summary: don't be an asshole, but do whatever you want with this code
Author: Patrick Moore:  patrick.moore.bu@gmail.com
'''
import bpy
import bmesh
from bpy.props import BoolProperty
import odcutils, mesh_cut, bridge_methods, bgl_utils, full_arch_methods
from odcutils import get_settings
import math
import time


class OPENDENTAL_OT_bridge_from_selected(bpy.types.Operator):
    ''''''
    bl_idname='opendental.define_bridge'
    bl_label="Units to Bridge"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        teeth = odcutils.tooth_selection(context)  #TODO:...make this poll work for all selected teeth...
        condition_1 = len(teeth) > 1       
        return condition_1
    
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        bridge_methods.bridge_from_selection(context, debug=dbg)
        
        return {'FINISHED'}

class OPENDENTAL_OT_bridge_prebridge(bpy.types.Operator):
    ''''''
    bl_idname='opendental.make_prebridge'
    bl_label="Make Pre-Bridge"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if bridge_methods.active_spanning_restoration(context) != []:
            bridge  = bridge_methods.active_spanning_restoration(context)[0]#TODO:...make this poll work for all selected teeth...
            if bridge:
                return True
            else:
                print('no  bridge for you')
                return False
    
        else:
            return False
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
         
        odc_bridge = bridge_methods.active_spanning_restoration(context)[0]
        bridge_methods.make_pre_bridge(context, odc_bridge, debug=dbg) #TODO: debug settings
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
            
        context.scene.layers[5] = True
        odcutils.layer_management(context.scene.odc_bridges, debug = dbg)
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_bridge_boolean(bpy.types.Operator):
    '''
    Cuation This may take up to 1 minute for long spans!!
    Be patient
    '''
    bl_idname='opendental.bridge_boolean'
    bl_label="Boolean Bridge"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if bridge_methods.active_spanning_restoration(context) != [None]:
            bridge = bridge_methods.active_spanning_restoration(context)[0]#TODO:...make this poll work for all selected teeth...
            if bridge:
                return True
            else:
                return False
        else:
            return False
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        odc_bridge = bridge_methods.active_spanning_restoration(context)[0]
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True        
        bridge_teeth = [context.scene.odc_teeth[name] for name in odc_bridge.tooth_string.split(sep=":")]
        
        contour_obs = [bpy.data.objects.get(tooth.contour) for tooth in bridge_teeth]
        if None in contour_obs:
            bad_unit = contour_obs.index(None)
            bad_tooth = bridge_teeth[bad_unit].name
            self.report({'ERROR'}, 'Full Contour design missing for ' + bad_tooth)
            return {'CANCELLED'}

        left_teeth = []
        right_teeth = []
        for tooth in bridge_teeth:
            if tooth.name.startswith('2') or tooth.name.startswith('3'):
                left_teeth.append(tooth)
            else:
                right_teeth.append(tooth)

        print('left teeth')
        print([tooth.name for tooth in left_teeth])
        def get_key(tooth):
            return tooth.name
        print([tooth.name for tooth in sorted(left_teeth, key = get_key, reverse = True)])
        if len(left_teeth):
            left_teeth_sorted = [tooth for tooth in sorted(left_teeth, key = get_key, reverse = True)]
            left_contours = [bpy.data.objects.get(tooth.contour) for tooth in left_teeth_sorted]    
            left_base_ob = left_contours[0]
            print(left_base_ob.name)
            left_bridge_me = left_base_ob.to_mesh(context.scene, apply_modifiers = True, settings = 'PREVIEW')
            left_bridge_ob = bpy.data.objects.new(odc_bridge.name, left_bridge_me)
            left_bridge_ob.matrix_world = left_base_ob.matrix_world
            context.scene.objects.link(left_bridge_ob)
            
            print(left_bridge_ob.name)
            for i in range(1, len(left_contours)):
                print('adding boolean modifier')
                mod = left_bridge_ob.modifiers.new(str(i), 'BOOLEAN')
                mod.operation = 'UNION'
                mod.object = left_contours[i]
                print(left_contours[i].name)
            
            left_final_me = left_bridge_ob.to_mesh(context.scene, apply_modifiers = True, settings = 'PREVIEW')
            mods = [mod for mod in left_bridge_ob.modifiers]
            for mod in mods:
                left_bridge_ob.modifiers.remove(mod)
            
            left_bridge_ob.data = left_final_me
            odc_bridge.bridge = left_bridge_ob.name
            
        if len(right_teeth):
            right_teeth_sorted = [tooth for tooth in sorted(right_teeth, key = get_key, reverse = True)]
            right_contours = [bpy.data.objects.get(tooth.contour) for tooth in right_teeth_sorted]    
            right_base_ob = right_contours[0]
            right_bridge_me = right_base_ob.to_mesh(context.scene, apply_modifiers = True, settings = 'PREVIEW')
            right_bridge_ob = bpy.data.objects.new(odc_bridge.name, right_bridge_me)
            right_bridge_ob.matrix_world = right_base_ob.matrix_world
            context.scene.objects.link(right_bridge_ob)
            
            for i in range(1, len(right_contours)):
                mod = right_bridge_ob.modifiers.new(str(i), 'BOOLEAN')
                mod.operation = 'UNION'
                mod.object = right_contours[i]
            
            right_final_me = right_bridge_ob.to_mesh(context.scene, apply_modifiers = True, settings = 'PREVIEW')
            mods = [mod for mod in right_bridge_ob.modifiers]
            for mod in mods:
                right_bridge_ob.modifiers.remove(mod)
            
            right_bridge_ob.data = right_final_me
            odc_bridge.bridge = right_bridge_ob.name
            
        if len(left_teeth) and len(right_teeth):
            mod = left_bridge_ob.modifiers.new('Midline', 'BOOLEAN')
            mod.operation = 'UNION'
            mod.object = right_bridge_ob
            
            left_bridge_ob.update_tag()
            context.scene.update()
            
            final_me = left_bridge_ob.to_mesh(context.scene, apply_modifiers = True, settings = 'PREVIEW')
            mods = [mod for mod in left_bridge_ob.modifiers]
            for mod in mods:
                left_bridge_ob.modifiers.remove(mod)
            
            left_bridge_ob.data = final_me
            context.scene.objects.unlink(right_bridge_ob)
            bpy.data.objects.remove(right_bridge_ob)
            bpy.data.meshes.remove(right_bridge_me)
        
            odc_bridge.bridge = left_bridge_ob.name
        return {'FINISHED'} 

class OPENDENTAL_OT_solid_bridge(bpy.types.Operator):
    ''''''
    bl_idname='opendental.solid_bridge'
    bl_label="Solidify Bridge"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if bridge_methods.active_spanning_restoration(context) != []:
            bridge  =   bridge_methods.active_spanning_restoration(context)[0]#TODO:...make this poll work for all selected teeth...
            if bridge:
                return True
            else:
                return False
    
        else:
            return False
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        odc_bridge = bridge_methods.active_spanning_restoration(context)[0]
        sce = context.scene
        Bridge = bpy.data.objects.get(odc_bridge.bridge)
        if not Bridge:
            self.report({'ERROR'}, 'Use "Boolean Bridge" to join individual units to an outer shell first')
        
        go_local = False
        if context.space_data.local_view:
            go_local = True
            bpy.ops.view3d.localview()
            
        if len(Bridge.modifiers):
            me = Bridge.to_mesh(context.scene, True, 'PREVIEW')
            mods = [mod for mod in Bridge.modifiers]
            for mod in mods:
                Bridge.modifiers.remove(mod)
            Bridge.data = me
        
        ### Remove the bottom 3 edge loops
        bridge_bme = bmesh.new()
        bridge_bme.from_object(Bridge, context.scene)
        
        bridge_bme.edges.ensure_lookup_table()
        bridge_bme.verts.ensure_lookup_table()
        bridge_bme.faces.ensure_lookup_table()
        
        for i in range(0,3):
            non_man_eds = [ed for ed in bridge_bme.edges if not ed.is_manifold]
            bmesh.ops.delete(bridge_bme, geom = non_man_eds, context = 2)
            
            non_man_vs = [v for v in bridge_bme.verts if not v.is_manifold]
            bmesh.ops.delete(bridge_bme, geom = non_man_vs, context = 1)
            
            bridge_bme.edges.ensure_lookup_table()
            bridge_bme.verts.ensure_lookup_table()
            bridge_bme.faces.ensure_lookup_table()
        
        bridge_bme.to_mesh(Bridge.data)
        
        ### DONE Removing bottom 3 edge loops  ###
        
                
        bridge_teeth = [context.scene.odc_teeth[name] for name in odc_bridge.tooth_string.split(sep=":")]
        intag_objects = [bpy.data.objects.get(tooth.intaglio) for tooth in bridge_teeth if tooth.rest_type != '1']
        if None in intag_objects:
            self.report({'ERROR'}, 'Missing Intaglio for some abutments')
        
        bpy.ops.object.select_all(action = 'DESELECT')
        
        join_obs = []
        for ob in intag_objects:
            new_me = ob.to_mesh(context.scene, True, 'PREVIEW')
            new_ob = bpy.data.objects.new(ob.name + ' dupli', new_me)
            new_ob.matrix_world = ob.matrix_world
            context.scene.objects.link(new_ob)
            join_obs.append(new_ob)
            
        print(join_obs)
        bpy.ops.object.select_all(action = 'DESELECT')
        for ob in join_obs:
            ob.select = True
        Bridge.hide = False    
        Bridge.select = True
        context.scene.objects.active = Bridge
        
        Bridge.name += '_solid'
        bpy.ops.object.join()
        
        bridge_bme.free()
        bridge_bme = bmesh.new()    
        bridge_bme.from_mesh(Bridge.data, True)
        bridge_bme.edges.ensure_lookup_table()
        bridge_bme.verts.ensure_lookup_table()
        bridge_bme.faces.ensure_lookup_table()
        
        
        non_man = [ed for ed in bridge_bme.edges if not ed.is_manifold]
        bmesh.ops.bridge_loops(bridge_bme, edges = non_man, use_pairs = True)
        #non_man = [ed.index for ed in bridge_bme.edges if not ed.is_manifold]
        #loops = mesh_cut.edge_loops_from_bmedges(bridge_bme, non_man)
        
        #for loop in loops:
            #for i in loop:
                #bridge_bme.verts[i].select_set(True)
        
        bmesh.ops.recalc_face_normals(bridge_bme, faces = bridge_bme.faces[:])        
        bridge_bme.to_mesh(Bridge.data)
        #bridge_bme.transform(Bridge.matrix_world)
        
        #new_me = bpy.data.meshes.new(odc_bridge.name + '_solid')
        #bridge_bme.to_mesh(new_me)
        bridge_bme.free()

        #new_ob = bpy.data.objects.new(odc_bridge.name + '_solid', new_me)
        #context.scene.objects.link(new_ob)
        if go_local:
            bpy.ops.view3d.localview()
        
        return {'FINISHED'}

class OPENDENTAL_OT_bridge_keep_arch_plan(bpy.types.Operator):
    '''
    Solidify the arch constraint on individual teeth
    Warning, not sure how this works with parents!
    '''
    bl_idname='opendental.arch_plan_keep'
    bl_label="Keep Arch Plan"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if context.object:
            if context.object.type == 'CURVE':
                return True
        else:
            return False
    
    def execute(self,context):
        curve = context.object
        settings = get_settings()
        dbg = settings.debug
        full_arch_methods.keep_arch_plan(context, curve,debug = dbg)
        
        return {'FINISHED'}
     
class OPENDENTAL_OT_bridge_individual(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.bridge_individual'
    bl_label = "Bridge Individual"
    bl_options = {'REGISTER','UNDO'}
    
    #properties   
    #mvert_adj = bpy.props.FloatProperty(name="M. Vertical Adjust", description="", default=0, min=-2, max=2, step=2, precision=1, options={'ANIMATABLE'})    
    #mlat_adj = bpy.props.FloatProperty(name="M. Lateral Adjust", description="", default=0, min=-2, max=2, step=2, precision=1, options={'ANIMATABLE'})    
    #dvert_adj = bpy.props.FloatProperty(name="D Vertical Adjust", description="", default=0, min=-2, max=2, step=2, precision=1, options={'ANIMATABLE'})    
    #dlat_adj = bpy.props.FloatProperty(name="D Lateral Adjust", description="", default=0, min=-2, max=2, step=2, precision=1, options={'ANIMATABLE'})
    
    bulbous = bpy.props.FloatProperty(name="bulbous", description="", default=.5, min=0, max=1.5, step=2, precision=1, options={'ANIMATABLE'})
    twist = bpy.props.IntProperty(name="twist", description="twist", default=0, min=-5, max=5, options={'ANIMATABLE'})     
    smooth = bpy.props.IntProperty(name="smooth", description="smooth", default=3, min=0, max=20, options={'ANIMATABLE'})     

    @classmethod
    def poll(cls,context):
        bridges = bridge_methods.active_spanning_restoration(context)
        
        if len(bridges):
            bridge = bridges[0]
            condition_1 = bridge.bridge and bridge.bridge in bpy.data.objects
        else:
            condition_1 = False
            
        return condition_1
    
    def mes_distal_determine(self):
        mid_test = int(self.a) - (math.floor(int(self.a)/10))*10
        
        #test to see if a midline tooth (eg, 8,9,24,25) or (11,21,31,41)
        if  mid_test == 1:
            self.a_group = self.b_group = "_Mesial Connector"
            if math.fmod(math.floor(int(self.a)/10)*10,20):
                self.b = str(int(self.a) + 10)
            else:
                self.b = str(int(self.a) - 10)
        else:        
            self.b = str(int(self.a)-1)
            self.a_group = "_Mesial Connector"
            self.b_group = "_Distal Connector"
            
        if self.b not in self.units:
            self.a = str(int(self.a)+1)
            self.b = str(int(self.a)-1)        
        
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}
       
        elif event.type in {'SPACE'} and event.value == 'PRESS':
            print('spacebar')
            self.execute(context)
            return {'RUNNING_MODAL'}
        
        elif event.type in {'WHEELUPMOUSE'}:
            self.target_index = int(math.fmod(self.target_index +1, len(self.units)))
            self.a = self.units[self.target_index]
            
            self.mes_distal_determine()
            
            self.message = "Bridge between %s and %s" % (self.a, self.b)
            return {'RUNNING_MODAL'}
        
        elif event.type in {'WHEELDOWNMOUSE'}:
            if self.target_index > 0:
                self.target_index = int(math.fmod(self.target_index - 1 , len(self.units)))
                self.a = self.units[self.target_index]
                
                self.mes_distal_determine()
                
                self.message = "Bridge between %s and %s" % (self.a, self.b)
            return {'RUNNING_MODAL'}
        
        
        elif event.type in {'RET'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
        
        elif event.type in {'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}
        
        '''
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            print('double click')
            self.execute(context)
            self.target_index = int(math.fmod(self.target_index +1, len(self.units)))
            self.a = self.units[self.target_index]
            
            
            
            self.message = "Bridge between %s and %s" % (self.a, self.b)
            
            return {'RUNNING_MODAL'}
        '''

        return {'RUNNING_MODAL'}
    def invoke(self, context, event):

        if context.space_data.type == 'VIEW_3D':
            self.odc_bridge = bridge_methods.active_spanning_restoration(context)[0]
            #list of all teeth in the bridge
            self.units = self.odc_bridge.tooth_string.split(sep=":")
            self.target_index = 0
            self.a = self.units[0]
            self.b = self.units[1]
            self.a_group = "_Mesial Connector"
            self.b_group = "_Distal Connector"
            
            self.mes_distal_determine()
                
            if self.b not in self.units:
                self.report({'ERROR'}, "No neighboring tooth or I haven't figured out how to deal with non adjacent teeth")
                return {'CANCELLED'}
            
            self._handle = bpy.types.SpaceView3D.draw_handler_add(bgl_utils.general_func_callback, (self, context), 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)


            #guess which teeth we want to bridge
            #TODO: International vs Universal
            self.message = "Bridge between %s and %s" % (self.a, self.b)
            
            help_message = ["Scroll wheel to select connector","SPC to confirm","Leftmouse to confirm and advance","Esc to cancel"]
            self.wrap = max([len(string) for string in help_message]) + 5
            self.help = ""
            for message in help_message:
                jmessage = message + " " * (self.wrap - len(message))
                self.help += jmessage
            
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
            
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        Bridge = bpy.data.objects[self.odc_bridge.bridge]
        
        mes_tooth_distal_connector = self.b + self.b_group
        dis_tooth_mesial_connector = self.a + self.a_group
        
        [ob_sets, tool_sets, space_sets] = odcutils.scene_preserv(context, debug=dbg) #TODO: global debug
        
        bridge_methods.bridge_loop(context, Bridge, mes_tooth_distal_connector, dis_tooth_mesial_connector, 2, self.twist, self.bulbous, group3 = "Connectors", debug=True)
        
        odcutils.scene_reconstruct(context, ob_sets, tool_sets, space_sets, debug=dbg)
        return {'FINISHED'}

class OPENDENTAL_OT_BreakContact(bpy.types.Operator):
    '''Gently Separate two objects with lattice deformation'''
    bl_idname = "opendental.break_contact"
    bl_label = "Break Contact"
    bl_options = {'REGISTER','UNDO'}

    #arg grid size
    method = bpy.props.EnumProperty(name='Method', items = (('0','DEFORM','0'),('1','SLICE','1')), default = '0')
    
    sep = bpy.props.FloatProperty(name="Separation", description="Slice Thickness", default=.5, min=-10, max=10, options={'ANIMATABLE'})
    
    apply = bpy.props.BoolProperty(name="Apply", description="Apply the deformatino and delete lattice", default=False, options={'ANIMATABLE'})
    

    @classmethod
    def poll(cls, context):
        cond_1 = context.object
        cond_2 = len(context.selected_objects) == 2
        
        return cond_1 and cond_2
    
    def execute(self, context):
        #dbg = context.user_preferences.addons['odc'].preferences.debug
        ob1 = context.selected_objects[0]
        ob2 = context.selected_objects[1]
        print(ob1)
        print(ob2)
        print('did we make it this far?')
        if self.method == '0':
            bridge_methods.break_contact_deform(context, ob1, ob2, debug = 1)
        elif self.method == '1':
            bridge_methods.break_contact_slice(context, ob1, ob2, self.sep, debug = 1)
        
        
        return {'FINISHED'}

class OPENDENTAL_OT_keep_shape(bpy.types.Operator):
    '''Confirm and Apply Lattice and Shrinkwrap Modifiers after deforming or breaking contact'''
    bl_idname = "opendental.keep_shape"
    bl_label = "Keep Tooth Shape"
    bl_options = {'REGISTER','UNDO'}


    @classmethod
    def poll(cls, context):
        cond_1 = context.object
        cond_2 = len(context.selected_objects) >= 1
        cond_3 = context.mode == 'OBJECT'
        return cond_1 and cond_2 and cond_3
    
    def execute(self, context):
        #dbg = context.user_preferences.addons['odc'].preferences.debug
        obs = context.selected_objects
        to_delete = []
        
        if context.object:
            c_ob = context.object
        else:
            c_ob = None
            
        for ob in obs:
            
            for mod in ob.modifiers:
                if mod.type in {'SHRINKWRAP','LATTICE'}:
                    context.scene.objects.active = ob
                    ob.hide = False
                    bpy.ops.object.modifier_apply(modifier = mod.name)
                    
                    if mod.type =='LATTICE':
                        to_delete.append(mod.object)
                        
            for mod in ob.modifiers:
                if mod.type == 'MULTIRES':
                    bpy.ops.object.multires_base_apply(modifier = mod.name)

                
        bpy.ops.object.select_all(action='DESELECT')        
        for ob in to_delete:
            ob.select = True
            context.scene.objects.active = ob
            bpy.ops.object.delete(use_global = True)
            #lat = ob.data
            #ob.user_clear()
            #bpy.data.objects.remove(ob)
            #bpy.data.lattices.remove(lat)
            
        #context.scene.update()   
        
        for ob in obs:
            ob.select = True
            
        if c_ob:
            context.scene.objects.active = c_ob
            
        return {'FINISHED'}        

class OPENDENTAL_OT_ClothFillTray(bpy.types.Operator):
    '''Fill a bez loop or mesh loop with remesh'''
    bl_idname = "opendental.cloth_fill_tray"
    bl_label = "Cloth Fill Tray"
    bl_options = {'REGISTER','UNDO'}

    #arg  octree
    oct = bpy.props.IntProperty(name="Resolution", description="Octree Depth", default=4, min=1, max=10, options={'ANIMATABLE'})
    #some day I will be able to estimate the grid based on onctree and scale
    #arg grid size
    grid = bpy.props.FloatProperty(name="Grid", description="Grid", default=1, min=.01, max=10, options={'ANIMATABLE'})

    smooth = bpy.props.IntProperty(name="smooth", description="# of smooth iterations", default=5, min=1, max=20, options={'ANIMATABLE'})
    
    '''
    @classmethod
    def poll(cls, context):
        cond_1 = context.object.type == 'CURVE'
        cond_2 = context.object.type == 'MESH' and (len(context.object.data.vertices) == len(context.object.data.edges))
        
        return cond_1 or cond_2
    '''
    def execute(self, context):
        loop_obj = context.object
        oct = self.oct
        smooth = self.smooth
        settings = get_settings()
        dbg = settings.debug
        full_arch_methods.cloth_fill_main(context, loop_obj, oct, smooth, debug = dbg)
           
        return {'FINISHED'}
    
def register():
    
    bpy.utils.register_class(OPENDENTAL_OT_bridge_from_selected)
    bpy.utils.register_class(OPENDENTAL_OT_bridge_keep_arch_plan)
    bpy.utils.register_class(OPENDENTAL_OT_bridge_prebridge)
    bpy.utils.register_class(OPENDENTAL_OT_bridge_individual)
    bpy.utils.register_class(OPENDENTAL_OT_ClothFillTray)
    bpy.utils.register_class(OPENDENTAL_OT_BreakContact)
    bpy.utils.register_class(OPENDENTAL_OT_keep_shape)
    bpy.utils.register_class(OPENDENTAL_OT_bridge_boolean)
    bpy.utils.register_class(OPENDENTAL_OT_solid_bridge)
    #bpy.utils.register_class(OPENDENTAL_OT_seat_to_margin)
    #bpy.utils.register_class(OPENDENTAL_OT_calculate_inside)
    #bpy.utils.register_class(OPENDENTAL_OT_crown_cervical_convergence)
    #bpy.utils.register_class(OPENDENTAL_make_solid_restoration)
    #bpy.utils.register_class(OPENDENTAL_OT_assess_contacts)
    #bpy.utils.register_class(ViewToZ)
    #bpy.utils.register_module(__name__)


    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_bridge_from_selected)
    bpy.utils.unregister_class(OPENDENTAL_OT_bridge_keep_arch_plan)
    bpy.utils.unregister_class(OPENDENTAL_OT_bridge_prebridge)
    bpy.utils.unregister_class(OPENDENTAL_OT_bridge_individual)
    bpy.utils.unregister_class(OPENDENTAL_OT_ClothFillTray)
    bpy.utils.unregister_class(OPENDENTAL_OT_BreakContact)
    bpy.utils.unregister_class(OPENDENTAL_OT_keep_shape)
    bpy.utils.unregister_class(OPENDENTAL_OT_bridge_boolean)
    bpy.utils.unregister_class(OPENDENTAL_OT_solid_bridge)
    #bpy.utils.unregister_class(OPENDENTAL_OT_seat_to_margin)
    #bpy.utils.unregister_class(OPENDENTAL_OT_calculate_inside)
    #bpy.utils.unregister_class(OPENDENTAL_OT_crown_cervical_convergence)
    #bpy.utils.unregister_class(OPENDENTAL_OT_assess_contacts)
    #bpy.utils.unregister_class(ViewToZ)
    #bpy.utils.unregister_class(OPENDENTAL_make_solid_restoration)
if __name__ == "__main__":
    register()