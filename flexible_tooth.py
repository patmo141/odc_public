import bpy
from mathutils import Vector
from common_utilities import bversion

upper_molar23 = [[198, 89,77], #central pit
           [241, 87, 240,239], #MMR
           [66,63,72], #DMR
           [234, 84, 235], #MB
           [94, 227,80], #ML
           [216, 209,56], #DB
           [70,220], #DL
           [126, 125, 256, 124], #mesial contact
           [131,34,38], #distal contact
           [258, 128, 203, 167], #lingual HoC
           [123,122,163],#buccal HoC
           [192, 193,194,286], #mesial margin
           [279, 184,278], #distal margin
           [287,187,288,188], #lingual margin
           [195, 196,205]]

upper_molar1 = [[42, 137,3,39 ], #central pit
           [142,140,145,82], #MMR
           [192,194,186], #DMR
           [51,53,52], #MB
           [84,70,69], #ML
           [152,153,204], #DB
           [201,200,197], #DL
           [273,330,352,351], #mesial contact
           [293,320,317,315], #distal contact
           [213,302,304], #lingual HoC
           [279,281,245],#buccal HoC
           [355,328,329,353], #mesial margin
           [322,321,319,318], #distal margin
           [310,307,308], #lingual margin
           [341,340,337,326]]    #buccal margin


#upper premolar 2
upper_premolar2 = [[125, 130, 128, 152], 
                   [132, 153, 126, 129], 
                   [91, 187, 88], 
                   [93, 92, 188], 
                   [57, 66, 145], 
                   [137, 2, 21], 
                   [94, 97, 191], 
                   [61, 144, 58], 
                   [71, 179, 65], 
                   [182, 98, 99], 
                   [134, 112, 149], 
                   [150, 114, 135], 
                   [194, 69, 63]]

upper_premolar1 = [[217, 167, 166], [144, 197, 147, 113], [179, 72, 230], [110, 109, 214], [190, 189, 219], [100, 33, 40, 203], [224, 124, 186], [117, 140, 206], [28, 227, 164], [96, 97, 205], [208, 106, 61, 107], [234, 175, 173]]
upper_canine = [[64, 65, 75], [46, 29, 59], [67, 70, 66], [213, 191, 214, 205, 267], [35, 31, 34], [186, 182, 201], [268, 236, 292], [37, 17, 63], [128, 129, 294], [220, 136, 137], [23, 7, 6], [245, 282, 244, 281]]
upper_lateral = [[71, 3, 103], [170, 173, 178], [106, 118, 107], [62, 35, 182, 263], [36, 196, 185], [76, 13, 121], [186, 202, 41], [157, 153, 160], [44, 24, 164, 247], [51, 50, 55], [239, 242, 240], [99, 95, 98]]
upper_central = [[196, 185, 36], [103, 71, 3], [13, 121, 76], [186, 202, 41], [157, 153, 160], [106, 118, 107], [50, 55, 51], [200, 198, 197], [24, 164, 25], [239, 242, 240], [95, 98, 99], [182, 34, 35]]
lower_central = [[215, 222, 218], [262, 249, 254, 259], [177, 113, 145], [11, 7, 5, 14], [153, 119, 92], [102, 155, 126], [121, 146, 133], [231], [160, 124, 90], [22, 20, 25], [171, 96, 129], [246, 252], [36, 33]]
lower_lateral = [[155, 160, 176, 110], [235, 224, 223], [131, 127, 134], [242, 239, 262], [86, 85, 93], [9, 96, 65], [137, 105, 170, 159], [84, 62, 3], [219, 217, 212], [144, 147, 152], [258, 250, 246], [80, 78, 81]]
lower_canine = [[64, 78, 65], [46, 47, 29], [67, 127, 104, 66], [206, 207, 214], [32, 35, 33], [215, 160, 221], [99, 107, 98], [112, 113, 111], [17, 63, 38], [192, 190, 193], [275, 273, 282], [133, 294, 132], [5, 22, 9]]
lower_premolar1 = [[48, 142, 55], [156, 170, 159], [91, 88, 109], [53, 143, 54], [92, 111, 93], [132, 153, 129], [137, 2, 21], [94, 101, 97], [112, 149, 134], [41, 40, 47], [114, 135, 150], [43, 44, 42], [98, 99, 102]]
lower_premolar2 = [[180, 185, 183], [216, 217, 222], [7, 5, 3], [225, 223, 226], [116, 114, 117, 115], [210, 192, 215, 213], [129, 120, 130, 131], [122, 123], [239, 243], [168, 171], [209, 207, 205], [103, 99], [234, 232, 235], [125, 124]]
lower_molar1 = [[166, 167, 165], [168, 249, 224], [22], [244, 242, 243], [280, 281, 279], [25, 30, 289], [45, 283], [138, 267, 137, 266], [174, 300], [214, 219, 215, 218], [34, 2, 35], [190, 108, 188], [40, 38, 36], [120, 146], [37], [8, 258, 7], [6, 52], [43]]
lower_molar23 = [[65, 106], [140, 155], [108, 104], [69, 52], [71, 60, 59], [220, 230, 219], [74, 90], [149], [62, 58, 79], [9, 84, 82], [192, 193, 198], [195, 196, 194], [204, 228, 233], [133], [137]]
lower_molar3 = [[185, 154], [229, 222, 223], [80, 7, 76, 74, 79], [65, 126, 113], [192, 191], [89, 119, 67], [121, 131, 134], [194, 195], [234, 232], [103, 108, 127], [164, 216], [203, 205], [130, 60, 136], [210, 209], [212, 213], [105, 71, 106]]


