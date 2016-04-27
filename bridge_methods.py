'''
Created on Jan 25, 2013

@author: Patrick
'''
import time
import math
import bpy
from mathutils import Vector, Matrix
import odcutils
from odcutils import get_settings

def active_spanning_restoration(context, exclude = [], debug = False):
    '''
    TODO: test robustness and implications of this logic
    looks at addon preferences
    returns a list,
    '''
    sce = context.scene
    bridges = []

    if not hasattr(context.scene, 'odc_props'): return [None]
    if len(context.scene.odc_bridges) == 0: return [None]
    settings = get_settings()
    b = settings.behavior
    behave_mode = settings.behavior_modes[int(b)]
    
    if behave_mode == 'LIST':
        #choose just one tooth in the list
        if len(sce.odc_bridges):
            bridge = sce.odc_bridges[sce.odc_bridge_index]
            bridges.append(bridge)
        
    elif behave_mode == 'ACTIVE':
        if len(sce.odc_bridges):
            for bridge in context.scene.odc_bridges:
            
                prop_keys = bridge.keys()
                prop_vals = bridge.values()
                if debug > 1:
                    print(prop_keys)
                    print(prop_vals)
                    
                ob = context.object
                if ob.name in prop_vals:
                    n = prop_vals.index(ob.name)
                    this_key = prop_keys[n]
                    
                    if debug:
                        print("found the object named %s as the property value: %s in bridge: %s" %(ob.name, this_key, bridge.name))
                if this_key and (this_key not in exclude):
                    bridges.append(bridge)
            
            tooth = odcutils.tooth_selection(context)[0]
            for bridge in sce.odc_bridges:
                if tooth.name in bridge.tooth_string.split(sep=":"):
                    if debug:
                        print('found tooth %s in bridge: %s' % (tooth.name, bridge.name))
                    bridges.append(bridge)
    
    elif behave_mode == 'ACTIVE_SELECTED':
        #make sure the active object has priority by checking that first.
        if len(sce.odc_bridges):
            for bridge in context.scene.odc_bridges:
                prop_keys = bridge.keys()
                prop_vals = bridge.values()
            
                if context.object:
                    if context.object.name in prop_vals:
                        n = prop_vals.index(context.object.name)
                        this_key = prop_keys[n]
                        if debug:
                            print("found the object named %s as the property value: %s in bridge: %s" %(ob.name, this_key, bridge.name))
                        bridges.append(bridge)
                   
            
            teeth = odcutils.tooth_selection(context)
            if teeth:
                for tooth in teeth:
                    for bridge in sce.odc_bridges:
                        if tooth.name in bridge.tooth_string.split(sep=":"):
                            if debug:
                                print('found tooth %s in bridge: %s' % (tooth.name, bridge.name))
                            if bridge not in bridges:
                                bridges.append(bridge)
    if debug > 1:
        print(bridges)
    return bridges

def bridge_from_selection(context, debug = False):
    #TODO check univ vs intl system
    teeth = odcutils.tooth_selection(context)
    names = [tooth.name for tooth in teeth]
    
    #check axes
    univ_names = [odcutils.intntl_universal[int(name)] for name in names]
    univ_names.sort()
    bridge_start = int(min(univ_names))
    bridge_end = int(max(univ_names))
    
    bridge_name = str(odcutils.universal_intntl[bridge_start]) + "x" + str(odcutils.universal_intntl[bridge_end])
    if debug:
        print(bridge_name)
        
    n = len(context.scene.odc_bridges)
    context.scene.odc_bridges.add()
    bridge = context.scene.odc_bridges[n]
    tooth_list =  [tooth.name for tooth in teeth]
    bridge.tooth_string = ":".join(tooth_list)
    bridge.name = bridge_name
    #bridge.save_components_to_string()
    
    
