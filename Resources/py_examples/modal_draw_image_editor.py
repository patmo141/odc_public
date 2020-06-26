'''
Created on Oct 16, 2016

@author: Patrick


This demo will allow navigation in the 3dview and in the image editor
It will also allow ray casting into the 3dview
It will allow clicked points in the Image editor
skeleton for 2d image registration using picked points to a 3d model.

#draw in different space types
http://blender.stackexchange.com/questions/57709/how-to-draw-shapes-in-the-node-editor-with-python-bgl

#post pixel and post_view drawing in the 3d View
http://blender.stackexchange.com/questions/61699/how-to-draw-geometry-in-3d-view-window-with-bgl

http://blender.stackexchange.com/users/3710/poor

Image pixel coordinates
http://blender.stackexchange.com/questions/53780/pixel-coordinates-of-image-with-python?rq=1

do some intense math
http://blender.stackexchange.com/questions/46208/points-only-camera-calibration/65152#65152
'''
import bpy
import bgl
import blf
import math
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d, region_2d_to_origin_3d, region_2d_to_vector_3d

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

##CALLBACKS TO BE ADDED TO EACH SPACE TYPE ##
def view3d_draw_callback_3d(self, context):
    #do 3d and geometry drawing here
    bgl.glEnable(bgl.GL_BLEND)

    if len(self.points_3d):
        draw_points_3d(self.points_3d, (1,1,0,1), 5, far = 0.9)

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
    for img_x, img_y in self.pixel_coords:
        img_size = self.imgeditor_area.spaces.active.image.size
        rx,ry = context.region.view2d.view_to_region(img_x/img_size[0], img_y/img_size[1], clip=True)
        
        if rx and ry:
            bgl.glVertex2f(rx, ry)
        
    bgl.glEnd()
    
    # restore opengl defaults
    bgl.glPointSize(1)
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


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
                    print('Clicked on ' + obj.name)
                    
                self.points_3d += [loc]
                
            elif (event.mouse_x > self.imgeditor_area.x and event.mouse_x < self.imgeditor_area.x + self.imgeditor_area.width) and \
                (event.mouse_y > self.imgeditor_area.y and event.mouse_y < self.imgeditor_area.y + self.imgeditor_area.height):
            
                coord_region = (event.mouse_x - self.imgeditor_region.x, event.mouse_y - self.imgeditor_region.y)
                reg_x, reg_y = event.mouse_region_x, event.mouse_region_y
                img_size = self.imgeditor_area.spaces.active.image.size
                
                
                uv_x, uv_y = self.imgeditor_region.view2d.region_to_view(coord_region[0], coord_region[1])
                print('The Region Coordinates')
                print((coord_region[0], coord_region[1]))
                
                print('The Image Size')
                print((img_size[0],img_size[1]))
                
                print('The UV Coordinates')
                print(uv_x, uv_y)
                img_x, img_y = uv_x * img_size[0], uv_y * img_size[1]
                
                print('The Pixel Coordinates')
                print(img_x, img_y)
                
                self.img_points += [coord_region]
                self.pixel_coords += [(img_x, img_y)]
                
                rx,ry = self.imgeditor_region.view2d.view_to_region(uv_x, uv_y, clip=False)
                print('back the coords out to the region space?')
                print((rx,ry))
                
                
                #just transform the mouse window coords into the region coords        
                self.mouse_region_coord = coord_region
                self.mouse_raw = (event.mouse_x, event.mouse_y)
                
                               
            return 'wait'
        
        elif event.type == 'ESC':
            return 'cancel'
        
        return 'wait'
    
    def invoke(self, context, event):
       
        #collect all the 3d_view regions
        #this can be done with other types
        
        self.mode = 'wait'
        
        self.view3d_area = None
        self.view3d_region = None
        self.points_3d = []
        
        self.imgeditor_area = None
        self.imgeditor_region = None
        self.img_points = []
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