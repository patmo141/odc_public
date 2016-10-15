'''
Created on Jan 20, 2013

@author: Patrick
'''

#python imports
import time
import math
import random

#blender imports
import bpy
import addon_utils
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.mesh_utils import edge_loops_from_edges
from mathutils.geometry import intersect_point_line
from mathutils.bvhtree import BVHTree
#odc imports

import odcutils
from odcutils import offset_bmesh_edge_loop
from bmesh_fns import join_bmesh_map
from mesh_cut import edge_loops_from_bmedges, space_evenly_on_path
import bmesh
from common_utilities import bversion

def pontificate(context, tooth, shell, p_type, offset):
    
    bpy.ops.object.mode_set(mode= 'OBJECT')
    bpy.ops.object.select_all(action = 'DESELECT')
    shell.select = True
    shell.hide = False
    context.scene.objects.active = shell
    context.tool_settings.mesh_select_mode = [False, True, True]
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold(extend=True)
    bpy.ops.object.mode_set(mode = 'OBJECT')
    eds = [ed for ed in shell.data.edges if ed.select]
    if len(eds) > 4:
        odcutils.fill_loop_scale(shell, eds, .3, debug = False)
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
    bpy.ops.object.mode_set(mode = 'EDIT')
        
    # select the filled_hole group, select more, make a new group
    bpy.ops.object.vertex_group_set_active(group = 'filled_hole')
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_more()
    n = len(shell.vertex_groups)
    bpy.ops.object.vertex_group_assign_new()
    shell.vertex_groups[n].name = "Tissue"
    bpy.ops.mesh.select_less()
    
    mx = shell.matrix_world
    me = shell.data    
    if p_type == 'OVATE':    
        #region to loop and #find the COM of said loop
        bpy.ops.mesh.region_to_loop()
        bpy.ops.object.mode_set(mode = 'OBJECT') #this updates the selection data...and does some other good stuff
        sel_verts = [v.index for v in me.vertices if v.select]
        
        COM = odcutils.get_com(me,sel_verts,mx)
    
        #get dimensions of loop (x,y)
    
        xs = [(mx*me.vertices[i].co)[0] for i in sel_verts]
        ys = [(mx*me.vertices[i].co)[1] for i in sel_verts]
        scale_x = (max(xs) - min(xs))/1.5
        scale_y = (max(ys) - min(ys))/1.5
    
        #add a sphere at COP
        context.scene.cursor_location = COM
        ov_loc = mx.inverted() * (COM + Vector((0,0,3)))
    
        current_objects=list(bpy.data.objects)                
        bpy.ops.mesh.primitive_uv_sphere_add(location = tuple(COM + Vector((0,0,3))))
        for o in bpy.data.objects:
            if o not in current_objects:
                #o.parent= Master #conside Master..but then you have to move them both #actually, dependency loop....sphere parent = pontic but pontic shrinkwrapped to sphere...problem.
                o.name = tooth.name + '_ovate'        
                Ovate = o
                Ovate.draw_type = 'WIRE'
            
        #pivot point at median point
        for A in bpy.context.window.screen.areas:
            if A.type == 'VIEW_3D':
                for s in A.spaces:
                    if s.type == 'VIEW_3D':
                        s.pivot_point = 'MEDIAN_POINT'
        #scale X
        scale_z = min([scale_x, scale_y])
        bpy.ops.transform.resize(value = (scale_x, scale_y, scale_z))

        #make pontic active and selected again
        bpy.ops.object.select_all(action = 'DESELECT')
        shell.select = True
        context.scene.objects.active = shell
    
        #shrinkwarp filled hole to this oval
        n=len(shell.modifiers)    
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        mod = shell.modifiers[n]
        mod.wrap_method='PROJECT'
        mod.vertex_group = "Tissue"       
        mod.use_negative_direction=True
        mod.use_positive_direction=False
        mod.use_project_z=True
        mod.offset=-0.2 #perhaps negative
        mod.target= Ovate
        mod.name="Ovate Pontic"
        mod.show_expanded=False
    
        for m in range(0,n):
            bpy.ops.object.modifier_move_up(modifier = "Ovate Pontic")
    
    bpy.ops.object.mode_set(mode='OBJECT') 
    
    if p_type == 'TISSUE':
        tissue = tooth.prep_model
        if tissue:
        
            Tissue = bpy.data.objects[tissue]
            #shrinkwarp filled hole to this oval
            n=len(shell.modifiers)    
            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            mod = shell.modifiers[n]
            mod.wrap_method='PROJECT'
            mod.vertex_group = "Tissue"        
            mod.use_negative_direction=True
            mod.use_positive_direction=True
            mod.use_project_z=True
            mod.offset=offset #perhaps negative
            mod.target= Tissue
            mod.name="Tissue Pontic"
            mod.show_expanded=False
        
            for m in range(0,n):
                print('move modifier up')
                bpy.ops.object.modifier_move_up(modifier = "Tissue Pontic")
    

        
    n=len(shell.modifiers)    
    bpy.ops.object.modifier_add(type='SMOOTH')
    mod = shell.modifiers[n]
    mod.vertex_group = "Tissue"        
    mod.iterations = 10
    mod.name="Pontic Smooth"
    mod.show_expanded=False
    
    if p_type == 'TISSUE':
        n = 2
    else:
        n = 1
        
    for i in range(0,n):
        bpy.ops.object.modifier_move_up(modifier = 'Pontic Smooth')