v_groups = {}
v_groups['11'] = upper_central
v_groups['21'] = upper_central
v_groups['12'] = upper_lateral
v_groups['22'] = upper_lateral
v_groups['13'] = upper_canine
v_groups['23'] = upper_canine
v_groups['14'] = upper_premolar1
v_groups['24'] = upper_premolar1
v_groups['15'] = upper_premolar2
v_groups['25'] = upper_premolar2
v_groups['16'] = upper_molar1
v_groups['26'] = upper_molar1
v_groups['17'] = upper_molar23
v_groups['27'] = upper_molar23
v_groups['18'] = upper_molar23
v_groups['28'] = upper_molar23

v_groups['31'] = lower_central
v_groups['32'] = lower_lateral
v_groups['33'] = lower_canine
v_groups['34'] = lower_premolar1
v_groups['35'] = lower_premolar2
v_groups['36'] = lower_molar1
v_groups['37'] = lower_molar23
v_groups['38'] = lower_molar3

v_groups['41'] = lower_central
v_groups['42'] = lower_lateral
v_groups['43'] = lower_canine
v_groups['44'] = lower_premolar1
v_groups['45'] = lower_premolar2
v_groups['46'] = lower_molar1
v_groups['47'] = lower_molar23
v_groups['48'] = lower_molar3


    
class OPENDENTAL_OT_hook_deform(bpy.types.Operator):
    '''
    Will add a hooks and laplacian deform modifier to an object
    Use "Keep Flexi Tooth" after modifying the control points
    Make sure there aren't any existing hook/laplacian modifiers
    '''
    bl_idname = 'opendental.flexitooth'
    bl_label = "FlexiTooth"
    bl_options = {'REGISTER','UNDO'}
    
    
    @classmethod
    def poll(cls, context):
        condition0 = context.mode == 'OBJECT'
        condition1 = context.object and context.object.type == 'MESH'
        
        return condition0 and condition1
    
    def execute(self, context):
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        for ob in context.selected_objects:
            mods = [mod.type for mod in ob.modifiers]
            if 'HOOK' in mods:
                self.report({'WARNING'}, 'There are hook modifiers in' + ob.name +'.  Please apply or remove them') 
            elif 'LAPLACIANDEFORM' in mods:
                self.report({'WARNING'}, 'There are laplacial deform modifiers in' + ob.name +'.  Please apply or remove them')  
            elif 'SHRINKWRAP' in mods:
                self.report({'WARNING'}, 'There are shrinkwrap modifiers in' + ob.name +'.  Use Flexi Tooth BEFORE any margin seating or contact grinding') 
                continue
            
            else:
                if ob.type == 'MESH':
                    mx = ob.matrix_world
                    imx = mx.inverted()
                    
                    if ob.data.name[0:2] not in v_groups: continue
                    
                    ob.lock_location = [True, True, True]
                    #ob.hide_select = True
                    data_name = ob.data.name[0:2]
                    
                    hook_parent = bpy.data.objects.new(data_name + '_hook', None)
                    context.scene.objects.link(hook_parent)
                    hook_parent.matrix_world = ob.matrix_world
                    
                    v_islands = v_groups[ob.data.name[0:2]]
                    modnames = [data_name + '_hook.'+str(k).zfill(3) for k in range(len(v_islands))]
                    
                    bpy.ops.object.select_all(action = 'DESELECT')
                    context.scene.objects.active = ob
                    ob.select = True
                    N_mods = len(ob.modifiers)
                    for grp, modname in  zip(v_islands,modnames):
                        bpy.ops.object.mode_set(mode = 'EDIT')
                        bpy.ops.mesh.select_all(action = 'DESELECT')
                        bpy.ops.object.mode_set(mode = 'OBJECT')
                        center = Vector((0,0,0))
                        for ind in grp:
                            ob.data.vertices[ind].select = True
                            center += ob.data.vertices[ind].co
                        center *= 1/len(grp)
                        
                        hook = bpy.data.objects.new(modname, None)
                        context.scene.objects.link(hook)
                        
                        if bversion() < '002.077.000':
                            new_loc, no, ind = ob.closest_point_on_mesh(center)
                        
                        else:
                            ok, new_loc, no, ind = ob.closest_point_on_mesh(center)
                        world_loc = mx * new_loc
                    

                        hook.parent = hook_parent
                        hook.matrix_world[0][3] = world_loc[0]
                        hook.matrix_world[1][3] = world_loc[1]
                        hook.matrix_world[2][3] = world_loc[2]
                        
                        hook.empty_draw_type = 'SPHERE'
                        hook.empty_draw_size = .5
                        
                        
                        mod = ob.modifiers.new(modname, type='HOOK')         
                        mod.object = hook
                        
                        for n in range(0, N_mods):
                            bpy.ops.object.modifier_move_up(modifier = mod.name)
                        bpy.ops.object.mode_set(mode = 'EDIT')
                        bpy.ops.object.hook_reset(modifier = mod.name)
                        bpy.ops.object.hook_assign(modifier=mod.name)
                        #old_obs = [ob.name for ob in bpy.data.objects]
                        #bpy.ops.object.hook_add_newob()
                        #for obj in bpy.data.objects:
                        #    if obj.name not in old_obs:
                        #        hook = obj
                        #        hook.name = modname
                        #        hook.empty_draw_type = 'SPHERE'
                        #        hook.empty_draw_size = .5
                        #        hook.show_x_ray = True
                        #        loc = hook.location
                        #        bpy.ops.object.mode_set(mode = 'OBJECT')
                        #        new_loc, no, ind = ob.closest_point_on_mesh(imx*loc)
                         #       hook.location = mx * new_loc
                                #TODO, parent in place and keep transform
                        
                        
                    
                    for mod in ob.modifiers:
                        if mod.type == 'HOOK':
                            mod.show_expanded = False
                    if 'Anchor' not in ob.vertex_groups:
                        ob.vertex_groups.new('Anchor')
                    
                    bpy.ops.object.vertex_group_set_active(group = 'Anchor')
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.object.vertex_group_remove_from(use_all_verts = True)
                    bpy.ops.mesh.select_all(action = 'DESELECT')
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    for grp in v_islands:
                        for v in grp:
                            ob.data.vertices[v].select = True
                            
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    context.scene.tool_settings.vertex_group_weight = 1
                    bpy.ops.object.vertex_group_assign()
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    
                    mod = ob.modifiers.new('flexitooth', 'LAPLACIANDEFORM')
                    mod.vertex_group = 'Anchor'
                    mod.iterations = 20
                    
                    for n in range(0, N_mods):      
                        bpy.ops.object.modifier_move_up(modifier = "flexitooth")
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.object.laplaciandeform_bind(modifier = "flexitooth")
                    bpy.ops.object.mode_set(mode = 'OBJECT')    
                    
                    for mod in ob.modifiers:
                        if mod.type == 'HOOK':
                            mod.show_expanded = False
                            
                            
                    #ob.modifiers.new
        
        return {'FINISHED'}

