'''
Created on Aug 18, 2016

@author: Patrick
some useful tidbits
http://blender.stackexchange.com/questions/28940/how-can-i-update-a-menu-via-an-operator
https://developer.blender.org/diffusion/B/browse/master/release/scripts/templates_py/ui_previews_dynamic_enum.py
http://inside.mines.edu/fs_home/gmurray/ArbitraryAxisRotation/
'''
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Color, Quaternion
from mathutils.bvhtree import BVHTree
from bpy_extras import view3d_utils
from common_utilities import bversion
import common_drawing
import bgl_utils
from mesh_cut import cross_section_seed_ver1, bound_box
from textbox import TextBox
from odcutils import get_settings, obj_list_from_lib, obj_from_lib

class BracketDataManager(object):
    '''
    a helper class for interactive editing of Blender object
    on surface of another object
    '''
    def __init__(self,context,snap_type ='SCENE', snap_object = None, name = 'Bracket', bracket = None):
        '''
        will create a new cube object if a bracket is not provided
        TODO, bracket meta data for offset axes (tip, torque offset etc)
        '''
        
        if bracket == None:
            self.bracket_data = bpy.data.meshes.new(name)
            bme = bmesh.new()
            bmesh.ops.create_cube(bme, size = 2, matrix = Matrix.Identity(4))
            bme.to_mesh(self.bracket_data)
            self.bracket_obj = bpy.data.objects.new(name,self.bracket_data)
            context.scene.objects.link(self.bracket_obj)
            self.bracket_obj.draw_type = 'WIRE'  #important to prevent scene ray_cast
        else:
            self.bracket_obj = bracket
            
        self.snap_type = snap_type  #'SCENE' 'OBJECT'
        self.snap_ob = snap_object
                
        self.grab_undo_mx = Matrix.Identity(4)
        self.mouse = (None, None)  
    
    def place_bracket(self,context,x,y, normal = False):
        self.grab_initiate()
        self.grab_mouse_move(context, x, y, normal = normal)
        self.grab_confirm()
        
    def grab_initiate(self):
        self.grab_undo_mx = self.bracket_obj.matrix_world.copy()
        return True
    
    def grab_mouse_move(self,context,x,y, normal = False):
        region = context.region
        rv3d = context.region_data
        coord = x, y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)

        
        hit = False
        if self.snap_type == 'SCENE':
            
            if bversion() < '002.077.000':
                res, obj, mx, loc, no = context.scene.ray_cast(ray_origin, ray_target)
            else:
                res, loc, no, ind, obj, mx = context.scene.ray_cast(ray_origin, view_vector)
            if res:
                hit = True
        
        elif self.snap_type == 'OBJECT':
            mx = self.snap_ob.matrix_world
            imx = mx.inverted()
            
            if bversion() < '002.077.000':
                loc, no, face_ind = self.snap_ob.ray_cast(imx * ray_origin, imx * ray_target)
                if face_ind != -1:
                    hit = True
            else:
                ok, loc, no, face_ind = self.snap_ob.ray_cast(imx * ray_origin, imx * ray_target - imx*ray_origin)
                if ok:
                    hit = True
   
        if not hit:
            self.grab_cancel()
            
        else:
            world_location = mx * loc
            imx = mx.inverted()
            
            #this will be the object Z axis
            world_normal = imx.transposed().to_3x3() * no

            if normal:
                ob_Z = world_normal
                ob_Z.normalize()
                
                view_Y = rv3d.view_rotation * Vector((0,1,0))
                if self.bracket_obj.name.startswith("U") or self.bracket_obj.name.startswith("u"):
                    view_Y *= -1
                
                #project view y into the tangetnt plane of teh surface
                ob_Y = view_Y - view_Y.dot(ob_Z)*ob_Z
                ob_Y.normalize()
                
                ob_X = ob_Y.cross(ob_Z)
                ob_X.normalize()
                
                #rotation matrix from principal axes
                T = Matrix.Identity(3)  #make the columns of matrix X, Y, Z
                T[0][0], T[0][1], T[0][2]  = ob_X[0] ,ob_Y[0],  ob_Z[0]
                T[1][0], T[1][1], T[1][2]  = ob_X[1], ob_Y[1],  ob_Z[1]
                T[2][0] ,T[2][1], T[2][2]  = ob_X[2], ob_Y[2],  ob_Z[2]
        
                rot = T.to_4x4()
                
            else:
                rot = self.bracket_obj.matrix_world.to_3x3().to_4x4()
                
            loc = Matrix.Translation(world_location)    
            self.bracket_obj.matrix_world = loc * rot
    
    def grab_cancel(self):
        self.bracket_obj.matrix_world = self.grab_undo_mx
        return
    
    def grab_confirm(self):
        self.grab_undo_mx = Matrix.Identity(4)
        return
    
    def spin_initiate(self):
        self.grab_undo_mx = self.bracket_obj.matrix_world.copy()
        return
    
    def spin_cancel(self):
        self.grab_undo_mx = self.bracket_obj.matrix_world.copy()
        return
    
    def spin_confirm(self):
        self.grab_undo_mx = Matrix.Identity(4)
        return
    
    def spin_event(self, event, shift):
        
        loc = Matrix.Translation(self.bracket_obj.matrix_world.to_translation())
        rot_base = self.bracket_obj.matrix_world.to_3x3()
        Z = rot_base * Vector((0,0,1))
        
        if shift:
            ang = .5 * math.pi/180
        else:
            ang = 2.5*math.pi/180
        if event in {'WHEELUPMOUSE', 'UP_ARROW'}:
            rot = Matrix.Rotation(ang, 3, Z)
            
            print(rot)
            print(rot_base)
            print(rot * rot_base)
            self.bracket_obj.matrix_world = loc * (rot * rot_base).to_4x4()
        elif event in {'WHEELDOWNMOUSE', 'DOWN_ARROW'}:
            rot = Matrix.Rotation(-ang, 3, Z)
            self.bracket_obj.matrix_world = loc * (rot * rot_base).to_4x4()
        
        else:
            return
        
    def rotate_event(self, event, shift):
        
        loc = Matrix.Translation(self.bracket_obj.matrix_world.to_translation())
        rot_base = self.bracket_obj.matrix_world.to_3x3()
        Y = rot_base * Vector((0,1,0))
        
        if shift:
            ang = .5 * math.pi/180
        else:
            ang = 2.5*math.pi/180
        if event in {'WHEELUPMOUSE', 'RIGHT_ARROW'}:
            rot = Matrix.Rotation(ang, 3, Y)
            
            print(rot)
            print(rot_base)
            print(rot * rot_base)
            self.bracket_obj.matrix_world = loc * (rot * rot_base).to_4x4()
        elif event in {'WHEELDOWNMOUSE', 'LEFT_ARROW'}:
            rot = Matrix.Rotation(-ang, 3, Y)
            self.bracket_obj.matrix_world = loc * (rot * rot_base).to_4x4()
        
        else:
            return
            
    def torque_event(self, event, shift):
        
        loc = Matrix.Translation(self.bracket_obj.matrix_world.to_translation())
        rot_base = self.bracket_obj.matrix_world.to_3x3()
        X = rot_base * Vector((1,0,0))
        
        if shift:
            ang = .5 * math.pi/180
        else:
            ang = 2.5*math.pi/180
        if event in {'WHEELUPMOUSE', 'UP_ARROW'}:
            rot = Matrix.Rotation(ang, 3, X)
            self.bracket_obj.matrix_world = loc * (rot * rot_base).to_4x4()
        elif event in {'WHEELDOWNMOUSE', 'DOWN_ARROW'}:
            rot = Matrix.Rotation(-ang, 3, X)
            self.bracket_obj.matrix_world = loc * (rot * rot_base).to_4x4()
        
        else:
            return           
    
    def draw(self,context):
        pass

