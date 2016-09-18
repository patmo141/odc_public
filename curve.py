'''
A couple of helper classes for curves
'''
import bpy
import bgl
import bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_point_line, intersect_line_plane
from mathutils.bvhtree import BVHTree
from bpy_extras import view3d_utils
 
import bgl_utils
import common_drawing
from mesh_cut import cross_section_2seeds_ver1, path_between_2_points, grow_selection_to_find_face, flood_selection_faces
import math
import random
import time
from common_utilities import bversion

class PolyLineKnife(object):
    '''
    A class which manages user placed points on an object to create a
    poly_line, adapted to the objects surface.
    '''
    def __init__(self,context, cut_object, ui_type = 'DENSE_POLY'):   
        self.cut_ob = cut_object
        self.bme = bmesh.new()
        self.bme.from_mesh(cut_object.data)
        self.bme.verts.ensure_lookup_table()
        self.bme.edges.ensure_lookup_table()
        self.bme.faces.ensure_lookup_table()
        
        self.bvh = BVHTree.FromBMesh(self.bme)
        
        self.cyclic = False
        self.pts = []
        self.cut_pts = []  #local points
        self.normals = []
        self.face_map = []
        self.face_changes = []
        self.new_cos = []
        self.ed_map = []
        self.ed_pcts = {}
        
        self.face_chain = set()  #all faces crossed by the cut curve
        if ui_type not in {'SPARSE_POLY','DENSE_POLY', 'BEZIER'}:
            self.ui_type = 'SPARSE_POLY'
        else:
            self.ui_type = ui_type
                
        self.selected = -1
        self.hovered = [None, -1]
        
        self.grab_undo_loc = None
        self.mouse = (None, None)
        
        #keep up with these to show user
        self.bad_segments = []
        self.split = False
        self.face_seed = None
    
    def reset_vars(self):
        '''
        TODOD, parallel workflow will make this obsolete
        '''
        self.cyclic = False
        self.pts = []
        self.cut_pts = []  #local points
        self.normals = []
        self.face_map = []
        self.face_changes = []
        self.new_cos = []
        self.ed_map = []
        self.ed_pcts = {}
        
        self.face_chain = set()  #all faces crossed by the cut curve
                
        self.selected = -1
        self.hovered = [None, -1]
        
        self.grab_undo_loc = None
        self.mouse = (None, None)
        
        #keep up with these to show user
        self.bad_segments = []
        self.face_seed = None
        
    def grab_initiate(self):
        if self.selected != -1:
            self.grab_undo_loc = self.pts[self.selected]
            return True
        else:
            return False
       
    def grab_mouse_move(self,context,x,y):
        region = context.region
        rv3d = context.region_data
        coord = x, y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)

        mx = self.cut_ob.matrix_world
        imx = mx.inverted()
        if bversion() < '002.077.000':
            loc, no, face_ind = self.cut_ob.ray_cast(imx * ray_origin, imx * ray_target)
        else:
            ok, loc, no, face_ind = self.cut_ob.ray_cast(imx * ray_origin, imx * ray_target - imx*ray_origin)
        
        if face_ind == -1:        
            self.grab_cancel()  
        else:
            self.pts[self.selected] = mx * loc
            self.cut_pts[self.selected] = loc
            self.normals[self.selected] = no
            self.face_map[self.selected] = face_ind
        
    def grab_cancel(self):
        self.pts[self.selected] = self.grab_undo_loc
        return
    
    def grab_confirm(self):
        self.grab_undo_loc = None
        return
               
    def click_add_point(self,context,x,y):
        '''
        x,y = event.mouse_region_x, event.mouse_region_y
        
        this will add a point into the bezier curve or
        close the curve into a cyclic curve
        '''
        region = context.region
        rv3d = context.region_data
        coord = x, y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)
        mx = self.cut_ob.matrix_world
        imx = mx.inverted()

        if bversion() < '002.077.000':
            loc, no, face_ind = self.cut_ob.ray_cast(imx * ray_origin, imx * ray_target)
        else:
            ok, loc, no, face_ind = self.cut_ob.ray_cast(imx * ray_origin, imx * ray_target - imx*ray_origin)
            
        if face_ind == -1: 
            self.selected = -1
            return
        
        if self.hovered[0] == None:  #adding in a new point
            self.pts += [mx * loc]
            self.cut_pts += [loc]
            self.normals += [no]
            self.face_map += [face_ind]
            self.selected = len(self.pts) -1
                
        if self.hovered[0] == 'POINT':
            self.selected = self.hovered[1]
            if self.hovered[1] == 0:  #clicked on first bpt, close loop
                self.cyclic = self.cyclic == False
            return
         
        elif self.hovered[0] == 'EDGE':  #cut in a new point
            self.pts.insert(self.hovered[1]+1, mx * loc)
            self.cut_pts.insert(self.hovered[1]+1, loc)
            self.normals.insert(self.hovered[1]+1, no)
            self.face_map.insert(self.hovered[1]+1, face_ind)
            self.selected = self.hovered[1] + 1
            return
    
    def click_delete_point(self, mode = 'mouse'):
        if mode == 'mouse':
            if not self.hovered[0] == 'POINT': return
            self.pts.pop(self.hovered[1])
            self.cut_pts.pop(self.hovered[1])
            self.normals.pop(self.hovered[1])
            self.face_map.pop(self.hovered[1])
        
        else:
            if self.selected == -1: return
            self.pts.pop(self.selected)
            self.cut_pts.pop(self.selected)
            self.normals.pop(self.selected)
            self.face_map.pop(self.selected)

    def hover(self,context,x,y):
        '''
        hovering happens in screen space, 20 pixels thresh for points, 30 for edges
        '''
        self.mouse = Vector((x, y))
        if len(self.pts) == 0:
            return

        def dist(v):
            diff = v - Vector((x,y))
            return diff.length
        
        loc3d_reg2D = view3d_utils.location_3d_to_region_2d
        screen_pts =  [loc3d_reg2D(context.region, context.space_data.region_3d, pt) for pt in self.pts]
        closest_point = min(screen_pts, key = dist)
        
        if (closest_point - Vector((x,y))).length  < 20:
            self.hovered = ['POINT',screen_pts.index(closest_point)]
            return

        if len(self.pts) < 2: 
            self.hovered = [None, -1]
            return
                    
        for i in range(0,len(self.pts)):   
            a  = loc3d_reg2D(context.region, context.space_data.region_3d,self.pts[i])
            next = (i + 1) % len(self.pts)
            b = loc3d_reg2D(context.region, context.space_data.region_3d,self.pts[next])
            
            if b == 0 and not self.cyclic:
                self.hovered = [None, -1]
                return
            
            if a and b:
                intersect = intersect_point_line(Vector((x,y)).to_3d(), a.to_3d(),b.to_3d()) 
                if intersect:
                    dist = (intersect[0].to_2d() - Vector((x,y))).length_squared
                    bound = intersect[1]
                    if (dist < 900) and (bound < 1) and (bound > 0):
                        self.hovered = ['EDGE',i]
                        return
                    
        self.hovered = [None, -1]
            
    def snap_poly_line(self):
        '''
        only needed if processing an outside mesh
        '''
        locs = []
        self.face_map = []
        self.normals = []
        self.face_changes = []
        mx = self.cut_ob.matrix_world
        imx = mx.inverted()
        for i, v in enumerate(self.pts):
            if bversion() < '002.077.000':
                loc, no, ind, d = self.bvh.find(imx * v)
            else:
                loc, no, ind, d = self.bvh.find_nearest(imx * v)
            
            self.face_map.append(ind)
            self.normals.append(no)
            locs.append(loc)
            if i > 0:
                if ind != self.face_map[i-1]:
                    self.face_changes.append(i-1)
            
            #do double check for the last point
            if i == len(self.pts) - 1:
                if ind != self.face_map[0] :
                    self.face_changes.append(i)      
        self.cut_pts = locs

    def click_seed_select(self, context, x, y):
        
        region = context.region
        rv3d = context.region_data
        coord = x, y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)
        mx = self.cut_ob.matrix_world
        imx = mx.inverted()
        if bversion() < '002.077.000':
            loc, no, face_ind = self.cut_ob.ray_cast(imx * ray_origin, imx * ray_target)
        else:
            ok, loc, no, face_ind = self.cut_ob.ray_cast(imx * ray_origin, imx * ray_target - imx*ray_origin)
        if face_ind != -1:
            self.face_seed = face_ind
            print('face selected!!')
            return True
            
        else:
            self.face_seed = None
            print('face not selected')
            return False
                     
    def make_cut(self):
            
        mx = self.cut_ob.matrix_world
        imx = mx.inverted()
        print('cutting!')
        self.new_cos = []
        self.ed_map = []
        
        self.face_chain = set()
        self.snap_poly_line()
        self.bad_segments = []
        
        print('there are %i cut points' % len(self.cut_pts))
        print('there are %i face changes' % len(self.face_changes))
        for m, ind in enumerate(self.face_changes):
            print('\n')
            
            if ind == len(self.face_changes) - 1 and not self.cyclic:
                'not cyclic, we are done'
                break
            
            
            n_p1 = (m + 1) % len(self.face_changes)
            ind_p1 = self.face_changes[n_p1]
            
            print('walk on edge pair %i, %i' % (m, n_p1))
            print('original faces in mesh %i, %i' % (self.face_map[ind], self.face_map[ind_p1]))
            
            f0 = self.bme.faces[self.face_map[ind]]
            f1 = self.bme.faces[self.face_map[ind_p1]]
            
            no0 = self.normals[ind]
            no1 = self.normals[ind_p1]
    
            surf_no = no0.lerp(no1, 0.5)  #must be a better way.
            
            
            #normal method 1
            e_vec = self.cut_pts[ind_p1] - self.cut_pts[ind]
            
            
            #normal method 2
            #v0 = self.cut_pts[ind] - self.cut_pts[ind-1]
            #v0.normalize()
            #v1 = self.cut_pts[ind + 1] - self.cut_pts[ind]
            #v1.normalize()
            
            #ang = v0.angle(v1, 0)
            #if ang > 1 * math.pi/180:
            #    curve_no = v0.cross(v1)
            #    cut_no = e_vec.cross(curve_no)
                
            #else: #method 2 using surface normal
            cut_no = e_vec.cross(surf_no)
                
            cut_pt = .5*self.cut_pts[ind_p1] + 0.5*self.cut_pts[ind]
    
            #find the shared edge
            cross_ed = None
            for ed in f0.edges:
                if f1 in ed.link_faces:
                    cross_ed = ed
                    break
            
            #if no shared edge, need to cut across to the next face    
            if not cross_ed:
                
                if self.face_changes.index(ind) != 0:
                    p_face = self.bme.faces[self.face_map[ind-1]]
                else:
                    p_face = None
                
                print('LINE WALK METHOD')
                vs = []
                epp = .0000000001
                use_limit = True
                attempts = 0
                while epp < .0001 and not len(vs) and attempts <= 5:
                    attempts += 1
                    vs, eds, eds_crossed, faces_crossed, error = path_between_2_points(self.bme, 
                                                             self.bvh, 
                                                             mx, 
                                                             self.cut_pts[ind], self.cut_pts[ind_p1], 
                                                             max_tests = 10000, debug = True, 
                                                             prev_face = p_face,
                                                             use_limit = use_limit)
                    if len(vs) and error == 'LIMIT_SET':
                        vs = []
                        use_limit = False
                        print('Limit was too limiting, relaxing that consideration')
                        
                    elif len(vs) == 0 and error == 'EPSILON':
                        print('Epsilon was too small, relaxing epsilon')
                        epp *= 10
                    elif len(vs) == 0 and error:
                        print("too bad, couldn't adjust")
                        break
                
                if not len(vs):
                    print('\n')
                    print('CUTTING METHOD')
                    
                    vs = []
                    epp = .0000000001
                    use_limit = True
                    attempts = 0
                    while epp < .0001 and not len(vs) and attempts <= 10:
                        attempts += 1
                        vs, eds, eds_crossed, faces_crossed, error = cross_section_2seeds_ver1(self.bme, mx, 
                                                        cut_pt, cut_no, 
                                                        f0.index,self.cut_pts[ind],
                                                        f1.index, self.cut_pts[ind_p1],
                                                        max_tests = 10000, debug = True, prev_face = p_face,
                                                        epsilon = epp)
                        if len(vs) and error == 'LIMIT_SET':
                            vs = []
                            use_limit = False
                        elif len(vs) == 0 and error == 'EPSILON':
                            epp *= 10
                        elif len(vs) == 0 and error:
                            print('too bad, couldnt adjust')
                            break
                        
                if len(vs):
                    for v,ed in zip(vs,eds_crossed):
                        self.new_cos.append(v)
                        self.ed_map.append(ed)
                        
                    self.face_chain.update(faces_crossed)
                        
                    if ind == len(self.face_changes) - 1:
                        print('THis is the loop closing segment.  %i' % len(vs))
                else:
                    self.bad_segments.append(ind)
                    print('cut failure!!!')
                continue
            
            p0 = cross_ed.verts[0].co
            p1 = cross_ed.verts[1].co
            v = intersect_line_plane(p0,p1,cut_pt,cut_no)
            if v:
                self.new_cos.append(v)
                self.ed_map.append(cross_ed)

    def calc_ed_pcts(self):
        '''
        not used utnil bmesh.ops uses the percentage index
        '''
        if not len(self.ed_map) and len(self.new_cos): return
        
        self.ed_pcts = {}
        for v, ed in zip(self.new_cos, self.ed_map):
            
            v0 = ed.verts[0].co
            v1 = ed.verts[1].co
            
            ed_vec = v1 - v0
            L = ed_vec.length
            
            cut_vec = v - v0
            l = cut_vec.length
            
            pct = l/L
            self.ed_pcts[ed] = pct
            
    def find_select_inner_faces(self):
        if not self.face_seed: return
        if len(self.bad_segments): return
        f0 = self.bme.faces[self.face_seed]
        inner_faces = flood_selection_faces(self.bme, set(), f0, max_iters=1000)
        
        for f in self.bme.faces:
            f.select_set(False)
        for f in inner_faces:
            f.select_set(True)
                 
    def confirm_cut_to_mesh(self):
        new_verts = []
        new_bmverts = []
        new_edges = []
        
        self.calc_ed_pcts()
        ed_set = set(self.ed_map)
        if len(self.ed_map) != len(set(self.ed_map)):  #doubles in ed dictionary
            seen = set()
            new_eds = []
            new_cos = []
            removals = []

            for i, ed in enumerate(self.ed_map):
                if ed not in seen and not seen.add(ed):
                    new_eds += [ed]
                    new_cos += [self.new_cos[i]]
                else:
                    removals.append(i)
            
            print(removals)
            
            self.ed_map = new_eds
            self.new_cos = new_cos
            
            
        start = time.time()
        print('bisecting edges')
        geom =  bmesh.ops.bisect_edges(self.bme, edges = self.ed_map,cuts = 1,edge_percents = self.ed_pcts)
        new_bmverts = [ele for ele in geom['geom_split'] if isinstance(ele, bmesh.types.BMVert)]

        #can't be that easy can it?
        for v, co in zip(new_bmverts, self.new_cos):
            v.co = co
            
        finish = time.time()
        print('Took %f seconds' % (finish-start))
        start = finish    
        ed_geom = bmesh.ops.connect_verts(self.bme, verts = new_bmverts, faces_exclude = [], check_degenerate = False)
        new_edges = ed_geom['edges']
        
        finish = time.time()
        print('took %f seconds' % (finish-start))
        
        start = finish
        
        print('splitting new edges')
        self.bme.verts.ensure_lookup_table()
        self.bme.edges.ensure_lookup_table()
        bmesh.ops.split_edges(self.bme, edges = new_edges, verts = [], use_verts = False) 
        
        self.bme.verts.ensure_lookup_table()
        self.bme.edges.ensure_lookup_table()
        self.bme.faces.ensure_lookup_table()
        finish = time.time()
        print('took %f seconds' % (finish-start))
        self.split = True
        
    def split_geometry(self):
        if not (self.split and self.face_seed): return
        
        self.find_select_inner_faces()
        
        self.bme.to_mesh(self.cut_ob.data)
        bpy.ops.object.mode_set(mode ='EDIT')
        bpy.ops.mesh.separate(type = 'SELECTED')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        #EXPENSIVE!!
        #self.bme = bmesh.new()
        #self.bme.from_mesh(self.cut_ob.data)
        #self.bme.verts.ensure_lookup_table()
        #self.bme.edges.ensure_lookup_table()
        #self.bme.faces.ensure_lookup_table()
        #self.bvh = BVHTree.FromBMesh(self.bme)
        #self.reset_vars()
          
    def replace_segment(self,start,end,new_locs):
        #http://stackoverflow.com/questions/497426/deleting-multiple-elements-from-a-list
        return
                
    def draw(self,context):
        if len(self.pts) == 0: return
        
        if self.cyclic and len(self.pts):
            common_drawing.draw_polyline_from_3dpoints(context, self.pts + [self.pts[0]], (.1,.2,1,.8), 2, 'GL_LINE_STRIP')
        
        else:
            common_drawing.draw_polyline_from_3dpoints(context, self.pts, (.1,.2,1,.8), 2, 'GL_LINE')
        
        if self.ui_type != 'DENSE_POLY':    
            bgl_utils.draw_3d_points(context,self.pts, 3)
            bgl_utils.draw_3d_points(context,[self.pts[0]], 8, color = (1,1,0,1))
            
        else:
            common_drawing.draw_3d_points(context,self.pts,(1,1,1,1),4) 
            bgl_utils.draw_3d_points(context,[self.pts[0]], 4, color = (1,1,0,1))
        
        
        if self.selected != -1 and len(self.pts) >= self.selected + 1:
            bgl_utils.draw_3d_points(context,[self.pts[self.selected]], 8, color = (0,1,1,1))
                
        if self.hovered[0] == 'POINT':
            bgl_utils.draw_3d_points(context,[self.pts[self.hovered[1]]], 8, color = (0,1,0,1))
     
        elif self.hovered[0] == 'EDGE':
            loc3d_reg2D = view3d_utils.location_3d_to_region_2d
            a = loc3d_reg2D(context.region, context.space_data.region_3d, self.pts[self.hovered[1]])
            next = (self.hovered[1] + 1) % len(self.pts)
            b = loc3d_reg2D(context.region, context.space_data.region_3d, self.pts[next])
            common_drawing.draw_polyline_from_points(context, [a,self.mouse, b], (0,.2,.2,.5), 2,"GL_LINE_STRIP")  

        if self.face_seed:
            #TODO direct bmesh face drawing util
            vs = self.bme.faces[self.face_seed].verts
            bgl_utils.draw_3d_points(context,[self.cut_ob.matrix_world * v.co for v in vs], 4, color = (1,1,.1,1))
            
            
        if len(self.new_cos):
            bgl_utils.draw_3d_points(context,[self.cut_ob.matrix_world * v for v in self.new_cos], 6, color = (.2,.5,.2,1))
        if len(self.bad_segments):
            for ind in self.bad_segments:
                m = self.face_changes.index(ind)
                m_p1 = (m + 1) % len(self.face_changes)
                ind_p1 = self.face_changes[m_p1]
                common_drawing.draw_polyline_from_3dpoints(context, [self.cut_pts[ind], self.cut_pts[ind_p1]], (1,.1,.1,1), 4, 'GL_LINE')
                                                                     
