'''
Created on Jan 11, 2013

@author: Patrick
'''

import bpy
import os
import math
from mathutils import Vector
from bpy_extras import view3d_utils
#from . 
import odcutils
#from . 
import bgl_utils
from curve import CurveDataManager
from textbox import TextBox
import bmesh
from mathutils.bvhtree import BVHTree
from mesh_cut import cross_section_seed_ver1, bound_box
import common_drawing
from common_utilities import bversion

#import odc.odcmenus.menu_utils as menu_utils
#import odc.odcmenus.button_data as button_data

 
class MarginSlicer(object):
    def __init__(self, tooth, context, crv_data_manager):
        '''
        manages a CurveDataManager
        '''
    
        if not crv_data_manager.snap_ob:
            return None
        
        self.crv_dat = crv_data_manager
        ob = self.crv_dat.snap_ob
        bme = bmesh.new()
        bme.from_object(ob, context.scene)
        self.snap_ob = ob
        self.bme = bme
        self.bvh = BVHTree.FromBMesh(self.bme)
        
        self.cut_pt = None
        self.cut_no = None
        self.slice_points = []
        self.points_2d = []
        self.active_point_2d = Vector((0,0,0))
        if tooth.axis != '':
            axis = bpy.data.objects[tooth.axis]
            axis_mx = axis.matrix_world
            self.Z = axis_mx.to_3x3() * Vector((0,0,1))
        else:
            self.Z = Vector((0,0,1))
    def get_pt_and_no(self):
        crv_mx = self.crv_dat.crv_obj.matrix_world
        N = len(self.crv_dat.b_pts)
        i = self.crv_dat.selected
        i_m1 = (i-1) % N
        self.cut_no = crv_mx * self.crv_dat.b_pts[i] - crv_mx*self.crv_dat.b_pts[i_m1]
        self.cut_no.normalize()
        self.cut_pt = crv_mx * self.crv_dat.b_pts[i]
        
    def slice(self):
        self.slice_points = []
        
        if len(self.crv_dat.b_pts) < 2 or self.crv_dat.selected == -1:
            return
        
        self.get_pt_and_no()
        
        mx = self.snap_ob.matrix_world
        imx = mx.inverted()
        if bversion() < '002.077.000':
            pt, no, seed, dist = self.bvh.find(imx * self.cut_pt)
        else:
            pt, no, seed, dist = self.bvh.find_nearest(imx * self.cut_pt)
        
        
        verts, eds = cross_section_seed_ver1(self.bme, mx, self.cut_pt, self.cut_no, seed, max_tests = 40)
        
        #put them in world space
        self.slice_points = [mx*v for v in verts]
    
    def make_points_2D(self):
        
        X = self.cut_no.cross(self.Z)
        X.normalize()
        Y = X.cross(self.cut_no)
        Y.normalize()
        points_centered = [v - self.slice_points[0] for v in self.slice_points]
        active_pt = self.cut_pt - self.slice_points[0]
        active_pt_2d = Vector((active_pt.dot(X), active_pt.dot(Y)))
        
        points_2d = [Vector((v.dot(X), v.dot(Y))) for v in points_centered]
        bounds = bound_box(points_2d)
        x_factor = 200/(bounds[0][1] - bounds[0][0])
        y_factor = 200/(bounds[1][1] - bounds[1][0])
        screen_factor = min(x_factor, y_factor)
        self.points_2d = [screen_factor*(v - Vector((bounds[0][0], bounds[1][0]))) for v in points_2d]
        self.active_pt2d = screen_factor*(active_pt_2d - Vector((bounds[0][0], bounds[1][0])))
        
    def prepare_slice(self):
        self.crv_dat.grab_initiate()
        self.slice()
        return
        
    def slice_mouse_move(self, context, x, y):
        self.crv_dat.grab_mouse_move(context, x, y)
        self.slice()
        self.make_points_2D()
        return  
    
    def slice_confirm(self):
        self.slice_points = []
        self.crv_dat.grab_confirm()
        return
    
    def slice_cancel(self):
        self.slice_points = []
        self.crv_dat.grab_cancel()
        return
    
    def draw(self,context):
        #draw a box
        #draw a box outline
        #draw a 2D represntation of the cross section
        if self.slice_points != []:
            common_drawing.draw_polyline_from_3dpoints(context, self.slice_points, (.1,.8,.4,.8), 2, 'GL_LINE')
            common_drawing.draw_polyline_from_points(context, self.points_2d, (1,1,1,1), 2, 'GL_LINE')
            common_drawing.draw_points(context, [self.active_pt2d], (1,.1,.1,1), 5)