class BracektSlicer(object):
    def __init__(self, context, bracket_data_manager):
        '''
        Gets info from bracket manager and siplays orthogonal
        slices on the snap object
        '''
    
        if not bracket_data_manager.bracket_obj:
            return None
        
        elif not bracket_data_manager.snap_ob:
            return None
        
        self.bracket_data = bracket_data_manager
        ob = self.bracket_data.snap_ob
        bme = bmesh.new()
        bme.from_object(ob, context.scene)
        self.snap_ob = ob
        self.bme = bme
        self.bvh = BVHTree.FromBMesh(self.bme)
        
        self.cut_pt = None
        self.cut_no_x = None
        self.cut_no_y = None
        
        self.slice_points_x = []
        self.slice_points_y = []
        self.reference_L = []
        
        self.points_2d = []
        self.active_point_2d = Vector((0,0,0))
        self.mx = self.bracket_data.bracket_obj.matrix_world.to_3x3()
        
        b_gauge = self.bracket_data.bracket_obj.get('bracket_gauge') 
        if b_gauge and not get_settings().bgauge_override:
            #read the prescription value from the objects
            self.b_gauge = b_gauge
        else:
            #override the rx value
            self.b_gauge = get_settings().bracket_gauge
        
    def get_pt_and_no(self):
        mx = self.bracket_data.bracket_obj.matrix_world
        self.cut_pt = mx.to_translation()
        self.cut_no_x = mx.to_3x3()*Vector((1,0,0))
        self.cut_no_y = mx.to_3x3()*Vector((0,1,0))
        
        z = mx.to_3x3()*Vector((0,0,1))
        
        tip =  self.bracket_data.bracket_obj.get('tip')
        quad = self.bracket_data.bracket_obj.get('quadrant')    
        #if properties of bracket exist, it willa adjust
        if tip and quad:
            if quad in {'UL','LR',2,4}:
                print('clockwise tip crown toward midline for UL, LR, 2, 4')
                tip *= -1
            else:
                print('counter clockwise tip crown toward midline for UR, LL, 1, 3')
                
            tip_rad = math.pi * tip / 180
            
            
            tip_quat = Quaternion(z, tip_rad)
            self.cut_no_x = tip_quat * self.cut_no_x
        
        
    def slice(self):
        self.clear_draw()
        
        self.get_pt_and_no()
        
        mx = self.snap_ob.matrix_world
        imx = mx.inverted()
        if bversion() < '002.077.000':
            pt, no, seed, dist = self.bvh.find(imx * self.cut_pt)
        else:
            pt, no, seed, dist = self.bvh.find_nearest(imx * self.cut_pt)
        
        verts_x, eds = cross_section_seed_ver1(self.bme, mx, self.cut_pt, self.cut_no_x, seed, max_tests = 100)
        verts_y, eds = cross_section_seed_ver1(self.bme, mx, self.cut_pt, self.cut_no_y, seed, max_tests = 100)
        #put them in world space
        
        if verts_x != None:
            self.slice_points_x = [mx*v for v in verts_x]
        else:
            self.slice_points_x = []
        if verts_y != None:
            self.slice_points_y = [mx*v for v in verts_y]
        else:
            self.slice_points_y = []
            
        bmx = self.bracket_data.bracket_obj.matrix_world
        bracket_x = bmx.to_3x3()*Vector((1,0,0))
        bracket_z = bmx.to_3x3()*Vector((0,0,1))
        bracket_y = bracket_z.cross(self.cut_no_x)
        
        v0 = self.cut_pt
        v1 = v0 + self.b_gauge * bracket_y
        v_l = v1 - 4 * bracket_z
        v_m = v1 + 2 * bracket_x
        v_d = v1 - 2 * bracket_x
        self.reference_L = [v0, v1, v_l, v_m, v_d]
        
    def clear_draw(self):
        self.slice_points_x = []
        self.slice_points_y = []
        self.reference_L = []
    def make_points_2D(self):
        pass
    
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
        self.bracket_data.grab_initiate()
        self.slice()
        return
        
    def slice_mouse_move(self, context, x, y):
        self.bracket_data.grab_mouse_move(context, x, y)
        self.slice()
        #self.make_points_2D()
        return  
    
    def slice_confirm(self):
        self.bracket_data.grab_confirm()
        return
    
    def slice_cancel(self):
        self.clear_draw()
        self.bracket_data.grab_cancel()
        return
    
    def draw(self,context):
        #draw a box
        #draw a box outline
        #draw a 2D represntation of the cross section
        if self.slice_points_x != []:
            common_drawing.draw_polyline_from_3dpoints(context, self.slice_points_x, (.1,.8,.4,.8), 2, 'GL_LINE')
        if self.slice_points_y != []:
            common_drawing.draw_polyline_from_3dpoints(context, self.slice_points_y, (.1,.8,.4,.8), 2, 'GL_LINE')
            
        if self.reference_L != []:
            common_drawing.draw_polyline_from_3dpoints(context, self.reference_L[0:3], (.1,.2,.8,.8), 2, 'GL_LINE')
            common_drawing.draw_polyline_from_3dpoints(context, self.reference_L[3:5], (.1,.2,.8,.8), 2, 'GL_LINE')
            #common_drawing.draw_polyline_from_points(context, self.points_2d, (1,1,1,1), 2, 'GL_LINE')
            #common_drawing.draw_points(context, [self.active_pt2d], (1,.1,.1,1), 5)
    def cache_slice_to_grease(self,context):
        
        if len(self.slice_points_x) == 0 and len(self.slice_points_y) == 0:
            return
        
        if not self.bracket_data.bracket_obj.grease_pencil:
            gp = bpy.data.grease_pencil.new('Bracket')
            self.bracket_data.bracket_obj.grease_pencil = gp
        else:
            gp = self.bracket_data.bracket_obj.grease_pencil
            print(gp.name)
            #clear existing layers.  Dangerous if bracketing on a non bracket...
        if gp.layers:
            layers = [l for l in gp.layers]
            for l in layers:
                gp.layers.remove(l)
        
        slice_layer = gp.layers.new('Slice')
        slice_layer.color = Color((.8,.1,.1))
        if slice_layer.frames:
            fr = slice_layer.active_frame
        else:
            fr = slice_layer.frames.new(1) 
            
        # Create a new stroke

        strx, stry = fr.strokes.new(), fr.strokes.new()
        strx.draw_mode, stry.draw_mode = '3DSPACE' , '3DSPACE'
        
        strx.points.add(count = len(self.slice_points_x))
        stry.points.add(count = len(self.slice_points_y))
        
        for i, pt in enumerate(self.slice_points_x):
            strx.points[i].co = pt
        for i, pt in enumerate(self.slice_points_y):
            stry.points[i].co = pt
            
        return
    