def break_contact_slice(context, ob1, ob2, space, before_multires = True, debug = False):
    '''
    slice through the best fit plane using a shrinkwrap
    modifier.  results in a knife like cut through the
    objects.
    
    args:
    
    ret:
    '''
    if debug:
        print('ob1 name: %s' % ob1.name)
        print('ob2 name: %s' % ob2.name)
    
    quat_1 = ob1.matrix_world.to_quaternion()
    quat_2 = ob2.matrix_world.to_quaternion()
         
    loc_1 = odcutils.get_bbox_center(ob1, world = True)
    loc_2 = odcutils.get_bbox_center(ob2, world = True)
    diff = loc_2 - loc_1

    
    #the directions to keep things simple.
    x = Vector((1,0,0))
    y = Vector((0,1,0))
    z = Vector((0,0,1))
    vecs = [x,y,z]
    #dot each of the x,y,z coords (transformed to workd dir) with the vector between
    #the two bounding box centers.
    
    dirs1 = [(quat_1 * x).dot(diff)**2, (quat_1 * y).dot(diff)**2, (quat_1 * z).dot(diff)**2]
    dirs2 = [(quat_2 * x).dot(diff)**2, (quat_2 * y).dot(diff)**2, (quat_2 * z).dot(diff)**2]
    
    #find the maximium dot product
    #this is the dirction which is most parallel
    dir1 = dirs1.index(max(dirs1))
    dir2 = dirs2.index(max(dirs2))
    
    #check i we need to negate eithe directions
    #don't get confused because we will negate again
    #when we put the shrinwrap mod on.  This is determinging
    #whether +x or -x points at the othe robject
    neg1 = 1 + -2 * ((quat_1 * vecs[dir1]).dot(diff) < 0)
    neg2 = 1 + -2 * ((quat_2 * vecs[dir2]).dot(diff) > 0)
    
    vec1 = neg1 * vecs[dir1]
    vec2 = neg2 * vecs[dir2]
    
    if debug:
        print(ob1.name + ' is pointed toward ' + ob2.name + ' in the direction:')
        print(vec1)
        print(ob2.name + ' is pointed toward ' + ob1.name + ' in the direction:')
        print(vec2)
    
    pt1 = odcutils.box_feature_locations(ob1, vec1)
    pt2 = odcutils.box_feature_locations(ob2, vec2)
    
    if debug:
        print(pt1)
        print(pt2)
     
    midpoint = .5 * (pt1 + pt2)
        
    pln_verts = [Vector((1,1,0)),Vector((-1,1,0)),Vector((-1,-1,0)),Vector((1,-1,0))]
    pln_faces = [(0,1,2,3)]
    pln_mesh = bpy.data.meshes.new('separator')
    pln_mesh.from_pydata(pln_verts,[],pln_faces)
    new_plane_ob = bpy.data.objects.new('Separator', pln_mesh)
    new_plane_ob.rotation_mode = 'QUATERNION'
    new_plane_ob.rotation_quaternion = odcutils.rot_between_vecs(Vector((0,0,1)), diff)
    new_plane_ob.location = midpoint
    new_plane_ob.scale = .5 * (ob1.dimensions + ob2.dimensions)
    new_plane_ob.draw_type = 'WIRE'
    context.scene.objects.link(new_plane_ob)
    
    mod1 = ob1.modifiers.new('Contact', 'SHRINKWRAP')
    mod2 = ob2.modifiers.new('Contact', 'SHRINKWRAP')
    
    mod1.wrap_method = 'PROJECT'
    mod2.wrap_method = 'PROJECT'
    
    if neg1 < 0:
        mod1.use_negative_direction = False
        mod1.use_positive_direction = True
    else:
        mod1.use_negative_direction = True
        mod1.use_positive_direction = False
        
    if neg2 < 0:
        mod2.use_negative_direction = False
        mod2.use_positive_direction = True
    else:
        mod2.use_negative_direction = True
        mod2.use_positive_direction = False
        
        
    if dir1 == 0:
        mod1.use_project_x = True
    elif dir1 == 1:
        mod1.use_project_y = True
    else:
        mod1.use_project_z = True
    
    if dir2 == 0:
        mod2.use_project_x = True
    elif dir2 == 1:
        mod2.use_project_y = True
    else:
        mod2.use_project_z = True
    
    mod1.target = new_plane_ob
    mod2.target = new_plane_ob
    
    mod1.offset =  space
    mod2.offset =  space  
    print('broken!')
        
    #move it to top?
    if before_multires:
        for ob in [ob1,ob2]:
            context.scene.objects.active = ob
            n = n = len(ob.modifiers)
            mod = ob.modifiers[n-1]
            for i in range(0,n):
                bpy.ops.object.modifier_move_up(modifier=mod.name)
    
    
    