class CurveDataManager(object):
    '''
    a helper class for interactive editing of Blender bezier curve
    data object
    '''
    def __init__(self,context,snap_type ='SCENE', snap_object = None, shrink_mod = False, name = 'Outline'):
        '''
        will create a new bezier object, with all auto
        handles. Links it to scene
        '''
        self.crv_data = bpy.data.curves.new(name,'CURVE')
        self.crv_data.splines.new('BEZIER')
        self.crv_data.splines[0].bezier_points[0].handle_left_type = 'AUTO'
        self.crv_data.splines[0].bezier_points[0].handle_right_type = 'AUTO'
        self.crv_data.dimensions = '3D'
        self.crv_obj = bpy.data.objects.new(name,self.crv_data)
        context.scene.objects.link(self.crv_obj)
        
        self.snap_type = snap_type  #'SCENE' 'OBJECT'
        self.snap_ob = snap_object
        
        if snap_object and shrink_mod:
            mod = self.crv_obj.modifiers.new('Wrap','SHRINKWRAP')
            mod.target = snap_object
            mod.use_keep_above_surface = True
            #mod.use_apply_on_spline = True
        
        self.started = False
        self.b_pts = []  #vectors representing locations of be
        self.selected = -1
        self.hovered = [None, -1]
        
        self.grab_undo_loc = None
        self.mouse = (None, None)
    
    def grab_initiate(self):
        if self.selected != -1:
            self.grab_undo_loc = self.b_pts[self.selected]
            return True
        
        else:
            return False
    
    def grab_mouse_move(self,context,x,y):
        region = context.region
        rv3d = context.region_data
        coord = x, y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)
        
        crv_mx = self.crv_obj.matrix_world
        i_crv_mx = crv_mx.inverted()  
        
        
        hit = False
        if self.snap_type == 'SCENE':
            
            mx = Matrix.Identity(4) #scene ray cast returns world coords
            if bversion() < '002.077.000':
                res, obj, omx, loc, no = context.scene.ray_cast(ray_origin, ray_target)
            else:
                res, loc, no, ind, obj, omx = context.scene.ray_cast(ray_origin, view_vector)
            
            if res:
                hit = True
        
            else:
                #cast the ray into a plane a
                #perpendicular to the view dir, at the last bez point of the curve
                hit = True
                view_direction = rv3d.view_rotation * Vector((0,0,-1))
                plane_pt = self.grab_undo_loc
                loc = intersect_line_plane(ray_origin, ray_target,plane_pt, view_direction)
                
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
            local_loc = i_crv_mx * mx * loc
            self.crv_data.splines[0].bezier_points[self.selected].co = local_loc
            self.b_pts[self.selected] = mx * loc
        
    def grab_cancel(self):
        crv_mx = self.crv_obj.matrix_world
        i_crv_mx = crv_mx.inverted()  
        
        old_co =  i_crv_mx * self.grab_undo_loc
        self.crv_data.splines[0].bezier_points[self.selected].co = old_co
        self.b_pts[self.selected] = old_co
        return
    
    def grab_confirm(self):
        self.grab_undo_loc = None
        return
               
    def click_add_point(self,context,x,y):
        '''
        x,y = event.mouse_region_x, event.mouse_region_y
        
        this will add a point into the bezier curve or
        close the curve into a cyclic curve
        '''
        region = context.region
        rv3d = context.region_data
        coord = x, y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)
        
        crv_mx = self.crv_obj.matrix_world
        i_crv_mx = crv_mx.inverted()  
        
        
        hit = False
        if self.snap_type == 'SCENE':
            mx = Matrix.Identity(4)  #loc is given in world loc...no need to multiply by obj matrix
            if bversion() < '002.077.000':
                res, obj, omx, loc, no = context.scene.ray_cast(ray_origin, ray_target)  #changed in 2.77
            else:
                res, loc, no, ind, obj, omx = context.scene.ray_cast(ray_origin, view_vector)
                
            hit = res
            if not hit:
                #cast the ray into a plane a
                #perpendicular to the view dir, at the last bez point of the curve
            
                view_direction = rv3d.view_rotation * Vector((0,0,-1))
            
                if len(self.b_pts):
                    if self.hovered[0] == 'EDGE':
                        plane_pt = self.b_pts[self.hovered[1]]
                    else:
                        plane_pt = self.b_pts[-1]
                else:
                    plane_pt = context.scene.cursor_location
                loc = intersect_line_plane(ray_origin, ray_target,plane_pt, view_direction)
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
            
            if face_ind != -1:
                hit = True
        
        if not hit: 
            self.selected = -1
            return
        
        if self.hovered[0] == None:  #adding in a new point
            if self.started:
                self.crv_data.splines[0].bezier_points.add(count = 1)
                bp = self.crv_data.splines[0].bezier_points[-1]
                bp.handle_right_type = 'AUTO'
                bp.handle_left_type = 'AUTO'
                bp.co =i_crv_mx* mx * loc
                self.b_pts.append(mx * loc)
                
            else:
                self.started = True
                delta = i_crv_mx *mx * loc - self.crv_data.splines[0].bezier_points[-1].co
                bp = self.crv_data.splines[0].bezier_points[0]
                bp.co += delta
                bp.handle_left += delta
                bp.handle_right += delta  
                self.b_pts.append(mx * loc) 
          
        if self.hovered[0] == 'POINT':
            self.selected = self.hovered[1]
            if self.hovered[1] == 0:  #clicked on first bpt, close loop
                self.crv_data.splines[0].use_cyclic_u = self.crv_data.splines[0].use_cyclic_u == False
            return

            
        elif self.hovered[0] == 'EDGE':  #cut in a new point
            self.b_pts.insert(self.hovered[1]+1, mx * loc)
            self.update_blender_curve_data()   
            return
    
    def click_delete_point(self, mode = 'mouse'):
        if mode == 'mouse':
            if not self.hovered[0] == 'POINT': return
            self.b_pts.pop(self.hovered[1])
            if len(self.b_pts) == 0:
                self.started = False
                return
            self.update_blender_curve_data()
        
        else:
            if self.selected == -1: return
            self.b_pts.pop(self.selected)
            if len(self.b_pts) == 0:
                self.started = False
                return
            self.update_blender_curve_data()
            

                          
    def update_blender_curve_data(self):
        #this may crash blender
        crv_data = bpy.data.curves.new('Outline','CURVE')
        crv_data.splines.new('BEZIER')
        crv_data.dimensions = '3D'
        #set any matrix stuff here
        crv_mx = self.crv_obj.matrix_world
        icrv_mx = crv_mx.inverted()
        
        bp = crv_data.splines[0].bezier_points[0]
        delta = self.b_pts[0] - bp.co
        bp.co += delta
        bp.handle_left += delta
        bp.handle_right += delta
        bp.handle_right_type = 'AUTO'
        bp.handle_left_type = 'AUTO'
        
        for i in range(1,len(self.b_pts)):
            crv_data.splines[0].bezier_points.add(count = 1)
            bp = crv_data.splines[0].bezier_points[i]
            bp.co = icrv_mx * self.b_pts[i]
            bp.handle_right_type = 'AUTO'
            bp.handle_left_type = 'AUTO'
        
        crv_data.splines[0].use_cyclic_u = self.crv_data.splines[0].use_cyclic_u
        self.crv_obj.data = crv_data
        self.crv_data.user_clear()
        bpy.data.curves.remove(self.crv_data)
        self.crv_data = crv_data
        
    def hover(self,context,x,y):
        '''
        hovering happens in screen space, 20 pixels
        '''
        self.mouse = Vector((x, y))
        if len(self.b_pts) == 0:
            return

        def dist(v):
            diff = v - Vector((x,y))
            return diff.length
        
        loc3d_reg2D = view3d_utils.location_3d_to_region_2d
        screen_pts =  [loc3d_reg2D(context.region, context.space_data.region_3d, b_pt) for b_pt in self.b_pts]
        closest_point = min(screen_pts, key = dist)
        
        if (closest_point - Vector((x,y))).length  < 20:
            self.hovered = ['POINT',screen_pts.index(closest_point)]
            return

        if len(self.b_pts) < 2: 
            self.hovered = [None, -1]
            return
            
        for i in range(0,len(self.b_pts)):   
            a  = loc3d_reg2D(context.region, context.space_data.region_3d,self.b_pts[i])
            next = (i + 1) % len(self.b_pts)
            b = loc3d_reg2D(context.region, context.space_data.region_3d,self.b_pts[next])
      
            if a and b:
                
                intersect = intersect_point_line(Vector((x,y)).to_3d(), a.to_3d(),b.to_3d()) 
                if intersect:
                    dist = (intersect[0].to_2d() - Vector((x,y))).length_squared
                    bound = intersect[1]
                    if (dist < 900) and (bound < 1) and (bound > 0):
                        self.hovered = ['EDGE',i]
                        return
            else:
                print('not a and b')
                print(a,b)
        self.hovered = [None, -1]
        
    def draw(self,context):
        if len(self.b_pts) == 0: return
        bgl_utils.draw_3d_points(context,self.b_pts, 3)
        bgl_utils.draw_3d_points(context,[self.b_pts[0]], 8, color = (1,1,0,1))
        
        if self.selected != -1:
            bgl_utils.draw_3d_points(context,[self.b_pts[self.selected]], 8, color = (0,1,1,1))
                
        if self.hovered[0] == 'POINT':
            bgl_utils.draw_3d_points(context,[self.b_pts[self.hovered[1]]], 8, color = (0,1,0,1))
     
        elif self.hovered[0] == 'EDGE':
            loc3d_reg2D = view3d_utils.location_3d_to_region_2d
            a = loc3d_reg2D(context.region, context.space_data.region_3d, self.b_pts[self.hovered[1]])
            next = (self.hovered[1] + 1) % len(self.b_pts)
            b = loc3d_reg2D(context.region, context.space_data.region_3d, self.b_pts[next])
            common_drawing.draw_polyline_from_points(context, [a,self.mouse, b], (0,.2,.2,.5), 2,"GL_LINE_STRIP")    