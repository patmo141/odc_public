'''
Created on Aug 18, 2016

@author: Patrick
some useful tidbits
http://blender.stackexchange.com/questions/44637/how-can-i-manually-calculate-bpy-types-posebone-matrix-using-blenders-python-ap?rq=1
http://blender.stackexchange.com/questions/1640/how-are-the-bones-assigned-to-the-vertex-groups-in-the-api?rq=1
http://blender.stackexchange.com/questions/46928/set-bone-constraints-via-python-api
http://blender.stackexchange.com/questions/40244/delete-bone-constraint-in-python
http://blender.stackexchange.com/questions/19602/child-of-constraint-set-inverse-with-python
http://blender.stackexchange.com/questions/28869/how-to-disable-loop-playback-of-animation
'''

#python imports :
import math

#Blender imports :
import bpy
import bmesh
from mathutils import Vector, Matrix, Color, Quaternion
from mathutils.bvhtree import BVHTree
from bpy_extras import view3d_utils

#Addon imports :
from Addon_utils.common_utilities import bversion
from Addon_utils.odcutils import get_settings, obj_list_from_lib, obj_from_lib

import Operators.common_drawing
import Operators.bgl_utils
from Operators.mesh_cut import cross_section_seed_ver1, bound_box, edge_loops_from_bmedges
from Operators.textbox import TextBox
import odcmenus.menu_utils as menu_utils


#TODO, better system for tooth # systems
TOOTH_NUMBERS = [11,12,13,14,15,16,17,18,
                 21,22,23,24,25,26,27,28,
                 31,32,33,34,35,36,37,38,
                 41,42,43,44,45,46,47,48]

def insertion_axis_draw_callback(self, context):
    self.help_box.draw()
    self.target_box.draw()
    bgl_utils.insertion_axis_callback(self,context)
 
def rapid_label_teeth_callback(self, context):
    self.help_box.draw()
    self.target_box.draw()
    
        
