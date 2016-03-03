'''
Created on Mar 6, 2013

@author: Patrick
'''
import time

import bpy
from mathutils import Vector, Matrix
#from . 
import odcutils
from odcutils import get_settings
import math

def place_implant(context, implant_space, location,orientation,imp, hardware = True):
    '''
    
    args:
        context
        implant_space - ODC Implant Space type
        location - Vector
        orientation - Matrix or Quaternion
        lib_implants - 
        imp - string representing implant object name in link library
    '''
    #check if space already has an implant object.
    #if so, delete, replace, print warning
    sce = context.scene
    if implant_space.implant and implant_space.implant in bpy.data.objects:
        print("replacing the existing implant with the one you chose")
        Implant = bpy.data.objects[implant_space.implant]
        #unlink it from the scene, clear it's useres, remove it.
        
        
        if Implant.children:
            for child in Implant.children:
                sce.objects.unlink(child)
                child.user_clear
                bpy.data.objects.remove(child)
                            
        sce.objects.unlink(Implant)
        implant_mesh = Implant.data
        
        Implant.user_clear()
        #remove the object
        bpy.data.objects.remove(Implant)
        implant_mesh.user_clear()
        bpy.data.meshes.remove(implant_mesh)
        
        sce.update()
        #TDOD what about the children/hardwares?
   
    world_mx = Matrix.Identity(4)
    world_mx[0][3]=location[0]
    world_mx[1][3]=location[1]
    world_mx[2][3]=location[2]
        
        #mx_b = Matrix.Identity(4)
        #mx_l = Matrix.Identity(4)
    #is this more memory friendly than listing all objects?
    current_obs = [ob.name for ob in bpy.data.objects]
    
    #link the new implant from the library
    settings = get_settings()
    odcutils.obj_from_lib(settings.imp_lib, imp)
    
    #this is slightly more robust than trusting we don't have duplicate names.
    for ob in bpy.data.objects:
        if ob.name not in current_obs:
            Implant = ob
    
    
    sce.objects.link(Implant)
    #Implant.matrix_basis = mx_b
    Implant.matrix_world = world_mx
    Implant.update_tag()
    sce.update()
    Implant.rotation_mode = 'QUATERNION'
    Implant.rotation_quaternion = orientation
    sce.update()
    #Implant.matrix_local = mx_l
    #Implant.location = L
    
    if sce.odc_props.master:
        Master = bpy.data.objects[sce.odc_props.master]
        odcutils.parent_in_place(Implant, Master)
    else:
        print('No Master Model, placing implant anyway, moving objects may not preserve spatial relationships')
    
    #looks a little redundant, but it ensure if any
    #duplicates exist our referencing stays accurate
    Implant.name = implant_space.name + "_" + Implant.name
    implant_space.implant = Implant.name
    
    if hardware:
        current_obs = [ob.name for ob in bpy.data.objects]
                    
        inc = imp + '_'
        
        settings = get_settings()
        hardware_list = odcutils.obj_list_from_lib(settings.imp_lib, include = inc)
        print(hardware_list)
        for ob in hardware_list:
            odcutils.obj_from_lib(settings.imp_lib,ob)
                
        for ob in bpy.data.objects:
            if ob.name not in current_obs:
                sce.objects.link(ob)
                ob.parent = Implant
                ob.layers[11] = True  #TODO: put this in layer management.
                                           
    return Implant

