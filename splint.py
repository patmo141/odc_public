import bpy
import bmesh
from bpy.types import Panel

def create_material(name):   
        if name in bpy.data.materials: #if material already exists, just configure it
            ob = bpy.context.object
            me = ob.data
            print("Material already exists: "+ name+ "; changing...")
            index = bpy.data.materials.find(name)
            mat = bpy.data.materials[index]
            mat.diffuse_color = (0.295508, 0.439708, 0.8, 0.5)
            mat.metallic = 1
            mat.roughness = 0.02

            if len(ob.material_slots) < 1: #check if the material slot already exists and use it
                me.materials.append(mat)
            else:
                bpy.ops.object.material_slot_remove()
                me.materials.append(mat)

        else: #Repeat in case material doesnt exist, bue creating it first
            ob = bpy.context.object
            me = ob.data        
            if len(ob.material_slots) < 1:
                mat = bpy.data.materials.new(name=name)
                mat.diffuse_color = (0.295508, 0.439708, 0.8, 0.5)
                mat.metallic = 1
                mat.roughness = 0.02
                me.materials.append(mat)
            else:
                bpy.ops.object.material_slot_remove()
                mat = bpy.data.materials.new(name=name)
                mat.diffuse_color = (0.295508, 0.439708, 0.8, 0.5)
                mat.metallic = 1
                mat.roughness = 0.02
                print("color " + name+" was created")
                me.materials.append(mat)

                return {'FINISHED'} 

def create_particles(name, vertexgroup): #Same process as with material but with a particle system, a bit more complicated
        if name in bpy.context.object.particle_systems:
            ob = bpy.context.object
            me = ob.data
            print("Particles system already exists: "+ name+ "; changing...")
            index = bpy.context.object.particle_systems.find(name)
            part = bpy.data.particles[index]
            part.type = 'HAIR'
            part.use_advanced_hair = True
            part.render_type = 'OBJECT'
            bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
            part.particle_size = 0.2
            part.count = 10000
            part.hair_length = 6

        else:
            ob = bpy.context.object
            me = ob.data   
            bpy.ops.object.particle_system_add()
            bpy.context.object.particle_systems[0].name = name

            findparticles = name in bpy.data.particles
            finddefaultp = 'ParticleSettings' in bpy.data.particles
    
            if findparticles == True:
                part = bpy.data.particles[index]
                part.name = name
                part.type = 'HAIR'
                part.use_advanced_hair = True
                part.render_type = 'OBJECT'
                bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
                part.particle_size = 0.2
                part.count = 10000
                part.hair_length = 6
                me.particles.append(part)
            else:
                if finddefaultp == True:
                    part = bpy.data.particles[0]
                    part.name = name
                    part.type = 'HAIR'
                    part.use_advanced_hair = True
                    part.render_type = 'OBJECT'
                    bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
                    part.particle_size = 0.2
                    part.count = 10000
                    part.hair_length = 6

                else:

                    part = bpy.data.particles.new(name=name)
                    part.name = name
                    part.type = 'HAIR'
                    part.use_advanced_hair = True
                    part.render_type = 'OBJECT'
                    bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
                    part.particle_size = 0.2
                    part.count = 10000
                    part.hair_length = 6
                    me.particles.append(part)
    

                return {'FINISHED'} 
    