class OPENDENTAL_OT_add_bone_roots(bpy.types.Operator):
    """Set the axis and direction of the roots for crowns from view"""
    bl_idname = "opendental.add_bone_roots"
    bl_label = "Add bone roots"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.mode != 'OBJECT':
            return False
        else:
            return True
        
    def set_axis(self, context, event):
        
        if not self.target:
            return
        
        empty_name = self.target.name + 'root_empty'
        if empty_name in context.scene.objects:
            ob = context.scene.objects[empty_name]
            ob.empty_draw_type = 'SINGLE_ARROW'
            ob.empty_draw_size = 10
        else:
            ob = bpy.data.objects.new(empty_name, None)
            ob.empty_draw_type = 'SINGLE_ARROW'
            ob.empty_draw_size = 10
            context.scene.objects.link(ob)
            
        coord = (event.mouse_region_x, event.mouse_region_y)
        v3d = context.space_data
        rv3d = v3d.region_3d
        view_vector = view3d_utils.region_2d_to_vector_3d(context.region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(context.region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)
        if bversion() < '002.077.000':
            res, obj, loc, no, mx = context.scene.ray_cast(ray_origin, ray_target)
        else:
            res, loc, no, ind, obj, mx = context.scene.ray_cast(ray_origin, view_vector)
        
        if res:
            if obj != self.target:
                return
                
            ob.location = loc
        else:
            return
            
        if ob.rotation_mode != 'QUATERNION':
            ob.rotation_mode = 'QUATERNION'
            
        vrot = rv3d.view_rotation    
        ob.rotation_quaternion = vrot
                   
    def advance_next_prep(self,context):
        if self.target == None:
            self.target = self.units[0]
            
        ind = self.units.index(self.target)
        prev = int(math.fmod(ind + 1, len(self.units)))
        self.target = self.units[prev]
        self.message = "Set axis for %s" % self.target.name
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()

        for obj in context.scene.objects:
            obj.select = False
        
        self.target.select = True
        context.space_data.region_3d.view_location = self.target.location
        
              
    def select_prev_unit(self,context):
        if self.target == None:
            self.target = self.units[0]
            
        ind = self.units.index(self.target)
        prev = int(math.fmod(ind - 1, len(self.units)))
        self.target = self.units[prev]
        self.message = "Set axis for %s" % self.target.name
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()

        for obj in context.scene.objects:
            obj.select = False
        
        self.target.select = True
        context.space_data.region_3d.view_location = self.target.location
                       
    def update_selection(self,context):
        if not len(context.selected_objects):
            self.message = "Right Click to Select"
            self.target = None
            return
        
        if context.selected_objects[0] not in self.units:
            self.message = "Selected Object must be tooth"      
            self.target = None
            return

        self.target = context.selected_objects[0]
        self.message = "Set axis for %s" % self.target.name
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
        
    def empties_to_bones(self,context):
        bpy.ops.object.select_all(action = 'DESELECT')
        
        arm_ob = bpy.data.objects['Roots']
        arm_ob.select = True
        context.scene.objects.active = arm_ob
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        for ob in self.units:
            e = context.scene.objects.get(ob.name + 'root_empty')
            b = arm_ob.data.edit_bones.get(ob.name + 'root')
            
            if e != None and b != None:
                b.transform(e.matrix_world) #this gets the local x,y,z in order
                Z = e.matrix_world.to_quaternion() * Vector((0,0,1))
                b.tail.xyz = e.location
                b.head.xyz = e.location - 16 * Z
                b.head_radius = 1.5
                b.tail_radius = 2.5
                
                context.scene.objects.unlink(e)
                e.user_clear()
                bpy.data.objects.remove(e)
            else:
                print('missing bone or empty')
                    
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
           
    def modal_main(self, context, event):
        # general navigation
        nmode = self.modal_nav(event)
        if nmode != '':
            return nmode  #stop here and tell parent modal to 'PASS_THROUGH'

        if event.type in {'RIGHTMOUSE'} and event.value == 'PRESS':
            self.update_selection(context)
            return 'pass'
        
        elif event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
            self.update_selection(context)
            if len(context.selected_objects):
                context.space_data.region_3d.view_location = context.selected_objects[0].location
            return 'main'
        
        elif event.type in {'LEFTMOUSE'} and event.value == 'PRESS':
            self.set_axis(context, event)
            self.advance_next_prep(context)
            return 'main'
        
        elif event.type in {'DOWN_ARROW'} and event.value == 'PRESS':
            self.select_prev_unit(context)
            return 'main'
        
        elif event.type in {'UP_ARROW'} and event.value == 'PRESS':
            self.advance_next_prep(context)
            return 'main'
                    
        elif event.type in {'ESC'}:
            #keep track of and delete new objects? reset old transforms?
            return'cancel'
        
        elif event.type in {'RET'} and event.value == 'PRESS':
            self.empties_to_bones(context)
            return 'finish'
        
        return 'main'
        
    def modal_nav(self, event):
        events_nav = {'MIDDLEMOUSE', 'WHEELINMOUSE','WHEELOUTMOUSE', 'WHEELUPMOUSE','WHEELDOWNMOUSE'} #TODO, better navigation, another tutorial
        handle_nav = False
        handle_nav |= event.type in events_nav

        if handle_nav: 
            return 'nav'
        return ''

    def modal(self, context, event):
        context.area.tag_redraw()

        FSM = {}    
        FSM['main']    = self.modal_main
        FSM['pass']    = self.modal_main
        FSM['nav']     = self.modal_nav
        
        nmode = FSM[self.mode](context, event)

        if nmode == 'nav': 
            return {'PASS_THROUGH'}
        
        if nmode in {'finish','cancel'}:
            #clean up callbacks
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}
        if nmode == 'pass':
            self.mode = 'main'
            return {'PASS_THROUGH'}
        
        if nmode: self.mode = nmode
        
        return {'RUNNING_MODAL'}
     
    def invoke(self, context, event):
        settings = get_settings()
        dbg = settings.debug
        
        if context.space_data.region_3d.is_perspective:
            #context.space_data.region_3d.is_perspective = False
            bpy.ops.view3d.view_persportho()
            
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

        #gather all the teeth in the scene TODO, keep better track
        self.units = []
        
        for i in TOOTH_NUMBERS:
            ob = context.scene.objects.get(str(i))
            if ob != None and not ob.hide:
                self.units.append(ob)
            
        if not len(self.units):
            self.report({'ERROR'}, "There are no teeth in the scene!, Teeth must be named 2 digits eg 11 or 46")
            return {'CANCELLED'}
        
        self.target = self.units[0]
        self.message = "Set axis for %s" %self.target.name
            
        #check for an armature
        bpy.ops.object.select_all(action = 'DESELECT')
        if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode = 'OBJECT')
                
        if context.scene.objects.get('Roots'):
            root_arm = context.scene.objects.get('Roots')
            root_arm.select = True
            root_arm.hide = False
            context.scene.objects.active = root_arm
            bpy.ops.object.mode_set(mode = 'EDIT')
            
            for ob in self.units:
                if ob.name + 'root' not in root_arm.data.bones:
                    bpy.ops.armature.bone_primitive_add(name = ob.name + 'root')
            
        else:
            root_data = bpy.data.armatures.new('Roots')
            root_arm = bpy.data.objects.new('Roots',root_data)
            context.scene.objects.link(root_arm)
            
            root_arm.select = True
            context.scene.objects.active = root_arm
            bpy.ops.object.mode_set(mode = 'EDIT')
            
            for ob in self.units:
                bpy.ops.armature.bone_primitive_add(name = ob.name + 'root')
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        root_arm.select = False
        self.units[0].select = True
            
        help_txt = "Right click to select a tooth \n Align View with root, mes and distal\n Up Arrow and Dn Arrow to select different units \n Left click in middle of prep to set axis \n Enter to finish \n ESC to cancel"
        self.help_box = TextBox(context,500,500,300,200,10,20,help_txt)
        self.help_box.fit_box_width_to_text_lines()
        self.help_box.fit_box_height_to_text_lines()
        self.help_box.snap_to_corner(context, corner = [1,1])
        
        aspect, mid = menu_utils.view3d_get_size_and_mid(context)
        self.target_box = TextBox(context,mid[0],aspect[1]-20,300,200,10,20,self.message)
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
        self.target_box.fit_box_height_to_text_lines()
        
        self.mode = 'main'
        context.window_manager.modal_handler_add(self)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(insertion_axis_draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

class OPENDENTAL_OT_fast_label_teeth(bpy.types.Operator):
    """Label teeth by clicking on them"""
    bl_idname = "opendental.fast_label_teeth"
    bl_label = "Fast Label Teeth"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.mode != 'OBJECT':
            return False
        else:
            return True
        
    def set_axis(self, context, event):
        
            
        coord = (event.mouse_region_x, event.mouse_region_y)
        v3d = context.space_data
        rv3d = v3d.region_3d
        view_vector = view3d_utils.region_2d_to_vector_3d(context.region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(context.region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)
        if bversion() < '002.077.000':
            res, obj, loc, no, mx = context.scene.ray_cast(ray_origin, ray_target)
        else:
            res, loc, no, ind, obj, mx = context.scene.ray_cast(ray_origin, view_vector)
        
        if res:
            obj.name = str(self.target)
            for ob in bpy.data.objects:
                ob.select = False
            obj.select = True
            obj.show_name = True
            context.scene.objects.active = obj
            bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY', center = 'BOUNDS')
            return True
        else:
            return False       
    def advance_next_prep(self,context):
        
        def next_ind(n):
            if math.fmod(n, 10) < 7:
                return n + 1
            elif math.fmod(n, 10) == 7:
                if n == 17: return 21
                elif n== 27: return 31
                elif n == 37: return 41
                elif n == 47: return 11
           
            
        self.target = next_ind(self.target)
        self.message = "Click on tooth % i" % self.target
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()

              
    def select_prev_unit(self,context):
        
        
        def prev_ind(n):
            if math.fmod(n, 10) > 1:
                return n - 1
            elif math.fmod(n, 10) == 1:
                if n == 11: return 41
                elif n== 21: return 11
                elif n == 31: return 21
                elif n == 41: return 31
                
                
        self.target = prev_ind(self.target)
       
        self.message = "Click on tooth %i" % self.target
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
    
           
    def modal_main(self, context, event):
        # general navigation
        nmode = self.modal_nav(event)
        if nmode != '':
            return nmode  #stop here and tell parent modal to 'PASS_THROUGH'

        if event.type in {'RIGHTMOUSE'} and event.value == 'PRESS':
            self.advance_next_prep(context)
            return 'pass'
        
        elif event.type in {'LEFTMOUSE'} and event.value == 'PRESS':
            res = self.set_axis(context, event)
            if res:
                self.advance_next_prep(context)
            return 'main'
        
        elif event.type in {'DOWN_ARROW'} and event.value == 'PRESS':
            self.select_prev_unit(context)
            return 'main'
        
        elif event.type in {'UP_ARROW'} and event.value == 'PRESS':
            self.advance_next_prep(context)
            return 'main'
                    
        elif event.type in {'ESC'}:
            #keep track of and delete new objects? reset old transforms?
            return'cancel'
        
        elif event.type in {'RET'} and event.value == 'PRESS':
            #self.empties_to_bones(context)
            return 'finish'
        
        return 'main'
        
    def modal_nav(self, event):
        events_nav = {'MIDDLEMOUSE', 'WHEELINMOUSE','WHEELOUTMOUSE', 'WHEELUPMOUSE','WHEELDOWNMOUSE'} #TODO, better navigation, another tutorial
        handle_nav = False
        handle_nav |= event.type in events_nav

        if handle_nav: 
            return 'nav'
        return ''

    def modal(self, context, event):
        context.area.tag_redraw()

        FSM = {}    
        FSM['main']    = self.modal_main
        FSM['pass']    = self.modal_main
        FSM['nav']     = self.modal_nav
        
        nmode = FSM[self.mode](context, event)

        if nmode == 'nav': 
            return {'PASS_THROUGH'}
        
        if nmode in {'finish','cancel'}:
            #clean up callbacks
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}
        if nmode == 'pass':
            self.mode = 'main'
            return {'PASS_THROUGH'}
        
        if nmode: self.mode = nmode
        
        return {'RUNNING_MODAL'}
     
    def invoke(self, context, event):
        settings = get_settings()
        dbg = settings.debug
        
        if context.space_data.region_3d.is_perspective:
            #context.space_data.region_3d.is_perspective = False
            bpy.ops.view3d.view_persportho()
            
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

        #gather all the teeth in the scene TODO, keep better track

        
        
        
        self.target = 11
        self.message = "Set axis for " + str(self.target)
            
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
                
        #check for an armature
        bpy.ops.object.select_all(action = 'DESELECT')
            
        help_txt = "Left click on the tooth indicated to label it. Right click skip a tooth \n Up or Dn Arrow to change label\n Enter to finish \n ESC to cancel"
        self.help_box = TextBox(context,500,500,300,200,10,20,help_txt)
        self.help_box.fit_box_width_to_text_lines()
        self.help_box.fit_box_height_to_text_lines()
        self.help_box.snap_to_corner(context, corner = [1,1])
        
        aspect, mid = menu_utils.view3d_get_size_and_mid(context)
        self.target_box = TextBox(context,mid[0],aspect[1]-20,300,200,10,20,self.message)
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
        self.target_box.fit_box_height_to_text_lines()
        
        self.mode = 'main'
        context.window_manager.modal_handler_add(self)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(rapid_label_teeth_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}
    
class OPENDENTAL_OT_simple_ortho_base(bpy.types.Operator):
    """Simple ortho base with height 5 - 50mm """
    bl_idname = "opendental.simple_base"
    bl_label = "Simple model base"
    bl_options = {'REGISTER', 'UNDO'}
    
    base_height = bpy.props.FloatProperty(name = 'Base Height', default = 10, min = -50, max = 50,  description = 'Base height added in mm')
    
    @classmethod
    def poll(cls, context):
        if context.mode == "OBJECT" and context.object != None and context.object.type == 'MESH':
            return True
        else:
            return False
        
    def execute(self, context):
        
        bme = bmesh.new()
        bme.from_mesh(context.object.data)
        
        bme.verts.ensure_lookup_table()
        bme.edges.ensure_lookup_table()
        bme.faces.ensure_lookup_table()
        
        non_man_eds = [ed.index for ed in bme.edges if not ed.is_manifold]
        loops = edge_loops_from_bmedges(bme, non_man_eds)
                
                
        if len(loops)>1:
            biggest_loop = max(loops, key = len)
        else:
            biggest_loop = loops[0]
            
        
        if biggest_loop[0] != biggest_loop[-1]:
            
            print('Biggest loop not a hole!')
            bme.free() 
            
            return {'FINISHED'}
        
        biggest_loop.pop()
        
        com = Vector((0,0,0))
        for vind in biggest_loop:
            com += bme.verts[vind].co
        com *= 1/len(biggest_loop)
        
        for vind in biggest_loop:
            bme.verts[vind].co[2] = com[2] + self.base_height
        
        bme.faces.new([bme.verts[vind] for vind in biggest_loop])
        bmesh.ops.recalc_face_normals(bme, faces = bme.faces)
        bme.to_mesh(context.object.data)
        bme.free()             
        return {'FINISHED'}
    
class OPENDENTAL_OT_setup_root_parenting(bpy.types.Operator):
    """Prepares model for gingival simulation"""
    bl_idname = "opendental.set_roots_parents"
    bl_label = "Set Root Parents"
    bl_options = {'REGISTER','UNDO'}
    
    link_to_cast = bpy.props.BoolProperty(default = False)
    @classmethod
    def poll(self,context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        
        #make sure we don't mess up any animations!
        context.scene.frame_set(0)
        
        max_ob = context.scene.objects.get('UpperJaw')
        man_ob = context.scene.objects.get('LowerJaw')
        arm_ob = context.scene.objects.get('Roots')
        
        if not self.link_to_cast:
            max_ob = None
            man_ob = None
            
        if arm_ob == None:
            self.report({'ERROR'}, "You need a 'Roots' armature, pease add one or see wiki")
            return {'CANCELLED'}
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
        context.scene.objects.active = arm_ob
        arm_ob.select = True
            
        #create a vertex group for every maxillary bone
        for bone in arm_ob.data.bones:
            if bone.name.startswith('1') or bone.name.startswith('2'):
                jaw_ob = max_ob
            else:
                jaw_ob = man_ob
                
            if jaw_ob != None:
            
                if bone.name not in jaw_ob.vertex_groups:
                    vg = jaw_ob.vertex_groups.new(name = bone.name)
                else:
                    vg = jaw_ob.vertex_groups[bone.name]
                #make all members, weight at 0    
                vg.add([i for i in range(0,len(jaw_ob.data.vertices))], 0, type = 'REPLACE')
                
            tooth = context.scene.objects.get(bone.name[0:2])
            if tooth == None: continue
            
            if jaw_ob != None:
                if tooth.name+'_prox' in jaw_ob.modifiers:
                    mod = jaw_ob.modifiers.get(tooth.name + '_prox')
                else:
                    mod = jaw_ob.modifiers.new(tooth.name + '_prox', 'VERTEX_WEIGHT_PROXIMITY')
                    
                mod.target = tooth
                mod.vertex_group = bone.name
                mod.proximity_mode = 'GEOMETRY'
                mod.min_dist = 10
                mod.max_dist = 0
                mod.falloff_type = 'SHARP'
                mod.show_expanded = False
            
            pbone = arm_ob.pose.bones[bone.name]
            
            if 'Child Of' in pbone.constraints:
                cons = pbone.constraints['Child Of']
                cons.target = tooth
            else:
                cons = pbone.constraints.new(type = 'CHILD_OF')
                cons.target = tooth
                    
                arm_ob.data.bones.active = pbone.bone
                bone.select = True
                bpy.ops.object.mode_set(mode = 'POSE')
                context_copy = bpy.context.copy()
                context_copy["constraint"] = pbone.constraints["Child Of"]    
                bpy.ops.constraint.childof_set_inverse(context_copy, constraint="Child Of", owner='BONE')
                bpy.ops.object.mode_set(mode = 'OBJECT')
            
        if max_ob != None:
            if 'Armature' in max_ob.modifiers:
                mod = max_ob.modifiers['Armature']
                max_ob.modifiers.remove(mod)
            mod = max_ob.modifiers.new('Armature', type = 'ARMATURE')
            mod.object = arm_ob
            mod.use_vertex_groups = True
        
        if man_ob != None:
            if 'Armature' in man_ob.modifiers:
                mod = man_ob.modifiers['Armature']
                man_ob.modifiers.remove(mod)
            mod = man_ob.modifiers.new('Armature', type = 'ARMATURE')
            mod.object = arm_ob
            mod.use_vertex_groups = True       
        return {'FINISHED'}

class OPENDENTAL_OT_adjust_roots(bpy.types.Operator):
    """Adjust root bones in edit_mode before moving teeth"""
    bl_idname = "opendental.adjust_bone_roots"
    bl_label = "Adjust Roots"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if 'Roots' in context.scene.objects:
            return True
        else:
            return False
        
    def execute(self, context):
        
        #make sure we don't mess up any animations!
        context.scene.frame_set(0)
        
        arm_ob = context.scene.objects.get('Roots')
        context.scene.objects.active = arm_ob
        
        if context.mode == 'POSE':
            self.report({'ERROR'}, "Roots Armature is in POSE Mode, must be in OBJECT or EDIT mode")
        
        if arm_ob == None:
            self.report({'ERROR'}, "You need a 'Roots' armature, pease add one or see wiki")
            return {'CANCELLED'}
        
        bpy.ops.object.mode_set(mode = 'EDIT')
         
        return {'FINISHED'}
    

class OPENDENTAL_OT_set_treatment_keyframe(bpy.types.Operator):
    """Sets a treatment stage at this frame"""
    bl_idname = "opendental.set_treatment_keyframe"
    bl_label = "Set Treatment Keyframe"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self, context):
        
        

        #find obs
        obs = []
        for num in TOOTH_NUMBERS:
            ob = context.scene.objects.get(str(num))
            if ob != None and not ob.hide:
                obs.append(ob)
                continue
            
            for ob in context.scene.objects:
                if ob.name.startswith(str(num)) and not ob.hide:
                    obs.append(ob)
        
        bpy.ops.object.select_all(action = 'DESELECT')
        for ob in obs:
            ob.select = True
        context.scene.objects.active = ob
        
        if context.scene.keying_sets.active == None:
            bpy.ops.anim.keying_set_active_set(type='BUILTIN_KSI_LocRot')
            
        bpy.ops.anim.keyframe_insert(type = 'BUILTIN_KSI_LocRot')      
        return {'FINISHED'}
              
class OPENDENTAL_OT_maxillary_view(bpy.types.Operator):
    '''Will hide all non maxillary objects'''
    bl_idname = "opendental.show_max_teeth"
    bl_label = "Show Maxillary Teeth"
    bl_options = {'REGISTER','UNDO'}

    show_master = bpy.props.BoolProperty(default = False)
    
    def execute(self, context):
        for ob in context.scene.objects:
            if ob.name.startswith('1') or ob.name.startswith('2'):
                ob.hide = False
            
            elif ('upper' in ob.name or 'Upper' in ob.name) and self.show_master:
                ob.hide = False
            elif ('maxil' in ob.name or 'Maxil' in ob.name) and self.show_master:
                ob.hide = False
            else:
                ob.hide = True              
        return {'FINISHED'}
     
class OPENDENTAL_OT_mandibular_view(bpy.types.Operator):
    '''Will hide all non mandibuar objects'''
    bl_idname = "opendental.show_man_teeth"
    bl_label = "Show Mandibular Teeth"
    bl_options = {'REGISTER','UNDO'}
    
    show_master = bpy.props.BoolProperty(default = False)
    
    def execute(self, context):
        for ob in context.scene.objects:
            if ob.name.startswith('3') or ob.name.startswith('4'):
                ob.hide = False
            
            elif ('lower' in ob.name or 'Lower' in ob.name) and self.show_master:
                ob.hide = False
            elif ('mand' in ob.name or 'Mand' in ob.name) and self.show_master:
                ob.hide = False
            else:
                ob.hide = True              
        return {'FINISHED'}
    
class OPENDENTAL_OT_right_view(bpy.types.Operator):
    '''Will hide all non right tooth objects'''
    bl_idname = "opendental.show_right_teeth"
    bl_label = "Show Right Teeth"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self, context):
        for ob in context.scene.objects:
            if ob.name.startswith('1') or ob.name.startswith('4'):
                ob.hide = False
            else:
                ob.hide = True              
        return {'FINISHED'}

    
