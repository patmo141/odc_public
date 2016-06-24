import bpy
import bmesh
from mathutils import Matrix, Vector


def join_bmesh_map(source, target, src_trg_map = None, src_mx = None, trg_mx = None):
    '''
    
    '''
    
 
    L = len(target.verts)
    
    if not src_trg_map:
        src_trg_map = {-1:-1}
    l = len(src_trg_map)
    print('There are %i items in the vert map' % len(src_trg_map))
    if not src_mx:
        src_mx = Matrix.Identity(4)
    
    if not trg_mx:
        trg_mx = Matrix.Identity(4)
        i_trg_mx = Matrix.Identity(4)
    else:
        i_trg_mx = trg_mx.inverted()
        
        
    old_bmverts = [v for v in target.verts]  #this will store them in order
    new_bmverts = [] #these will be created in order
    
    source.verts.ensure_lookup_table()

    for v in source.verts:
        if v.index not in src_trg_map:
            new_ind = len(target.verts)
            new_bv = target.verts.new(i_trg_mx * src_mx * v.co)
            new_bmverts.append(new_bv)  #gross...append
            src_trg_map[v.index] = new_ind
            
        else:
            print('vert alread in the map %i' % v.index)
    
    lverts = old_bmverts + new_bmverts
    
    target.verts.index_update()
    target.verts.ensure_lookup_table()
    
    new_bmfaces = []
    for f in source.faces:
        v_inds = []
        for v in f.verts:
            new_ind = src_trg_map[v.index]
            v_inds.append(new_ind)
            
        if any([i > len(lverts)-1 for i in v_inds]):
            print('impending index error')
            print(len(lverts))
            print(v_inds)
            
        if target.faces.get(tuple(lverts[i] for i in v_inds)):
            print(v_inds)
            continue
        new_bmfaces += [target.faces.new(tuple(lverts[i] for i in v_inds))]
    
        target.faces.ensure_lookup_table()
    target.verts.ensure_lookup_table()

    new_L = len(target.verts)
    
    if src_trg_map:
        if new_L != L + len(source.verts) -l:
            print('seems some verts were left in that should not have been')
 
def join_bmesh(source, target, src_mx = None, trg_mx = None):

    src_trg_map = dict()
    L = len(target.verts)
    if not src_mx:
        src_mx = Matrix.Identity(4)
    
    if not trg_mx:
        trg_mx = Matrix.Identity(4)
        i_trg_mx = Matrix.Identity(4)
    else:
        i_trg_mx = trg_mx.inverted()
        
        
    new_bmverts = []
    source.verts.ensure_lookup_table()

    for v in source.verts:
        if v.index not in src_trg_map:
            new_ind = len(target.verts)
            new_bv = target.verts.new(i_trg_mx * src_mx * v.co)
            new_bmverts.append(new_bv)
            src_trg_map[v.index] = new_ind
    
    
    target.verts.index_update()
    target.verts.ensure_lookup_table()

    new_bmfaces = []
    for f in source.faces:
        v_inds = []
        for v in f.verts:
            new_ind = src_trg_map[v.index]
            v_inds.append(new_ind)
            
        new_bmfaces += [target.faces.new(tuple(target.verts[i] for i in v_inds))]
    
    target.faces.ensure_lookup_table()
    target.verts.ensure_lookup_table()
    target.verts.index_update()
    
   
    target.verts.index_update()        
    target.verts.ensure_lookup_table()
    target.faces.ensure_lookup_table()
    
    new_L = len(target.verts)
    

    if new_L != L + len(source.verts):
        print('seems some verts were left out')
            
           
def join_objects(obs, name = ''):
    '''
    uses BMesh to join objects.  Advantage is that it is context
    agnostic, so no editmoe or bpy.ops has to be used.
    
    Args:
        obs - list of Blender objects
    
    Returns:
        new object with name specified.  Otherwise '_joined' will
        be added to the name of the first object in the list
    '''
    target_bme = bmesh.new()
    target_bme.verts.ensure_lookup_table()
    target_bme.faces.ensure_lookup_table()
    trg_mx = obs[0].matrix_world
    if name == '':
        name = obs[0].name + '_joined'
    
    for ob in obs:
        src_mx = ob.matrix_world

        if ob.data.is_editmode:
            src_bme = bmesh.from_editmesh(ob.data)
        else:
            src_bme = bmesh.new()
            src_bme.from_mesh(ob.data)
             
        join_bmesh(src_bme, target_bme, src_mx, trg_mx)

        src_bme.free()
    
    new_me = bpy.data.meshes.new(name)    
    new_ob = bpy.data.objects.new(name, new_me)
    target_bme.to_mesh(new_me)
    target_bme.free()
    return new_ob
    