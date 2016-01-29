'''
Created on May 12, 2015

@author: Patrick
'''
# Add the current __file__ path to the search path
import sys, os

import math
import copy
import time
import bpy, bmesh, blf, bgl
from bpy.props import EnumProperty, StringProperty,BoolProperty, IntProperty, FloatVectorProperty, FloatProperty
from bpy.types import Operator, AddonPreferences
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d, region_2d_to_location_3d
from mathutils import Vector
from mathutils.geometry import intersect_line_plane, intersect_point_line

import common_utilities
import common_drawing

class TextBox(object):
    
    def __init__(self,context,x,y,width,height,border, margin, message):
        
        self.x = x #middle of text box
        self.y = y #top of text box
        self.def_width = width
        self.def_height = height
        self.hang_indent = '-'
        
        self.width = width
        self.height = height
        self.border = border
        self.margin = margin
        self.spacer = 7  # pixels between text lines
        self.is_collapsed = False
        self.is_hovered = False
        self.collapsed_msg = "Click for Help"

        self.text_size = 12
        self.text_dpi = context.user_preferences.system.dpi
        blf.size(0, self.text_size, self.text_dpi)
        self.line_height = blf.dimensions(0, 'A')[1]
        self.raw_text = message
        self.text_lines = []
        self.format_and_wrap_text()
        
    def hover(self,mouse_x, mouse_y):
        regOverlap = bpy.context.user_preferences.system.use_region_overlap
        if regOverlap == True:
            tPan = self.discover_panel_width_and_location('TOOL_PROPS')
            nPan = self.discover_panel_width_and_location('UI')
            if tPan != 0 and nPan != 0:
                left = (self.x - self.width/2) - (nPan + tPan)
            elif tPan != 0:
                left = (self.x - self.width/2) - tPan
            elif nPan != 0:
                left = (self.x - self.width/2) - nPan
            else:
                left = self.x - self.width/2
        else:
            left = self.x - self.width/2
        right = left + self.width
        bottom = self.y - self.height
        top = self.y
        
        if mouse_x > left and mouse_x < right and mouse_y < top and mouse_y > bottom:
            self.is_hovered = True
            return True
        else:
            self.is_hovered = False
            return False
        
        
    def discover_panel_width_and_location(self, panelType):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for reg in area.regions:
                    if reg.type == panelType:
                        if reg.width > 1:
                            if reg.x == 0:
                                return 0
                            else:
                                return reg.width
                        else:
                            return 0
                        
    def screen_boudaries(self):
        print('to be done later')

    def collapse(self):
        line_height = blf.dimensions(0, 'A')[1]
        self.is_collapsed = True
        self.width = blf.dimensions(0,self.collapsed_msg)[0] + 2 * self.border
        self.height = line_height + 2*self.border
        
    def uncollapse(self):
        self.is_collapsed = False
        self.width = self.def_width
        self.format_and_wrap_text()
        self.fit_box_height_to_text_lines()
        
    def snap_to_corner(self,context,corner = [1,1]):
        '''
        '''
        if not context.region: 
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    for reg in area.regions:
                        print(reg.type)
                        if reg.type == 'VIEW_3D':
                            break
            
        else:
            reg = context.region
            print('cotnext reg type')
            print(reg.type)
            
        if not reg: return
        
        self.x = self.margin + .5*self.width + corner[0]*(reg.width - self.width - 2*self.margin)
        self.y = self.margin + self.height + corner[1]*(reg.height - 2*self.margin - self.height)
             
    
    def fit_box_width_to_text_lines(self):
        '''
        '''
        simple_text_lines = self.raw_text.split('\n')
        max_width = max([blf.dimensions(0,line)[0] for line in simple_text_lines]) 
        
        if max_width > self.width: #this only happnes if text has significantly changed
            self.width = self.def_width  
        if max_width < self.width - 2*self.border:
            self.width = max_width + 2*self.border
            
        
        
        
    def fit_box_height_to_text_lines(self):
        '''
        will make box height match all text lines
        '''
        line_height = blf.dimensions(0, 'A')[1]
        self.height = len(self.text_lines)*(line_height+self.spacer)+2*self.border
        
    def format_and_wrap_text(self):
        '''
        '''
        self.text_lines = []
        #TODO text size settings?
        useful_width = self.def_width - 2 * self.border
        spc_size = blf.dimensions(0,' ')
        spc_width = spc_size[0]
        
        max_width = max([blf.dimensions(0,line)[0] for line in self.raw_text.split('\n')])
        #dim_raw = blf.dimensions(0,self.raw_text)
        if max_width < useful_width:
            self.text_lines = self.raw_text.split('\n')
            return
        
        #clean up line seps, double spaces
        self.raw_text = self.raw_text.replace('\r','')
        #self.raw_text.replace('  ',' ')
        
        def crop_word(word, width):
            '''
            word will be cropped to less than width
            '''
            ltr_indx = 0
            wrd_width = 0
            while ltr_indx < len(word) and wrd_width < width:
                wrd_width += blf.dimensions(0,word[ltr_indx])[0]
                ltr_indx += 1
                
            return word[0:ltr_indx - 1]  #TODO, check indexing for slice op
        
        def wrap_line(txt_line,width):
            '''
            takes a string, returns a list of strings, corresponding to wrapped
            text of the specified pixel width, given current BLF settings
            '''
            if blf.dimensions(0,txt_line)[0] < useful_width:
                #TODO fil
                return [txt_line]
            
            txt = txt_line  #TODO Clean this
            words = txt.split(' ')
            new_lines = []
            current_line = []
            cur_line_len = 0
            for i,wrd in enumerate(words):
                
                word_width = blf.dimensions(0, wrd)[0]
                if word_width >= useful_width and cur_line_len == 0:
                    crp_wrd = crop_word(wrd, useful_width - cur_line_len)
                        
                    if len(current_line):
                        new_lines.append(' '.join(current_line) + ' ' + crp_wrd)
                    else:
                        new_lines.append(crp_wrd)
                    
                    current_line = []
                    cur_line_len = 0
                    continue
                
                elif cur_line_len + word_width < useful_width:
                    current_line.append(wrd)
                    cur_line_len += word_width
                    if i < len(words)-1:
                        cur_line_len += spc_size[0]
                else:
                    new_lines.append(' '.join(current_line))
                    if new_lines[0].startswith(self.hang_indent):
                        current_line = ['  ' + wrd]
                        cur_line_len = word_width + 2 * spc_width
                    else:
                        current_line = [wrd]
                        cur_line_len = word_width
                    if i < len(words)-1: #meaning still words to go
                        cur_line_len += spc_size[0]

                if i == len(words) - 1 and len(current_line):
                    new_lines.append(' '.join(current_line))
                         
            return new_lines          
        
        lines = self.raw_text.split('\n')
        for ln in lines:
            self.text_lines.extend(wrap_line(ln, useful_width))

        self.fit_box_height_to_text_lines()
        if len(self.text_lines) == 1 or len(lines) == len(self.text_lines):
            self.fit_box_width_to_text_lines()
        return
    
    def draw(self):
        regOverlap = bpy.context.user_preferences.system.use_region_overlap
        
        bgcol = bpy.context.user_preferences.themes[0].user_interface.wcol_menu_item.inner
        bgR = bgcol[0]
        bgG = bgcol[1]
        bgB = bgcol[2]
        bgA = .5
        bg_color = (bgR, bgG, bgB, bgA)
        
        txtcol = bpy.context.user_preferences.themes[0].user_interface.wcol_menu_item.text
        txR = txtcol[0]
        txG = txtcol[1]
        txB = txtcol[2]
        txA = .9
        txt_color = (txR, txG, txB, txA)
        
        bordcol = bpy.context.user_preferences.themes[0].user_interface.wcol_menu_item.outline
        hover_color = bpy.context.user_preferences.themes[0].user_interface.wcol_menu_item.inner_sel
        bordR = bordcol[0]
        bordG = bordcol[1]
        bordB = bordcol[2]
        bordA = .8
        if self.is_hovered:
            border_color = (hover_color[0], hover_color[1], hover_color[2], bordA)
        else:
            border_color = (bordR, bordG, bordB, bordA)
        
        if regOverlap == True:
            tPan = self.discover_panel_width_and_location('TOOL_PROPS')
            nPan = self.discover_panel_width_and_location('UI')
            if tPan != 0 and nPan != 0:
                left = (self.x - self.width/2) - (nPan + tPan)
            elif tPan != 0:
                left = (self.x - self.width/2) - tPan
            elif nPan != 0:
                left = (self.x - self.width/2) - nPan
            else:
                left = self.x - self.width/2
        else:
            left = self.x - self.width/2
        right = left + self.width
        bottom = self.y - self.height
        top = self.y
        
        #draw the whole menu bacground
        line_height = blf.dimensions(0, 'A')[1]
        outline = common_drawing.round_box(left, bottom, left +self.width, bottom + self.height, (line_height + 2 * self.spacer)/6)
        common_drawing.draw_outline_or_region('GL_POLYGON', outline, bg_color)
        common_drawing.draw_outline_or_region('GL_LINE_LOOP', outline, border_color)
        
        dpi = bpy.context.user_preferences.system.dpi
        blf.size(0, self.text_size, dpi)
        
        if self.is_collapsed:
            txt_x = left + self.border
            txt_y = top - self.border - line_height
            blf.position(0,txt_x, txt_y, 0)
            bgl.glColor4f(*txt_color)
            blf.draw(0, self.collapsed_msg)
            return
        
        for i, line in enumerate(self.text_lines):
            
            txt_x = left + self.border
            txt_y = top - self.border - (i+1) * (line_height + self.spacer)
                
            blf.position(0,txt_x, txt_y, 0)
            bgl.glColor4f(*txt_color)
            blf.draw(0, line)