def break_contact_deform(context, ob1,ob2, debug = False):
    '''
    separate two objects by deforming a lattice with
    a plane.  Results in a smooth separation.
    
    args:
    
    ret:
    
    '''

    
    if debug:
        print('ob1 name: %s' % ob1.name)
        print('ob2 name: %s' % ob2.name)
    quat_1 = ob1.matrix_world.to_quaternion()
    quat_2 = ob2.matrix_world.to_quaternion()
    
    lat1 = odcutils.bbox_to_lattice(context.scene, ob1)
    lat2 = odcutils.bbox_to_lattice(context.scene, ob2)
    
    print('we made lattices?')
    loc_1 = odcutils.get_bbox_center(ob1, world = True)
    loc_2 = odcutils.get_bbox_center(ob2, world = True)
    diff = loc_2 - loc_1

    
    #the directions to keep things simple.
    x = Vector((1,0,0))
    y = Vector((0,1,0))
    z = Vector((0,0,1))
    vecs = [x,y,z]
    #dot each of the x,y,z coords (transformed to workd dir) with the vector between
    #the two bounding box centers.
    
    dirs1 = [(quat_1 * x).dot(diff)**2, (quat_1 * y).dot(diff)**2, (quat_1 * z).dot(diff)**2]
    dirs2 = [(quat_2 * x).dot(diff)**2, (quat_2 * y).dot(diff)**2, (quat_2 * z).dot(diff)**2]
    
    #find the maximium dot product
    #this is the dirction which is most parallel
    dir1 = dirs1.index(max(dirs1))
    dir2 = dirs2.index(max(dirs2))
    
    #check i we need to negate eithe directions
    #don't get confused because we will negate again
    #when we put the shrinwrap mod on.  This is determinging
    #whether +x or -x points at the othe robject
    neg1 = 1 + -2 * ((quat_1 * vecs[dir1]).dot(diff) < 0)
    neg2 = 1 + -2 * ((quat_2 * vecs[dir2]).dot(diff) > 0)
    
    vec1 = neg1 * vecs[dir1]
    vec2 = neg2 * vecs[dir2]
    
    if debug:
        print(ob1.name + ' is pointed toward ' + ob2.name + ' in the direction:')
        print(vec1)
        print(ob2.name + ' is pointed toward ' + ob1.name + ' in the direction:')
        print(vec2)
    
    pt1 = odcutils.box_feature_locations(ob1, vec1)
    pt2 = odcutils.box_feature_locations(ob2, vec2)
    
    if debug:
        print(pt1)
        print(pt2)
     
    midpoint = .5 * (pt1 + pt2)
    
    pln_verts = [Vector((1,1,0)),Vector((-1,1,0)),Vector((-1,-1,0)),Vector((1,-1,0))]
    pln_faces = [(0,1,2,3)]
    pln_mesh = bpy.data.meshes.new('separator')
    pln_mesh.from_pydata(pln_verts,[],pln_faces)
    new_plane_ob = bpy.data.objects.new('Separator', pln_mesh)
    new_plane_ob.rotation_mode = 'QUATERNION'
    new_plane_ob.rotation_quaternion = odcutils.rot_between_vecs(Vector((0,0,1)), diff)
    new_plane_ob.location = midpoint
    new_plane_ob.scale = .5 * (ob1.dimensions + ob2.dimensions)
    
    context.scene.objects.link(new_plane_ob)
    
    mod1 = lat1.modifiers.new('Contact', 'SHRINKWRAP')
    mod2 = lat2.modifiers.new('Contact', 'SHRINKWRAP')

    mod1.wrap_method = 'PROJECT'
    mod2.wrap_method = 'PROJECT'
    
    if neg1 < 0:
        mod1.use_negative_direction = False
        mod1.use_positive_direction = True
    else:
        mod1.use_negative_direction = True
        mod1.use_positive_direction = False
        
    if neg2 < 0:
        mod2.use_negative_direction = False
        mod2.use_positive_direction = True
    else:
        mod2.use_negative_direction = True
        mod2.use_positive_direction = False
        
        
    if dir1 == 0:
        mod1.use_project_x = True
    elif dir1 == 1:
        mod1.use_project_y = True
    else:
        mod1.use_project_z = True
    
    if dir2 == 0:
        mod2.use_project_x = True
    elif dir2 == 1:
        mod2.use_project_y = True
    else:
        mod2.use_project_z = True
    
    mod1.target = new_plane_ob
    mod2.target = new_plane_ob    
    print('broken!')
          