def bracket_placement_draw_callback(self, context):  
    
    #self.help_box.draw()
    if self.bracket_slicer:
        self.bracket_slicer.draw(context)
    
class OPENDENTAL_OT_place_bracket(bpy.types.Operator):
    """Place Bracket on surface of selected object"""
    bl_idname = "opendental.place_ortho_bracket"
    bl_label = "Ortho Bracket Place"
    bl_options = {'REGISTER', 'UNDO'}
    

    @classmethod
    def poll(cls, context):
        if context.mode == "OBJECT" and context.object != None:
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

        if event.type == 'G' and event.value == 'PRESS' and self.bracket_slicer:
            self.bracket_slicer.prepare_slice()
            return 'grab'
        
        if event.type == 'T' and event.value == 'PRESS' and self.bracket_slicer:
            self.bracket_slicer.prepare_slice()
            return 'torque'
        
        if event.type == 'R' and event.value == 'PRESS' and self.bracket_slicer:
            self.bracket_slicer.prepare_slice()
            return 'rotate'
        
        if event.type == 'S' and event.value == 'PRESS' and self.bracket_slicer:
            self.bracket_slicer.prepare_slice()
            return 'tip'
        
        if event.type == 'MOUSEMOVE':  
            return 'main'
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            x, y = event.mouse_region_x, event.mouse_region_y
            self.bracket_manager.place_bracket(context, x,y)
            return 'main'
                               
        if event.type == 'RET' and event.value == 'PRESS':
            if self.bracket_slicer:
                self.bracket_slicer.cache_slice_to_grease(context)
                
            return 'finish'
            
        elif event.type == 'ESC' and event.value == 'PRESS':
            del_obj = self.bracket_manager.bracket_obj
            context.scene.objects.unlink(del_obj)
            bpy.data.objects.remove(del_obj)
            return 'cancel' 

        return 'main'
    
    def modal_torque(self,context,event):
        # no navigation in grab mode
        
        if event.type in {'LEFTMOUSE','RET','ENTER'} and event.value == 'PRESS':
            #confirm location
            self.bracket_slicer.slice_confirm()
            return 'main'
        
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            #put it back!
            self.bracket_slicer.slice_cancel()
            return 'main'
        
        #elif event.type == 'MOUSEMOVE':
            #update the b_pt location
        #    self.bracket_slicer.slice_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
        #    return 'torque'
        
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'UP_ARROW','DOWN_ARROW'}:
            self.bracket_manager.torque_event(event.type, event.shift)
            self.bracket_slicer.slice()
            return 'torque'
    
    def modal_rotate(self,context,event):
        # no navigation in grab mode
        
        if event.type in {'LEFTMOUSE','RET','ENTER'} and event.value == 'PRESS':
            #confirm location
            self.bracket_slicer.slice_confirm()
            return 'main'
        
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            #put it back!
            self.bracket_slicer.slice_cancel()
            return 'main'
        
        #commented out, no longer want to move the mouse
        #elif event.type == 'MOUSEMOVE':
            #update the b_pt location
        #    self.bracket_slicer.slice_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
        #    return 'rotate'
        
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'LEFT_ARROW','RIGHT_ARROW'}:
            self.bracket_manager.rotate_event(event.type, event.shift)
            self.bracket_slicer.slice()
            return 'rotate'
        
        else:
            return 'rotate'
    
    def modal_tip(self,context,event):
    # no navigation in grab mode
        
        if event.type in {'LEFTMOUSE','RET','ENTER'} and event.value == 'PRESS':
            #confirm location
            self.bracket_slicer.slice_confirm()
            return 'main'
        
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            #put it back!
            self.bracket_slicer.slice_cancel()
            return 'main'
        
        #commented out, no longer want to move the mouse
        #elif event.type == 'MOUSEMOVE':
            #update the b_pt location
        #    self.bracket_slicer.slice_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
        #    return 'rotate'
        
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'LEFT_ARROW','RIGHT_ARROW'}:
            self.bracket_manager.spin_event(event.type, event.shift)
            self.bracket_slicer.slice()
            return 'tip'
        
        else:
            return 'tip'
    def modal_start(self,context,event):
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            #confirm location
            self.bracket_slicer.slice_confirm()
            return 'main'
        
        elif event.type == 'MOUSEMOVE':
            x, y = event.mouse_region_x, event.mouse_region_y
            self.bracket_manager.place_bracket(context, x,y, normal = True)
            self.bracket_slicer.slice_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
            return 'start'
        
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'UP_ARROW','DOWN_ARROW'}:
            self.bracket_manager.spin_event(event.type, event.shift)
            self.bracket_slicer.slice()
            return 'start'
        
        elif event.type == "RIGTMOUSE" and event.value == 'PRESS':
            del_obj = self.bracket_manager.bracket_obj
            context.scene.objects.unlink(del_obj)
            bpy.data.objects.remove(del_obj)
            return 'cancel'
        
        else:
            return 'start'
           
    def modal_grab(self,context,event):
        # no navigation in grab mode
        #uses the slicer to manage the grab
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            #confirm location
            self.bracket_slicer.slice_confirm()
            return 'main'
        
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            #put it back!
            self.bracket_slicer.slice_cancel()
            return 'main'
        
        elif event.type == 'MOUSEMOVE':
            #update the b_pt location
            self.bracket_slicer.slice_mouse_move(context,event.mouse_region_x, event.mouse_region_y)
            return 'grab'
        
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'UP_ARROW','DOWN_ARROW'}:
            self.bracket_manager.spin_event(event.type, event.shift)
            self.bracket_slicer.slice()
            return 'grab'
      
    def modal(self, context, event):
        context.area.tag_redraw()
        
        FSM = {}
        FSM['start']   = self.modal_start
        FSM['main']    = self.modal_main
        FSM['rotate']    = self.modal_rotate
        FSM['grab']   = self.modal_grab
        FSM['torque']  = self.modal_torque
        FSM['tip']  = self.modal_tip
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

        settings = get_settings()
        libpath = settings.ortho_lib
        assets = obj_list_from_lib(libpath)
        
        if settings.bracket in assets:
            current_obs = [ob.name for ob in bpy.data.objects]
            obj_from_lib(settings.ortho_lib,settings.bracket)
            for ob in bpy.data.objects:
                if ob.name not in current_obs:
                    Bracket = ob
                    Bracket.hide = False
                        
            context.scene.objects.link(Bracket)
        else:
            Bracket = None
            
        if context.object and context.object.type == 'MESH':
            self.bracket_manager = BracketDataManager(context,snap_type ='OBJECT', 
                                                      snap_object = context.object, 
                                                      name = 'Bracket', bracket = Bracket)
            self.bracket_slicer = BracektSlicer(context, self.bracket_manager)
        else:
            self.bracket_manager = BracketDataManager(context,snap_type ='SCENE', 
                                                      snap_object = None, 
                                                      name = 'Bracket', 
                                                      bracket = Bracket)
            self.bracket_slicer = None
        
        
        help_txt = "DRAW MARGIN OUTLINE\n\nLeft Click on model to place bracket.\n G to grab  \n S to show slice \n ENTER to confirm \n ESC to cancel"
        self.help_box = TextBox(context,500,500,300,200,10,20,help_txt)
        self.help_box.snap_to_corner(context, corner = [1,1])
        self.mode = 'start'
        self._handle = bpy.types.SpaceView3D.draw_handler_add(bracket_placement_draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
class OPENDENTAL_OT_place_bracket_static(bpy.types.Operator):
    '''Places bracket or swaps existing bracket with new bracket of your choice'''
    bl_idname = "opendental.place_static_bracket"
    bl_label = "Place Bracket Static"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "ob"

    def item_cb(self, context):
        return [(obj.name, obj.name, '') for obj in self.objs]
 
    objs = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    
    ob = bpy.props.EnumProperty(name="Bracket Library Objects", 
                                 description="A List of the ortho library", 
                                 items=item_cb)
    
    def invoke(self, context, event): 
        self.objs.clear()
        settings = get_settings()
        libpath = settings.ortho_lib
        assets = obj_list_from_lib(libpath)
       
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
          
        world_mx = Matrix.Identity(4)
            
        world_mx[0][3]=sce.cursor_location[0]
        world_mx[1][3]=sce.cursor_location[1]
        world_mx[2][3]=sce.cursor_location[2]
                                        
        #is this more memory friendly than listing all objects?
        current_obs = [ob.name for ob in bpy.data.objects]
                
        #link the new implant from the library
        obj_from_lib(settings.ortho_lib,self.ob)
                
        #this is slightly more robust than trusting we don't have duplicate names.
        for ob in bpy.data.objects:
            if ob.name not in current_obs:
                Bracket = ob
                        
        sce.objects.link(Bracket)
        rv3d = context.region_data
        view_mx = rv3d.view_rotation.to_matrix()
    
        Bracket.matrix_world = world_mx * view_mx.to_4x4()              
        return {'FINISHED'}
     
def register():
    bpy.utils.register_class(OPENDENTAL_OT_place_bracket)
    bpy.utils.register_class(OPENDENTAL_OT_place_bracket_static)
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_place_bracket)
    bpy.utils.unregister_class(OPENDENTAL_OT_place_bracket_static)

if __name__ == "__main__":
    register()