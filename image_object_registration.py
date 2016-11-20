'''
Created on Oct 16, 2016
@author: Patrick Moore...and ____________ <--This could be you!

Modal Operator to generate a Blender Camera that matches 
an image of a known object

The user will select corresponding sets of points in the 3DView
and in the image editor.  The matching set of points will be used 
to calculate a perspective matrix P.  Then the matrix P, along with 
any know information about the actual camera, will be used to 
create a Blender camera and the image set as the background image.

#Solving for P from the input data.
http://www1.cs.columbia.edu/~atroccol/3DPhoto/3D-2D_registration.html
http://dsp.stackexchange.com/questions/1727/3d-position-estimation-using-2d-camera
http://blender.stackexchange.com/questions/46208/points-only-camera-calibration/65152#65152
http://stackoverflow.com/questions/24913232/using-numpy-np-linalg-svd-for-singular-value-decomposition

#Building Camera from P (Dr. Fabbri's Code)
http://blender.stackexchange.com/questions/40650/blender-camera-from-3x4-matrix?rq=1

#Calculating P from a Blender Camera (Dr. Fabbri's Code)
http://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera
http://blender.stackexchange.com/questions/15102/what-is-blenders-camera-projection-matrix-model?rq=1
http://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix

#OTHER References
https://developer.blender.org/diffusion/B/browse/master/release/scripts/modules/bpy_extras/object_utils.py$285
http://blender.stackexchange.com/questions/882/how-to-find-image-coordinates-of-the-rendered-vertex/884#884

#For picking the points in 3D View and Image Editor
See modal_draw_multi_area.py and modal_draw_imgeditor_view3d.py

#understanding camera/projection in general
http://www.cse.psu.edu/~rtc12/CSE486/lecture12.pdf
http://www.cse.psu.edu/~rtc12/CSE486/lecture13.pdf

'''
import bpy
import bgl
import blf
import math

import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d, region_2d_to_origin_3d, region_2d_to_vector_3d
import bpy_extras

#BGL wrappers/utils
def draw_line_3d(color, start, end, width=1):
    bgl.glLineWidth(width)
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex3f(*start)
    bgl.glVertex3f(*end)

def draw_points_3d(points, color, size, far=0.997):
    bgl.glColor4f(*color)
    bgl.glPointSize(size)
    bgl.glDepthRange(0.0, far)
    bgl.glBegin(bgl.GL_POINTS)
    for coord in points: bgl.glVertex3f(*coord)
    bgl.glEnd()
    bgl.glPointSize(1.0)
    
def draw_typo_2d(color, text):
    font_id = 0  # XXX, need to find out how best to get this.
    # draw some text
    bgl.glColor4f(*color)
    blf.position(font_id, 20, 70, 0)
    blf.size(font_id, 20, 72)
    blf.draw(font_id, text)

#### MATRIX CAMER MATH HELPERS
# Input: P 3x4 numpy matrix
# Output: K, R, T such that P = K*[R | T], det(R) positive and K has positive diagonal
#
# Reference implementations: 
#   - Oxford's visual geometry group matlab toolbox 
#   - Scilab Image Processing toolbox
def KRT_from_P(P):
    N = 3
    H = P[:,0:N]  # if not numpy,  H = P.to_3x3()

    [K,R] = rf_rq(H)

    K /= K[-1,-1]

    # from http://ksimek.github.io/2012/08/14/decompose/
    # make the diagonal of K positive
    sg = np.diag(np.sign(np.diag(K)))

    K = K * sg
    R = sg * R
    # det(R) negative, just invert; the proj equation remains same:
    if (np.linalg.det(R) < 0):
        R = -R
    # C = -H\P[:,-1]
    C = np.linalg.lstsq(-H, P[:,-1])[0]
    T = -R*C
    return K, R, T

# RQ decomposition of a numpy matrix, using only libs that already come with
# blender by default
#
# Author: Ricardo Fabbri
# Reference implementations: 
#   Oxford's visual geometry group matlab toolbox 
#   Scilab Image Processing toolbox
#
# Input: 3x4 numpy matrix P
# Returns: numpy matrices r,q
def rf_rq(P):
    P = P.T
    # numpy only provides qr. Scipy has rq but doesn't ship with blender
    q, r = np.linalg.qr(P[ ::-1, ::-1], 'complete')
    q = q.T
    q = q[ ::-1, ::-1]
    r = r.T
    r = r[ ::-1, ::-1]

    if (np.linalg.det(q) < 0):
        r[:,0] *= -1
        q[0,:] *= -1
    return r, q