def prep_from_shell(context, shell, axis_mx, shoulder_width = .75, reduction = 1, base_res = .3, margin_loop = None, debug = False):
    '''
    shell: blender object representing tooth outer shell
    axis_mx = orientation matrix represneing the insertion axis of the prep
    shoulder_width = depth of axial inward step from margin perpendicular to insertion axis
    chamfer = angle of prep
    base_res = base resolution of mesh before multires subdivision
    margin_loop = blender bezier closed curve if none, uses nonmanifold edge of shell
    '''
    if debug:
        start = time.time()
        
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    #if loop: convert to mesh of resolution base_res
    current_obs = [ob for ob in bpy.data.objects]
    
    if margin_loop:
        if margin_loop.type != 'CURVE':
            print('failed, not a curve object')
            return {'CANCELLED'}
        context.scene.objects.active = margin_loop
        margin_loop.select = True
        margin_loop.hide = False
        bpy.ops.object.convert(target='MESH', keep_original=True)
    
    else:
        context.scene.objects.active = shell
        shell.select = True
        shell.hide = False
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        context.tool_settings.mesh_select_mode = [False,True,False]
        bpy.ops.mesh.select_non_manifold()
        bpy.ops.mesh.duplicate_move()
        bpy.ops.mesh.separate(type = 'SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        
    for ob in bpy.data.objects:
        if ob not in current_obs:
            prep = ob
            
            mx = prep.matrix_world.copy()
            
            for const in prep.constraints:
                prep.constraints.remove(const)
            
            prep.matrix_world = mx
            
            
            odcutils.reorient_object(prep, axis_mx)
    
    #snap in case multires is involved
    #hint..this op needs to be bmesh
    context.scene.update()
    if len(shell.modifiers):
        for v in prep.data.vertices:
            if bversion() < '002.077.000':
                v.co = prep.matrix_world.inverted() * shell.matrix_world * shell.closest_point_on_mesh(shell.matrix_world.inverted() * prep.matrix_world * v.co)[0]
            else:
                v.co = prep.matrix_world.inverted() * shell.matrix_world * shell.closest_point_on_mesh(shell.matrix_world.inverted() * prep.matrix_world * v.co)[1]
    context.scene.update()           
    bpy.ops.object.select_all(action='DESELECT')
    context.scene.objects.active = prep
    prep.select = True
    
    #remove modifiers
    for mod in prep.modifiers:
        if mod.type not in {'MULTIRES', 'SUBSURF'}:
            
            bpy.ops.object.modifier_apply(modifier = mod.name)
        else:
            bpy.ops.object.modifier_remove(modifier = mod.name)
    
    #clean out the vertex groups
    bpy.ops.object.vertex_group_remove(all = True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=base_res)
    bpy.ops.mesh.select_all(action='SELECT')
    
    bpy.ops.mesh.extrude_edges_move()
    bpy.context.tool_settings.mesh_select_mode = [True, False, False]
    bpy.ops.object.mode_set(mode='OBJECT')
    #bpy.ops.object.editmode_toggle()
    sel_eds = [ed for ed in prep.data.edges if ed.select]
    loc_z = axis_mx.to_quaternion() * Vector((0,0,1))
    odcutils.extrude_edges_in(prep.data, sel_eds, prep.matrix_world, loc_z, shoulder_width*.9, debug=debug)
    bpy.ops.object.editmode_toggle()
    
    
    bpy.ops.mesh.extrude_edges_move()
    bpy.ops.object.mode_set(mode='OBJECT')
    #bpy.ops.object.editmode_toggle()
    sel_eds = [ed for ed in prep.data.edges if ed.select]
    loc_z = axis_mx.to_quaternion() * Vector((0,0,1))
    odcutils.extrude_edges_in(prep.data, sel_eds, prep.matrix_world, loc_z, shoulder_width*.1, debug=debug)
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    sel_eds = [ed for ed in prep.data.edges if ed.select]
    odcutils.fill_loop_scale(prep, sel_eds, base_res, debug=debug)
    bpy.ops.mesh.select_all(action = 'SELECT')
    bpy.ops.mesh.normals_make_consistent(inside = False)
    
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold(extend = False)
    n = len(prep.vertex_groups)
    bpy.ops.object.vertex_group_assign_new()
    prep.vertex_groups[n].name = 'Margin'
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    
    #project up onto shell
    n=len(prep.modifiers)            
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    mod = prep.modifiers[n]
    mod.wrap_method='PROJECT'
    mod.vertex_group = 'filled_hole'       
    mod.use_negative_direction=False
    mod.use_positive_direction=True
    mod.use_project_z=True
    mod.offset = -1*reduction        
    mod.target=shell
    mod.cull_face = 'OFF'
    mod.name = "Occlusal Reduction"
    
    #multires?
    bpy.ops.object.modifier_add(type='MULTIRES')
    for i in range(0,3):
        bpy.ops.object.multires_subdivide(modifier="Multires")

    if debug:
        print("calced prep from shell in %f seconds" % (time.time() - start))
        
    return prep

def calc_intaglio(context, sce, tooth, chamfer, gap, holy_zone, no_undercuts = True, debug = False):

    #Get ahold of all relevant tooth items
    margin = tooth.margin
    prep = tooth.prep_model
    axis = tooth.axis
    restoration = tooth.contour #TODO make sure this is  handled later
    pmargin = tooth.pmargin
    
    Prep = bpy.data.objects[prep]
    prep_bvh = BVHTree.FromObject(Prep, sce)
    prep_imx = Prep.matrix_world.inverted()
    prep_mx = Prep.matrix_world
    
    Margin = bpy.data.objects[margin]
    margin_mx = Margin.matrix_world
    
    Axis = bpy.data.objects[axis]
    #we wil use these to control our translations
    axis_quat = Axis.matrix_world.to_quaternion()
    axis_mx = Axis.matrix_world
    axis_imx = axis_mx.inverted()
    axis_z = axis_quat * Vector((0,0,1))
    
    Restoration = bpy.data.objects[restoration]
    mx = Restoration.matrix_world
    imx = Restoration.matrix_world.inverted()
    
    #rays transform straightforward inverse, unsure on normals
    local_z = imx.to_3x3() * axis_z
    local_z.normalize()
    
    #get the non manifold edge of the crown and delete all other geometry 
    intag_bme = bmesh.new()
    intag_bme.from_object(Restoration, context.scene)
    intag_bme.verts.ensure_lookup_table()
    intag_bme.edges.ensure_lookup_table()
    
    non_man_eds = [ed for ed in intag_bme.edges if not ed.is_manifold]
    non_man_verts = set()
    for ed in non_man_eds:
        non_man_verts.add(ed.verts[0])
        non_man_verts.add(ed.verts[1])
    
    to_del = [v for v in intag_bme.verts if v not in non_man_verts]        
    bmesh.ops.delete(intag_bme, geom = to_del, context = 1)
    
    intag_bme.edges.ensure_lookup_table()
    intag_bme.verts.ensure_lookup_table()
    
    #space the margin out evenly
    loops = edge_loops_from_bmedges(intag_bme, [ed.index for ed in non_man_eds])
    
    if len(loops) > 1:
        print('you had another hole in your tooth, go see a dentist')
        print('there can not be any holes in the tooth mesh for this step')
        return
    
    vs = [intag_bme.verts[i] for i in loops[0][:-1]]
    eds = [(0,1),(1,0)]  #fake edges...makes them cyclic
    vert_path = [v.co for v in vs] + [vs[0].co] #cyclic for space evenly calculation
    spaced_coords, eds = space_evenly_on_path(vert_path, eds, len(vert_path)-1 , shift = 0, debug = False)
    
    for i, loc in enumerate(spaced_coords):
        vs[i].co = loc

    #extrude the edge perpendicular to insertion axis the holy zone width and maintain quads
    min_ed = min(non_man_eds, key = lambda ed: ed.calc_length())
    offset = min(.03, .75*min_ed.calc_length())
    
    print('offset is %f' % offset)
    print('holy zone width is %f' % holy_zone)
    print('%i edge loops in holy zone' % math.ceil(holy_zone/offset))
    
    hz_verts = []
    new_bmedges = non_man_eds
    for i in range(0, math.ceil(holy_zone/offset)):
        ret = bmesh.ops.extrude_edge_only(intag_bme, edges = new_bmedges, use_select_history = False)
        new_bmverts = [ele for ele in ret['geom'] if isinstance(ele, bmesh.types.BMVert)]
        hz_verts += new_bmverts
        
        new_bmedges = [ele for ele in ret['geom'] if isinstance(ele, bmesh.types.BMEdge)]
        new_bmfaces = [ele for ele in ret['geom'] if isinstance(ele, bmesh.types.BMFace)]
    
    
        offset_bmesh_edge_loop(intag_bme, [ed.index for ed in new_bmedges], local_z, offset, debug = False)
        
        loops = edge_loops_from_bmedges(intag_bme, [ed.index for ed in new_bmedges])
        vs = [intag_bme.verts[i] for i in loops[0]]
        fake_eds = [(0,1),(1,0)]
        vert_path = [v.co for v in vs] #cyclic for space evenly calculation
        spaced_coords, eds = space_evenly_on_path(vert_path, fake_eds, len(vert_path)-1 , shift = 0, debug = False)
    
        for n, loc in enumerate(spaced_coords):
            co = loc + 1.5 * chamfer * offset * local_z
            snap, no, ind, d = prep_bvh.find_nearest(prep_imx*mx*co)
            vs[n].co = imx * prep_mx * snap
            
        if i == 0:
            #get faces oreinted correctly on first pass
            print('recalcing normals')
            bmesh.ops.recalc_face_normals(intag_bme, faces = new_bmfaces)
    
    
    bmeds_inds = [ed.index for ed in new_bmedges]
    filled_vs = odcutils.fill_bmesh_loop_scale(intag_bme, bmeds_inds, 2 * offset, debug = False)
    intag_bme.verts.index_update()
    for v in filled_vs:
        v.co += 15 * local_z
    
    hz_inds = [v.index for v in hz_verts]
    filled_inds = [v.index for v in filled_vs]

    print('there are %i HZ inds' % len(hz_inds))
    print('there are %i filled inds' % len(filled_inds))
    intag_me = bpy.data.meshes.new(tooth.name +'_intaglio')
    intag_ob = bpy.data.objects.new(tooth.name + 'intaglio', intag_me)
    intag_ob.matrix_world = mx
    intag_bme.to_mesh(intag_me)
    
    #change intag local coords so that local z is aligned to
    #insertion axis.
    intag_ob.data.transform(mx.to_3x3().to_4x4())
    intag_ob.data.transform(axis_imx.to_3x3().to_4x4())
    intag_ob.matrix_world = axis_mx.to_3x3().to_4x4()
    intag_ob.location = mx.to_translation()
        
    context.scene.objects.link(intag_ob)
    context.scene.objects.active = intag_ob
    intag_ob.select = True 
    
    hz_group = intag_ob.vertex_groups.new(name = 'Holy Zone')
    hz_group.add(hz_inds, 1, 'ADD')
    
    filled_group = intag_ob.vertex_groups.new(name = 'Filled Zone')
    
    #weird bug where vert group has verts alread in it!
    
    filled_group.remove([v.index for v in intag_ob.data.vertices])
    filled_group.add(filled_inds, 1, 'ADD')
    
    mod = intag_ob.modifiers.new('Project Undercuts', 'SHRINKWRAP')
    mod.wrap_method = 'PROJECT'
    mod.use_negative_direction = True
    mod.use_positive_direction = False
    mod.use_project_z = True
    mod.target = Prep
    mod.vertex_group = 'Filled Zone'
    
    if no_undercuts:
        mod = intag_ob.modifiers.new('Smooth', 'SMOOTH') 
        mod.iterations = 20
        mod.vertex_group = 'Filled Zone'
    
    mod = intag_ob.modifiers.new('Cement Gap', 'SHRINKWRAP')
    mod.wrap_method = 'NEAREST_SURFACEPOINT'
    mod.target = Prep
    mod.vertex_group = 'Filled Zone'
    mod.offset = gap
    mod.use_keep_above_surface = True
    
    Restoration.hide = True
    tooth.intaglio = intag_ob.name
    intag_bme.free()
    del prep_bvh
    return  
           
def calc_intaglio2(context, sce, tooth, chamfer, gap, holy_zone, debug = False):
    if debug:
        start = time.time()
    #Get ahold of all relevant tooth items
    margin = tooth.margin
    prep = tooth.prep_model
    axis = tooth.axis
    restoration = tooth.contour #TODO make sure this is  handled later
    pmargin = tooth.pmargin
    master = sce.odc_props.master
    
    
    Margin = bpy.data.objects[margin]
    Prep = bpy.data.objects[prep]
    Axis = bpy.data.objects[axis]
    Restoration = bpy.data.objects[restoration]
    Psuedomargin = bpy.data.objects[pmargin]
    
    #we wil use these to control our translations
    axis_quat = Axis.matrix_world.to_quaternion()
    axis_z = axis_quat * Vector((0,0,1))
    
    #take control of the scene TODO:consider overriding context
    bpy.ops.object.select_all(action='DESELECT')
    current_objects=list(bpy.data.objects)
    Restoration.hide = False
    sce.objects.active=Restoration
    Restoration.select = True
    
    #we want to make a temporary copy of the resoration so that
    #we can apply all the dynamic modifiers but still have the option
    #to go back and make changes if necessary.        
    bpy.ops.object.duplicate()
    
    intaglio=str(tooth.name + "_Intaglio")
    for o in bpy.data.objects:
        if o not in current_objects:
            o.name=intaglio
            o.parent= sce.objects[master]
            
    bpy.ops.object.select_all(action='DESELECT')
    Intaglio = bpy.data.objects[intaglio] 
    sce.objects.active=Intaglio
    Intaglio.select = True
    
    bpy.ops.object.multires_base_apply(modifier="Multires")
    
    

    #make sure local z is aligned with insertion axis
    orientation = Axis.matrix_world
    odcutils.reorient_object(Intaglio,orientation)
    
    #save these for later.  Currently multires level 3 is th
    #all that is needed but I want to keep the option open
    #to let the user define the amount of precision.
    multires_cuts = Restoration.modifiers['Multires'].levels 
    bpy.ops.object.modifier_remove(modifier="Multires")
    for mod in Intaglio.modifiers:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    
    #clean out the vertex groups
    bpy.ops.object.vertex_group_remove(all = True)
 
    sce.objects.active=Intaglio
    Intaglio.select=True
    Restoration.hide=False
    
    #Keep just the free edge of the of resoration to use as a starting ppint
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.context.tool_settings.mesh_select_mode = [False, True, False]
    bpy.ops.mesh.select_non_manifold()        
    bpy.context.tool_settings.mesh_select_mode = [True, False, False]
    bpy.ops.mesh.select_all(action="INVERT")
    bpy.ops.mesh.delete()
    
    me = Intaglio.data
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')

    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    sel_edges=[e for e in me.edges if e.select == True]
    odcutils.extrude_edges_in(me, sel_edges, Intaglio.matrix_world, axis_z, .02, debug = debug)
    

    bpy.ops.mesh.extrude_edges_move()

    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()  #this is to update the selected vertices
           
    sel_edges=[e for e in me.edges if e.select == True]
    sel_verts=[v for v in me.vertices if v.select == True]
    
    odcutils.extrude_edges_in(me, sel_edges, Intaglio.matrix_world, axis_z, holy_zone)
    bpy.ops.transform.translate(value = holy_zone*chamfer*2*axis_z)
          
    n = len(Intaglio.vertex_groups)
    bpy.ops.object.vertex_group_assign_new()
    Intaglio.vertex_groups[n].name = 'Holy Zone'
    
    bpy.ops.object.editmode_toggle() #Back out to object mode
    
    n = len(Intaglio.modifiers)
    bpy.ops.object.modifier_add(type = 'SHRINKWRAP')
    mod = Intaglio.modifiers[n]
    mod.target = Prep
    mod.vertex_group = 'Holy Zone'
    mod.wrap_method = 'NEAREST_SURFACEPOINT'
    
    bpy.ops.object.modifier_apply(modifier = mod.name)        
    
    bpy.ops.object.editmode_toggle()  #this is to update the selected vertices 

    sel_edges=[e for e in me.edges if e.select == True]
    
    odcutils.fill_loop_scale(Intaglio, sel_edges, .3 , debug = debug)  #is this a good scale??.3^3 = 1/27mm
    
    bpy.ops.object.vertex_group_select() #active group is 'filled hole'
    bpy.ops.transform.translate(value = 10* axis_z)
    
    bpy.ops.mesh.select_all(action="INVERT")        
    bpy.ops.transform.translate(value = .5 * axis_z)
    
    #Make normals consistent, very important for projections
    #and upcoming modifiers
    bpy.ops.mesh.select_all(action = 'SELECT')
    bpy.ops.mesh.normals_make_consistent()      
    bpy.ops.object.mode_set(mode='OBJECT')
    
    #Project down and then lift off the intaglio
    #Think of this as teasing on/off an acrylic temporary
    n=len(Intaglio.modifiers)            
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    mod = bpy.context.object.modifiers[n]
    mod.wrap_method='PROJECT'
    mod.vertex_group = 'filled_hole'       
    mod.use_negative_direction=True
    mod.use_positive_direction=False
    mod.use_project_z=True
    mod.offset = 8            
    mod.target=Prep
    mod.cull_face = 'BACK'
    mod.name = "Initial Projection"
    
          
    #give the margin back it's v.group
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.mesh.select_non_manifold()
    
    bpy.context.tool_settings.vertex_group_weight = 1
    n = len(Intaglio.vertex_groups)
    bpy.ops.object.vertex_group_assign_new()
    Intaglio.vertex_groups[n].name = margin
    bpy.ops.object.mode_set(mode='OBJECT')

    #Subdivide to the same level as the Restoration
    bpy.ops.object.modifier_add(type = 'MULTIRES')        
    for i in range(0,int(multires_cuts)):
        bpy.ops.object.multires_subdivide(modifier = 'Multires')
    
    
    #Apply both modifiers and fix some vertex groups weights
    #note. vertex groups 'grow' during multires subdivision
    for mod in Intaglio.modifiers:
        bpy.ops.object.modifier_apply(modifier = mod.name)
    
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.vertex_group_set_active(group = 'filled_hole')
    bpy.ops.object.vertex_group_select()
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    bpy.ops.object.vertex_group_set_active(group = 'Holy Zone')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.vertex_group_select()
    sce.tool_settings.vertex_group_weight = 1
    bpy.ops.object.vertex_group_assign()
    
    bpy.ops.object.mode_set(mode = 'OBJECT')  
       
    #poject the high res mesh onto the prep   
    n=len(Intaglio.modifiers)            
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    mod = bpy.context.object.modifiers[n]
    mod.wrap_method='PROJECT'        
    mod.use_negative_direction=True
    mod.use_positive_direction=False
    mod.use_project_z= True         
    mod.target= Prep
    mod.auxiliary_target = Psuedomargin
    mod.name = "Final Seat"
    
    #Snap The Edge to the Margin
    n=len(Intaglio.modifiers)                    
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    mod = Intaglio.modifiers[n]
    mod.name = 'Marginal Seal'
    mod.vertex_group = margin
    mod.wrap_method='NEAREST_VERTEX'                  
    mod.target=Margin
    
    #Seal the holy zone to the prep        
    n=len(Intaglio.modifiers)                    
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    mod = Intaglio.modifiers[n]
    mod.name = 'HZ Seal'
    mod.vertex_group = 'Holy Zone'
    mod.wrap_method='NEAREST_SURFACEPOINT'
    mod.use_keep_above_surface = True                
    mod.target=Prep
    
    #Establish the Cement Gap
    n = len(Intaglio.modifiers)
    bpy.ops.object.modifier_add(type = 'SHRINKWRAP')        
    mod = Intaglio.modifiers[n]
    
    mod.name = 'Cement Gap'
    mod.offset = gap                
    mod.vertex_group = 'filled_hole'
    mod.wrap_method = 'NEAREST_SURFACEPOINT'
    mod.use_keep_above_surface = True
    mod.target = Prep
    
    #Apply the "final seat" modifier because it is direction dependent
    #and we do not want further rotations to affect it.
    bpy.ops.object.modifier_apply(modifier="Final Seat")
    
    Restoration.hide = True
    tooth.intaglio = intaglio

    
    #for a in bpy.context.window.screen.areas:
    #    if a.type == 'VIEW_3D':
    #        for s in a.spaces:
    #            if s.type == 'VIEW_3D':
    #                if not s.local_view:
    #                    bpy.ops.view3d.localview()
                
    if tooth.bubble:
        Bubble = sce.objects[tooth.bubble]
        Bubble.hide = True  
        
    if debug:
        print("calced intaglio in %f seconds" % (time.time() - start))  
 

def cervical_convergence_improved(context, tooth, angle, selected = False, debug = False):
    
    if debug:
        start = time.time()
    
    sce = context.scene
    restoration=tooth.contour #TODO:...put this back to restoration after get crown form is all tidied up.
    axis = tooth.axis
    
    Axis = bpy.data.objects[axis]
    Restoration=bpy.data.objects[restoration]
    matrix1 = Restoration.matrix_world
    
    bpy.ops.object.select_all(action='DESELECT')
    Restoration.hide = False
    Restoration.select = True
    sce.objects.active = Restoration
    
    #find the margin.
    bpy.ops.object.mode_set(mode = 'EDIT')
    context.tool_settings.mesh_select_mode = [True, False, False]
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.mesh.select_non_manifold()

    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle() #ob
    
    Restoration=bpy.data.objects[restoration]
    vs = Restoration.data.vertices
    margin_verts = set([v.index for v in vs if v.select])  #unordere set
    
    
    if debug > 1:
        print(margin_verts)
        print("#######################")
        print("Margin verts selected at %f" % (start - time.time()))
    #print(margin_verts)
    ###  Additionally Select the Next Loop (but not connecting edges)
    
    bpy.ops.object.editmode_toggle() #ed
    bpy.ops.mesh.select_more()
    
    bpy.ops.object.editmode_toggle() #ob
    #make a set of all the keys for the selected edges
    #later we will subtract circumfrential edges to 
    #acvieve just vertical edges
    v_edges = {e.key for e in Restoration.data.edges if e.select}
    
    #select just the loops
    bpy.ops.object.editmode_toggle() #ed
    context.tool_settings.mesh_select_mode = [False, True, False]
    bpy.ops.mesh.region_to_loop()
    
    ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle() #ob

    eds = [e for e in Restoration.data.edges if e.select]
    loops = edge_loops_from_edges(Restoration.data, eds)
    exclude_edges = {e.key for e in eds}  #a set of the the circumfrential loops edges
    
    if loops[0][0] in margin_verts:
        ring_vert_loop = loops[1]
        margin_vert_loop = loops[0]
    else:
        ring_vert_loop = loops[0]
        margin_vert_loop = loops[1]  
    margin_vert_loop.pop()
    ring_vert_loop.pop()
    
    
    margin_set = set(margin_vert_loop)
    ring_set = set(ring_vert_loop)
    
    vertical_edge_set = v_edges - exclude_edges
    
    if debug > 1:
        print(vertical_edge_set)
        print(margin_set)
        print(ring_set)
    
    n = 0
    #ed = vertical_edge_set.pop()
    for ed in vertical_edge_set:  #this should only take one try..perhaps pop one item out and try is.
        vert1 = set(ed) & margin_set
        vert2 = set(ed) & ring_set
        
        if debug > 1:
            print(vert1)
            print(vert2)
        if vert1 and vert2:
            
            #identify the indices in the loops
            #reverse mapping from mesh vert index to edge_loop list index
            
            indx_1 = margin_vert_loop.index(list(vert1)[0])  #index in edge_loop list
            indx_2 = ring_vert_loop.index(list(vert2)[0])
            
            #need to test if the lists are reversed relative to each other
            #y seeing if the verts one behind in the list also form an 
            #existing vertical edge in the mesh.
            test_edge_key = margin_vert_loop[indx_1 -1], ring_vert_loop[indx_2-1]
            test_edge_key1 = test_edge_key[1], test_edge_key[0]  #possible that (a,b) isnt in the list but (b,a) is
            
            if not (test_edge_key in vertical_edge_set) or (test_edge_key1 in vertical_edge_set):
                ring_vert_loop.reverse()
                indx_2 = ring_vert_loop.index(list(vert2)[0]) #need to find the new index...we could do math...but why
            
            ring_vert_loop = odcutils.list_shift(ring_vert_loop, indx_2 - indx_1)
            #offsets[i] = offsets[i-1] + indx_2 - indx_1
            if debug > 2:
                print('found linK in %d iterations' % n)
                print("         ")
                print(ring_vert_loop)
                print("       ")
                print(margin_vert_loop)
            
            break
        n += 1


    
    ### iterate thourhg and translate the top vertex of each vertical edge
    ### to make the proper angle of cervical convergence.
    insertion_z = Axis.matrix_world.to_quaternion() * Vector((0,0,1))
    local_z = matrix1.to_quaternion().inverted() * insertion_z
    local_z.normalize()
    me = Restoration.data
    
    for i in range(0,len(margin_vert_loop)):
        
        bot = margin_vert_loop[i]
        tp = ring_vert_loop[i]
        
        
        v1 = me.vertices[bot].co
        v2 = me.vertices[tp].co
        
        normal = me.vertices[tp].normal  #lets presume all the normals are right
        
        edge_v = v2 - v1
        
        if debug > 1:
            print(bot)
            print(tp)
            print(edge_v.length)
        
            
        #A = edge_v.normalized()

        # keep in mind, axis is important for direction...rotated z down to a
        # meaning positive angles rotate away from z and toward A
        #if A is inside of the  z axis...it will rotate inside
        #may need to do some ccw, cs test on the margin loop or
        #use normals....lets just test and see what happens.
        axis = local_z.cross(normal) 
        axis.normalize()
        
        sin = math.sin(angle/2)
        cos = math.cos(angle/2)
    
        quat = Quaternion((cos, sin*axis[0], sin*axis[1], sin*axis[2]))
        quat.normalize()
        vec = edge_v.length * local_z
        me.vertices[tp].co = v1 + quat * vec
        
        #print('translating' + str(trans))
        context.tool_settings.mesh_select_mode = [True, False, False]
    if debug:
        finish = time.time() - start    
        print('completed cerv convergnce in %f seconds' % finish)


def seat_to_margin_improved(context, sce, tooth, influence, debug = False):
    if debug:
        start = time.time()
        
    contour = tooth.contour
    margin = tooth.margin
    
    Restoration = bpy.data.objects[contour]
    Margin = bpy.data.objects[margin]
    
    restoration_mx = Restoration.matrix_world
    margin_mx = Margin.matrix_world
    
    Restoration.hide = False
    Restoration.select = True
    sce.objects.active = Restoration
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Ensure non manifold edge is the margin of the crown and that it is
    #grouped correctly in case the mesh has been altered from its original
    #topology.
    if margin in bpy.context.object.vertex_groups: #dependent on name being the same
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.object.vertex_group_set_active(group = margin)
        bpy.ops.object.vertex_group_remove_from()        
    
    
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle() #object
    bpy.ops.object.editmode_toggle() #edit
    sce.tool_settings.vertex_group_weight = 1
    if margin not in Restoration.vertex_groups:
        n=len(Restoration.vertex_groups)
        bpy.ops.object.vertex_group_assign_new()
        Restoration.vertex_groups[n].name = margin
    else:
        bpy.ops.object.vertex_group_set_active(group = margin)
        bpy.ops.object.vertex_group_assign()
    
    #method is as follows
    #I..get edge loops for rings from margin to equator
    bpy.ops.object.mode_set(mode='OBJECT')
    eds = [e for e in Restoration.data.edges if e.select]
    margin_verts = edge_loops_from_edges(Restoration.data, eds)[0]
    margin_verts.pop() #get rid of the last one
    

    bpy.ops.object.vertex_group_set_active(group = 'Equator')
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.object.vertex_group_select()
    
    
    #The next operator will leav us with the enture
    #bottom half of the tooth selected
    bpy.ops.mesh.loop_to_region()
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.mode_set(mode='OBJECT')
    seat_region_verts = [v for v in Restoration.data.vertices if v.select]
    
    #we will make a set of all the edge vertex indices...and remove the
    #circumfrential edges so we can test vertical edges later
    vertical_edge_set = set([e.key for e in Restoration.data.edges if e.select])


    n_verts_loop = len(margin_verts)
    n_loops = int(len(seat_region_verts)/n_verts_loop)
    if debug ==2:
        print("there are %d verts in the margin loop" % len(margin_verts))
        
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    region_loops = [None]*n_loops
    region_loops[0] = margin_verts
    
    sce.tool_settings.mesh_select_mode = [False, True, False]
    
    
    for n in range(0,n_loops-1):
        
        bpy.ops.mesh.region_to_loop()
        
        bpy.ops.object.mode_set(mode='OBJECT')
        eds = [e for e in Restoration.data.edges if e.select]
        
        #we take out the horzontal edges at each iteration
        #leaving us with just the vertical edgse
        horizotal_edge_set = set(e.key for e in eds)
        vertical_edge_set -= horizotal_edge_set
        
        loops = edge_loops_from_edges(Restoration.data, eds)
        if loops[1][0] not in margin_verts:
            loop_index = 1
        else:
            loop_index = 0
        loops[loop_index].pop()
        region_loops[n_loops-(n+1)] = loops[loop_index]
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.loop_to_region() 
        bpy.ops.mesh.select_less()

    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    Restoration.data.vertices[region_loops[-1][0]].select = True
    Restoration.data.vertices[region_loops[0][0]].select = True
    sce.tool_settings.mesh_select_mode = [True, False, False]
    #bpy.ops.object.mode_set(mode='EDIT')
    
    #This allows a shorter subset of edges to test for
    #vertical connections between our loops
    #but...blender has to test them all first, so is this
    #double work for computer, lazy work for programmer?
    #bpy.ops.mesh.select_vertex_path(type='EDGE_LENGTH')
    
    
    #bpy.ops.object.mode_set(mode='OBJECT')

    #find the links between them by making set's for fast a in b searches
    #we still have to know the indices so perhaps sticking with list comprehension
    #will be faster?  Will Test this. 
    link_ed_sets = [set(ed) for ed in vertical_edge_set]  #make each edge key a set
    loop_sets = [set(loop) for loop in region_loops] #because edges are vertical, we just want one index in the whole loop

    #bpy.ops.object.editmode_toggle()
    #bpy.ops.mesh.select_all(action = 'DESELECT')
    #bpy.ops.object.editmode_toggle()
    
    #offsets = [0]*(n_loops-1)
    for i in range(0, n_loops -1):
        for ed in link_ed_sets:
            vert1 = ed & loop_sets[i]
            vert2 = ed & loop_sets[i+1]
            

            if vert1 and vert2:
                if debug > 1:
                    print('found link between loops at %s and %s' % (str(vert1), str(vert2)))
                #identify the indices in the loops
                #reverse mapping from mesh vert index to edge_loop list index
                
                indx_1 = region_loops[i].index(list(vert1)[0])  #index in edge_loop list
                indx_2 = region_loops[i+1].index(list(vert2)[0])
                
                #need to test if the lists are reversed relative to each other
                #y seeing if the verts one behind in the list also form an 
                #existing vertical edge in the mesh.
                test_edge_key = region_loops[i][indx_1 -1], region_loops[i+1][indx_2-1]
                test_edge_key1 = test_edge_key[1], test_edge_key[0]  #possible that (a,b) isnt in the list but (b,a) is
                
                if (test_edge_key not in vertical_edge_set) and (test_edge_key1 not in vertical_edge_set):
                    region_loops[i+1].reverse()
                    if debug:
                        print("reversing list")
                    indx_2 = region_loops[i+1].index(list(vert2)[0]) #need to find the new index...we could do math...but why
                
                if debug:
                    print("shifting list by %i" % (indx_2 - indx_1))
                region_loops[i+1] = odcutils.list_shift(region_loops[i+1], indx_2 - indx_1)
                
                if debug > 1:
                    for loop in region_loops:
                        print(loop)
                #offsets[i] = offsets[i-1] + indx_2 - indx_1
                break
            
    if debug > 1:
        for loop in region_loops:
            print(loop)
            
    crown_margin_com = odcutils.get_com(Restoration.data, region_loops[0], restoration_mx)  
    margin_com = odcutils.get_bbox_center(Margin, world = True)
    delta = restoration_mx.to_3x3().inverted() * (margin_com - crown_margin_com)  #the difference in local coordinates of crown
    
    #TODO: is this faster or the old way?
    for ind in region_loops[0]:
        Restoration.data.vertices[ind].co += delta
    
    if margin not in Restoration.modifiers:
        n = len(Restoration.modifiers)    
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        mod = Restoration.modifiers[n]
        mod.wrap_method='NEAREST_VERTEX' 
        mod.name = margin
        mod.target = Margin
        mod.vertex_group = margin
        for i in range(0,n):
            bpy.ops.object.modifier_move_up(modifier=margin)
    else:
        mod = Restoration.modifiers[margin]
    
    current_mods = [mod.name for mod in Restoration.modifiers]
    bpy.ops.object.modifier_copy(modifier = margin)
    new_mod = [mod.name for mod in Restoration.modifiers if mod not in current_mods]
    bpy.ops.object.modifier_apply(modifier=new_mod[0])

    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    me = Restoration.data
    
    #iterate through the base margin loop
    for i in range(0,len(region_loops[0])):
        
        #location of vertex on margin loop
        margin_pt = me.vertices[region_loops[0][i]].co

        #corresponding vertex location
        equator_pt = me.vertices[region_loops[-1][i]].co  #equator indicies in the 
        #line connecting them
        vec = equator_pt - margin_pt
        
        #numer of segments between margin and equator
        #which is one more than the loops sgmenting the
        #band between margin and equator
        segments = n_loops - 1
        for n in range(0,n_loops-2):
            loc = margin_pt + (n+1)/segments*vec
            me.vertices[region_loops[n+1][i]].co = loc
            
        
    #final seal after multires
    mod = Restoration.modifiers.new('Final Seal','SHRINKWRAP')
    mod.wrap_method='NEAREST_VERTEX' 
    mod.target = Margin
    mod.vertex_group = margin
      
    if debug:
        duration = time.time() - start
        print("seated to margin in %f seconds" % duration)
        
    return region_loops
               
                  
def seat_to_margin(context, sce, tooth, influence, debug = False):
    #TODO..investigate premolar seating issues
    #Get our relevant info
    #current times range .33 to .86 seconds per tooth! Too slow
    if debug:
        start = time.time()
    
    restoration = tooth.contour #TODO: feed this correct information
    margin = tooth.margin
    
    Restoration=bpy.data.objects[restoration]
    Margin = bpy.data.objects[margin]
    
    Restoration.hide = False
    Restoration.select = True
    sce.objects.active = Restoration
    
    #transform operators use world coordinates so we will need
    #access to the world matrices        
    matrix1=Restoration.matrix_world
    matrix2=Margin.matrix_world 
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Ensure non manifold edge is the margin of the crown and that it is
    #grouped correctly in case the mesh has been altered from its original
    #topology.
    if margin in bpy.context.object.vertex_groups:
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.object.vertex_group_set_active(group = margin)
        bpy.ops.object.vertex_group_remove_from()
        
        
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    if margin not in Restoration.vertex_groups:
        n=len(Restoration.vertex_groups)
        bpy.ops.object.vertex_group_assign_new()
        Restoration.vertex_groups[n].name = margin
    else:
        bpy.ops.object.vertex_group_set_active(group = margin)
        bpy.ops.object.vertex_group_assign()
    
    ####  Condense fill loops up to equator start ###
    #################################################
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    #only for testing
    #time.sleep(.5)
    #bpy.ops.wm.redraw()
    
    #count the number of vertices in the margin loop and therefore in
    #the equator loop and any fill loops in  between.
    Restoration=bpy.data.objects[restoration]
    vs = Restoration.data.vertices
    sverts = [v for v in vs if v.select]
    vperl = len(sverts)  #verts per loop
    if debug:
        print('there are ' + str(vperl) + ' verts in the loop')
    
    bpy.ops.object.vertex_group_set_active(group = 'Equator')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.loop_to_region()      
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    #only for testing
    #time.sleep(.5)
    #bpy.ops.wm.redraw()
    Restoration=bpy.data.objects[restoration]
    vs = Restoration.data.vertices
    sverts = [v for v in vs if v.select]
    print(str(len(sverts)))
    
    n_loops = len(sverts)/vperl - 2
    if debug:
        print('nloops is' + str(n_loops))
    
    
    if n_loops == 2:
        bpy.ops.object.vertex_group_set_active(group = margin)
        bpy.ops.object.vertex_group_deselect()    
        bpy.ops.mesh.select_less()
        
        
        ## ###Toggle for selection and groups to udpate #####
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
    
        
        #establish COM of loop to test which way to edge slide
        Restoration=bpy.data.objects[restoration]
        vs = Restoration.data.vertices
        sverts = [v for v in vs if v.select]
        svl = Vector((0,0,0))
        for v in sverts:
            svl= svl + v.co
        n = len(sverts)
        svl_i = matrix1 * (svl/n)
        
        bpy.ops.transform.edge_slide(value = .01)
        
        ## ###Toggle for selection and groups to udpate #####
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        
        #establish new COM of loop to test which way to edge slide
        Restoration=bpy.data.objects[restoration]
        vs = Restoration.data.vertices
        sverts = [v for v in vs if v.select]
        svl = Vector((0,0,0))
        for v in sverts:
            svl= svl + v.co
        n = len(sverts)
        svl_f = matrix1 * (svl/n)
        
        if svl_f[2] > svl_i[2]:
            bpy.ops.transform.edge_slide(value = .85)
        else:
            bpy.ops.transform.edge_slide(value = -.85)
            
        #only for testing
        #bpy.ops.wm.redraw()
        #time.sleep(.5)
        
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.vertex_group_set_active(group = margin)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_more()
    bpy.ops.object.vertex_group_deselect()
    Restoration=bpy.data.objects[restoration]
    vs = Restoration.data.vertices
    sverts = [v for v in vs if v.select]
    svl = Vector((0,0,0))
    for v in sverts:
        svl= svl + v.co
    n = len(sverts)
    svl_i = matrix1 * (svl/n)
    
    bpy.ops.transform.edge_slide(value = .01)
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    #only for testing        
    #bpy.ops.wm.redraw()
    #time.sleep(.5)
        
    #establish new COM of loop to test which way to edge slide
    Restoration=bpy.data.objects[restoration]
    vs = Restoration.data.vertices
    sverts = [v for v in vs if v.select]
    svl = Vector((0,0,0))
    for v in sverts:
        svl= svl + v.co
    n = len(sverts)
    svl_f = matrix1 * (svl/n)
    
    if svl_f[2] > svl_i[2]:
        bpy.ops.transform.edge_slide(value = .85)
    else:
        bpy.ops.transform.edge_slide(value = -.85)
    
    #only for testing        
    #bpy.ops.wm.redraw()
    #time.sleep(.5)
    
    ####  Condense fill loops up to equator ###
    ###############    End   ##################
    
    
    
    #Median of template margin match bbox cent marked margin #
    ######################  Start  ###########################
    
    #Get the bounding box center of the marked margin in world coordinates
    #(Does this require applying location/rotation to margin?        
    mbbc = Vector((0,0,0))
    for v in Margin.bound_box:
        mbbc = mbbc + matrix2 * Vector(v)
    Mbbc = mbbc/8
    
    ## Get the median point of the crown form margin
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()  
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    Restoration=bpy.data.objects[restoration]
    vs = Restoration.data.vertices
    
    #sverts: selected vertices
    sverts = [v for v in vs if v.select]
    
    #svl: selected vertices location
    svl = Vector((0,0,0))
    for v in sverts:
        svl= svl + v.co
    n = len(sverts)
    svl = matrix1 * (svl/n)
    
    #The tranform.translate operator takes a vector in world coords
    trans = Mbbc - svl
    trans = Vector((0,0,trans[2]))
    bpy.ops.transform.translate(value = trans)
    
    
    bpy.ops.transform.resize(value = (1.1, 1.1, 1.1))
    
    
    #Median of template margin match bbox cent marked margin #
    ######################  End  ###########################
             
    
    
    # Snap Crown form margin to closest marked margin point  #
    ######################  Start  ###########################
    
    
    
    #We don't know the indices of the vertices in the vertex group
    #This is my brute force way of keeping track of them for later
    #use
    
    vertex_list=[]
    vg = Restoration.vertex_groups[margin]
    vs = Restoration.data.vertices
    
    #TODO: get rid of list append for performance
    for v in vs:    
        for g in v.groups:
            if g.group == vg.index:
                vertex_list.append(v.index)
                
    if debug > 1:
        print(vertex_list)
    
    bpy.context.tool_settings.mesh_select_mode = [True,False,False]
    for b in vertex_list:
        
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        Restoration.data.vertices[b].select = True  #Select one vertex
        bpy.ops.object.editmode_toggle() 
    
        distancesmag=[]  #prepare a list of the distances to all the vertices in the other mesh
        distancesvec=[]  #Since i have to calculate this to calculate the distance i just save it in a list...poor memory management
        
        for v in Margin.data.vertices:
            distance = matrix2 * v.co - matrix1 * Restoration.data.vertices[b].co #calculate real world vector between objects
    
            distancesvec.append(distance)  #add that vector to a list
    
            #magnitude=sqrt(distance*distance)   #calculate the magnitude of that vector (eg, the distance)
            magnitude=distance.length
            
            distancesmag.append(magnitude)   #add that value to a list           
    
        smallest_distance=min(distancesmag)  #find the smallest distance (eg, the closest point)
        
        smallest_index=distancesmag.index(smallest_distance)
        
        translate=distancesvec[smallest_index]
    
    
        d_index=0
        for d in distancesmag:     #I need a good way to find the index of the smallest value. for now brute force
            if d == smallest_distance:
                translate=distancesvec[d_index]            
            d_index+=1
    
    
        bpy.ops.transform.translate(value=translate, constraint_axis=(False, False, False), mirror=False, proportional='ENABLED', proportional_edit_falloff='SMOOTH', proportional_size=influence+.01, snap=False, snap_target='ACTIVE', snap_align=False, release_confirm=True)            
        bpy.ops.mesh.hide()
        
    
    bpy.ops.mesh.reveal()
    
    # Snap Crown form margin to closest marked margin point #
    ######################  End   ###########################
    
    
    # Smooth between equator and margin        #
    ##############  Start   ####################
    
    
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.vertex_group_set_active(group = margin)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_more()
    bpy.ops.object.vertex_group_deselect()
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    
    Restoration=bpy.data.objects[restoration]
    vs = Restoration.data.vertices
    sverts = [v for v in vs if v.select]
    svl = Vector((0,0,0))
    for v in sverts:
        svl= svl + v.co
    n = len(sverts)
    svl_i =matrix1 * (svl/n) 
    
    bpy.ops.transform.edge_slide(value = .01)
    
    ## ###Toggle for selection and groups to udpate #####
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
        
    #establish new COM of loop to test which way to edge slide
    Restoration=bpy.data.objects[restoration]
    vs = Restoration.data.vertices
    sverts = [v for v in vs if v.select]
    svl = Vector((0,0,0))
    for v in sverts:
        svl= svl + v.co
    n = len(sverts)
    svl_f = matrix1 * (svl/n)
    
    if svl_f[2] < svl_i[2]:
        down = 1
    else:
        down = -1
        
        
    if n_loops == 2:
        bpy.ops.transform.edge_slide(value = down*.68)
        
    else:
        bpy.ops.transform.edge_slide(value = down*.52)
        
      
    if n_loops == 2:
        bpy.ops.mesh.select_all(action = 'DESELECT')
        
        bpy.ops.object.vertex_group_set_active(group = 'Equator')
        bpy.ops.object.vertex_group_select() 
        
        
        bpy.ops.object.vertex_group_set_active(group = margin)
        bpy.ops.object.vertex_group_select()
        
        bpy.ops.mesh.loop_to_region()
        bpy.ops.object.vertex_group_deselect()
            
        bpy.ops.mesh.select_less()
        
        
        ## ###Toggle for selection and groups to udpate #####
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        
        #establish COM of loop to test which way to edge slide
        Restoration=bpy.data.objects[restoration]
        vs = Restoration.data.vertices
        sverts = [v for v in vs if v.select]
        svl = Vector((0,0,0))
        for v in sverts:
            svl= svl + v.co
        n = len(sverts)
        svl_i = matrix1 * (svl/n)
        
        bpy.ops.transform.edge_slide(value = .01)
        
        ## ###Toggle for selection and groups to udpate #####
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        
        #establish new COM of loop to test which way to edge slide
        Restoration=bpy.data.objects[restoration]
        vs = Restoration.data.vertices
        sverts = [v for v in vs if v.select]
        svl = Vector((0,0,0))
        for v in sverts:
            svl= svl + v.co
        n = len(sverts)
        svl_f = matrix1 * (svl/n)
        
        if svl_f[2] < svl_i[2]:
            down = 1
            
        else:
            down = -1
            
        bpy.ops.transform.edge_slide(value = down*.45)    
         
    
    
    
    # Smooth between equator and margin        #
    ##############   End    ####################
    
    #Add Dynamic Margin Modifier Above Multires#
    ##############   Start  ####################
    
    n=len(bpy.context.object.modifiers)
    
    margin = tooth.margin
    
    if margin not in Restoration.modifiers:
            
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        mod = Restoration.modifiers[n]
        mod.wrap_method='NEAREST_VERTEX'        
        mod.offset=0
        mod.vertex_group=margin #the vertex group in the crown form and the name of the actual margin object are the same.
        mod.target=bpy.data.objects[margin]
        mod.name = margin
        mod.show_expanded=False
    
        for i in range(0,n):
            bpy.ops.object.modifier_move_up(modifier=margin)
    
    bpy.ops.object.editmode_toggle()  
    if debug:
        duration = time.time() - start
        print("seated to margin in %f seconds" % duration)

def make_solid_restoration(context, tooth, debug = False):
    
    if debug:
        start = time.time()
         
    sce = context.scene
    if  bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        

    restoration=tooth.contour  #TODO: fix restoration vs contour
    Restoration=bpy.data.objects[restoration]
    
    intaglio=tooth.intaglio
    Intaglio = bpy.data.objects[intaglio]
    
    bpy.ops.object.select_all(action='DESELECT')
    sce.objects.active = Restoration
    Restoration.select=True
    Restoration.hide=False
    Intaglio.select=True
    Intaglio.hide=False
            
    current_objects=list(bpy.data.objects)

    #duplicate both objects
    bpy.ops.object.duplicate()
    
    bpy.ops.object.select_all(action='DESELECT')
    
    #apply any and all modifiers to both
    for o in bpy.data.objects:
        if o not in current_objects:
            sce.objects.active=o
            o.select = True
            n = len(o.modifiers)
            for i in range(0,n):
                name = o.modifiers[0].name
                bpy.ops.object.modifier_apply(modifier=name)
                                    
    bpy.ops.object.join()
    
    Solid_Restoration = context.object   
    Solid_Restoration.name = tooth.name + "_SolidResetoration"
    tooth.solid = Solid_Restoration.name
    
    bpy.ops.object.mode_set(mode='EDIT')
    me = Solid_Restoration.data
    
    ### Weld the Two Parts together ###  (boolean modifier may be better depending on code?)
    
    bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    
    #figure out how many non manifold we have
    bpy.ops.object.mode_set(mode='OBJECT')       
    sel_verts = [v.index for v in me.vertices if v.select]
    bpy.ops.object.mode_set(mode='EDIT')
    
    #first weld all the very close verts at the resoution of the margin resolution
    bpy.ops.mesh.remove_doubles(threshold = .025)
    bpy.ops.mesh.select_all(action = 'DESELECT')
    
    res = .03
    n = 0
    
    while n < 5 and len(sel_verts) > 0:
         
        #select any remaining non manifold edges and try again after subdividing and using a larger merge
        bpy.context.scene.tool_settings.mesh_select_mode = [False, True, False]        
        bpy.ops.mesh.select_non_manifold()
        bpy.ops.mesh.subdivide()
        bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False] 
        bpy.ops.mesh.remove_doubles(threshold = res)
    
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.mesh.select_non_manifold()
    
        bpy.ops.object.mode_set(mode = 'OBJECT')
        sel_verts = [v.index for v in me.vertices if v.select]
        bpy.ops.object.mode_set(mode = 'EDIT')
        if debug > 1:
            print("%d non manifold verts remaining at iteration %d" % (len(sel_verts), n))
        res += .02
        n += 1
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode = 'OBJECT')    
    if debug:
        duration = start - time.time()
        print('Welded solid model for tooth %s in %f seconds' % (tooth.name, duration))


