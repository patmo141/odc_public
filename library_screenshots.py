#    Addon info
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
import bpy
import math
import time


bl_info = {
    'name': "Scene Object Screenshot Generator",
    'author': "Patrick R. Moore",
    'version': (0,0,1),
    'blender': (2, 6, 6),
    'api': 53613,
    'location': "3D View -> Tool Shelf",
    'description': "Makes a tiled image of all objects in scene",
    'warning': "",
    'wiki_url': "",
    'tracker_url': "",
    'category': '3D View'}


#variables/arguments
#image size
#number of obejcts
#thumbnail size
#scene


def icon_mn_to_index(m,n,n_columns):
    index = n*n_columns + m
    return index

def icon_index_to_nm(i,n_columns):
        
    m = math.floor(i/n_columns)
    n = math.fmod(i,n_columns)
    
    return [m,n]

def icon_index_to_pixel_array(index,thumb_x, thumb_y, sheex_x, n_columns):
    '''
    returns the pixel array indices as an array of lists
    '''
    
    if index != 0:
        m = int(math.fmod(index,n_columns))
    else:
        m = 0
    n = int(math.floor(index/n_columns))
    
    
    #print('the m x n value is %s' % str([m,n]))
    #the bottom left corner pixel...
    #x = midpoint of first block + n*width of blocks -16 pixels, -1 for indexing?
    #y = the number of blocks, - 1/2 a bloc, - 16 pixels + offset of 
    x = m*thumb_x
    y = n*thumb_y
    
    '''
    #print('the x y value is %s' % str([x,y]))

    img_width = 1204
    img_array = [0]*32*32*4
    
    for i in range(0,32):
        
        start = 4*((y+i)*img_width + x)
        end = start + 32*4
        
        #print(start)
        #print(end)
        
        img_array[i*32*4:(i+1)*32*4] = icon_source.pixels[start:end]

    
    return img_array
    '''
    
    
def main(context, obj): #, thumbnail_size):
    
    #object mode
    if context.object.mode != 'OBJEECT':
        bpy.ops.object.mode_set(mode = 'OBJECT')
    

    #select object, unhide it, active
    obj.hide = False
    obj.select = True
    context.scene.objects.active = obj
    
    #hide everything else
    for ob in bpy.data.objects:
        if ob.name != obj.name:
            ob.hide = True

    
    #this makes it have to run from operator in 3d view
    #cant run as script
    region = context.region  
    space = context.space_data
    #rv3d = space.region_3d
    
    if not space.local_view:
        bpy.ops.view3d.localview()
        
    bpy.ops.view3d.view_selected()
    bpy.ops.view3d.viewnumpad(type='TOP', align_active=True)
    bpy.ops.view3d.view_orbit(type='ORBITDOWN')
    bpy.ops.view3d.view_orbit(type='ORBITDOWN')
    bpy.ops.view3d.view_orbit(type='ORBITLEFT')
    #bpy.ops.render.opengl(animation=False, sequencer=False, write_still=False, view_context=True)
    


class SceneObjectThumbnails(bpy.types.Operator):
    """Takes a screen shot of every object in scene"""
    bl_idname = "wm.scene_objects_thumbnails"
    bl_label = "Scene Object Thumbnails"

    _timer = None

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        elif event.type == 'TIMER' and ((time.time()-self.time_point) > self.delta):
            if context.space_data.local_view:
                bpy.ops.view3d.localview()
            ob = self.ob_list[self.iter]
            main(context, ob)
            self.iter += 1
            self.time_point = time.time()
            if self.iter < self.n_obs:
                return {'RUNNING_MODAL'}
            else:
                context.window_manager.event_timer_remove(self._timer)
                return {'FINISHED'}
        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        
        self.ob_list = [ob for ob in context.scene.objects if ob.type not in {'CAMERA','EMPTY'}]
        print(self.ob_list)
        self.n_obs = len(self.ob_list)
        self.iter = 0
        self.time_point = time.time()
        self.delta = 0.5
        
        self._timer = context.window_manager.event_timer_add(10, context.window)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
        
    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        return {'CANCELLED'}


def register():
    bpy.utils.register_class(SceneObjectThumbnails)


def unregister():
    bpy.utils.unregister_class(SceneObjectThumbnails)


if __name__ == "__main__":
    register()