# Creates a blender camera consistent with a given 3x4 computer vision P matrix
# Run this in Object Mode
# scale: resolution scale percentage as in GUI, known a priori
# P: numpy 3x4
def get_blender_camera_from_3x4_P(P, scale):
    # get krt
    K, R_world2cv, T_world2cv = KRT_from_P(np.matrix(P))

    scene = bpy.context.scene
    sensor_width_in_mm = K[1,1]*K[0,2] / (K[0,0]*K[1,2])
    sensor_height_in_mm = 1  # doesn't matter
    resolution_x_in_px = K[0,2]*2  # principal point assumed at the center
    resolution_y_in_px = K[1,2]*2  # principal point assumed at the center

    s_u = resolution_x_in_px / sensor_width_in_mm
    s_v = resolution_y_in_px / sensor_height_in_mm
    # TODO include aspect ratio
    f_in_mm = K[0,0] / s_u
    # recover original resolution
    scene.render.resolution_x = resolution_x_in_px / scale
    scene.render.resolution_y = resolution_y_in_px / scale
    scene.render.resolution_percentage = scale * 100

    # Use this if the projection matrix follows the convention listed in my answer to
    # http://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    # Use this if the projection matrix follows the convention from e.g. the matlab calibration toolbox:
    # R_bcam2cv = Matrix(
    #     ((-1, 0,  0),
    #      (0, 1, 0),
    #      (0, 0, 1)))

    R_cv2world = R_world2cv.T
    rotation =  Matrix(R_cv2world.tolist()) * R_bcam2cv
    location = -R_cv2world * T_world2cv

    # create a new camera
    bpy.ops.object.add(
        type='CAMERA',
        location=location)
    ob = bpy.context.object
    ob.name = 'CamFrom3x4PObj'
    cam = ob.data
    cam.name = 'CamFrom3x4P'

    # Lens
    cam.type = 'PERSP'
    cam.lens = f_in_mm 
    cam.lens_unit = 'MILLIMETERS'
    cam.sensor_width  = sensor_width_in_mm
    ob.matrix_world = Matrix.Translation(location)*rotation.to_4x4()

    #     cam.shift_x = -0.05
    #     cam.shift_y = 0.1
    #     cam.clip_start = 10.0
    #     cam.clip_end = 250.0
    #     empty = bpy.data.objects.new('DofEmpty', None)
    #     empty.location = origin+Vector((0,10,0))
    #     cam.dof_object = empty

    # Display
    cam.show_name = True
    # Make this the current camera
    scene.camera = ob
    bpy.context.scene.update()

def test2():
    P = Matrix([
    [2. ,  0. , - 10. ,   282.  ],
    [0. ,- 3. , - 14. ,   417.  ],
    [0. ,  0. , - 1.  , - 18.   ]
    ])
    # This test P was constructed as k*[r | t] where
    #     k = [2 0 10; 0 3 14; 0 0 1]
    #     r = [1 0 0; 0 -1 0; 0 0 -1]
    #     t = [231 223 -18]
    # k, r, t = KRT_from_P(numpy.matrix(P))
    get_blender_camera_from_3x4_P(P, 1)
        


#---------------------------------------------------------------
# 3x4 P matrix from Blender camera
#---------------------------------------------------------------