#DEPRICATED, LEFT AS CODE EXAMPLE            
class OPENDENTAL_OT_initiate_margin(bpy.types.Operator):
    '''Places a bezier curve to be extruded around the edge of the prep'''
    bl_idname = 'opendental.initiate_margin'
    bl_label = "Initiate Margin"
    bl_options = {'REGISTER','UNDO'}
    
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        teeth = odcutils.tooth_selection(context)
        
        if teeth != []:#This can only happen one tooth at a time
            tooth = teeth[0]
            return tooth.prep_model in bpy.data.objects
        else:
            return False            

    def execute(self, context):
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        tooth = odcutils.tooth_selection(context)[0]
        sce=bpy.context.scene
        a = tooth.name
        prep = tooth.prep_model
        margin = str(a + "_Margin")
        
        Prep = bpy.data.objects[prep]
        Prep.hide = False
        L = Prep.location
        #L = bpy.context.scene.cursor_location
        
        
        ###Keep a list of unhidden objects
        for o in sce.objects:
            if o.name != prep and not o.hide:
                o.hide = True
        
        master=sce.odc_props.master
        if master:
            Master = bpy.data.objects[master]
        else:
            self.report('WARNING', "No master model...there are risks!")
        
        bpy.ops.view3d.viewnumpad(type='TOP')
        bpy.ops.object.select_all(action='DESELECT')
        #bpy.context.scene.cursor_location = L
        bpy.ops.curve.primitive_bezier_curve_add(view_align=True, enter_editmode=True, location=L)
        bpy.context.tool_settings.use_snap = True
        bpy.context.tool_settings.snap_target= 'ACTIVE'
        bpy.context.tool_settings.snap_element = 'FACE'
        bpy.context.tool_settings.proportional_edit = 'DISABLED'
        o=bpy.context.object
        o.name=margin
        if master:
            o.parent=Master #maybe this should go in the "Accept Margin" function/step
        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
        bpy.ops.curve.select_all(action='DESELECT')
        bpy.context.object.data.splines[0].bezier_points[1].select_control_point=True
        bpy.ops.curve.delete()
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        mod = bpy.context.object.modifiers[0]
        
        #this could also be the active object...?
        #in a different behavior mode...
        mod.target=Prep
    
        tooth.margin = margin
        
        odcutils.layer_management(sce.odc_teeth)
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[4] = True
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_initiate_auto_margin(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.initiate_auto_margin'
    bl_label = "Initiate Auto Margin"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self, context):
        
        
        sce=bpy.context.scene
        tooth = odcutils.tooth_selection(context)[0]  #Can only happen on one tooth at a time
        a = tooth.name
        prep = tooth.prep_model
        margin = str(a + "_Margin")
        
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
        Prep = bpy.data.objects[prep]
        Prep.hide = False
        Prep.show_transparent = False
        
        bpy.ops.object.select_all(action='DESELECT')
        Prep.select = True
        sce.objects.active = Prep
        
        prep_cent = Vector((0,0,0))
        for v in Prep.bound_box:
            prep_cent = prep_cent + Prep.matrix_world * Vector(v)
        Prep_Center = prep_cent/8
        
        sce.cursor_location = Prep_Center     
        ###Keep a list of unhidden objects?
        for o in sce.objects:
            if o.name != prep and not o.hide:
                o.hide = True
        
        bpy.ops.view3d.viewnumpad(type='FRONT')
        bpy.ops.view3d.view_orbit(type = 'ORBITDOWN')
        
        
        current_grease = [gp.name for gp in bpy.data.grease_pencil]        
        bpy.ops.gpencil.data_add()
        bpy.ops.gpencil.layer_add()        
        for gp in bpy.data.grease_pencil:
            if gp.name not in current_grease:           
                print(gp.name)
                gplayer = gp.layers[0]
                gp.draw_mode = 'SURFACE'
                gp.name = margin + '_tracer'
                gplayer.info = margin + '_tracer'
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_walk_around_margin(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.walk_around_margin'
    bl_label = "Walk Around Margin"
    bl_options = {'REGISTER','UNDO'}
    
    resolution = bpy.props.IntProperty(name="Resolution", description="Number of sample points", default=50, min=0, max=100, options={'ANIMATABLE'})
    extra = bpy.props.IntProperty(name="Extra", description="Extra Stes", default=4, min=0, max=10, options={'ANIMATABLE'})    
    search = bpy.props.FloatProperty(name="Width of Search Band", description="", default=1.25, min=.2, max=2, step=5, precision=2, options={'ANIMATABLE'})
    
    def invoke(self, context, event): 
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        
        tooth = odcutils.tooth_selection( context)[0]  #This could theoretically happen to multiple teeth...but not likely
        sce=bpy.context.scene

        a = tooth.name
        prep = tooth.prep_model
        margin = str(a + "_Margin")
        
        Prep = bpy.data.objects[prep]
        Prep.hide = False
        
        master=sce.odc_props.master
        Master = bpy.data.objects[master]
        
        gp_margin = bpy.data.grease_pencil.get(margin + "_tracer")
        if not gp_margin:
            self.report("ERROR", "No grease pencil margin trace mark, please 'Initiate Auto Margin' first")
            return {'CANCELLED'}
        
        #Set up the rotation center as the 3d Cursor
        for A in bpy.context.window.screen.areas:
            if A.type == 'VIEW_3D':
                for s in A.spaces:
                    if s.type == 'VIEW_3D':
                        s.pivot_point = 'CURSOR'
        
        #set the trasnform orientation to the insertion axis so our z is well definined
        #this function returns the current transform so we can put it back later
        current_transform = odcutils.transform_management(tooth, sce, bpy.context.space_data)
        
                        
        #Get the prep BBox center for later       
        prep_cent = Vector((0,0,0))
        for v in Prep.bound_box:
            prep_cent = prep_cent + Prep.matrix_world * Vector(v)
        Prep_Center = prep_cent/8
        
        
        bpy.ops.gpencil.convert(type = 'PATH')
        bpy.ops.object.select_all(action='DESELECT')
        trace_curve = bpy.data.objects[margin + "_tracer"] #refactor to test for new object in scene
        context.scene.objects.active = trace_curve
        trace_curve.select = True
        bpy.ops.object.convert(target = 'MESH')
        
        #get our data
        trace_obj = bpy.context.object
        trace_data = trace_obj.data
        
        #place the intitial shrinkwrap modifier
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        mod = trace_obj.modifiers[0]
        mod.target=Prep
        mod.show_in_editmode = True
        mod.show_on_cage = True
        
        bpy.ops.object.modifier_copy(modifier = mod.name)
        
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action = 'SELECT')
         
        #test the resolution of the stroke
        #subdivide if necessary
        linear_density = odcutils.get_linear_density(me, edges, mx, debug)
        
        #flatten and space to make my simple curvature more succesful :-)
        bpy.ops.mesh.looptools_flatten(influence=90, plane='best_fit', restriction='none')
        bpy.ops.mesh.looptools_space(influence=90, input='selected', interpolation='cubic')
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.modifier_apply(modifier = trace_obj.modifiers[1].name)
        
        #Now we should essentially have a nice, approximately 2D and evenly spaced line
        #And we will find the sharpest point and save it.
        verts = trace_data.vertices
        v_ind = [v.index for v in trace_data.vertices]
        eds = [e for e in trace_data.edges if e.select] #why would we filter for selection here?
        ed_vecs = [(verts[e.vertices[1]].co - verts[e.vertices[0]].co) for e in eds]
        locs = []
        curves = []

        for i in range(3,len(eds)-3):
            a1 = ed_vecs[i-1].angle(ed_vecs[i+1])
            a2 = ed_vecs[i-2].angle(ed_vecs[i+2])
            a3 = ed_vecs[i-3].angle(ed_vecs[i+3])
    
            l1 = ed_vecs[i-1].length + ed_vecs[i+1].length
            l2 = ed_vecs[i-2].length + ed_vecs[i+2].length
            l3 = ed_vecs[i-3].length + ed_vecs[i+3].length
    
    
            curve = 1/6 * (3*a1/l1 + 2 * a2/l2 + a3/l3)
            curves.append(curve)
    
        c = max(curves)
        n = curves.index(c)
        max_ed = eds[n+3] #need to check this indexing
        loc = .5 * (verts[max_ed.vertices[0]].co + verts[max_ed.vertices[1]].co)
        
        
        locs.append(loc)

        
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        bpy.context.scene.cursor_location = locs[0]
        bpy.ops.transform.resize(value = (0,0,1))
        bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic')
        
        bpy.context.scene.cursor_location = Prep_Center
        bpy.ops.transform.rotate(value = (2*math.pi/self.resolution), axis = (0,0,1))
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.modifier_copy(modifier = mod.name)
        bpy.ops.object.modifier_apply(modifier = trace_obj.modifiers[1].name)
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        bpy.ops.mesh.looptools_flatten(influence=90, plane='best_fit', restriction='none')
        bpy.ops.mesh.looptools_space(influence=90, input='selected', interpolation='cubic')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        for b in range(1,self.resolution+self.extra):
            verts = trace_data.vertices
            eds = [e for e in trace_data.edges if e.select]
            ed_vecs = [(verts[e.vertices[1]].co - verts[e.vertices[0]].co) for e in eds]
            curves = []

            for i in range(3,len(eds)-3):
                a1 = ed_vecs[i-1].angle(ed_vecs[i+1])
                a2 = ed_vecs[i-2].angle(ed_vecs[i+2])
                a3 = ed_vecs[i-3].angle(ed_vecs[i+3])
    
                l1 = ed_vecs[i-1].length + ed_vecs[i+1].length
                l2 = ed_vecs[i-2].length + ed_vecs[i+2].length
                l3 = ed_vecs[i-3].length + ed_vecs[i+3].length
    
    
                curve = 1/6 * (3*a1/l1 + 2 * a2/l2 + a3/l3)
                curves.append(curve)
    
            c = max(curves)
            n = curves.index(c)
            max_ed = eds[n+3] #need to check this indexing
            loc = .5 * (verts[max_ed.vertices[0]].co + verts[max_ed.vertices[1]].co)
        
            locs.append(loc)
            
            
            
            bpy.ops.object.mode_set(mode = 'EDIT')
            
            bpy.context.scene.cursor_location = locs[b]
            zscale = self.search/trace_obj.dimensions[2]  #if the shrinkwrapping has resulted in contraction or dilation, we want to fix that.
            bpy.ops.transform.resize(value = (0,0,zscale))
            bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic')
        
            bpy.context.scene.cursor_location = Prep_Center
            
            COM = odcutils.get_com(trace_data,v_ind,'')
            delt = locs[b] - COM
            
            bpy.ops.transform.translate(value = (delt[0], delt[1], delt[2]))
            bpy.ops.transform.rotate(value = (2*math.pi/self.resolution), axis = (0,0,1))
            
            
        
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.modifier_copy(modifier = mod.name)
            bpy.ops.object.modifier_apply(modifier = trace_obj.modifiers[1].name)
            bpy.ops.object.mode_set(mode = 'EDIT')
        
            bpy.ops.mesh.looptools_flatten(influence=90, plane='best_fit', restriction='none')
            bpy.ops.mesh.looptools_space(influence=90, input='selected', interpolation='cubic')
            
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.modifier_copy(modifier = mod.name)
            bpy.ops.object.modifier_apply(modifier = trace_obj.modifiers[1].name)
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold = .025) #this is probably the limit of any scanner accuracy anyway
            
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
        
        margin_data = bpy.data.meshes.new(margin)
        
        edges = []
        for i in range(0,len(locs)-1):
            edges.append([i,i+1])
        edges.append([len(locs)-1,0])
        faces = []
        
        margin_data.from_pydata(locs,edges,faces)
        margin_data.update()
        
        Margin = bpy.data.objects.new(margin, margin_data)
        sce.objects.link(Margin)
        
        current_objects = list(bpy.data.objects)
        bpy.ops.mesh.primitive_uv_sphere_add(size = .1)
        
        for ob in sce.objects:
            if ob not in current_objects:
                ob.name = margin + "_marker"
                ob.parent = Margin
                me = ob.data
                #me.materials.append(bpy.data.materials['intaglio_material'])
        
        Margin.dupli_type = 'VERTS'
        Margin.parent = Master     
        tooth.margin = margin
        
        #put the transform orientation back
        bpy.context.space_data.transform_orientation = current_transform
       
        return {'FINISHED'}  
          
