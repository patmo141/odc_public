import time
import bpy
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_point_line
from bpy_extras import view3d_utils
import bgl
import blf

#from . 
import odcutils
from odcutils import get_settings
import bgl_utils
import common_drawing
import common_utilities
#from . 
import full_arch_methods
from textbox import TextBox
from curve import CurveDataManager, PolyLineKnife

class OPENDENTAL_OT_link_selection_splint(bpy.types.Operator):
    ''''''
    bl_idname='opendental.link_selection_splint'
    bl_label="Link Units to Splint"
    bl_options = {'REGISTER','UNDO'}
    
    clear = bpy.props.BoolProperty(name="Clear", description="Replace existing units with selected, \n else add selected to existing", default=False)
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        teeth = odcutils.tooth_selection(context)  #TODO:...make this poll work for all selected teeth...
        condition_1 = len(teeth) > 0
        implants = odcutils.implant_selection(context)  
        condition_2 = len(implants) > 0
        return condition_1 or condition_2
    
    def execute(self,context):
        settings = get_settings()
        dbg =settings.debug
        n = context.scene.odc_splint_index
        odc_splint = context.scene.odc_splints[n]
        full_arch_methods.link_selection_to_splint(context, odc_splint, debug=dbg)
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_splint_bone(bpy.types.Operator):
    '''
    Will assign the active object as the bone model
    Only use if making multi tissue support.  eg bone
    and teeth.
    '''
    bl_idname='opendental.bone_model_set'
    bl_label="Splint Bone"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):

        condition_1 = context.object
                
        return condition_1
    
    def execute(self,context):
        settings = get_settings()
        dbg =settings.debug
        n = context.scene.odc_splint_index
        
        if len(context.scene.odc_splints) != 0:
            
            odc_splint = context.scene.odc_splints[n]
            odc_splint.bone = context.object.name
            
        else:
            self.report({'WARNING'}, "there are not guides, bone will not be linked to a guide")
        
        context.scene.odc_props.bone = context.object.name
        
        return {'FINISHED'}

class OPENDENTAL_OT_splint_model(bpy.types.Operator):
    '''
    Will assign the active object as the  model to build
    a splint on.  Needed if an object was not linked
    when splint was planned
    '''
    bl_idname='opendental.model_set'
    bl_label="Set Splint Model"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):

        condition_1 = context.object
        condition_2 = len(context.scene.odc_splints)       
        return condition_1
    
    def execute(self,context):
        settings = get_settings()
        dbg =settings.debug
        n = context.scene.odc_splint_index
        
        if len(context.scene.odc_splints) != 0:
            
            odc_splint = context.scene.odc_splints[n]
            odc_splint.model = context.object.name
            
        else:
            self.report({'WARNING'}, "there are not guides, bone will not be linked to a guide")
        
        context.scene.odc_props.bone = context.object.name
        
        return {'FINISHED'}    