class OPENDENTAL_OT_left_view(bpy.types.Operator):
    '''Will hide all non left toot objects'''
    bl_idname = "opendental.show_left_teeth"
    bl_label = "Show Left Teeth"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self, context):
        for ob in context.scene.objects:
            if ob.name.startswith('2') or ob.name.startswith('3'):
                ob.hide = False
            else:
                ob.hide = True              
        return {'FINISHED'}

class OPENDENTAL_OT_physics_scene(bpy.types.Operator):
    '''Take selected objects into a separate scene for physics simulation'''
    bl_idname = "opendental.add_physics_scene"
    bl_label = "Physics Scene for Simulation"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == "Physics Sim":
            return False
        else:
            return True
    def execute(self, context):
        obs = [ob for ob in context.selected_objects]
        
        if "Physics Sim" not in bpy.data.scenes:
            pscene = bpy.data.scenes.new("Physics Sim")
        else:
            pscene = bpy.data.scenes["Physics Sim"]
                
        #TODO Clear existing objects and any physics cache
        for ob in pscene.objects:
            pscene.objects.unlink(ob)
            ob.user_clear()
            bpy.data.objects.remove(ob)
        
        context.screen.scene = pscene
        context.scene.frame_set(0)
        
        for ob in obs:    
            #new_ob = bpy.data.objects.new(ob.name[0:2]+'_p', ob.data)
            pscene.objects.link(ob)
            ob.select = True
            
        bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object = True, obdata = False)             
        bpy.ops.object.visual_transform_apply()
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_physics_setup(bpy.types.Operator):
    '''Make objects rigid bodies for physics simulation'''
    bl_idname = "opendental.physics_sim_setup"
    bl_label = "Setup Physics for Simulation"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    def execute(self, context):

        context.scene.use_gravity = False
        #clear existing rigidbody
        if context.scene.rigidbody_world:
            bpy.ops.rigidbody.world_remove()
            bpy.ops.rigidbody.world_add()
        else:
            bpy.ops.rigidbody.world_add()
            
        #potentially adjust these values    
        rbw = context.scene.rigidbody_world
        rbw.solver_iterations = 15
        rbw.point_cache.frame_end = 500 #more time for sim.
        context.scene.frame_end = 500
        context.scene.frame_set(0)
        
        obs = [ob for ob in context.selected_objects]
        bpy.ops.object.select_all(action = 'DESELECT')
        
        for ob in obs:
            context.scene.objects.active = ob
            ob.select = True
            if not ob.rigid_body:
                bpy.ops.rigidbody.object_add()
            else:
                bpy.ops.rigidbody.object_remove()
                bpy.ops.rigidbody.object_add()
            
            
            ob.lock_rotations_4d = True
            ob.lock_rotation[0] = True
            ob.lock_rotation[1] = True
            ob.lock_rotation[2] = True
            ob.lock_rotation_w = True
                
            rb = ob.rigid_body
            rb.friction = .1
            rb.use_margin = True
            rb.collision_margin = .05
            rb.collision_shape = 'CONVEX_HULL'
            rb.restitution = 0
            rb.linear_damping = 1
            rb.angular_damping = .9
            rb.mass = 3
            ob.select = False          
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_add_forcefields(bpy.types.Operator):
    '''Add forcefields to selected objects'''
    bl_idname = "opendental.add_forcefields"
    bl_label = "Add Forcefields All"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    def execute(self, context):
        obs = [ob for ob in context.selected_objects]
        bpy.ops.object.select_all(action = 'DESELECT')
        
        for ob in obs:
            if ob.type != 'MESH': continue
            empty = bpy.data.objects.new(ob.name[0:2] + 'force', None)
            context.scene.objects.link(empty)
            context.scene.objects.active = empty
            empty.parent = ob
            empty.matrix_world = ob.matrix_world
            empty.select = True
            bpy.ops.object.forcefield_toggle()
            empty.field.strength = -1000
            empty.field.falloff_type = 'SPHERE'
            empty.field.use_radial_min = True
            empty.field.use_radial_max = True
            empty.field.radial_min = ob.dimensions[0]/1.8
            empty.field.radial_max = 10
            empty.select = False
            
        return {'FINISHED'} 
    