def make_pre_bridge(context, odc_bridge, debug = False):
    if debug:
        start = time.time()
    
    ####  Find out which teeth are in the bridge
    bridge_teeth = [context.scene.odc_teeth[name] for name in odc_bridge.tooth_string.split(sep=":")]

    #Duplicate them, rename their vertex groups and join them.        
    bpy.ops.object.select_all(action='DESELECT')
    
    for tooth in bridge_teeth:
        if tooth.margin:
            margin = tooth.margin
            Margin = bpy.data.objects[margin]
            
            Margin.hide = False
            Margin.select = True
            context.scene.objects.active = Margin
            
    #not sure why this is commented out, I may revisit it    
    #bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)    
    if len(context.selected_editable_objects):
        current_objects=list(bpy.data.objects)                
        bpy.ops.object.duplicate()
        bpy.ops.object.join()
    
        for ob in bpy.data.objects:
            if ob not in current_objects:
                ob.name = odc_bridge.name + "_Margin"
                odc_bridge.margin = ob.name
                Margin = ob
        bpy.ops.object.select_all(action='DESELECT')

    
    for tooth in bridge_teeth:
    
        if tooth.restoration:
            restoration = tooth.restoration
        elif tooth.contour:
            restoration = tooth.contour
        else:
            continue    
        ob = bpy.data.objects[restoration]
        ob.select = True
        ob.hide = False
        
        #test out deleting the fake user...
        me = ob.data
        if me.use_fake_user:
            me.use_fake_user = False               
        
        #Change this later since it resets the active objects len(bridge) times
        #but it ends with one of the teeth as the active object, so...
        context.scene.objects.active = ob
        bpy.ops.object.multires_base_apply(modifier = 'Multires')
        
        if 'Dynamic Margin' in ob.modifiers:
            bpy.ops.object.modifier_apply(modifier = 'Dynamic Margin')
            bpy.ops.object.multires_base_apply()
        for mod in ob.modifiers:
            if mod.name != 'Multires':
                bpy.ops.object.modifier_apply(modifier = mod.name)
    
    
    current_objects=list(bpy.data.objects)                
    bpy.ops.object.duplicate()

    #rename their vertex groups
    for tooth in bpy.context.selected_objects:
        j = tooth.name.partition('_')
        pref = j[0]
    
        for g in tooth.vertex_groups:
            if pref not in g.name:
                new_name = str(pref + "_" + g.name)
                g.name = new_name
       
    bpy.ops.object.join()

    for ob in bpy.data.objects:
        if ob not in current_objects:
            ob.name = odc_bridge.name + '_Bridge'
            odc_bridge.bridge = ob.name
            Bridge = ob
        
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active=Bridge
    Bridge.select = True
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action = 'DESELECT')
    for g in Bridge.vertex_groups:
        if 'Margin' in g.name:
            bpy.ops.object.vertex_group_set_active(group = g.name)
            bpy.ops.object.vertex_group_select()
    
    n = len(Bridge.vertex_groups)
    bpy.context.tool_settings.vertex_group_weight = 1
    bpy.ops.object.vertex_group_assign_new()
    Bridge.vertex_groups[n].name = 'Bridge Margin'

    n = len(Bridge.vertex_groups)
    bpy.context.tool_settings.vertex_group_weight = 1
    bpy.ops.object.vertex_group_add()
    Bridge.vertex_groups[n].name = 'Connectors'

    bpy.ops.mesh.select_all(action = 'SELECT')
    #bpy.ops.mesh.vertices_sort()
    bpy.ops.mesh.sort_elements(type='SELECTED', elements={'VERT'}, reverse=False, seed=0)

    bpy.ops.object.mode_set(mode='OBJECT')
    #remove all the modifiers
    for mod in Bridge.modifiers:
        if mod.name != 'Multires':
            bpy.ops.object.modifier_remove(modifier = mod.name)
            
    #Add back the maringal modifier
    n = len(Bridge.modifiers)
    bpy.ops.object.modifier_add(type = 'SHRINKWRAP')
    mod = Bridge.modifiers[n]
    mod.name = 'Bridge Margin'
    mod.vertex_group = 'Bridge Margin'
    mod.wrap_method = 'NEAREST_VERTEX'
    if odc_bridge.margin:
        mod.target = bpy.data.objects[odc_bridge.margin] 
    
    #put in a smooth modifier for connectors after multires
    n = len(Bridge.modifiers)
    bpy.ops.object.modifier_add(type = 'SMOOTH')
    mod = Bridge.modifiers[n]
    mod.name = 'Smooth Connectors'
    mod.vertex_group = 'Connectors'
    mod.factor = 1
    mod.iterations = 20
    
    #put in a smooth modifier for connectors before multires
    n = len(Bridge.modifiers)
    bpy.ops.object.modifier_add(type = 'SMOOTH')
    mod = Bridge.modifiers[n]
    mod.name = 'Embrasure Form'
    mod.vertex_group = 'Connectors'
    mod.factor = .5
    mod.iterations = 3
    for i in range(0,n): #n still references number of modifies before adding a new one :-)
        bpy.ops.object.modifier_move_up(modifier="Embrasure Form")
    for tooth in bridge_teeth:
        if tooth.restoration:
            restoration = tooth.restoration
        else:
            restoration = tooth.contour
            
        Restoration = context.scene.objects[restoration]
        Restoration.hide = True
        
    if debug:
        print('made pre bridge in %f seconds' % (time.time() - start))


