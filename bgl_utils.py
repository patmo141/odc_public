#----------------------------------------------------------
# File bgl_utils.py
#----------------------------------------------------------
'''
Created on Nov 20, 2012

@author: Patrick
'''
import bpy
import bgl
import blf
import math
import time
import os
from odcutils import get_settings
from odcmenus import menu_utils
from odcmenus import button_data
from bpy_extras import view3d_utils 


from math import fmod
from mathutils.geometry import intersect_line_line_2d
from mathutils import Vector, Matrix
from bpy_extras.image_utils import load_image

def draw_polyline_from_coordinates(context, points, width, LINE_TYPE = 'GL_LINE_STRIP', color = (1,1,1,1)):  
    region = context.region  
    rv3d = context.space_data.region_3d  
  
    bgl.glColor4f(*color)  
    bgl.glLineWidth(width)
    if LINE_TYPE == "GL_LINE_STIPPLE":  
        bgl.glLineStipple(4, 0x5555)  
        bgl.glEnable(bgl.GL_LINE_STIPPLE)    
        
    
    bgl.glBegin(bgl.GL_LINE_STRIP) 
    for coord in points:  
        vector3d = (coord.x, coord.y, coord.z)  
        vector2d = view3d_utils.location_3d_to_region_2d(region, rv3d, vector3d)  
        bgl.glVertex2f(*vector2d)  
    bgl.glEnd()  
    bgl.glLineWidth(1) 

      
    return

def draw_polyline_2d_loop(context, points, scale, offset, color, LINE_TYPE):
    '''
    '''
    bgl.glColor4f(*color)  #black or white?

    if LINE_TYPE == "GL_LINE_STIPPLE":
        bgl.glLineStipple(4, 0x5555)
        bgl.glEnable(bgl.GL_LINE_STIPPLE)
        bgl.glColor4f(0.3, 0.3, 0.3, 1.0) #boring grey
    
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for coord in points:
        bgl.glVertex2f(scale*coord[0]+offset[0], scale*coord[1] + offset[1])
    bgl.glVertex2f(scale*points[0][0]+offset[0], scale*points[0][1] + offset[1])
    bgl.glEnd()
    
    if LINE_TYPE == "GL_LINE_STIPPLE":
        bgl.glDisable(bgl.GL_LINE_STIPPLE)
        bgl.glEnable(bgl.GL_BLEND)  # back to uninterupted lines    
    return

def outside_loop(loop, scale, offset):    
    xs = [scale*v[0] + offset[0] for v in loop]
    ys = [scale*v[1] + offset[1]  for v in loop]
    
    maxx = max(xs)
    maxy = max(ys)
    
    bound = (1.1*maxx, 1.1*maxy)
    return bound

def point_inside_loop(loop, point, scale, offset):
        
    nverts = len(loop)
    
    #vectorize our two item tuple
    out = Vector(outside_loop(loop, scale, offset))
    pt = Vector(point)
    
    intersections = 0
    for i in range(0,nverts):
        a = scale*Vector(loop[i-1]) + Vector(offset)
        b = scale*Vector(loop[i]) + Vector(offset)
        if intersect_line_line_2d(pt,out,a,b):
            intersections += 1
    
    inside = False
    if fmod(intersections,2):
        inside = True
    
    return inside

def insertion_axis_callback(self,context):
    aspect, mid = menu_utils.view3d_get_size_and_mid(context)
    
    #place 50 pixel arrow at right edge
    path1 = menu_utils.transform_points(button_data.arrow_right, aspect[0]-20,mid[1],50,100,0)
    path2 = menu_utils.transform_points(button_data.arrow_left, 20,mid[1],50,100,0)
    
    bgl.glColor4f(*(1,1,1,1))
    menu_utils.draw_outline_or_region(bgl.GL_LINE_LOOP, path1)
    menu_utils.draw_outline_or_region(bgl.GL_LINE_LOOP, path2)
    
    #put words in the arrows
    blf.size(0,20,76)
    dimension = blf.dimensions(0,"Mesial")
    blf.position(0,aspect[0]-70-dimension[0]/2,mid[1]-dimension[1]/2,0)
    blf.draw(0,"Mesial")
    
    dimension = blf.dimensions(0,"Distal")
    blf.position(0,70-dimension[0]/2,mid[1]-dimension[1]/2,0)
    blf.draw(0,"Distal")