# Build intrinsic camera parameters from Blender camera data
#
# See notes on this in 
# blender.stackexchange.com/questions/15102/what-is-blenders-camera-projection-matrix-model
def get_calibration_matrix_K_from_blender(camd):
    f_in_mm = camd.lens
    scene = bpy.context.scene
    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y
    scale = scene.render.resolution_percentage / 100
    sensor_width_in_mm = camd.sensor_width
    sensor_height_in_mm = camd.sensor_height
    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    if (camd.sensor_fit == 'VERTICAL'):
        # the sensor height is fixed (sensor fit is horizontal), 
        # the sensor width is effectively changed with the pixel aspect ratio
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio 
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else: # 'HORIZONTAL' and 'AUTO'
        # the sensor width is fixed (sensor fit is horizontal), 
        # the sensor height is effectively changed with the pixel aspect ratio
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm


    # Parameters of intrinsic calibration matrix K
    alpha_u = f_in_mm * s_u
    alpha_v = f_in_mm * s_v
    u_0 = resolution_x_in_px * scale / 2
    v_0 = resolution_y_in_px * scale / 2
    skew = 0 # only use rectangular pixels

    K = Matrix(
        ((alpha_u, skew,    u_0),
        (    0  , alpha_v, v_0),
        (    0  , 0,        1 )))
    return K

# Returns camera rotation and translation matrices from Blender.
# 
# There are 3 coordinate systems involved:
#    1. The World coordinates: "world"
#       - right-handed
#    2. The Blender camera coordinates: "bcam"
#       - x is horizontal
#       - y is up
#       - right-handed: negative z look-at direction

#    3. The desired computer vision camera coordinates: "cv"
#       - x is horizontal
#       - y is down (to align to the actual pixel coordinates 
#         used in digital images)
#       - right-handed: positive z look-at direction
def get_3x4_RT_matrix_from_blender(cam):
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    # Transpose since the rotation is object rotation, 
    # and we want coordinate rotation
    # R_world2bcam = cam.rotation_euler.to_matrix().transposed()
    # T_world2bcam = -1*R_world2bcam * location
    #
    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam*cam.location
    # Use location from matrix_world to account for constraints:     
    T_world2bcam = -1*R_world2bcam * location

    # Build the coordinate transform matrix from world to computer vision camera
    R_world2cv = R_bcam2cv*R_world2bcam
    T_world2cv = R_bcam2cv*T_world2bcam

    # put into 3x4 matrix
    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
         ))
    return RT

def get_3x4_P_matrix_from_blender(cam):
    K = get_calibration_matrix_K_from_blender(cam.data)
    RT = get_3x4_RT_matrix_from_blender(cam)
    return K*RT, K, RT

# ----------------------------------------------------------
# Alternate 3D coordinates to 2D pixel coordinate projection code
# adapted from http://blender.stackexchange.com/questions/882/how-to-find-image-coordinates-of-the-rendered-vertex?lq=1
# to have the y axes pointing up and origin at the top-left corner
def project_by_object_utils(cam, point):
    scene = bpy.context.scene
    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, cam, point)
    render_scale = scene.render.resolution_percentage / 100
    render_size = (
            int(scene.render.resolution_x * render_scale),
            int(scene.render.resolution_y * render_scale),
            )
    return Vector((co_2d.x * render_size[0], render_size[1] - co_2d.y * render_size[1]))

# ----------------------------------------------------------
#if __name__ == "__main__":
    # Insert your camera name here
#    cam = bpy.data.objects['Camera.001']
#    P, K, RT = get_3x4_P_matrix_from_blender(cam)
#    print("K")
#    print(K)
#    print("RT")
#    print(RT)
#    print("P")
#    print(P)

#    print("==== Tests ====")
#    e1 = Vector((1, 0,    0, 1))
#    e2 = Vector((0, 1,    0, 1))
#    e3 = Vector((0, 0,    1, 1))
#    O  = Vector((0, 0,    0, 1))

#    p1 = P * e1
#    p1 /= p1[2]
#    print("Projected e1")
#    print(p1)
#    print("proj by object_utils")
#    print(project_by_object_utils(cam, Vector(e1[0:3])))

#    p2 = P * e2
#    p2 /= p2[2]
#    print("Projected e2")
#    print(p2)
#    print("proj by object_utils")
#    print(project_by_object_utils(cam, Vector(e2[0:3])))

#    p3 = P * e3
#    p3 /= p3[2]
#    print("Projected e3")
#    print(p3)
#    print("proj by object_utils")
#    print(project_by_object_utils(cam, Vector(e3[0:3])))

#    pO = P * O
#    pO /= pO[2]
#    print("Projected world origin")
#    print(pO)
#    print("proj by object_utils")
#    print(project_by_object_utils(cam, Vector(O[0:3])))

    # Bonus code: save the 3x4 P matrix into a plain text file
    # Don't forget to import numpy for this