class OPENDENTAL_OT_refine_margin(bpy.types.Operator):
    '''
    Converts the bez spline margin into a mesh, kicks into edit mode and enables porportional editing
    '''
    bl_idname = 'opendental.refine_margin'
    bl_label = "Refine Margin"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if not hasattr(context.scene, 'odc_props'): return False
        if not len(context.scene.odc_teeth): return False
        if not len(odcutils.tooth_selection(context)): return False
        
        tooth = odcutils.tooth_selection(context)[0]  #TODO:...make this poll work for all selected teeth...
        condition_1 = tooth.margin in bpy.data.objects
        return condition_1
    
    def execute(self, context):
        
        tooth = odcutils.tooth_selection(context)[0]
        sce=bpy.context.scene
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        prep = tooth.prep_model
        Prep = bpy.data.objects.get(prep)
        
        margin = tooth.margin
        if margin not in bpy.data.objects:
            self.report({'ERROR'},'No Margin to Refine!  Please mark margin first')
        if not Prep:
            self.report({'WARNING'},'No Prep to snap margin to!')
            
        Margin = bpy.data.objects[margin]
        Margin.dupli_type = 'NONE'
        
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        bpy.ops.object.select_all(action='DESELECT')
        
        bpy.context.tool_settings.use_snap = True
        bpy.context.tool_settings.snap_target= 'ACTIVE'
        bpy.context.tool_settings.snap_element = 'FACE'
        
        if Margin.type != 'MESH':  
            me_data = odcutils.bezier_to_mesh(Margin,  tooth.margin, n_points = 200)
            mx = Margin.matrix_world  
            context.scene.objects.unlink(Margin)
            bpy.data.objects.remove(Margin)
            new_obj = bpy.data.objects.new(tooth.margin, me_data)
            new_obj.matrix_world = mx
            context.scene.objects.link(new_obj)
            tooth.margin = new_obj.name #just in case of name collisions
            Margin = new_obj
        
        Margin.select = True
        sce.objects.active = Margin
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        
        if Prep and 'SHRINKWRAP' not in Margin.modifiers:
            i = len(Margin.modifiers)
            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            mod = Margin.modifiers[i]
            mod.target=Prep
            mod.show_on_cage = True

        bpy.context.tool_settings.use_snap = True
        bpy.context.tool_settings.snap_target= 'ACTIVE'
        bpy.context.tool_settings.snap_element = 'FACE'
        bpy.context.tool_settings.proportional_edit = 'ENABLED'
        bpy.context.tool_settings.proportional_size=1
        
        bpy.ops.object.editmode_toggle()
        
        
        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[4] = True
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_accept_margin(bpy.types.Operator):
    '''Confirm the marked margin'''
    bl_idname = 'opendental.accept_margin'
    bl_label = "Accept Margin"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        
        #restoration exists and is in scene
        if not hasattr(context.scene, 'odc_props'): return False
        if not len(context.scene.odc_teeth): return False
        if not len(odcutils.tooth_selection(context)): return False
        
        tooth = odcutils.tooth_selection(context)[0]  #TODO:...make this poll work for all selected teeth...
        condition_1 = tooth.margin in bpy.data.objects

        return condition_1

    def execute(self, context):
        
        #picks tooth based on selected/active object...will refactor soon
        tooth = odcutils.tooth_selection(context)[0]
        sce=bpy.context.scene
        a = tooth.name
        mesial = tooth.mesial
        distal = tooth.distal
        margin = tooth.margin
        axis = tooth.axis
        
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        if margin not in bpy.data.objects:
            self.report({'ERROR'},'No Margin to accept!')
            return {'CANCELLED'}
        if axis not in bpy.data.objects:
            self.report({'ERROR'}, 'No insertion axis for ' + a + ', please define insertion axis')
            print(tooth.margin)
            print(tooth.axis)
            print(tooth.name)
            
            print([ob.name for ob in bpy.data.objects])
            
            return {'CANCELLED'}
        
        
        Margin=bpy.data.objects[margin]
        Axis = bpy.data.objects[axis]
        if Margin.type != 'MESH':  
            me_data = odcutils.bezier_to_mesh(Margin,  tooth.margin, n_points = 200)
            mx = Margin.matrix_world  
            context.scene.objects.unlink(Margin)
            bpy.data.objects.remove(Margin)
            new_obj = bpy.data.objects.new(tooth.margin, me_data)
            new_obj.matrix_world = mx
            context.scene.objects.link(new_obj)
            tooth.margin = new_obj.name #just in case of name collisions
            Margin = new_obj
        
        master=sce.odc_props.master
        Margin.dupli_type = 'NONE'
        if mesial:
            bpy.data.objects[mesial].hide = False
            
        if distal:
            bpy.data.objects[distal].hide = False
        
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        psuedo_margin= str(a + "_Psuedo Margin")
        tooth.pmargin = psuedo_margin
        p_margin_me = Margin.to_mesh(context.scene, True, 'PREVIEW')
        p_margin_bme = bmesh.new()
        p_margin_bme.from_mesh(p_margin_me)
        
        Z = Axis.matrix_world.to_3x3() * Vector((0,0,1))
        odcutils.extrude_bmesh_loop(p_margin_bme, p_margin_bme.edges, Margin.matrix_world, Z, .2, move_only = True)
        odcutils.extrude_bmesh_loop(p_margin_bme, p_margin_bme.edges, Margin.matrix_world, Z, -.4, move_only = False)
        p_margin_bme.to_mesh(p_margin_me)
        PMargin = bpy.data.objects.new(psuedo_margin,p_margin_me)
        PMargin.matrix_world = Margin.matrix_world
        context.scene.objects.link(PMargin)
        bpy.data.objects[psuedo_margin].hide=True

        
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.proportional_edit = 'DISABLED'
        
        #Now we want to overpack the verts so that when the edge of the
        #restoration is snapped to it, it won't displace them too much
        # I have estimated ~25 microns as a fine linear packin
        #density....another option is to leave the curve as an
        #implicit function.... hmmmmm


        for i, layer in enumerate(layers_copy):
            context.scene.layers[i] = layer
        context.scene.layers[4] = True
        return {'FINISHED'}

