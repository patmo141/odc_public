import bpy

from bpy.props import StringProperty, FloatProperty, EnumProperty, FloatVectorProperty


class ODC_modops_props(bpy.types.PropertyGroup):

    base_height : FloatProperty(description="Enter Base Height", default= 6, step=10, precision=2, max= 20, min= 6 ,unit='LENGTH')
    offset : FloatProperty(description="Enter offset value", default=0.20, step=1, precision=2, subtype='DISTANCE', unit='LENGTH')


    # Cutting tools props :

    cutting_tool = ["Curve Cutting Tool", "Square Cutting Tool"]
    items = []
    for i in range(len(cutting_tool)):
        item = (str(cutting_tool[i]), str(cutting_tool[i]), str(""), int(i))
        items.append(item)

    cutting_tool : EnumProperty(items=items, description="", default="Curve Cutting Tool")

    cutting_target = StringProperty(name="", default = "No Target !", description="Target",)

    cutting_mode = ["Cut inner", "Keep inner"]
    items = []
    for i in range(len(cutting_mode)):
        item = (str(cutting_mode[i]), str(cutting_mode[i]), str(""), int(i))
        items.append(item)

    cutting_mode : EnumProperty(items=items, description="", default="Cut inner")

    no_material_prop = StringProperty(name="No Material", default = "No Color", description="No material_slot found for active object")

    base_location_prop : FloatVectorProperty(name="Base location", description="stors the Model base location", size=3)






classes = [
    ODC_modops_props,
]


def register():
    
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.ODC_modops_props = bpy.props.PointerProperty(type=ODC_modops_props)
    


def unregister():
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.ODC_modops_props
    