class OPENDENTAL_OT_splint_report(bpy.types.Operator):
    '''
    Will add a text object to the .blend file which tells
    the information about a surgical guide and it's various
    details.
    '''
    bl_idname='opendental.splint_report'
    bl_label="Splint Report"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):

        condition_1 = len(context.scene.odc_splints) > 0
        return condition_1
    
    def execute(self,context):

        sce = context.scene
        if 'Report' in bpy.data.texts:
            Report = bpy.data.texts['Report']
            Report.clear()
        else:
            Report = bpy.data.texts.new("Report")
    
    
        Report.write("Open Dental CAD Implant Guide Report")
        Report.write("\n")
        Report.write('Date and Time: ')
        Report.write(time.asctime())
        Report.write("\n")
    
        Report.write("There is/are %i guide(s)" % len(sce.odc_splints))
        Report.write("\n")
        Report.write("_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _")
        Report.write("\n")
        Report.write("\n")
    
        for splint in sce.odc_splints:
            imp_names = splint.implant_string.split(":")
            imp_names.pop(0)
            Report.write("Splint Name: " + splint.name)
            Report.write("\n")
            Report.write("Number of Implants: %i" % len(imp_names))
            Report.write("\n")
            Report.write("Implants: ")
            Report.write(splint.implant_string)
            Report.write("\n")
            
            
            for name in imp_names:
                imp = sce.odc_implants[name]
                Report.write("\n")
                Report.write("Implant: " + name + "\n")
                
                if imp.implant and imp.implant in bpy.data.objects:
                    implant = bpy.data.objects[imp.implant]
                    V = implant.dimensions
                    width = '{0:.{1}f}'.format(V[0], 2)
                    length = '{0:.{1}f}'.format(V[2], 2)
                    Report.write("Implant Dimensions: " + width + "mm x " + length + "mm")
                    Report.write("\n")
                    
                if imp.inner and imp.inner in bpy.data.objects:
                    inner = bpy.data.objects[imp.inner]
                    V = inner.dimensions
                    width = '{0:.{1}f}'.format(V[0], 2)
                    Report.write("Hole Diameter: " + width + "mm")
                    Report.write("\n")
                else:
                    Report.write("Hole Diameter: NO HOLE")    
                    Report.write("\n")
                    
                    
                if imp.outer and imp.outer in bpy.data.objects and imp.implant and imp.implant in bpy.data.objects:
                    implant = bpy.data.objects[imp.implant]
                    guide = bpy.data.objects[imp.outer]
                    v1 = implant.matrix_world.to_translation()
                    v2 = guide.matrix_world.to_translation()
                    V = v2 - v1
                    depth = '{0:.{1}f}'.format(V.length, 2)
                    print(depth)
                    Report.write("Cylinder Depth: " + depth + "mm")
                    Report.write("\n")
                else:
                    Report.write("Cylinder Depth: NO GUIDE CYLINDER \n")
                    
                if imp.sleeve and imp.sleeve in bpy.data.objects and imp.implant and imp.implant in bpy.data.objects:
                    implant = bpy.data.objects[imp.implant]
                    guide = bpy.data.objects[imp.sleeve]
                    v1 = implant.matrix_world.to_translation()
                    v2 = guide.matrix_world.to_translation()
                    V = v2 - v1
                    depth = '{0:.{1}f}'.format(V.length, 2)
                    Report.write("Sleeve Depth: " + depth + "mm")
                    Report.write("\n")
                else:
                    Report.write("Sleeve Depth: NO SLEEVE")    
                    Report.write("\n")
                    
            Report.write("_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _")
            Report.write("\n")
            Report.write("\n")
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_splint_subtract_holes(bpy.types.Operator):
    ''''''
    bl_idname='opendental.splint_subtract_holes'
    bl_label="Subtract Splint Holes"
    bl_options = {'REGISTER','UNDO'}
    
    finalize = bpy.props.BoolProperty(default = True, name = "Finalize", description="Apply all modifiers to splint before adding guides?  may take longer, less risk of crashing")
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        #TODO..polling
        return True
    
    def execute(self,context):
        settings = get_settings()
        dbg =settings.debug
        n = context.scene.odc_splint_index
        odc_splint = context.scene.odc_splints[n]
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        if not odc_splint.splint:
            self.report({'ERROR'},'No splint model to add guide cylinders too')
        if dbg:
            start_time = time.time()
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        sce = context.scene
        bpy.ops.object.select_all(action='DESELECT')
        
        new_objs = []
        implants = []
        imp_list = odc_splint.implant_string.split(sep=":")
        for name in imp_list:
            implant = context.scene.odc_implants.get(name)
            if implant:
                implants.append(implant)
                
        for space in implants:
            if space.inner:
                Guide_Cylinder = bpy.data.objects[space.inner]
                Guide_Cylinder.hide = True
                new_data = Guide_Cylinder.to_mesh(sce,True, 'RENDER')
                new_obj = bpy.data.objects.new("temp_holes", new_data)
                new_obj.matrix_world = Guide_Cylinder.matrix_world
                new_objs.append(new_obj)
                sce.objects.link(new_obj)
                new_obj.select = True
        
        if len(new_objs):   
            sce.objects.active = new_objs[0]
            bpy.ops.object.join()
            
        else:
            return{'CANCELLED'}
        
        bpy.ops.object.select_all(action='DESELECT')
        Splint = bpy.data.objects[odc_splint.splint]
        Splint.select = True
        Splint.hide = False
        sce.objects.active = Splint
        if self.finalize:
            for mod in Splint.modifiers:
                if mod.type in {'BOOLEAN', 'SHRINKWRAP'}:
                    if mod.type == 'BOOLEAN' and mod.object:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    elif mod.type == 'SHRINKWRAP' and mod.target:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                else:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
        
        bool_mod = Splint.modifiers.new('OUTER','BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = new_objs[0] #hopefully this is still the object?
        new_objs[0].hide = True   
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[10] = True
        
        if dbg:
            finish = time.time() - start_time
            print("finished subtracting holes in %f seconds..boy that took a long time" % finish)
        
        return {'FINISHED'}
        
class OPENDENTAL_OT_splint_subtract_sleeves(bpy.types.Operator):
    '''
    '''
    bl_idname='opendental.splint_subtract_sleeves'
    bl_label="Subtract Splint Sleeves"
    bl_options = {'REGISTER','UNDO'}
    
    finalize = bpy.props.BoolProperty(default = True, name = "Finalize", description="Apply all modifiers to splint before adding guides?  may take longer, less risk of crashing")
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        #TODO..polling
        return True
    
    def execute(self,context):
        settings = get_settings()
        dbg =settings.debug
        n = context.scene.odc_splint_index
        odc_splint = context.scene.odc_splints[n]
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        if not odc_splint.splint:
            self.report({'ERROR'},'No splint model to add guide cylinders too')
        if dbg:
            start_time = time.time()
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        sce = context.scene
        bpy.ops.object.select_all(action='DESELECT')
        
        implants = []
        imp_list = odc_splint.implant_string.split(sep=":")
        for name in imp_list:
            implant = context.scene.odc_implants.get(name)
            if implant:
                implants.append(implant)
                
        new_objs = []
        for space in implants:
            if space.sleeve:
                Sleeve_Female = bpy.data.objects[space.sleeve]
                Sleeve_Female.hide = True
                new_data = Sleeve_Female.to_mesh(sce,True, 'RENDER')
                new_obj = bpy.data.objects.new("temp_holes", new_data)
                new_obj.matrix_world = Sleeve_Female.matrix_world
                new_objs.append(new_obj)
                sce.objects.link(new_obj)
                new_obj.select = True
        
        if len(new_objs):   
            sce.objects.active = new_objs[0]
            bpy.ops.object.join()
            
        else:
            return{'CANCELLED'}
        
        bpy.ops.object.select_all(action='DESELECT')
        Splint = bpy.data.objects[odc_splint.splint]
        Splint.select = True
        Splint.hide = False
        sce.objects.active = Splint
        if self.finalize:
            for mod in Splint.modifiers:
                if mod.type in {'BOOLEAN', 'SHRINKWRAP'}:
                    if mod.type == 'BOOLEAN' and mod.object:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    elif mod.type == 'SHRINKWRAP' and mod.target:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                else:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    
        bool_mod = Splint.modifiers.new('Sleeves','BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = new_objs[0] #hopefully this is still the object?
        new_objs[0].hide = True   
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[11] = True
        
        if dbg:
            finish = time.time() - start_time
            print("finished subtracting Sleeves in %f seconds..boy that took a long time" % finish)
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_splint_add_guides(bpy.types.Operator):
    ''''''
    bl_idname='opendental.splint_add_guides'
    bl_label="Merge Guide Cylinders to Splint"
    bl_options = {'REGISTER','UNDO'}
    
    finalize = bpy.props.BoolProperty(default = True, name = "Finalze",description="Apply all modifiers to splint before adding guides?  may take longer, less risk of crashing")
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        #TODO..polling
        if not len(context.scene.odc_splints): return False
        n = context.scene.odc_splint_index
        odc_splint = context.scene.odc_splints[n]
        imp_list = odc_splint.implant_string.split(sep=":")
        
        if len(imp_list) == 0: return False
        
        return True
    
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        n = context.scene.odc_splint_index
        odc_splint = context.scene.odc_splints[n]
        
        if not odc_splint.splint:
            self.report({'ERROR'},'No splint model to add guide cylinders too')
        if dbg:
            start_time = time.time()
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
            
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        sce = context.scene
        bpy.ops.object.select_all(action='DESELECT')
        
        new_objs = []
        
        implants = []
        imp_list = odc_splint.implant_string.split(sep=":")
        for name in imp_list:
            implant = context.scene.odc_implants.get(name)
            if implant:
                implants.append(implant)
        for space in implants:
            if space.outer and space.outer in bpy.data.objects:
                Guide_Cylinder = bpy.data.objects[space.outer]
                Guide_Cylinder.hide = True
                new_data = Guide_Cylinder.to_mesh(sce,True, 'RENDER')
                new_obj = bpy.data.objects.new("temp_guide", new_data)
                new_obj.matrix_world = Guide_Cylinder.matrix_world
                new_objs.append(new_obj)
                sce.objects.link(new_obj)
                new_obj.select = True
        
        if len(new_objs):   
            sce.objects.active = new_objs[0]
            bpy.ops.object.join()
        else:
            return{'CANCELLED'}
        
        bpy.ops.object.select_all(action='DESELECT')
        Splint = bpy.data.objects[odc_splint.splint]
        Splint.select = True
        Splint.hide = False
        sce.objects.active = Splint
        if self.finalize:
            for mod in Splint.modifiers:
                if mod.type in {'BOOLEAN', 'SHRINKWRAP'}:
                    if mod.type == 'BOOLEAN' and mod.object:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    elif mod.type == 'SHRINKWRAP' and mod.target:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                else:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
        
        bool_mod = Splint.modifiers.new('OUTER','BOOLEAN')
        bool_mod.operation = 'UNION'
        bool_mod.object = new_objs[0] #hopefully this is still the object?
        new_objs[0].hide = True   
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[11] = True
        
        if dbg:
            finish = time.time() - start_time
            print("finished merging guides in %f seconds..boy that took a long time" % finish)
        
        return {'FINISHED'}

#Depricated, no longer used
class OPENDENTAL_OT_initiate_arch_curve(bpy.types.Operator):
    '''Places a bezier curve to be extruded around the planned plane of occlussion'''
    bl_idname = 'opendental.initiate_arch_curve'
    bl_label = "Arch Plan Curve"
    bl_options = {'REGISTER','UNDO'}
    
    
    @classmethod
    def poll(cls, context):
        if context.object and context.mode == 'OBJECT':
            return True
        else:
            return False
        #return len(context.scene.odc_splints) > 0             

    def execute(self, context):
        
        sce=bpy.context.scene
        ob = context.object
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        if ob:

            L = odcutils.get_bbox_center(ob, world=True)
        
        elif sce.odc_props.master:
            ob = bpy.data.objects[sce.odc_props.master]
            L = odcutils.get_bbox_center(ob, world=True)
            
        else:
            L = bpy.context.scene.cursor_location

        bpy.ops.view3d.viewnumpad(type='TOP')
        bpy.ops.object.select_all(action='DESELECT')
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        #bpy.context.scene.cursor_location = L
        bpy.ops.curve.primitive_bezier_curve_add(view_align=True, enter_editmode=True, location=L)
        PlanCurve = context.object
        PlanCurve.layers[4] = True
        PlanCurve.layers[0] = True
        PlanCurve.layers[1] = True
        PlanCurve.layers[3] = True
        
        context.tool_settings.use_snap = True
        context.tool_settings.snap_target= 'ACTIVE'
        context.tool_settings.snap_element = 'FACE'
        context.tool_settings.proportional_edit = 'DISABLED'
        context.tool_settings.use_snap_project = False
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
        bpy.ops.curve.select_all(action='DESELECT')
        context.object.data.splines[0].bezier_points[1].select_control_point=True
        bpy.ops.curve.delete()
        bpy.ops.curve.select_all(action='SELECT')
            
        odcutils.layer_management(sce.odc_splints)
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[3] = True
        return {'FINISHED'}

def arch_crv_draw_callback(self, context):  
    self.crv.draw(context)
    self.help_box.draw()      
    

class OPENDENTAL_OT_arch_curve(bpy.types.Operator):
    """Draw a line with the mouse to extrude bezier curves"""
    bl_idname = "opendental.draw_arch_curve"
    bl_label = "Arch Curve"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls,context):
        return True
    
    def modal_nav(self, event):
        events_nav = {'MIDDLEMOUSE', 'WHEELINMOUSE','WHEELOUTMOUSE', 'WHEELUPMOUSE','WHEELDOWNMOUSE'} #TODO, better navigation, another tutorial
        handle_nav = False
        handle_nav |= event.type in events_nav

        if handle_nav: 
            return 'nav'
        return ''
    
    def modal_main(self,context,event):
        # general navigation
        nmode = self.modal_nav(event)
        if nmode != '':
            return nmode  #stop here and tell parent modal to 'PASS_THROUGH'

        #after navigation filter, these are relevant events in this state
        if event.type == 'G' and event.value == 'PRESS':
            if self.crv.grab_initiate():
                return 'grab'
            else:
                #error, need to select a point
                return 'main'
        
        if event.type == 'MOUSEMOVE':
            self.crv.hover(context, event.mouse_region_x, event.mouse_region_y)    
            return 'main'
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            x, y = event.mouse_region_x, event.mouse_region_y
            self.crv.click_add_point(context, x,y)
            return 'main'
        
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            self.crv.click_delete_point(mode = 'mouse')
            return 'main'
        
        if event.type == 'X' and event.value == 'PRESS':
            self.crv.delete_selected(mode = 'selected')
            return 'main'
            
        if event.type == 'RET' and event.value == 'PRESS':
            return 'finish'
            
        elif event.type == 'ESC' and event.value == 'PRESS':
            return 'cancel' 

        return 'main'
    
    def modal_grab(self,context,event):
        # no navigation in grab mode
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            #confirm location
            self.crv.grab_confirm()
            return 'main'
        
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            #put it back!
            self.crv.grab_cancel()
            return 'main'
        
        elif event.type == 'MOUSEMOVE':
            #update the b_pt location
            self.crv.grab_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
            return 'grab'
        
    def modal(self, context, event):
        context.area.tag_redraw()
        
        FSM = {}    
        FSM['main']    = self.modal_main
        FSM['grab']    = self.modal_grab
        FSM['nav']     = self.modal_nav
        
        nmode = FSM[self.mode](context, event)
        
        if nmode == 'nav': 
            return {'PASS_THROUGH'}
        
        if nmode in {'finish','cancel'}:
            #clean up callbacks
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}
        
        if nmode: self.mode = nmode
        
        return {'RUNNING_MODAL'}

    def invoke(self,context, event):
        
        if context.object:
            ob = context.object
            L = odcutils.get_bbox_center(ob, world=True)
            context.scene.cursor_location = L
        
        self.crv = CurveDataManager(context,snap_type ='SCENE', snap_object = None, shrink_mod = False, name = 'Plan Curve')
         
        #TODO, tweak the modifier as needed
        help_txt = "DRAW ARCH OUTLINE\n\nLeft Click in scene to draw a curve \nPoints will snap to objects under mouse \nNot clicking on object will make points at same depth as 3D cursor \n Right click to delete a point n\ G to grab  \n ENTER to confirm \n ESC to cancel"
        self.help_box = TextBox(context,500,500,300,200,10,20,help_txt)
        self.help_box.snap_to_corner(context, corner = [1,1])
        self.mode = 'main'
        self._handle = bpy.types.SpaceView3D.draw_handler_add(arch_crv_draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self) 
        return {'RUNNING_MODAL'}
    
