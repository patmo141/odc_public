'''
Created on Oct 16, 2016

@author: Patrick

http://blender.stackexchange.com/questions/57709/how-to-draw-shapes-in-the-node-editor-with-python-bgl
http://blender.stackexchange.com/users/3710/poor

Image pixel coordinates
http://blender.stackexchange.com/questions/53780/pixel-coordinates-of-image-with-python?rq=1

'''
import bpy
import bgl
import blf
import math

# based on http://slabode.exofire.net/circle_draw.shtml
def draw_circle_2d(color, cx, cy, r, num_segments):
    theta = 2 * 3.1415926 / num_segments
    c = math.cos(theta) #precalculate the sine and cosine
    s = math.sin(theta)
    x = r # we start at angle = 0 
    y = 0
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    for i in range (num_segments):
        bgl.glVertex2f(x + cx, y + cy) # output vertex 
        # apply the rotation matrix
        t = x
        x = c * x - s * y
        y = s * t + c * y
    bgl.glEnd()

def draw_line_2d(color, start, end):
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(*start)
    bgl.glVertex2f(*end)
    bgl.glEnd()

def draw_typo_2d(color, text):
    font_id = 0  # XXX, need to find out how best to get this.
    # draw some text
    bgl.glColor4f(*color)
    blf.position(font_id, 20, 70, 0)
    blf.size(font_id, 20, 72)
    blf.draw(font_id, text)

def draw_callback_px(self, context):

    bgl.glPushAttrib(bgl.GL_ENABLE_BIT)
    # glPushAttrib is done to return everything to normal after drawing

    bgl.glLineStipple(10, 0x9999)
    bgl.glEnable(bgl.GL_LINE_STIPPLE)

    # 50% alpha, 2 pixel width line
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
    bgl.glLineWidth(5)

    bgl.glBegin(bgl.GL_LINE_STRIP)
    for x, y in self.mouse_path:
        bgl.glVertex2i(x, y)

    bgl.glEnd()
    bgl.glPopAttrib()

    bgl.glEnable(bgl.GL_BLEND)

    # ...api_current/bpy.types.Area.html?highlight=bpy.types.area
    header_height = context.area.regions[0].height # 26px
    width = context.area.width
    height = context.area.height - header_height

    p1_2d = (0,0)
    p2_2d = (width, height)
    p3_2d = (width, 0)
    p4_2d = (0, height)

    # green line
    bgl.glLineWidth(3)

    draw_line_2d((0.0, 1.0, 0.0, 0.8), p1_2d, p2_2d)

    # yellow line
    bgl.glLineWidth(5)
    draw_line_2d((1.0, 1.0, 0.0, 0.8), p3_2d, p4_2d) 

    # white circle
    bgl.glLineWidth(4)
    draw_circle_2d((1.0, 1.0, 1.0, 0.8), width/2, height/2, 70, 360)

    # red circle
    bgl.glLineWidth(5)
    draw_circle_2d((1.0, 0.0, 0.0, 0.4), width/2, height/2, 230, 5)

    # draw text
    draw_typo_2d((1.0, 1.0, 1.0, 1), "Hello Word " + str(len(self.mouse_path)))

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


class ModalDrawOperator(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "image.modal_operator"
    bl_label = "Simple Modal Image Editor Operator"

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

        elif event.type == 'LEFTMOUSE':
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'IMAGE_EDITOR':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceImageEditor.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.mouse_path = []

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "IMAGE_EDITOR not found, cannot run operator")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(ModalDrawOperator)

def unregister():
    bpy.utils.unregister_class(ModalDrawOperator)

if __name__ == "__main__":
    register()