#    nP = numpy.matrix(P)
#    numpy.savetxt("/tmp/P3x4.txt", nP)  # to select precision, use e.g. fmt='%.2f'


        
##CALLBACKS TO BE ADDED TO EACH SPACE TYPE ##
def view3d_draw_callback_3d(self, context):
    #do 3d and geometry drawing here
    bgl.glEnable(bgl.GL_BLEND)

    if len(self.points_3d):
        draw_points_3d(self.points_3d, (1,1,0,1), 10, far = 0.9)

    #TODO maybe draw some integers with points
    bgl.glEnd()
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

def view3d_draw_callback_2d(self, context):
    #do text and pixel drawing here
    bgl.glEnable(bgl.GL_BLEND)

    # draw text
    draw_typo_2d((1.0, 1.0, 1.0, 1), "3D View Window")

    bgl.glEnd()
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


def img_editor_draw_callback_px(self, context):

    # draw text
    draw_typo_2d((1.0, 1.0, 1.0, 1), "Image Editor Window")
    
    #draw the user clicked points on the image
    bgl.glPointSize(5)
    bgl.glBegin(bgl.GL_POINTS)
    bgl.glColor4f(0.8, 0.2, 0.5, 1.0)
    for pix in self.pixel_coords:
        img_x, img_y = pix[0], pix[1]
        img_size = self.imgeditor_area.spaces.active.image.size
        rx,ry = context.region.view2d.view_to_region(img_x/img_size[0], (img_size[1] - img_y)/img_size[1], clip=True)
        
        if rx and ry:
            bgl.glVertex2f(rx, ry)
        
    bgl.glEnd()
    
    # restore opengl defaults
    bgl.glPointSize(1)
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

    font_id = 0
    for pix in self.pixel_coords:
        img_x, img_y = pix[0], pix[1]
        img_size = self.imgeditor_area.spaces.active.image.size
        
        rx,ry = context.region.view2d.view_to_region(img_x/img_size[0], (img_size[1] - img_y)/img_size[1], clip=True)
        
        blf.position(font_id, rx+5, ry+5, 0)
        text = str((round(pix[0]),round(pix[1])))
        
        blf.draw(font_id, text)
        
        blf.position(font_id, rx+5, ry+20, 0)
        text = str((round(pix[0]),round(pix[1])))
        
def tag_redraw_view3d_imgeditor(context):
    # Py cant access notifers
    #iterate through and tag all 'VIEW_3D' regions
    #for drawing
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D' or area.type == 'IMAGE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region.tag_redraw()
                        