def general_func_callback(self,context):
    aspect, mid = menu_utils.view3d_get_size_and_mid(context)
        # draw some text
    blf.position(0, mid[0], mid[1]+100, 0)
    blf.size(0, 20, 72)
    blf.draw(0, self.message)
    menu_utils.blf_text_wrap(self.help, self.wrap, 0, 12 , 76, 10, aspect[1]-30)
    

def draw_callback_tooth_select(self, context):
    
    #draw all the buttons
    color = (1.0,1.0,1.0,1.0)
    for i in range(0,len(button_data.tooth_button_data)): #each of those is a loop        
        button = button_data.tooth_button_data[i]
        
        #check if it's in the rest_type, draw it green.
        #print(len(self.rest_lists))
        
        #draw it yellowish if it's in another type of restoration
        for j in range(0,len(self.rest_lists)):
            if button_data.tooth_button_names[i] in self.rest_lists[j]:
                color = (1.0,1.0,0.5,1.0)
                
        
        #draw it green if it's in the current type of restoration and selected
        if button_data.tooth_button_names[i] in self.rest_lists[self.rest_index]:
            color = (0.1,1.0,0.1,0.5)
        
        #draw it red if the button is hovered
        if self.tooth_button_hover[i]:
            color = (1.0,0.1,0.1,0.5)
        
        draw_polyline_2d_loop(context, button, self.menu_width, self.menu_loc, color,"GL_BLEND")
        color = (1.0,1.0,1.0,1.0)
        
    color = (1.0,1.0,1.0,1.0)
    
    for n in range(0,len(button_data.rest_button_data)): #each of those is a loop        
        button = button_data.rest_button_data[n]
        
        #draw it red if the button is selected or hovered
        if self.rest_button_select[n]:
            color = (0.1,1.0,0.1,0.5)
        
        draw_polyline_2d_loop(context, button, self.menu_width*.5, self.rest_menu_loc , color,"GL_BLEND")
        color = (1.0,1.0,1.0,1.0)    

#borrowed from edge filet from Zeffi (included with blend)  
def draw_3d_points(context, points, size, color = (1,0,0,1)):  
    region = context.region  
    rv3d = context.space_data.region_3d  
      
      
    bgl.glEnable(bgl.GL_POINT_SMOOTH)  
    bgl.glPointSize(size)  
    # bgl.glEnable(bgl.GL_BLEND)  
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)  
      
    bgl.glBegin(bgl.GL_POINTS)  
    # draw red  
    bgl.glColor4f(*color)      
    for coord in points:  
        vector3d = (coord.x, coord.y, coord.z)  
        vector2d = view3d_utils.location_3d_to_region_2d(region, rv3d, vector3d)  
        bgl.glVertex2f(*vector2d)  
    bgl.glEnd()  
      
    bgl.glDisable(bgl.GL_POINT_SMOOTH)  
    bgl.glDisable(bgl.GL_POINTS)  
    return

def draw_callback_crevice_walking(self,context):
    
    #draw put a big ole target over the mouse or something
    draw_3d_points(context, [self.current_bias_point], 4)
    
    #draw the user control points
    draw_3d_points(context, self.bias_points, 4)
    
    #draw the existing/confirmed walked points
    draw_3d_points(context, self.pending_path, 4)
    
    #draw the unconfirmed iterative points
    
    
if __name__ == "__main__":
    print('do something here?')
'''
def register():  
    print('register utils')
def unregister():     
    print('unregister utils')
if __name__ == "__main__":
    register()
'''  