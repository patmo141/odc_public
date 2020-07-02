'''
Created on Aug 19, 2016

@author: Patrick
'''
import bpy, math

S  = bpy.context.scene

# Create grease pencil data if none exists
if not S.grease_pencil:
    a = [ a for a in bpy.context.screen.areas if a.type == 'VIEW_3D' ][0]
    override = {
        'scene'         : S,
        'screen'        : bpy.context.screen,
        'object'        : bpy.context.object,
        'area'          : a,
        'region'        : a.regions[0],
        'window'        : bpy.context.window,
        'active_object' : bpy.context.object
    }

    bpy.ops.gpencil.data_add( override )

gp = S.grease_pencil

# Reference grease pencil layer or create one of none exists
if gp.layers:
    gpl = gp.layers[0]
else:
    gpl = gp.layers.new('gpl', set_active = True )

# Reference active GP frame or create one of none exists    
if gpl.frames:
    fr = gpl.active_frame
else:
    fr = gpl.frames.new(1) 

# Create a new stroke
str = fr.strokes.new()
str.draw_mode = '3DSPACE'

# Number of stroke points
strokeLength = 500 

# Add points
str.points.add(count = strokeLength )

pi, twopi = math.pi, 2*math.pi

theta = [20 * twopi * i / strokeLength for i in range(strokeLength)]

mean  = sum(theta)/float(len(theta))

theta = [th - mean for th in theta]

r = [4 - 2*math.cos(0.1*th) for th in theta]

y = [th/twopi for th in theta]
x = [a*math.cos(b) for a, b in zip(r, theta)]
z = [a*math.sin(b) for a, b in zip(r, theta)]

krazy_koil_points = list(zip(x, y, z))

points = str.points
for i, point in enumerate(points):
    points[i].co = krazy_koil_points[i]