class OPENDENTAL_OT_place_margin_tracer(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "opendental.palce_margin_tracer"
    bl_label = "Place Margin Tracer"
    bl_options = {'REGISTER','UNDO'}
    
    radius = bpy.props.FloatProperty(
            name="Tracer Radius",
            default=1,
            min = .2,
            max = 5,
            step = 20,
            precision = 1)
       
    spokes = bpy.props.IntProperty(
            name = "Tracer Arms",
            default = 4,
            min = 4,
            max = 8,
            )
    @classmethod
    def poll(self, context):
        #picks tooth based on selected/active object...will refactor soon
        if len(odcutils.tooth_selection(context)):
            tooth = odcutils.tooth_selection(context)[0]
            if tooth.prep_model and tooth.prep_model in bpy.data.objects:
                return True
        else:
            return False
    
    
    def execute(self, context):
        #picks tooth based on selected/active object...will refactor soon
        tooth = odcutils.tooth_selection( context)
        sce=bpy.context.scene
        a = tooth.name
        
        prep = tooth.prep_model
        Prep = bpy.data.objects[prep]
        
        #TODO scene preservation
        
        #add tracer
        Tracer = odcutils.tracer_mesh_add(self.radius, context.scene.cursor_location,self.spokes, .1, Prep)
        Tracer.name += "_tracer"
        
        #TODO add margin tracer to property group
        odcutils.align_to_view(context, Tracer)
        
        #TODO project into prep surface
        
        #TODO Align to view
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_trace_walking(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "opendental.trace_crevice_walking"
    bl_label = "Trace Crevice"

    def modal(self, context, event):
        context.area.tag_redraw()

        
        if event.type in {'MIDDLEMOUSE','WHELLUPMOUSE','WHEELDOWNMOUSE'}:
            #let the user pan and rotate around (translate?)
            return {'PASS_THROUGH'}
        
        if event.type == 'TIMER':
            #iterate....check convergence.
            if self.keep_iterating:
                self.iterate(context)

            return {'PASS_THROUGH'}
        
        elif event.type == 'MOUSEMOVE':
            #change the active bias
            region = context.region  
            rv3d = context.space_data.region_3d
            coord = event.mouse_region_x, event.mouse_region_y
            vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = view3d_utils.region_2d_to_location_3d(region, rv3d, coord, vec)  - 5000*vec  
            target = bpy.data.objects[self.target_name]
            #raycast onto active object
            ray_target = ray_origin + 5000*vec
            [hit, normal, face] = odcutils.obj_ray_cast(target, target.matrix_world, ray_origin, ray_target)
            
            if hit:
                self.current_bias_point = target.matrix_world * hit

            '''
            if not self.keep_iterating:
                self.bias_point = (event.mouse_region_x, event.mouse_region_y)
                self.keep_iterating = True
            '''
        
        elif event.type == 'LEFTMOUSE' and event.value == "PRESS":
            #confirm the existing walking cache
            
            #if continue_iterating still true, append the last confirmed point to the bias points
            #change the active bias
            region = context.region  
            rv3d = context.space_data.region_3d
            coord = event.mouse_region_x, event.mouse_region_y
            target = bpy.data.objects[self.target_name]
            vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = view3d_utils.region_2d_to_location_3d(region, rv3d, coord, vec)    
    
            #raycast onto active object
            ray_target = ray_origin + 3000*vec
            [hit, normal, face] = odcutils.obj_ray_cast(target, target.matrix_world, ray_origin, ray_target)
            
            if hit:
                self.bias_points.append(target.matrix_world * hit)
                
            #keep iterating to mouse projection on model
            self.keep_iterating = not self.keep_iterating
            return {'RUNNING_MODAL'}

        elif event.type == 'RIGHTMOUSE' and event.value == "PRESS":
            #pop off a bias point
            self.bias_points.pop()
            #pop off a bias normal
            
            #pop off stack of confirmed crevice points prior to that
                        #keep iterating to mouse projection on model
            self.keep_iterating = not self.keep_iterating
            return {'RUNNING_MODAL'}


        elif event.type in {'ESC'}:
            context.window_manager.event_timer_remove(self._timer)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        elif event.type in {'RETURN'}:
            context.window_manager.event_time_remove(self._timer)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            self._timer = context.window_manager.event_timer_add(.1, context.window)  #bpy.types.WindoManager.event_time_add?
            self._handle = bpy.types.SpaceView3D.draw_handler_add(bgl_utils.draw_callback_crevice_walking, args, 'WINDOW', 'POST_PIXEL')

            #initialze important values and gather important info
            region = context.region  
            rv3d = context.space_data.region_3d
            coord = event.mouse_region_x, event.mouse_region_y
            
            self.tracer_name = context.object.name #adding bpy here because getting weird error
            self.target_name = [ob.name for ob in context.selected_editable_objects if ob.name != self.tracer_name][0]
            
            tracer = bpy.data.objects[self.tracer_name]
            target = bpy.data.objects[self.target_name]
            
            #target.select = False
            tracer.select = True
            context.scene.objects.active = tracer
            
            #mod = tracer.modifers['Shrinkwrap']  #going to need to do some checking for dumb scenarios
            #self.target = mod.target
                      
            vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = view3d_utils.region_2d_to_location_3d(region, rv3d, coord, vec)    
    
            #raycast onto active object
            ray_target = ray_origin + 10000*vec
            [hit, normal, face] = odcutils.obj_ray_cast(target, target.matrix_world, ray_origin, ray_target)
            
            self.max_iters = 50
            self.keep_iterating = False  #turn this off/on when we get convergence on the bias point or add a new bias point
            self.session_iterations = 0
            
            if hit:
                self.current_bias_point = target.matrix_world * hit
            else:
                self.current_bias_point = target.location
            
            
            self.confirmed_path = []
            self.pending_path = [tracer.location.copy()]
            self.bias_points = []
            self.bias_normals = []  #gotta keep track of the normals so we can re-orient the tracker pointed the right way
            
            self.step_size = .5
            self.convergence_limit = 5
            

            

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
        
    def iterate(self, context):
        
        if self.session_iterations < self.max_iters and self.keep_iterating:
            tracer = bpy.data.objects[self.tracer_name]
            me = odcutils.tracer_settle(tracer, settling_treshold = .001, max_settles=10, debug = False)
            
            if len(self.pending_path) >1:
                bias = self.pending_path[-1] - self.pending_path[-2]
            else:
                bias = tracer.matrix_world.to_3x3() * Vector((0,0,1))
            
            prop_dir = odcutils.determine_trace_propogate_direction(tracer, me, bias)
            tracer.location += self.step_size*prop_dir
            
            convergence = bias - tracer.location
            self.pending_path.append(tracer.location)
            
            if convergence.length < self.convergence_limit:
                self.keep_iterating = False
            
            self.session_iterations += 1
        
    def execute(self,context):
        print('execute')

def icrnmgn_draw_callback(self, context):  
    self.crv.draw(context)
    self.help_box.draw()
    if self.margin_manager:
        self.margin_manager.draw(context)
    
class OPENDENTAL_OT_mark_crown_margin(bpy.types.Operator):
    """Mark Margin.  Draw a line with the mouse to extrude bezier curves"""
    bl_idname = "opendental.mark_crown_margin"
    bl_label = "Mark Crown Margin"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        teeth = odcutils.tooth_selection(context)
        
        if teeth != []:#This can only happen one tooth at a time
            #tooth = teeth[0]
            #return tooth.prep_model in bpy.data.objects
            return True
        else:
            return False   
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
        
        if event.type == 'S' and event.value == 'PRESS' and self.margin_manager:
            self.margin_manager.prepare_slice()
            return 'slice'
            
        if event.type == 'RET' and event.value == 'PRESS':
            return 'finish'
            
        elif event.type == 'ESC' and event.value == 'PRESS':
            del_obj = self.crv.crv_obj
            context.scene.objects.unlink(del_obj)
            bpy.data.objects.remove(del_obj)
            self.tooth.margin = ''
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
    
    def modal_slice(self,context,event):
        # no navigation in grab mode
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            #confirm location
            self.margin_manager.slice_confirm()
            return 'main'
        
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            #put it back!
            self.margin_manager.slice_cancel()
            return 'main'
        
        elif event.type == 'MOUSEMOVE':
            #update the b_pt location
            self.margin_manager.slice_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
            return 'slice'
         
    def modal(self, context, event):
        context.area.tag_redraw()
        
        FSM = {}    
        FSM['main']    = self.modal_main
        FSM['grab']    = self.modal_grab
        FSM['slice']   = self.modal_slice
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
    
    def invoke(self, context, event):
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        tooth = odcutils.tooth_selection(context)[0]
        self.tooth = tooth
        sce=bpy.context.scene
        a = tooth.name
        prep = tooth.prep_model
        margin = str(a + "_Margin")
        self.crv = None
        self.margin_manager = None
        if margin in bpy.data.objects:
            self.report({'WARNING'}, "you have already made a margin for this tooth, hit esc and then undo if you didn't want to replace it")
        
        if prep and prep in bpy.data.objects:
            Prep = bpy.data.objects[prep]
            Prep.hide = False
            L = Prep.location
            ###Keep a list of unhidden objects
            for o in sce.objects:
                if o.name != prep and not o.hide:
                    o.hide = True
                    
            self.crv = CurveDataManager(context,snap_type ='OBJECT', snap_object = Prep, shrink_mod = True, name = margin)
            
            self.margin_manager = MarginSlicer(tooth, context, self.crv)
        else:
            self.report({'WARNING'}, "There is no prep for this tooth, your margin will snap to the master model or all objects in scene")
        
        master=sce.odc_props.master
        if master and master in bpy.data.objects:
            Master = bpy.data.objects[master]
            if prep not in bpy.data.objects:
                self.crv = CurveDataManager(context,snap_type ='OBJECT', snap_object = Master, shrink_mod = True, name = margin)
                self.margin_manager = MarginSlicer(tooth, context, self.crv)
        else:
            self.report({'WARNING'}, "No master model...there are risks!")
        
        if not self.crv:
            self.crv = CurveDataManager(context,snap_type ='SCENE', snap_object = None, shrink_mod = False, name = margin)
        
        tooth.margin = self.crv.crv_obj.name
        
        help_txt = "DRAW MARGIN OUTLINE\n\nLeft Click on model to draw outline \nRight click to delete a point \nLeft Click last point to make loop \n G to grab  \n S to show slice \n ENTER to confirm \n ESC to cancel"
        self.help_box = TextBox(context,500,500,300,200,10,20,help_txt)
        self.help_box.snap_to_corner(context, corner = [1,1])
        self.mode = 'main'
        self._handle = bpy.types.SpaceView3D.draw_handler_add(icrnmgn_draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
       
def register():
    #bpy.utils.register_class(OPENDENTAL_OT_initiate_margin)
    #bpy.utils.register_class(OPENDENTAL_OT_initiate_auto_margin)
    #bpy.utils.register_class(OPENDENTAL_OT_walk_around_margin)
    bpy.utils.register_class(OPENDENTAL_OT_mark_crown_margin)
    bpy.utils.register_class(OPENDENTAL_OT_refine_margin)
    bpy.utils.register_class(OPENDENTAL_OT_accept_margin)
    #bpy.utils.register_class(OPENDENTAL_OT_trace_walking)
    #bpy.utils.register_class(OPENDENTAL_OT_place_margin_tracer)
    #bpy.utils.register_class(OPENDENTAL_OT_mark_crown_margin)
    
    #bpy.utils.register_module(__name__)


    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_mark_crown_margin)
    #bpy.utils.unregister_class(OPENDENTAL_OT_initiate_margin)
    #bpy.utils.unregister_class(OPENDENTAL_OT_initiate_auto_margin)
    #bpy.utils.unregister_class(OPENDENTAL_OT_walk_around_margin)
    bpy.utils.unregister_class(OPENDENTAL_OT_refine_margin)
    bpy.utils.unregister_class(OPENDENTAL_OT_accept_margin)
    #bpy.utils.unregister_class(OPENDENTAL_OT_trace_walking)
    #bpy.utils.unregister_class(OPENDENTAL_OT_place_margin_tracer)

if __name__ == "__main__":
    register()