def bridge_loop_2(context, ob, group1, group2, segments, twist, cubic, group3 = None, debug = False):
    '''
    group3 the group to add the new bridge verts too.
    '''
    
    
    if debug:
        start = time.time()
    bpy.ops.object.select_all(action='DESELECT')    
    if context.object != ob:
        context.scene.objects.active = ob
    ob.hide = False
    ob.select = True
        
    if context.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
        
    bpy.ops.mesh.select_all(action='DESELECT')
    context.tool_settings.mesh_select_mode = [True,False,False]
    for group in [group1, group2]:
        bpy.ops.object.vertex_group_set_active(group = group)
        bpy.ops.object.vertex_group_select()
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    n_faces = len([f for f in ob.data.polygons if f.select])
    if debug:
        print("there were %i faces in the groups" % n_faces)
    
    if n_faces:
        bpy.ops.mesh.delete(type='FACE')
        for group in [group1, group2]:
            bpy.ops.object.vertex_group_set_active(group = group)
            bpy.ops.object.vertex_group_select()
            #bpy.ops.mesh.looptools_circle(custom_radius=False, fit='inside', flatten=True, influence=20, radius=1, regular=True)
            bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='3', regular=True)
            
        #bpy.ops.object.mode_set(mode='OBJECT')
        #return
    else:
        bpy.ops.mesh.loop_to_region(select_bigger=False)
        bpy.ops.mesh.delete(type='FACE')
        
        for group in [group1, group2]:
            bpy.ops.object.vertex_group_set_active(group = group)
            bpy.ops.object.vertex_group_select()
        #bpy.ops.object.mode_set(mode='OBJECT')
        #return
      

    #bpy.ops.mesh.loop_to_region(select_bigger=False)
    context.tool_settings.mesh_select_mode = [False,True,False]
    #loopstools bridge giving weird results w/o the edimode toggle
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.bridge_edge_loops(type='SINGLE', use_merge=False, merge_factor=0.5, number_cuts=2, interpolation='PATH', smoothness=1, profile_shape_factor=0, profile_shape='SMOOTH')
    #bpy.ops.mesh.looptools_bridge(cubic_strength=cubic, interpolation='cubic', loft=False, loft_loop=False, min_width=75, mode='shortest', remove_faces=False, reverse=False, segments=segments, twist=twist)
    
    context.tool_settings.mesh_select_mode = [True,False,False]
    
    if group3: #TODO: check for existence of group3
        context.tool_settings.vertex_group_weight = 1
        bpy.ops.object.vertex_group_set_active(group = group3)
        bpy.ops.object.vertex_group_assign()
    
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_loose()
    bpy.ops.mesh.delete()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent()
    
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    if debug:
        print("bridged %s and %s in %f seconds" % (group1, group2, time.time() - start))
        
    return

