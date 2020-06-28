'''
Created on Nov 22, 2016

@author: Patrick
'''
import bpy

class OPENDENTAL_OT_check_clearance(bpy.types.Operator):
    '''
    select 2 objects, and adds a proximity modifier and
    vertex paint to demonstrate the clearance between them
    '''
    bl_idname = 'opendental.check_clearance'
    bl_label = "Check Clearance"
    bl_options = {'REGISTER','UNDO'}
    
    min_d = bpy.props.FloatProperty(name="Touching", description="", default=0, min=0, max=1, step=5, precision=2, options={'ANIMATABLE'})
    max_d = bpy.props.FloatProperty(name="Max D", description="", default=.5, min=.1, max=2, step=5, precision=2, options={'ANIMATABLE'})
    
    @classmethod
    def poll(cls, context):
        
        cond1 = context.object != None
        cond2 = len(context.selected_objects) == 2
        cond3 = all([ob.type == 'MESH' for ob in context.selected_objects])
        cond4 = context.mode == 'OBJECT'
        
        return cond1 & cond2 & cond3 & cond4
        
    def execute(self, context):
        
        ob0 = context.object
        ob1 = [ob for ob in context.selected_objects if ob != ob0][0]
        
        grp0 = "clearance " + ob1.name
        grp1 = "clearance " + ob0.name
        
        #check if group exists
        group0 = ob0.vertex_groups.get(grp0)
        group1 = ob1.vertex_groups.get(grp1)
        
        inds0 = [i for i in range(0, len(ob0.data.vertices))]
        inds1 = [i for i in range(0, len(ob1.data.vertices))]
                                  
        if not group0:
            group0 = ob0.vertex_groups.new(grp0)
            group0.add(inds0, 1, 'REPLACE')
        else:
            group0.add(inds0, 1, 'REPLACE')
            
        if not group1:
            group1 = ob1.vertex_groups.new(grp1)
            group1.add(inds1, 1, 'REPLACE')
        else:
            group1.add(inds1, 1, 'REPLACE')
        
        mod0 = ob0.modifiers.get('VertexWeightProximity')
        if not mod0:
            mod0 = ob0.modifiers.new(type ='VERTEX_WEIGHT_PROXIMITY', name = 'VertexWeightProximity')
        
        mod1 = ob1.modifiers.get('VertexWeightProximity')
        if not mod1:
            mod1 = ob1.modifiers.new(type = 'VERTEX_WEIGHT_PROXIMITY', name = 'VertexWeightProximity')
            
        mod0.vertex_group = group0.name
        mod0.min_dist = .3
        mod0.max_dist = 0
        mod0.proximity_mode = 'GEOMETRY'
        mod0.proximity_geometry = {'FACE'}
        mod1.vertex_group = group1.name
        mod1.min_dist = .3
        mod1.max_dist = 0
        mod1.proximity_mode = 'GEOMETRY'
        mod1.proximity_geometry = {'FACE'}
        #Do this last, it's the slow part
        mod0.target = ob1
        mod1.target = ob0
        
          
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OPENDENTAL_OT_check_clearance)
    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_check_clearance)
    
if __name__ == "__main__":
    register()