class btn_Splint_draw(bpy.types.Operator):
    bl_idname = "object.splint_draw"
    bl_label = "Draw splint"


    def execute(self, context):

        # First rename de model to 'model'
        ob = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = ob
        ob.name = "model"
        
        # Check if there's already a metaball in the scene
        foundmeta = 'Mball' in bpy.data.objects
        
        #If there's not a metaball create the meta and setup resolution and material
        if foundmeta == False:
            bpy.ops.object.metaball_add(type='BALL', enter_editmode=False, align='WORLD', location=(0, 0, 100))
            ob = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = ob
            bpy.context.object.data.resolution = 1
            bpy.context.object.data.threshold = 0.01  
            create_material('splintmat')


            
        #If its already created setup resolution and material
        else:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Mball'].select_set(True)
            ob = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = ob
            bpy.context.object.data.resolution = 1
            bpy.context.object.data.threshold = 0.01
            create_material('splintmat')


        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['model'].select_set(True)
        ob = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = ob #Set the model as active object

        #We check if the model already has a vertex group and rename it as VG_Influence, we create if it doesnt exist
        
        if len(ob.vertex_groups) == 0:
            bpy.ops.object.vertex_group_add()
            ob.vertex_groups[0].name = 'VG_Influence'
        else:
            ob.vertex_groups[0].name = 'VG_Influence'
        
        #We finally create the particle system on the model and point to the metaball
        create_particles('particulas', 'VG_Influence')
        bpy.data.particles['particulas'].instance_object = bpy.data.objects['Mball']

        #Go to weight paint mode and setup the brush

        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        bpy.ops.brush.curve_preset(shape='MAX')
        bpy.data.brushes["Draw"].use_frontface = False
        return {"FINISHED"}

class btn_Splint_make(bpy.types.Operator):
    bl_idname = "object.splint_make"
    bl_label = "Make Splint"
    
    def execute(self, context):
        
        #We first limit the limits of the wieghts to consider for the generated vertex group
        
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=1)
        bpy.ops.brush.curve_preset(shape='MAX')
        bpy.ops.object.vertex_group_clean()
        
        #Let's go to edit mode, then deselect everything, select the vertex group, duplicate and separate vertex.
        #Select new object and set as active object.
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_pattern(pattern="*001")
        ob = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = ob
        ob.name = "Splint" #Name the object as Splint (just splint as i assume we will only make 1 splint
        create_material('splintmat') #Apply material

       #Metaballs in fact where only for visualize, we use other method to create final splint, becasue with metaballs everything gets so bulgy 
        #Clean free borders 
        me = bpy.context.object.data
        bm = bmesh.new()   # create an empty BMesh
        bm.from_mesh(me)   # fill it in from a Mesh
        # Erase single vertices (not forming faces)
        for v in bm.verts:
            if not v.link_edges:
                v.select = True
                bm.verts.remove(v)
        # Erase edges not forming faces
        for ed in bm.edges:
            if len(ed.link_faces) == 0:
                for v in ed.verts:
                    if len(v.link_faces) == 0:
                        v.select = True
                        bm.verts.remove(v)
        # Erase trienagles with less than 2 neighbours
        for v in bm.verts:
            if len(v.link_edges) == 2:
                v.select = True
                bm.verts.remove(v)
        bm.to_mesh(me)
        me.update()
        bm.free() 
        
        # Edit model again, select non-manifold and generate a face, voxel remesh, solidify 1 mm, voxel remesh and smooth the result

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_non_manifold()
        bpy.ops.mesh.edge_face_add()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.data.remesh_voxel_size = 0.5
        bpy.context.object.data.use_remesh_fix_poles = False
        bpy.context.object.data.use_remesh_smooth_normals = True
        bpy.ops.object.voxel_remesh()
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].thickness = 1
        bpy.context.object.modifiers["Solidify"].offset = 1
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Solidify")
        bpy.ops.object.voxel_remesh()
        bpy.ops.object.modifier_add(type='SMOOTH')
        bpy.context.object.modifiers["Smooth"].factor = 1
        bpy.context.object.modifiers["Smooth"].iterations = 7
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Smooth")
        objs = [ob for ob in bpy.context.scene.objects if ob.type in ('METABALL')]
        bpy.ops.object.delete({"selected_objects": objs})

        
        






        return {"FINISHED"}


def register():
    bpy.utils.register_class(btn_Splint_draw)
    bpy.utils.register_class(btn_Splint_make)

    
def unregister():
    bpy.utils.unregister_class(btn_Splint_draw)
    bpy.utils.unregister_class(btn_Splint_make)