import bpy
import bmesh
from mathutils import Matrix, Vector

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
    list of objects
    new object will have same matrix world as the first object in list
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
    