def bridge_loop(context, ob, group1, group2, segments, twist, cubic, group3 = None, debug = False):
    '''
    group3 the group to add the new bridge verts too.
    '''
    if debug:
        start = time.time()
    bpy.ops.object.select_all(action='DESELECT')    
    if context.object != ob:
        context.scene.objects.active = ob
    ob.hide = False
    ob.select = True
        
    if context.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
        
    bpy.ops.mesh.select_all(action='DESELECT')
    context.tool_settings.mesh_select_mode = [True,False,False]
    for group in [group1, group2]:
        bpy.ops.object.vertex_group_set_active(group = group)
        bpy.ops.object.vertex_group_select()
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    n_faces = len([f for f in ob.data.polygons if f.select])
    if debug:
        print("there were %i faces in the groups" % n_faces)
    
    if n_faces:
        bpy.ops.mesh.delete(type='FACE')
        for group in [group1, group2]:
            bpy.ops.object.vertex_group_set_active(group = group)
            bpy.ops.object.vertex_group_select()
            #bpy.ops.mesh.looptools_circle(custom_radius=False, fit='inside', flatten=True, influence=20, radius=1, regular=True)
            bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='3', regular=True)
            
        #bpy.ops.object.mode_set(mode='OBJECT')
        #return
    else:
        bpy.ops.mesh.loop_to_region(select_bigger=False)
        bpy.ops.mesh.delete(type='FACE')
        
        for group in [group1, group2]:
            bpy.ops.object.vertex_group_set_active(group = group)
            bpy.ops.object.vertex_group_select()
        #bpy.ops.object.mode_set(mode='OBJECT')
        #return
      

    #bpy.ops.mesh.loop_to_region(select_bigger=False)
    context.tool_settings.mesh_select_mode = [False,True,False]
    #loopstools bridge giving weird results w/o the edimode toggle
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.bridge_edge_loops(type='SINGLE', use_merge=False, merge_factor=0.5, number_cuts=1, interpolation='SURFACE', smoothness=1, profile_shape_factor=0, profile_shape='SMOOTH')
    #bpy.ops.mesh.looptools_bridge(cubic_strength=cubic, interpolation='cubic', loft=False, loft_loop=False, min_width=75, mode='shortest', remove_faces=False, reverse=False, segments=segments, twist=twist)
    
    context.tool_settings.mesh_select_mode = [True,False,False]
    
    if group3: #TODO: check for existence of group3
        context.tool_settings.vertex_group_weight = 1
        bpy.ops.object.vertex_group_set_active(group = group3)
        bpy.ops.object.vertex_group_assign()
    
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_loose()
    bpy.ops.mesh.delete()
    bpy.ops.mesh.select_all(action='SELECT')
    #bpy.ops.mesh.normals_make_consistent()
    
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    if debug:
        print("bridged %s and %s in %f seconds" % (group1, group2, time.time() - start))
        
    return