class OPENDENTAL_OT_limit_movements(bpy.types.Operator):
    '''Add constraints to limit movements in simulation'''
    bl_idname = "opendental.limit_physics_movements"
    bl_label = "Limit Physics Movements"
    bl_options = {'REGISTER','UNDO'}
    
    buc_ling = bpy.props.FloatProperty(name = 'Facial/Lingual', default = 2)
    mes_dis = bpy.props.FloatProperty(name = 'Mesial/Distal', default = 2)
    occlusal = bpy.props.FloatProperty(name = 'Occluso/Gingival', default = 0)
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self, width=300, height=20)
        
    
    def execute(self, context):
        
        context.scene.frame_set(0)
        obs = [ob for ob in context.selected_objects]

        #bpy.ops.object.select_all(action = 'DESELECT')
        
        for ob in obs:
            if ob.type != 'MESH': continue
            
            if 'Limit Location' not in ob.constraints:
                limit = ob.constraints.new('LIMIT_LOCATION')
            else:
                limit = ob.constraints['Limit Location']
                ob.constraints.remove(limit)
                limit = ob.constraints.new('LIMIT_LOCATION')
            
            imx = ob.matrix_world.inverted()
            world_loc = ob.matrix_world.to_translation()
            rot = ob.matrix_world.to_quaternion()
            
            X = world_loc.dot(rot * Vector((1,0,0)))
            Y = world_loc.dot(rot * Vector((0,1,0)))
            Z = world_loc.dot(rot * Vector((0,0,1)))
            
            limit.use_min_x = True
            limit.use_min_y = True
            limit.use_min_z = True
            limit.use_max_x = True
            limit.use_max_y = True
            limit.use_max_z = True
            limit.use_transform_limit = False
            
            limit.owner_space = 'LOCAL'
            limit.min_x, limit.max_x = X-self.mes_dis, X+self.mes_dis
            limit.min_y, limit.max_y = Y-self.buc_ling, Y+self.buc_ling
            limit.min_z, limit.max_z = Z-self.occlusal, Z+self.occlusal    
        return {'FINISHED'}