def make_solid_restoration2(context, tooth, debug = False):
    
    if debug:
        start = time.time()
         
    sce = context.scene
    if  bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        

    restoration=tooth.contour  #TODO: fix restoration vs contour
    Restoration=bpy.data.objects[restoration]
    
    intaglio=tooth.intaglio
    Intaglio = bpy.data.objects[intaglio]
    i_bme = bmesh.new()
    i_bme.from_object(Intaglio, context.scene)
    intag_bme = i_bme.copy()
    i_bme.free()
    
    intag_bme.edges.ensure_lookup_table()
    intag_bme.verts.ensure_lookup_table()
    intag_bme.faces.ensure_lookup_table()
    
    #get modifier applied version of crown, without altering it!
    c_bme = bmesh.new()
    c_bme.from_object(Restoration, context.scene)
    crown_bme = c_bme.copy()
    c_bme.free()
    
    crown_bme.edges.ensure_lookup_table()
    crown_bme.verts.ensure_lookup_table()
    crown_bme.faces.ensure_lookup_table()                                
    
    
    for i in range(0,4):
        non_man_eds = [ed for ed in crown_bme.edges if not ed.is_manifold]
        bmesh.ops.delete(crown_bme, geom = non_man_eds, context = 2)
            
        non_man_vs = [v for v in crown_bme.verts if not v.is_manifold]
        bmesh.ops.delete(crown_bme, geom = non_man_vs, context = 1)
            
        #crown_bme.edges.ensure_lookup_table()
        #crown_bme.verts.ensure_lookup_table()
        #crown_bme.faces.ensure_lookup_table()
    crown_bme.verts.index_update()
    crown_bme.verts.ensure_lookup_table()
    
    #now that bottom rows deleted, join the intaglio data in
    join_bmesh_map(intag_bme, crown_bme, 
               src_trg_map = None,
               src_mx = Intaglio.matrix_world, 
               trg_mx = Restoration.matrix_world)
    
    
    crown_bme.verts.ensure_lookup_table()
    crown_bme.edges.ensure_lookup_table()
    crown_bme.faces.ensure_lookup_table()
    
    
    non_man = [ed for ed in crown_bme.edges if not ed.is_manifold]
    current_vs = set(crown_bme.edges)
    geom = bmesh.ops.bridge_loops(crown_bme, edges = non_man, use_pairs = True)
    new_faces = geom['faces']
    new_edges = geom['edges']
    
    ret = bmesh.ops.subdivide_edges(crown_bme, edges = new_edges, cuts = 3)#, interp_mode, smooth, cuts, profile_shape, profile_shape_factor)
    vs = [ele for ele in ret['geom_inner'] if isinstance(ele, bmesh.types.BMVert)]
    crown_bme.verts.ensure_lookup_table()
    vs_inds = [v.index for v in vs]
    
    
    bmesh.ops.recalc_face_normals(crown_bme, faces = crown_bme.faces[:])        
            
    #mesh bridge the ring around the margin
    solid_rest_me = bpy.data.meshes.new(tooth.name + "_SolidResetoration")
    Solid_Restoration = bpy.data.objects.new(tooth.name + "_SolidResetoration", solid_rest_me)  
    Solid_Restoration.matrix_world = Restoration.matrix_world
    
    crown_bme.to_mesh(solid_rest_me)
    tooth.solid = Solid_Restoration.name
    
    cej_group = Solid_Restoration.vertex_groups.new(name = 'CEJ')
    cej_group.remove([v.index for v in solid_rest_me.vertices]) #Vertex Group Bug
    cej_group.add(vs_inds, 1, 'ADD')
    
    context.scene.objects.link(Solid_Restoration)    
    
    
    mod = Solid_Restoration.modifiers.new('Shrink', 'SHRINKWRAP')
    mod.wrap_method = 'NEAREST_SURFACEPOINT'
    mod.target = Restoration
    mod.vertex_group = 'CEJ'
    
    
    
    if debug:
        duration = start - time.time()
        print('Welded solid model for tooth %s in %f seconds' % (tooth.name, duration))
    
    crown_bme.free()
    intag_bme.free()
                     