def make_bridge_intaglio(context, bridge, debug = False):
    if debug:
        start = time.time()
    
    sce=context.scene
    
    bridge_teeth = [context.scene.odc_teeth[name] for name in bridge.tooth_string.split(sep=":")]
    #gather a list of the inside objects
    insides = [[None]]*len(bridge_teeth)
    for i, tooth in enumerate(bridge_teeth):
        insides[i] = tooth.intaglio

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action = 'DESELECT')


    # apply all the modifiers
    for intaglio in insides:
        Inside = sce.objects[intaglio]
        sce.objects.active = Inside
        Inside.hide = False
        Inside.select = True
    
        for mod in Inside.modifiers:
            bpy.ops.object.modifier_apply(modifier = mod.name)
        
    bpy.ops.object.select_all(action = 'DESELECT')
    
    #join all the insides
    for intaglio in insides:
        Inside = sce.objects[intaglio]
        sce.objects.active = Inside
        Inside.hide = False
        Inside.select = True
    
    current_objects=list(bpy.data.objects)
    bpy.ops.object.duplicate()
    bpy.ops.object.join() 

    for ob in bpy.data.objects:
        if ob not in current_objects:                
            ob.name=bridge.name + "_intaglio"
            bridge.intaglio = ob.name
            ob.data.name = bridge.name + "_intaglio"
            BridgeInside = ob
    
    if debug:
        finish = time.time()-start
        print("finished bridge intaglio in %f seconds" % finish)
        
    return BridgeInside

def stitch_bridge(context, bridge, debug = False):
    if debug:
        start = time.time()
    
    sce = context.scene
    
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    Intaglio = bpy.data.objects[bridge.intaglio]
    Bridge = bpy.data.objects[bridge.bridge]
       
    bpy.ops.object.select_all(action = 'DESELECT')            
    current_objects=list(bpy.data.objects)
    
    sce.objects.active = Bridge
    Bridge.select = True
    Bridge.hide = False
    
    for mod in Bridge.modifiers:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        
        
    Intaglio.select = True
    Intaglio.hide = False
    sce.objects.active = Bridge
    for mod in Intaglio.modifiers:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        
    bpy.ops.object.join()
    
    ob = context.object
    ob.name = bridge.name + "_FinalRestoration"
    SolidBridge = ob

    bpy.ops.object.mode_set(mode = 'EDIT')    
    me = SolidBridge.data

    ### Weld the Two Parts together ###  (boolean modifier may be better depending on code?)
    bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
           
    
    #first weld all the very close verts at the resoution of the margin resolution
    bpy.ops.mesh.remove_doubles(threshold = .025)
    bpy.ops.mesh.select_all(action = 'DESELECT')
    
    nverts = 1
    attempts = 0
    while nverts > 0 and attempts < 6:
        
        #select any remaining non manifold edges and try again after subdividing and using a larger merge
        bpy.context.scene.tool_settings.mesh_select_mode = [False, True, False]        
        bpy.ops.mesh.select_non_manifold()
        bpy.ops.mesh.subdivide()
        bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False] 
        bpy.ops.mesh.remove_doubles(threshold = .03*(attempts + 1))
    
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.mesh.select_non_manifold()
    
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')
    
        nverts = len([v.index for v in me.vertices if v.select])
        if debug > 1:
            print('%d verts left to merge at attempt %d and threshold %f' % (nverts, attempts, (.03*(attempts+1))))
            
        attempts +=1
        
    
    bpy.ops.object.mode_set(mode ='OBJECT')
    '''
    for a in bpy.context.window.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    if not s.local_view:
                        bpy.ops.view3d.localview() 
    '''                       
    if debug:
        finish = time.time()-start
        print("finished stitching in %f seconds" % finish)
        
    return SolidBridge