class OPENDENTAL_OT_unlimit_movements(bpy.types.Operator):
    '''Removes limitations'''
    bl_idname = "opendental.unlimit_physics_movements"
    bl_label = "Unlimit Physics Movements"
    bl_options = {'REGISTER','UNDO'}
    
    buc_ling = bpy.props.FloatProperty(name = 'Facial/Lingual', default = 2)
    mes_dis = bpy.props.FloatProperty(name = 'Mesial/Distal', default = 2)
    occlusal = bpy.props.FloatProperty(name = 'Occluso/Gingival', default = 0)
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self, width=300, height=20)
        
    
    def execute(self, context):
        
        context.scene.frame_set(0)
        obs = [ob for ob in context.selected_objects]

        #bpy.ops.object.select_all(action = 'DESELECT')
        
        for ob in obs:
            
            if ob.type != 'MESH': continue
            
            if 'Limit Location' in ob.constraints:
                limit = ob.constraints['Limit Location']
                ob.constraints.remove(limit)   
        return {'FINISHED'}
       
class OPENDENTAL_OT_lock_movements(bpy.types.Operator):
    '''Prevent Selected Teeth from moving in any direction '''
    bl_idname = "opendental.lock_physics_movements"
    bl_label = "Lock Physics Movements"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    
    def execute(self, context):
        obs = [ob for ob in context.selected_objects]
        
        for ob in obs:
            if ob.type != 'MESH': continue
            ob.lock_location[0], ob.lock_location[1], ob.lock_location[2] = True, True, True

        return {'FINISHED'}    