def ispltmgn_draw_callback(self, context):  
    self.crv.draw(context)
    self.help_box.draw()      
    

class OPENDENTAL_OT_splint_margin(bpy.types.Operator):
    """Draw a line with the mouse to extrude bezier curves"""
    bl_idname = "opendental.initiate_splint_outline"
    bl_label = "Splint Outine"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls,context):
        condition_1 = context.object != None
        return condition_1
    
    def modal_nav(self, event):
        events_nav = {'MIDDLEMOUSE', 'WHEELINMOUSE','WHEELOUTMOUSE', 'WHEELUPMOUSE','WHEELDOWNMOUSE'} #TODO, better navigation, another tutorial
        handle_nav = False
        handle_nav |= event.type in events_nav

        if handle_nav: 
            return 'nav'
        return ''
    
    def modal_main(self,context,event):
        # general navigation
        nmode = self.modal_nav(event)
        if nmode != '':
            return nmode  #stop here and tell parent modal to 'PASS_THROUGH'

        #after navigation filter, these are relevant events in this state
        if event.type == 'G' and event.value == 'PRESS':
            if self.crv.grab_initiate():
                return 'grab'
            else:
                #error, need to select a point
                return 'main'
        
        if event.type == 'MOUSEMOVE':
            self.crv.hover(context, event.mouse_region_x, event.mouse_region_y)    
            return 'main'
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            x, y = event.mouse_region_x, event.mouse_region_y
            self.crv.click_add_point(context, x,y)
            return 'main'
        
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            self.crv.click_delete_point(mode = 'mouse')
            return 'main'
        
        if event.type == 'X' and event.value == 'PRESS':
            self.crv.delete_selected(mode = 'selected')
            return 'main'
            
        if event.type == 'RET' and event.value == 'PRESS':
            return 'finish'
            
        elif event.type == 'ESC' and event.value == 'PRESS':
            return 'cancel' 

        return 'main'
    
    def modal_grab(self,context,event):
        # no navigation in grab mode
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            #confirm location
            self.crv.grab_confirm()
            return 'main'
        
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            #put it back!
            self.crv.grab_cancel()
            return 'main'
        
        elif event.type == 'MOUSEMOVE':
            #update the b_pt location
            self.crv.grab_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
            return 'grab'
        
    def modal(self, context, event):
        context.area.tag_redraw()
        
        FSM = {}    
        FSM['main']    = self.modal_main
        FSM['grab']    = self.modal_grab
        FSM['nav']     = self.modal_nav
        
        nmode = FSM[self.mode](context, event)
        
        if nmode == 'nav': 
            return {'PASS_THROUGH'}
        
        if nmode in {'finish','cancel'}:
            #clean up callbacks
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}
        
        if nmode: self.mode = nmode
        
        return {'RUNNING_MODAL'}


    def invoke(self,context, event):
        
        if len(context.scene.odc_splints) == 0 and context.object:
            #This is a hidden cheat, allowing quick starting of a splint
            my_item = context.scene.odc_splints.add()        
            my_item.name = context.object.name + '_Splint'
            my_item.model = context.object.name
            self.report({'WARNING'}, "Assumed you wanted to start a new splint on the active object!  If not, then UNDO")
            
            for ob in bpy.data.objects:
                ob.select = False
                
            context.object.select = True
            bpy.ops.view3d.view_selected()
            self.splint = my_item
            
        else:
            self.splint = odcutils.splint_selction(context)[0]
            
        self.crv = None
        margin = self.splint.name + '_outline'
        
        if (self.splint.model == '' or self.splint.model not in bpy.data.objects) and not context.object:
            self.report({'WARNING'}, "There is no model, the curve will snap to anything in the scene!")
            self.crv = CurveDataManager(context,snap_type ='SCENE', snap_object = None, shrink_mod = False, name = margin)
            
        elif self.splint.model != '' and self.splint.model in bpy.data.objects:
            Model = bpy.data.objects[self.splint.model]
            for ob in bpy.data.objects:
                ob.select = False
            Model.select = True
            Model.hide = False
            context.scene.objects.active = Model
            bpy.ops.view3d.view_selected()
            self.crv = CurveDataManager(context,snap_type ='OBJECT', snap_object = Model, shrink_mod = True, name = margin)
            self.crv.crv_obj.parent = Model
            
        if self.crv == None:
            self.report({'ERROR'}, "Not sure what you want, you may need to select an object or plan a splint")
            return {'CANCELLED'}
        
        self.splint.margin = self.crv.crv_obj.name
        
        if 'Wrap' in self.crv.crv_obj.modifiers:
            mod = self.crv.crv_obj.modifiers['Wrap']
            mod.offset = .75
            mod.use_keep_above_surface = True
        
            mod = self.crv.crv_obj.modifiers.new('Smooth','SMOOTH')
            mod.iterations = 10
            
        #TODO, tweak the modifier as needed
        help_txt = "DRAW MARGIN OUTLINE\n\nLeft Click on model to draw outline \nRight click to delete a point \nLeft Click last point to make loop \n G to grab  \n ENTER to confirm \n ESC to cancel"
        self.help_box = TextBox(context,500,500,300,200,10,20,help_txt)
        self.help_box.snap_to_corner(context, corner = [1,1])
        self.mode = 'main'
        self._handle = bpy.types.SpaceView3D.draw_handler_add(ispltmgn_draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self) 
        return {'RUNNING_MODAL'}
    
    