def check_contacts(context, tooth, min_d, max_d, debug = False):
    '''
    #TODO: docstring
    #TODO: pull occlusion and contact preferences from addon preferences
    '''
    if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    sce=bpy.context.scene
    ob_dict = {}
    
    if tooth.restoration:
        restoration=tooth.contour  #TODO: back to tooth.restoration
    elif tooth.contour:
        restoration=tooth.contour

    Restoration=bpy.data.objects[restoration]
    
    if tooth.opposing:
        Opposing = bpy.data.objects[tooth.opposing]
        ob_dict["Occlusion"] = Opposing
    if tooth.mesial:
        Mesial = bpy.data.objects[tooth.mesial]
        ob_dict["Mesial_check"] = Mesial
    if tooth.distal:
        Distal =  bpy.data.objects[tooth.distal]
        ob_dict["Distal_check"] = Distal
    
    sce.objects.active=Restoration
    Restoration.select=True
    
    #check and see if it has vertex group
    for key in ob_dict.keys():
        group = Restoration.vertex_groups.get(key)
        mod = Restoration.modifiers.get(key)

    
        if (not group) and (not mod):
            omod = odcutils.add_proximity_mod(Restoration, ob_dict[key], min_d, max_d, group_name = None)
            omod.name = key
            Restoration.vertex_groups["Proximity"].name = key
            omod.vertex_group = key
    
        if group and not mod:
            omod = odcutils.add_proximity_mod(Restoration, ob_dict[key], min_d, max_d, group_name = key)
    
        if group and mod: #perhaps I should overwrite them...eeeh, who knows.
            mod.min_dist = min_d
            mod.max_dist = max_d
        
  
def register():
    pass

def unregister():
    pass
            
if __name__ == "__main__":
    register()
    print('do something here?')