class OPENDENTAL_OT_unlock_movements(bpy.types.Operator):
    '''Allows Selected Teeth to move in any direction '''
    bl_idname = "opendental.unlock_physics_movements"
    bl_label = "Unlock Physics Movements"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    
    def execute(self, context):
        obs = [ob for ob in context.selected_objects]
        
        for ob in obs:
            if ob.type != 'MESH': continue
            ob.lock_location[0], ob.lock_location[1], ob.lock_location[2] = False, False, False

        return {'FINISHED'} 

class OPENDENTAL_OT_keep_simulation_result(bpy.types.Operator):
    '''Kepe results of simulation at current frame, and apply back to design scene '''
    bl_idname = "opendental.keep_simulation_results"
    bl_label = "Keep Simulation Results"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    
    def execute(self, context):
        other_scenes = [sce for sce in bpy.data.scenes if sce.name != 'Physics Sim']
        scene = other_scenes[0]
        
        for ob in context.scene.objects:
            ob.select = True
        
        context.scene.objects.active = ob
        
        #this ruins the phys simulation but OH WELL!
        bpy.ops.object.visual_transform_apply()
        
        for pob in bpy.data.scenes['Physics Sim'].objects:
            for ob in scene.objects:
                if pob.data == ob.data:
                    ob.matrix_world = pob.matrix_world
        
        #todo, trash all the objects and physics sim
        
        #switch back to the old scene             
        context.screen.scene = scene
        
        return {'FINISHED'}        