class OPENDENTAL_OT_keep_hook(bpy.types.Operator):
    '''
    Will apply all the hook modifiers
    and laplacian deform modifiers
    '''
    bl_idname = 'opendental.flexitooth_keep'
    bl_label = "FlexiTooth Keep"
    bl_options = {'REGISTER','UNDO'}
    
    
    @classmethod
    def poll(cls, context):
        condition0 = context.mode == 'OBJECT'
        condition1 = context.object and context.object.type == 'MESH'
        
        return condition0 and condition1
    
    def execute(self, context):
        layers_copy = [layer for layer in context.scene.layers]
        context.scene.layers[0] = True
        
        to_delete = []
        for ob in context.selected_objects:
            mods = [mod.type for mod in ob.modifiers]
            if 'HOOK' not in mods:
                self.report({'WARNING'}, 'There are no hook modifiers in' + ob.name +'.  Please run flexttooth first or remove them') 
                continue
            
                    
                    
            bpy.ops.object.select_all(action = 'DESELECT')
            context.scene.objects.active = ob
            ob.select = True
            ob.lock_location = [False, False, False]
            #ob.hide_select = False    
            
            for mod in ob.modifiers:
                if mod.type in {'HOOK','LAPLACIANDEFORM'}:
                    ob.hide = False
                    bpy.ops.object.modifier_apply(modifier = mod.name)
                    
                    if mod.type =='HOOK':
                        to_delete.append(mod.object)
                        if mod.object.parent and mod.object.parent not in to_delete:
                            to_delete.append(mod.object.parent)
                
        bpy.ops.object.select_all(action='DESELECT')        
        for ob in to_delete:
            ob.select = True
            context.scene.objects.active = ob
            bpy.ops.object.delete(use_global = True)
            #lat = ob.data
            #ob.user_clear()
            #bpy.data.objects.remove(ob)
            #bpy.data.lattices.remove(lat)
            
        
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OPENDENTAL_OT_hook_deform)
    bpy.utils.register_class(OPENDENTAL_OT_keep_hook)
        
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_hook_deform)
    bpy.utils.unregister_class(OPENDENTAL_OT_keep_hook)