def implant_outer_cylinder(context, space, 
                           width, depth, trim = 0, 
                           wedge = False, wedge_pct = .7,
                           debug = False):
    
    if debug:
        start_time = time.time()
    
    scene = bpy.context.scene
    Implant = scene.objects[space.implant]
    mx_w = Implant.matrix_world.copy()
    
    if Implant.rotation_mode != 'QUATERNION':
        Implant.rotation_mode = 'QUATERNION'
        Implant.update_tag()
        context.scene.update()
    
    R = width/2
    H = .1
    if wedge:
        bm = odcutils.primitive_wedge_cylinder(R, wedge_pct, 64, H)
        
    else:
        bm = odcutils.primitive_flattened_cylinder(R, R-trim, 64, H)

    if space.outer and space.outer in bpy.data.objects:
        Cylinder = bpy.data.objects[space.outer]
        me = Cylinder.data
        if len(Cylinder.modifiers):
            for mod in Cylinder.modifiers:
                Cylinder.modifiers.remove(mod)
    
    else:
        me = bpy.data.meshes.new(Implant.name + '_GC')
        Cylinder = bpy.data.objects.new(Implant.name + '_GC', me)
        scene.objects.link(Cylinder)
        name = Implant.name + '_GC'
        Cylinder.name = name
    
        #point the right direction
        Cylinder.rotation_mode = 'QUATERNION'
        Cylinder.rotation_quaternion = mx_w.to_quaternion()
        
        Cylinder.update_tag()
        context.scene.update()
    
        Trans = Implant.rotation_quaternion * Vector((0,0,-depth))
        Cylinder.matrix_world[0][3] = mx_w[0][3] + Trans[0]
        Cylinder.matrix_world[1][3] = mx_w[1][3] + Trans[1]
        Cylinder.matrix_world[2][3] = mx_w[2][3] + Trans[2]
    
    bm.to_mesh(me)
    bm.free()

    #vert group    
    Cylinder.vertex_groups.clear() 
    Cylinder.vertex_groups.new("Project")
    vert_inds = [v.index for v in Cylinder.data.vertices if v.index%2]
    Cylinder.vertex_groups["Project"].add(vert_inds, 1,'REPLACE')

    Cylinder.update_tag()
    context.scene.update()

    if len(scene.odc_splints):
        splint = scene.odc_splints[scene.odc_splint_index]
        if splint.splint in bpy.data.objects:
            Splint = bpy.data.objects[splint.splint]
        
            mod = Cylinder.modifiers.new('Project','SHRINKWRAP')
            mod.wrap_method = 'PROJECT'
            mod.use_project_z = True
            mod.use_project_y = False
            mod.use_project_x = False
            mod.offset = .5
            mod.target = Splint
            mod.vertex_group = 'Project'
    

    space.outer = Cylinder.name
    
    odcutils.parent_in_place(Cylinder, Implant)
    if debug:
        print('finished outer cylinder for %s in %f seconds' % (space.name, time.time() - start_time))

def implant_inner_cylinder(context, space, thickness = None, debug = False):
    
    if debug:
        start_time = time.time()
    sce = context.scene
    Implant = sce.objects[space.implant]
    mx_w = Implant.matrix_world.copy()
    
    if thickness:
        D = thickness
    else:
        D = Implant.dimensions[0]
        
    #create a bmesh cylinder
    R = D/2
    bm = odcutils.primitive_flattened_cylinder(R, R, 64, 30)
    
    if Implant.rotation_mode != 'QUATERNION':
        Implant.rotation_mode = 'QUATERNION'
        Implant.update_tag()
        context.scene.update()

    if space.inner and space.inner in bpy.data.objects:
        Cylinder = bpy.data.objects[space.inner]
        me = Cylinder.data
        
    else:
        me = bpy.data.meshes.new(Implant.name + '_GC')
        Cylinder = bpy.data.objects.new(Implant.name + '_IC', me)
        # Add the mesh to the scene
        scene = bpy.context.scene
        scene.objects.link(Cylinder)
        
        #point the right direction
        Cylinder.rotation_mode = 'QUATERNION'
        Cylinder.rotation_quaternion = mx_w.to_quaternion()
    
        #now we must update to propagate changes to the
        #world matrix.  Otherwise, when we access matrix_world
        #it will not have the new information about scale and
        #rotation...and they changes will be lost when we access
        #the matrix to assign different values to other elements
        Cylinder.update_tag()
        context.scene.update()
    
        Trans = Implant.rotation_quaternion * Vector((0,0,- (30 + Implant.dimensions[2])))
        Cylinder.matrix_world[0][3] = mx_w[0][3] + Trans[0]
        Cylinder.matrix_world[1][3] = mx_w[1][3] + Trans[1]
        Cylinder.matrix_world[2][3] = mx_w[2][3] + Trans[2]

    #Write the bmesh into a new mesh or replace the old mesh?
    bm.to_mesh(me)
    bm.free()

    Cylinder.vertex_groups.clear()        
    Cylinder.vertex_groups.new("Project")
    
    #rodd verts added to the "Project Group"
    vert_inds = [v.index for v in Cylinder.data.vertices if v.index%2]
    Cylinder.vertex_groups["Project"].add(vert_inds, 1,'REPLACE')
        
    Cylinder.update_tag()
    context.scene.update()
    
    space.inner = Cylinder.name
    
    odcutils.parent_in_place(Cylinder, Implant)
    if debug:
        print('finished inner cylinder for %s in %f seconds' % (space.name, time.time() - start_time))