def register():
    bpy.utils.register_class(OPENDENTAL_OT_mandibular_view)
    bpy.utils.register_class(OPENDENTAL_OT_maxillary_view)
    bpy.utils.register_class(OPENDENTAL_OT_left_view)
    bpy.utils.register_class(OPENDENTAL_OT_right_view)
    bpy.utils.register_class(OPENDENTAL_OT_add_bone_roots)
    bpy.utils.register_class(OPENDENTAL_OT_fast_label_teeth)
    bpy.utils.register_class(OPENDENTAL_OT_adjust_roots)
    bpy.utils.register_class(OPENDENTAL_OT_setup_root_parenting)
    bpy.utils.register_class(OPENDENTAL_OT_set_treatment_keyframe)
    bpy.utils.register_class(OPENDENTAL_OT_keep_simulation_result)
    bpy.utils.register_class(OPENDENTAL_OT_unlock_movements)
    bpy.utils.register_class(OPENDENTAL_OT_lock_movements)
    bpy.utils.register_class(OPENDENTAL_OT_limit_movements)
    bpy.utils.register_class(OPENDENTAL_OT_unlimit_movements)
    bpy.utils.register_class(OPENDENTAL_OT_add_forcefields)
    bpy.utils.register_class(OPENDENTAL_OT_physics_setup)
    bpy.utils.register_class(OPENDENTAL_OT_physics_scene)
    bpy.utils.register_class(OPENDENTAL_OT_simple_ortho_base)
    
    
    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_mandibular_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_maxillary_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_left_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_right_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_add_bone_roots)
    bpy.utils.unregister_class(OPENDENTAL_OT_fast_label_teeth)
    bpy.utils.unregister_class(OPENDENTAL_OT_setup_root_parenting)
    bpy.utils.unregister_class(OPENDENTAL_OT_set_treatment_keyframe)
    bpy.utils.unregister_class(OPENDENTAL_OT_adjust_roots)
    bpy.utils.unregister_class(OPENDENTAL_OT_keep_simulation_result)
    bpy.utils.unregister_class(OPENDENTAL_OT_unlock_movements)
    bpy.utils.unregister_class(OPENDENTAL_OT_lock_movements)
    bpy.utils.unregister_class(OPENDENTAL_OT_limit_movements)
    bpy.utils.unregister_class(OPENDENTAL_OT_unlimit_movements)
    bpy.utils.unregister_class(OPENDENTAL_OT_add_forcefields)
    bpy.utils.unregister_class(OPENDENTAL_OT_physics_setup)
    bpy.utils.unregister_class(OPENDENTAL_OT_physics_scene)
    bpy.utils.unregister_class(OPENDENTAL_OT_simple_ortho_base)
    
if __name__ == "__main__":
    register()