class VIEW3D_OT_image_view3d_modal(bpy.types.Operator):
    """Click on Image and On Object"""
    bl_idname = "view3d.img_obj_register"
    bl_label = "Register Image to Object"

    @classmethod
    def poll(cls, context):
        #TODO, some nice poling
        return True

    def modal(self, context, event):
        
        tag_redraw_view3d_imgeditor(context)
        FSM = {}
        FSM['nav']  = self.modal_nav
        FSM['wait'] = self.modal_wait
        
        nmode = FSM[self.mode](context, event)
        
        if nmode == 'nav': 
            return {'PASS_THROUGH'}
        
        if nmode in {'finish','cancel'}:
            #clean up callbacks
            bpy.types.SpaceView3D.draw_handler_remove(self._handle2d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle3d, 'WINDOW')
            bpy.types.SpaceImageEditor.draw_handler_remove(self._handle_image, 'WINDOW')
            
            return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}
        
        if nmode: self.mode = nmode
        
        return {'RUNNING_MODAL'}   
        
    def modal_nav(self, context, event):
        '''
        Determine/handle navigation events.
        FSM passes control through to underlying panel if we're in 'nav' state
        '''
 
        handle_nav = False
        handle_nav |= event.type in {'WHEELUPMOUSE','WHEELDOWNMOUSE','MIDDLEMOUSE'}
        
        if handle_nav:
            self.post_update   = True
            self.is_navigating = True
            return 'wait' if event.value =='RELEASE' else 'nav'

        self.is_navigating = False
        return ''
       
    def modal_wait(self, context, event):
        
        # general navigation
        nmode = self.modal_nav(context, event)
        if nmode != '':
            return nmode  #stop here and tell parent modal to 'PASS_THROUGH'
        
        #TODO, tag redraw current if only needing to redraw that single window
        #depends on what information you are changing
        
        if event.type == 'MOUSEMOVE':
            
            #get the appropriate region and region_3d for ray_casting
            #also, important because this is what your blf and bgl
            #wrappers are going to draw in at that moment
            
            if (event.mouse_x > self.view3d_area.x and event.mouse_x < self.view3d_area.x + self.view3d_area.width) and \
                (event.mouse_y > self.view3d_area.y and event.mouse_y < self.view3d_area.y + self.view3d_area.height):
            
                for reg in self.view3d_area.regions:
                    if reg.type == 'WINDOW':
                        region = reg
                for spc in self.view3d_area.spaces:
                    if spc.type == 'VIEW_3D':
                        rv3d = spc.region_3d
            
                #just transform the mouse window coords into the region coords        
                coord_region = (event.mouse_x - region.x, event.mouse_y - region.y)
                
    
                self.mouse_region_coord = coord_region
                self.mouse_raw = (event.mouse_x, event.mouse_y)
            
            elif (event.mouse_x > self.imgeditor_area.x and event.mouse_x < self.imgeditor_area.x + self.imgeditor_area.width) and \
                (event.mouse_y > self.imgeditor_area.y and event.mouse_y < self.imgeditor_area.y + self.imgeditor_area.height):
            
                for reg in self.imgeditor_area.regions:
                    if reg.type == 'WINDOW':
                        region = reg
                #for spc in self.imgeditor_area.spaces:
                
                #just transform the mouse window coords into the region coords        
                coord_region = (event.mouse_x - region.x, event.mouse_y - region.y)
                self.mouse_region_coord = coord_region
                self.mouse_raw = (event.mouse_x, event.mouse_y)
                        
            return 'wait'
        
        if event.type == 'M' and event.value == 'PRESS':
            self.build_matrix()
            
            return 'wait'
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            
            #get the appropriate region and region_3d for ray_casting
            if (event.mouse_x > self.view3d_area.x and event.mouse_x < self.view3d_area.x + self.view3d_area.width) and \
                (event.mouse_y > self.view3d_area.y and event.mouse_y < self.view3d_area.y + self.view3d_area.height):
            
                for reg in self.view3d_area.regions:
                    if reg.type == 'WINDOW':
                        region = reg
                for spc in self.view3d_area.spaces:
                    if spc.type == 'VIEW_3D':
                        rv3d = spc.region_3d
            
                #just transform the mouse window coords into the region coords        
                coord_region = (event.mouse_x - self.view3d_region.x, event.mouse_y - self.view3d_region.y)
                self.mouse_region_coord = coord_region
                self.mouse_raw = (event.mouse_x, event.mouse_y)
                
                #this is the important part, using the correct region and rv3d
                #to get the ray.
                view_vector = region_2d_to_vector_3d(region, rv3d, coord_region)
                ray_origin = region_2d_to_origin_3d(region, rv3d, coord_region)
                ray_target = ray_origin + (view_vector * 10000)

                res, loc, no, ind, obj, mx = context.scene.ray_cast(ray_origin, view_vector)
                if res:
                    self.points_3d += [loc]
                    cam = bpy.data.objects.get('Test Camera')
                    if cam:
                        pix_click = project_by_object_utils(cam, loc)
                        print(round(pix_click[0]), round(pix_click[1]))
                    
                else:
                    print('DID NOT CLICK OBJECT')
                    
            elif (event.mouse_x > self.imgeditor_area.x and event.mouse_x < self.imgeditor_area.x + self.imgeditor_area.width) and \
                (event.mouse_y > self.imgeditor_area.y and event.mouse_y < self.imgeditor_area.y + self.imgeditor_area.height):
            
                coord_region = (event.mouse_x - self.imgeditor_region.x, event.mouse_y - self.imgeditor_region.y)
                reg_x, reg_y = event.mouse_region_x, event.mouse_region_y
                img_size = self.imgeditor_area.spaces.active.image.size

                uv_x, uv_y = self.imgeditor_region.view2d.region_to_view(coord_region[0], coord_region[1])
                #print('The Region Coordinates')
                #print((coord_region[0], coord_region[1]))
                
                #print('The Image Size')
                #print((img_size[0],img_size[1]))
                
                if uv_x < 0 or uv_x > 1:
                    print('off image')
                    return 'wait'
                if uv_y < 0 or uv_y > 1:
                    print('off image')
                    return 'wait'
                
                #print('The UV Coordinates')
                #print(uv_x, uv_y)...origin at BOTTOM left corner
                
                #pixel coords origin at TOP left corner
                img_x, img_y = uv_x * img_size[0], img_size[1] - uv_y * img_size[1]
                
                #print('The Pixel Coordinates') #perhaps we need to make these reference top left corner! yes
                #print(img_x, img_y)
                
                self.pixel_coords += [Vector((img_x, img_y))]
                print(round(img_x), round(img_y))
                #back the coords out ot region space, compare to reg_x, reg_y
                rx,ry = self.imgeditor_region.view2d.view_to_region(uv_x, uv_y, clip=False)

                #just transform the mouse window coords into the region coords        
                self.mouse_region_coord = coord_region
                self.mouse_raw = (event.mouse_x, event.mouse_y)
                
                               
            return 'wait'
        
        elif event.type == 'ESC':
            return 'cancel'
        
        return 'wait'
    
    def build_matrix(self):
        
        #make sure we have enough points
        if len(self.pixel_coords) < 6:
            print('not enough image points')
            return
        elif len(self.points_3d) < 6:
            print('not enough 3d points')
            return
        
        
        
        #make corresponding lists, assumes the user selected in same order
        #at a minimum, ensure lists are same size
        L = min(len(self.points_3d),len(self.pixel_coords))
        pts_3d = self.points_3d[0:L]
        pts_2d = self.pixel_coords[0:L]
        
        #calculate origin center.  TODO, use numpy instead of dumb for loops
        orig_3d = Vector((0,0,0))
        orig_2d = Vector((0,0))
        
        for v in pts_3d:
            orig_3d += 1/L * v
            
        for px in pts_2d:
            orig_2d += 1/L * px
            
        #move the data to the center
        #pts_3d = [v - orig_3d for v in pts_3d]
        #pts_2d = [v - orig_2d for v in pts_2d]
        
        #scale so that mean distance to center is sqrt(3) and sqrt(2)
        RMS_2d = (sum([v.length**2 for v in pts_2d]))**.5
        RMS_3d = (sum([v.length**2 for v in pts_3d]))**.5
        
        #pts_3d = [3**.5/RMS_3d * v for v in pts_3d]
        #pts_2d = [2**.5/RMS_2d * v for v in pts_2d]
        
        print('The RMS Factors')
        print((3**.5/RMS_3d, 2**.5/RMS_2d))
        #Now, check that the centroid and the RMS values are correclty scaled for sanity
        #Check the centroid
        #orig_3d_check = Vector((0,0,0))
        #orig_2d_check = Vector((0,0))
        
        #for v in pts_3d:
        #    orig_3d_check += v
            
        #for px in pts_2d:
        #    orig_2d_check += px
            
        #orig_3d_check *= 1/L
        #orig_2d_check *= 1/L
        #print('CHECK THE CENTROID TRANSLATION WAS CORRECT')
        #print(orig_3d_check, orig_2d_check)
        
        #Check the RMS
        #RMS_2d_check = (sum([v.length**2 for v in pts_2d]))**.5
        #RMS_3d_check = (sum([v.length**2 for v in pts_3d]))**.5
        
        #print('CHECK THE RMS SCALING WAS CORRECT')
        #print((RMS_2d_check, 2**.5))
        #print((RMS_3d_check, 3**.5))
        
        mx_rows = []
        for i in range(0,L):
            X,Y,Z,W = pts_3d[i].to_4d()
            x,y,w = pts_2d[i].to_3d()
            
            r0 = np.array([0,0,0,0,-X*w, -Y*w, -Z*w, -W*w, X*y, Y*y, Z*y,W*y])
            r1 = np.array([X*w, Y*w, Z*w, W*w, 0, 0, 0, 0, -X*x, -Y*x, -Z*x, -W*x])
            
            mx_rows.append(r0)
            mx_rows.append(r1)
        
        #will try mx_rows.reverse() next
        A = np.vstack(mx_rows)
        
        #print(mx_rows[0])
        #print(A[:][0])
        
        u, s, vh = np.linalg.svd(A, full_matrices = False)
        
        #print(u.shape, vh.shape, s.shape)
        
        '''
        New in version 1.8.0.

        The SVD is commonly written as a = U S V.H. The v returned by this function is V.H and u = U.
        If U is a unitary matrix, it means that it satisfies U.H = inv(U).
        The rows of v are the eigenvectors of a.H a. The columns of u are the eigenvectors of a a.H.
        For row i in v and column i in u, the corresponding eigenvalue is s[i]**2.
        If a is a matrix object (as opposed to an ndarray), then so are all the return values
        '''
        
        #rows of v are the eigen vectors....! (I reckon)
        
        best_s = min(s)
        #print('the minimum value of s is %f' % best_s)
        n = np.nonzero(s==best_s)[0][0]
        print('EIGENVALUES')
        print(s)
        
        print('SOLUTION FOR P from vh')
        P_vector_v = vh[n,:]
        print(P_vector_v)
        
        P_v_list = [P_vector_v[0:4],
                    P_vector_v[4:8], 
                    P_vector_v[8:12]]
        P_v = Matrix(P_v_list)
        
        
        print('SOLUTION FOR P from U')
        P_vector_u = u[:,n]
        print(P_vector_u)
        
        #P_u_list = [P_vector_u[0:3],
        #            P_vector_u[3:6], 
        #            P_vector_u[6:9],
        #           P_vector_u[9:12]]
        P_u_list = [P_vector_u[0:4],
                    P_vector_u[4:8], 
                    P_vector_u[8:12]]
        P_u = Matrix(P_u_list)
        
        print('Calculated from SVD Eigenvector')
        print(P_u)
        cam = bpy.data.objects.get('Test Camera')
        if cam:    
            P, K, RT = get_3x4_P_matrix_from_blender(cam)
            print('Calculated from Test Camera')
            print(P)
            
    
        get_blender_camera_from_3x4_P(P_u, 1) 
        #get_blender_camera_from_3x4_P(P_v, 1) 
        
        
        
    def invoke(self, context, event):
       
        #collect all the 3d_view regions
        #this can be done with other types
        
        self.mode = 'wait'
        
        self.view3d_area = None
        self.view3d_region = None
        self.points_3d = []
        
        self.imgeditor_area = None
        self.imgeditor_region = None
        self.pixel_coords = []
        
        #TODO, check that only one of each area is open
        #TODO, manufacture one or 2 areas?
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    self.view3d_area = area
                    for region in area.regions:
                        if region.type == 'WINDOW': #ignore the tool-bar, header etc
                            self.view3d_region = region
                            
                elif area.type == 'IMAGE_EDITOR':
                    self.imgeditor_area = area
                    for region in area.regions:
                        if region.type == 'WINDOW': #ignore the tool-bar, header etc
                            self.imgeditor_region = region
        
        if self.view3d_area == None:
            #error message
            return {'CANCELLED'}
    
        if self.imgeditor_area == None:
            
            return {'CANCELLED'}
        
        self.mouse_screen_coord = (0,0)
        context.window_manager.modal_handler_add(self)
        
        #the different drawing handles
        self._handle2d = bpy.types.SpaceView3D.draw_handler_add(view3d_draw_callback_2d, (self, context), 'WINDOW', 'POST_PIXEL')
        self._handle3d = bpy.types.SpaceView3D.draw_handler_add(view3d_draw_callback_3d, (self, context), 'WINDOW', 'POST_VIEW')
        self._handle_image = bpy.types.SpaceImageEditor.draw_handler_add(img_editor_draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')

        return {'RUNNING_MODAL'}
    
def register():
    bpy.utils.register_class(VIEW3D_OT_image_view3d_modal)

def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_image_view3d_modal)

if __name__ == "__main__":
    register()