def plyknife_draw_callback(self, context):
    self.knife.draw(context)
    self.help_box.draw()
    if len(self.sketch):
        common_drawing.draw_polyline_from_points(context, self.sketch, (.3,.3,.3,.8), 2, "GL_LINE_SMOOTH")
        
class OPENDENTAL_OT_mesh_trim_polyline(bpy.types.Operator):
    """Draw a line with the mouse to cut mesh into pieces"""
    bl_idname = "opendental.trim_mesh"
    bl_label = "Polyline Trim Mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def sketch_confirm(self, context, event):
        print('sketch confirmed')
        if len(self.sketch) < 5 and self.knife.ui_type == 'DENSE_POLY':
            print('sketch too short, cant confirm')
            return
        x, y = event.mouse_region_x, event.mouse_region_y
        last_hovered = self.knife.hovered[1] #guaranteed to be a point by criteria to enter sketch mode
        self.knife.hover(context,x,y)
        print('last hovered %i' % last_hovered)
        
        sketch_3d = common_utilities.ray_cast_path(context, self.knife.cut_ob,self.sketch)
        
        if self.knife.hovered[0] == None:
            #add the points in
            if last_hovered == len(self.knife.pts) - 1:
                self.knife.pts += sketch_3d[0::5]
                print('add on to the tail')

                
            else:
                self.knife.pts = self.knife.pts[:last_hovered] + sketch_3d[0::5]
                print('snipped off and added on to the tail')
        
        else:
            print('inserted new segment')
            print('now hovered %i' % self.knife.hovered[1])
            new_pts = sketch_3d[0::5]
            if last_hovered > self.knife.hovered[1]:
                new_pts.reverse()
                self.knife.pts = self.knife.pts[:self.knife.hovered[1]] + new_pts + self.knife.pts[last_hovered:]
            else:
                self.knife.pts = self.knife.pts[:last_hovered] + new_pts + self.knife.pts[self.knife.hovered[1]:]
        self.knife.snap_poly_line()
        
    def modal_nav(self, event):
        events_nav = {'MIDDLEMOUSE', 'WHEELINMOUSE','WHEELOUTMOUSE', 'WHEELUPMOUSE','WHEELDOWNMOUSE'} #TODO, better navigation, another tutorial
        handle_nav = False
        handle_nav |= event.type in events_nav

        if handle_nav: 
            return 'nav'
        return ''
    
    def modal_main(self,context,event):
        # general navigation
        nmode = self.modal_nav(event)
        if nmode != '':
            return nmode  #stop here and tell parent modal to 'PASS_THROUGH'

        #after navigation filter, these are relevant events in this state
        if event.type == 'G' and event.value == 'PRESS':
            if self.knife.grab_initiate():
                return 'grab'
            else:
                #need to select a point
                return 'main'
        
        if event.type == 'MOUSEMOVE':
            self.knife.hover(context, event.mouse_region_x, event.mouse_region_y)    
            return 'main'
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            
            x, y = event.mouse_region_x, event.mouse_region_y
            self.knife.click_add_point(context, x,y)  #takes care of selection too
            if self.knife.ui_type == 'DENSE_POLY' and self.knife.hovered[0] == 'POINT':
                self.sketch = [(x,y)]
                return 'sketch'
            return 'main'
        
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            self.knife.click_delete_point(mode = 'mouse')
            return 'main'
        
        if event.type == 'X' and event.value == 'PRESS':
            self.knife.delete_selected(mode = 'selected')
            return 'main'
        
        if event.type == 'C' and event.value == 'PRESS':
            self.knife.make_cut()
            return 'main' 
        if event.type == 'D' and event.value == 'PRESS':
            print('confirm cut')
            if len(self.knife.new_cos) and len(self.knife.bad_segments) == 0 and not self.knife.split:
                print('actuall confirm cut')
                self.knife.confirm_cut_to_mesh()
                return 'main' 
            
        if event.type == 'E' and event.value == 'PRESS':     
            if self.knife.split and self.knife.face_seed and len(self.knife.ed_map):
                self.knife.split_geometry()
                return 'finish' 
            
        if event.type == 'S' and event.value == 'PRESS':
            return 'inner'
          
        if event.type == 'RET' and event.value == 'PRESS':
            self.knife.confirm_cut_to_mesh()
            return 'finish'
            
        elif event.type == 'ESC' and event.value == 'PRESS':
            return 'cancel' 

        return 'main'
    
    def modal_grab(self,context,event):
        # no navigation in grab mode
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            #confirm location
            self.knife.grab_confirm()
            return 'main'
        
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            #put it back!
            self.knife.grab_cancel()
            return 'main'
        
        elif event.type == 'MOUSEMOVE':
            #update the b_pt location
            self.knife.grab_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
            return 'grab'
    
    def modal_sketch(self,context,event):
        if event.type == 'MOUSEMOVE':
            x, y = event.mouse_region_x, event.mouse_region_y
            if not len(self.sketch):
                return 'main'
            (lx, ly) = self.sketch[-1]
            ss0,ss1 = self.stroke_smoothing ,1-self.stroke_smoothing
            self.sketch += [(lx*ss0+x*ss1, ly*ss0+y*ss1)]
            return 'sketch'
        
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.sketch_confirm(context, event)
            self.sketch = []
            return 'main'
        
    def modal_inner(self,context,event):
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            print('left click modal inner')
            x, y = event.mouse_region_x, event.mouse_region_y
            if self.knife.click_seed_select(context, x,y):
                print('seed set')
                return 'main'
            else:
                return 'inner'
        
        if event.type in {'RET', 'ESC'}:
            return 'main'
            
    def modal(self, context, event):
        context.area.tag_redraw()
        
        FSM = {}    
        FSM['main']    = self.modal_main
        FSM['sketch']  = self.modal_sketch
        FSM['grab']    = self.modal_grab
        FSM['nav']     = self.modal_nav
        FSM['inner']   = self.modal_inner
        
        nmode = FSM[self.mode](context, event)
        
        if nmode == 'nav': 
            return {'PASS_THROUGH'}
        
        if nmode in {'finish','cancel'}:
            #clean up callbacks
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}
        
        if nmode: self.mode = nmode
        
        return {'RUNNING_MODAL'}
    
    def invoke(self,context,event):
        self.mode = 'main'
        help_txt = "DRAW CUT OUTLINE\n\nLeft Click on model to draw outline outline \nRight click to delete \nLeft Click last point to close loop\n C to preview cut n\ Adjustt red segements and re-cut \n S and then click in region to split to make cut and split mesh \n ENTER to confirm"
        
        self.stroke_smoothing = .4
        self.sketch = []
        
        self.help_box = TextBox(context,500,500,300,200,10,20,help_txt)
        self.help_box.snap_to_corner(context, corner = [1,1])
        self.knife = PolyLineKnife(context,context.object)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(plyknife_draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
       

#### Depricated, left for coding example for bezier data managemetn###

class OPENDENTAL_OT_initiate_splint_margin(bpy.types.Operator):
    '''Places a bezier curve to be extruded around the boundaries of a splint'''
    bl_idname = 'opendental.initiate_splint_margin'
    bl_label = "Initiate Splint Margin"
    bl_options = {'REGISTER','UNDO'}
        
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        return len(context.scene.odc_splints) > 0             

    def execute(self, context):
        
        sce=bpy.context.scene
        n = sce.odc_splint_index
        splint = sce.odc_splints[n]
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        model = splint.model
        Model = bpy.data.objects[model]

        L = odcutils.get_bbox_center(Model, world=True)
        #L = bpy.context.scene.cursor_location

        #bpy.ops.view3d.viewnumpad(type='TOP')
        bpy.ops.object.select_all(action='DESELECT')
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        #bpy.context.scene.cursor_location = L
        bpy.ops.curve.primitive_bezier_curve_add(view_align=True, enter_editmode=True, location=L)
        
        context.tool_settings.use_snap = True
        context.tool_settings.snap_target= 'ACTIVE'
        context.tool_settings.snap_element = 'FACE'
        context.tool_settings.proportional_edit = 'DISABLED'
        
        Margin =context.object
        Margin.name=splint.name + "_margin"
        Margin.parent = Model
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
        bpy.ops.curve.select_all(action='DESELECT')
        context.object.data.splines[0].bezier_points[1].select_control_point=True
        bpy.ops.curve.delete()
        bpy.ops.curve.select_all(action='SELECT')
        
        mod = Margin.modifiers.new('Wrap','SHRINKWRAP')
        mod.target = Model
        mod.offset = .75
        mod.use_keep_above_surface = True
        
        mod = Margin.modifiers.new('Smooth','SMOOTH')
        mod.iterations = 10
        
        splint.margin = Margin.name
        odcutils.layer_management(sce.odc_splints)
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[4] = True
        return {'FINISHED'}
    
class OPENDENTAL_OT_survey_model(bpy.types.Operator):
    '''Calculates silhouette of object which surveys convexities AND concavities from the current view axis'''
    bl_idname = 'opendental.view_silhouette_survey'
    bl_label = "Survey Model From View"
    bl_options = {'REGISTER','UNDO'}
    
    world = bpy.props.BoolProperty(default = True, name = "Use world coordinate for calculation...almost always should be true.")
    smooth = bpy.props.BoolProperty(default = True, name = "Smooth the outline.  Slightly less acuurate in some situations but more accurate in others.  Default True for best results")

    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        C0 = context.space_data.type == 'VIEW_3D'
        C1 = context.object != None
        if C1:
            C2 = context.object.type == 'MESH'
        else:
            C2 = False
        return  C0 and C1 and C2

    def execute(self, context):
        settings = get_settings()
        dbg = settings.debug
        ob = context.object
        view = context.space_data.region_3d.view_rotation * Vector((0,0,1))
        odcutils.silouette_brute_force(context, ob, view, self.world, self.smooth, debug = dbg)
        return {'FINISHED'}
      
class OPENDENTAL_OT_splint_bezier_model(bpy.types.Operator):
    '''Calc a Splint/Tray from a model and a curve'''
    bl_idname = "opendental.splint_from_curve"
    bl_label = "Calculate Bezier Splint"
    bl_options = {'REGISTER','UNDO'}

    #splint thickness
    thickness = bpy.props.FloatProperty(name="Thickness", description="Splint Thickness", default=2, min=.3, max=5, options={'ANIMATABLE'})
    
    #cleanup models afterward
    cleanup = bpy.props.BoolProperty(name="Cleanup", description="Apply Modifiers and cleanup models \n Do not use if planning bone support", default=True)
    
    @classmethod
    def poll(cls, context):
        if len(context.scene.odc_splints):
            settings = get_settings()
            dbg = settings.debug
            b = settings.behavior
            behave_mode = settings.behavior_modes[int(b)]
            if  behave_mode in {'ACTIVE','ACTIVE_SELECTED'} and dbg > 2:
                obs =  context.selected_objects
                cond_1 = len(obs) == 2
                ob_types = set([obs[0].type, obs[1].type])
                cond_2 = ('MESH' in ob_types) and ('CURVE' in ob_types)
                return cond_1 and cond_2
                
            else: #we know there are splints..we will determine active one later
                return context.mode == 'OBJECT'
        else:
            return False
            
        
    
    def execute(self, context):
        
            
        settings = get_settings()
        dbg = settings.debug
        
        #first, ensure all models are present and not deleted etc
        odcutils.scene_verification(context.scene, debug = dbg)      
        b = settings.behavior
        behave_mode = settings.behavior_modes[int(b)]
        
        settings = get_settings()
        dbg = settings.debug    
        [ob_sets, tool_sets, space_sets] = odcutils.scene_preserv(context, debug=dbg)
        
        #this is sneaky way of letting me test different things
        if behave_mode in {'ACTIVE','ACTIVE_SELECTED'} and dbg > 2:
            obs = context.selected_objects
            if obs[0].type == 'CURVE':
                model = obs[1]
                margin = obs[0]
            else:
                model = obs[0]
                margin = obs[1]
        
                exclude = ['name','teeth','implants','tooth_string','implant_string']
                splint = odcutils.active_odc_item_candidate(context.scene.odc_splints, obs[0], exclude)
        
        else:
            j = context.scene.odc_splint_index
            splint =context.scene.odc_splints[j]
            if splint.model in bpy.data.objects and splint.margin in bpy.data.objects:
                model = bpy.data.objects[splint.model]
                margin = bpy.data.objects[splint.margin]
            else:
                print('whoopsie...margin and model not defined or something is wrong')
                return {'CANCELLED'}
        
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        z = Vector((0,0,1))
        vrot= context.space_data.region_3d.view_rotation
        Z = vrot*z
        
        [Splint, Falloff, Refractory] = full_arch_methods.splint_bezier_step_1(context, model, margin, Z, self.thickness, debug=dbg)

        splint.splint = Splint.name #that's a pretty funny statement.
        
        if splint.bone and splint.bone in bpy.data.objects:
            mod = Splint.modifiers['Bone']
            mod.target = bpy.data.objects[splint.bone]
        
        if self.cleanup:
            context.scene.objects.active = Splint
            Splint.select = True
            
            for mod in Splint.modifiers:
                
                if mod.name != 'Bone':
                    if mod.type in {'BOOLEAN', 'SHRINKWRAP'}:
                        if mod.type == 'BOOLEAN' and mod.object:
                            bpy.ops.object.modifier_apply(modifier=mod.name)
                        elif mod.type == 'SHRINKWRAP' and mod.target:
                            bpy.ops.object.modifier_apply(modifier=mod.name)
                    else:
                        bpy.ops.object.modifier_apply(modifier=mod.name)

            context.scene.objects.unlink(Falloff)    
            Falloff.user_clear()
            bpy.data.objects.remove(Falloff)
            
            context.scene.objects.unlink(Refractory)
            Refractory.user_clear()
            bpy.data.objects.remove(Refractory)
            odcutils.scene_reconstruct(context, ob_sets, tool_sets, space_sets, debug=dbg)  
            
        else:
            odcutils.scene_reconstruct(context, ob_sets, tool_sets, space_sets, debug=dbg)  
            Falloff.hide = True
            Refractory.hide = True
                
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[10] = True
          
        odcutils.material_management(context, context.scene.odc_splints, debug = dbg)
        odcutils.layer_management(context.scene.odc_splints, debug = dbg)   
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OPENDENTAL_OT_link_selection_splint)
    bpy.utils.register_class(OPENDENTAL_OT_splint_bezier_model)
    bpy.utils.register_class(OPENDENTAL_OT_splint_add_guides)
    bpy.utils.register_class(OPENDENTAL_OT_splint_subtract_holes)
    bpy.utils.register_class(OPENDENTAL_OT_survey_model)
    #bpy.utils.register_class(OPENDENTAL_OT_initiate_arch_curve)
    bpy.utils.register_class(OPENDENTAL_OT_arch_curve)
    bpy.utils.register_class(OPENDENTAL_OT_splint_subtract_sleeves)
    bpy.utils.register_class(OPENDENTAL_OT_splint_bone)
    bpy.utils.register_class(OPENDENTAL_OT_splint_model)
    bpy.utils.register_class(OPENDENTAL_OT_splint_report)
    bpy.utils.register_class(OPENDENTAL_OT_splint_margin)
    #bpy.utils.register_class(OPENDENTAL_OT_mesh_trim_polyline)
    #bpy.utils.register_module(__name__)
    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_link_selection_splint)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_bezier_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_add_guides)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_subtract_holes)
    bpy.utils.unregister_class(OPENDENTAL_OT_survey_model)
    #bpy.utils.unregister_class(OPENDENTAL_OT_initiate_arch_curve)
    bpy.utils.unregister_class(OPENDENTAL_OT_arch_curve)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_subtract_sleeves)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_bone)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_report)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_margin)
    #bpy.utils.unregister_class(OPENDENTAL_OT_mesh_trim_polyline)
    
if __name__ == "__main__":
    register()
