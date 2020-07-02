# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

#import odc_public
#from  odc_public import odcutils, load_post_method

#from . import odcutils, load_post_method

'''
Template for classes and properties from Cycles Addon

class CyclesStyleClass(bpy.types.PropertyGroup):
    @classmethod
    def (cls):
        bpy.types.ParticleSettings.cycles = PointerProperty(
                name="Cycles Hair Settings",
                description="Cycles hair settings",
                type=cls,
                )
        cls.root_width = FloatProperty(

    @classmethod
    def unregister(cls):
        del bpy.types.ParticleSettings.cycles
'''
#Python imports :
import sys, os, inspect

#Blender imports :
import bpy

#Addon imports :
from odcmenus import button_data
from odcmenus import menu_utils

#Addon path :
addons_folder = os.path.abspath('odc_2')
#enums
rest_types=['CONTOUR','PONTIC','COPING','ANATOMIC COPING']
rest_enum = []
for index, item in enumerate(rest_types):
    rest_enum.append((str(index), rest_types[index], str(index)))
    
teeth = ['11','12','13','14','15','16','17','18','21','22','23','24','25','26','27','28','31','32','33','34','35','36','37','38','41','42','43','44','45','46','47','48']    
teeth_enum=[]
for index, item in enumerate(teeth):
    teeth_enum.append((str(index), item, str(index)))
    
def index_update(self,context):
    #perhaps do some magic here to only call it later?
    bpy.ops.ed.undo_push(message="Changed active tooth index")
    
#classes
class ODCProps(bpy.types.PropertyGroup):
    
    @classmethod
    def register(cls):
        bpy.types.Scene.odc_props = bpy.props.PointerProperty(type=cls)
        
        cls.master = bpy.props.StringProperty(
                name="Master Model",
                default="")
        cls.opposing = bpy.props.StringProperty(
                name="Opposing Model",
                default="")
        
        cls.bone = bpy.props.StringProperty(
                name="Bone Model",
                default="")
        
        cls.register_II = bpy.props.BoolProperty(
                name="2nd Registration",
                default=False)
        
        cls.work_log = bpy.props.StringProperty(name="Work Log", default = "")
        cls.work_log_path = bpy.props.StringProperty(name="Work Log File", subtype = "DIR_PATH", default = "")
        
        ###Toolbar show/hide booleans for tool options###
        cls.show_modops = bpy.props.BoolProperty(
                name="Model Operations",
                default=False)
        cls.show_teeth = bpy.props.BoolProperty(
                name="Tooth Panel",
                default=False)
        
        cls.show_bridge = bpy.props.BoolProperty(
                name="Bridge Panel",
                default=False)
        
        cls.show_implant = bpy.props.BoolProperty(
                name="Implant Panel",
                default=False)
        
        cls.show_splint = bpy.props.BoolProperty(
                name="Splint Panel",
                default=False)
        
        cls.show_ortho = bpy.props.BoolProperty(
                name="Ortho Panel",
                default=False)
        cls.show_dentures = bpy.props.BoolProperty(
                name="Dentures",
                default=False)
        #implant panel
        #bridge panel
        #splint panel       
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.odc_props    

class ODCSettings(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.odc_settings = bpy.props.PointerProperty(type=cls)
        
        cls.panel1 = bpy.props.BoolProperty(name="Panel1", default=False)
        cls.panel2 = bpy.props.BoolProperty(name="Panel2", default=False)
        cls.panel3 = bpy.props.BoolProperty(name="Panel3", default=False)
        cls.panel4 = bpy.props.BoolProperty(name="Panel4", default=False)
        cls.panel5 = bpy.props.BoolProperty(name="Panel5", default=False)
        cls.panel6 = bpy.props.BoolProperty(name="Panel6", default=False)
        cls.panel7 = bpy.props.BoolProperty(name="Panel7", default=False)
        
        
        #addons_folder = bpy.utils.script_paths('addons')[0]
        data_folder =os.path.join(addons_folder,'Resources\\data\\')
        def_tooth_lib = data_folder + "odc_tooth_library.blend"
        def_mat_lib = data_folder + "odc_mat_library.blend"
        print(data_folder)
        
        cls.tooth_lib = bpy.props.StringProperty(
            name="Tooth Library",
            default=def_tooth_lib,
            subtype='FILE_PATH')
        
        cls.mat_lib = bpy.props.StringProperty(
            name="Material Library",
            default=def_mat_lib,
            subtype='FILE_PATH')
                
        cls.cement_gap = bpy.props.FloatProperty(
            name="Default Cement Gap",
            default=.07)
        cls.i_contact = bpy.props.FloatProperty(
            name="Def IP Contact",
            default=.025)
        cls.o_contact = bpy.props.FloatProperty(
            name="Default Occlusal Contact",
            default=.025)            
        cls.holy_zone = bpy.props.FloatProperty(
            name="Default Holy Zone Width",
            default=.5)            
        cls.thickness = bpy.props.FloatProperty(
            name="Default Min Thickness",
            default=.75)
        cls.coping_thick = bpy.props.FloatProperty(
            name="Default Coping Thickness",
            default=.45)
        
        margin_methods = ['MANUAL', 'PROJECTION', 'WALKING']
        marg_enum = []
        for index, type in enumerate(margin_methods):
            marg_enum.append((str(index), margin_methods[index], str(index)))
         
        cls.margin_method = bpy.props.EnumProperty(
            name="Margin Method",
            description="The way the margin is marked",
            items=marg_enum,
            default='0')
            
            
        design_stages =['0.ALL',
                        '1.BULK PROCESSING',
                        '2.SEGMENTATION',
                        '3.MARGIN MARKING',
                        '4.RESTORATION DESIGN',
                        '5.FINALIZATION',
                        'EXPERIMENTAL']
        stages_enum = []
        for index, type in enumerate(design_stages):
            stages_enum.append((str(index), design_stages[index], str(index)))
         
        cls.design_stage = bpy.props.EnumProperty(
            name="Design Stage",
            description="Stage of design process",
            items=stages_enum,
            default='0')

        cls.dynamic_oc = bpy.props.BoolProperty("Dyn. Occlusion")
        cls.dynamic_ipm = bpy.props.BoolProperty("Dyn. Mesial")
        cls.dynamic_ipd = bpy.props.BoolProperty("Dyn. Distal")
        cls.dynamic_margin = bpy.props.BoolProperty("Dyn. Margin")

        cls.all_functions = bpy.props.BoolProperty("Show All Functions")
        cls.help = bpy.props.BoolProperty("Show Help Text")
    
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.odc_settings
        
        
class ToothRestoration(bpy.types.PropertyGroup):
    '''
    Class to keep track of all the models and relationships for a
    tooth restoration in a project.  It would be nice if these were saved
    with a blend file.
    '''
    @classmethod
    def register(cls):
        bpy.types.Scene.odc_teeth = bpy.props.CollectionProperty(type=cls)
        bpy.types.Scene.odc_tooth_index = bpy.props.IntProperty(name = "Working Tooth Index", min=0, default=0, update=index_update)
        
        cls.name = bpy.props.StringProperty(name="Tooth Number",default="Unknown")
        cls.axis = bpy.props.StringProperty(name="Insertion Axis",default="")
        cls.mesial = bpy.props.StringProperty(name="Distal Model",default="")
        cls.distal = bpy.props.StringProperty(name="Distal Model",default="")
        cls.opposing = bpy.props.StringProperty(name="Opposing Model",default="")
        cls.prep_model = bpy.props.StringProperty(name="Prep Model",default="")
        cls.margin = bpy.props.StringProperty(name="Margin",default="")
        cls.pmargin = bpy.props.StringProperty(name="PsMargin",default="")
        cls.bubble = bpy.props.StringProperty(name="Bubble",default="")
        cls.restoration = bpy.props.StringProperty(name="Restoration",default="")
        cls.contour = bpy.props.StringProperty(name="Full Contour",default="")
        cls.coping = bpy.props.StringProperty(name="Simple Coping",default="")
        cls.acoping = bpy.props.StringProperty(name="Anatomic Coping",default="")
        cls.intaglio = bpy.props.StringProperty(name="intaglio",default="")
        cls.in_bridge = bpy.props.BoolProperty(name="Incude in Bridge", default=False) #may be derprecated now
        cls.solid = bpy.props.StringProperty(name="Final Solid Tooth",default="")
        cls.log = bpy.props.StringProperty(name="Function Log",default="")
    

        cls.rest_type = bpy.props.EnumProperty(
            name="Restoration Type", 
            description="The type of restoration for this tooth", 
            items=rest_enum, 
            default='0',
            options={'ANIMATABLE'})
        
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.odc_teeth
        del bpy.types.Scene.odc_tooth_index
 
class ImplantRestoration(bpy.types.PropertyGroup):
    
    @classmethod
    def register(cls):
        bpy.types.Scene.odc_implants = bpy.props.CollectionProperty(type = cls)
        bpy.types.Scene.odc_implant_index = bpy.props.IntProperty(name = "Working Implant Index", min=0, default=0, update=index_update)#, update=update_func)
        
        cls.name = bpy.props.StringProperty(name="Tooth Number",default="")
        cls.implant = bpy.props.StringProperty(name="Implant Model",default="")
        cls.implant_lib_path = bpy.props.StringProperty(name="Implant Path",default="")
        cls.outer = bpy.props.StringProperty(name="Outer Cylinder",default="")
        cls.inner = bpy.props.StringProperty(name="Inner Cylinder",default="")
        cls.sleeve = bpy.props.StringProperty(name="Sleeve",default="")
        cls.drill = bpy.props.StringProperty(name="Drill",default="")
        cls.safety = bpy.props.StringProperty(name="Safety",default="")
        cls.cutout = bpy.props.StringProperty(name="Cutout Cylinder",default="")
        cls.abut_axis =  bpy.props.StringProperty(name="Insertion Axis",default="")
        cls.tissue = bpy.props.StringProperty(name="Tissue Model",default="")
        cls.log = bpy.props.StringProperty(name="Function Log",default="")
    
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.odc_implants
        del bpy.types.Scene.odc_implant_index

class BridgeRestoration(bpy.types.PropertyGroup):
    
    @classmethod
    def register(cls):
        bpy.types.Scene.odc_bridges = bpy.props.CollectionProperty(type = cls)
        bpy.types.Scene.odc_bridge_index = bpy.props.IntProperty(name = "Working Implant Index", min=0, default=0, update=index_update)
  
        cls.name = bpy.props.StringProperty(name="Bridge Name",default="")
        cls.axis = bpy.props.StringProperty(name="Bridge Insertion",default="")
        cls.margin = bpy.props.StringProperty(name="Bridge Margin",default="")
        cls.bridge = bpy.props.StringProperty(name="Bridge Restoration",default="")
        cls.intaglio = bpy.props.StringProperty(name="Bridge Intaglio",default="")
        cls.final_restoration = bpy.props.StringProperty(name="Final Restoration",default="")

  
        cls.tooth_string = bpy.props.StringProperty(name="teeth in bridge names separated by : or \n",default="")
        cls.implant_string = bpy.props.StringProperty(name="implants in bridge names separated by : or \n",default="")
    
        cls.teeth = []
        cls.implants = []
        
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.odc_bridges
        del bpy.types.Scene.odc_bridge_index
        
    def calc_connectors(self):
        for tooth in self.teeth:
            print(tooth.name)
            
    def load_components_from_string(self,scene):
        tooth_list = self.tooth_string.split(sep=":")
        #self.teeth = []  #temporary clear this thing?
        for name in tooth_list:
            tooth = scene.odc_teeth.get(name)
            if tooth and tooth not in self.teeth:
                self.teeth.append(tooth)
        
        imp_list = self.implant_string.split(sep=":")
        for name in imp_list:
            implant = scene.odc_implants.get(name)
            if implant and implant not in self.implants:
                self.implants.append(tooth)
                
    def save_components_to_string(self):
        print(self.tooth_string)
        print(self.implant_string)
                
    def add_tooth(self,tooth):
        name = tooth.name
        if len(self.tooth_string):
            tooth_list = self.tooth_string.split(sep=":")
            if name not in tooth_list:
                tooth_list.append(name)
                tooth_list.sort()
                self.tooth_string = ":".join(tooth_list)
                self.teeth.append(tooth)
                
class SplintRestoration(bpy.types.PropertyGroup):
    
    @classmethod
    def register(cls):
        bpy.types.Scene.odc_splints = bpy.props.CollectionProperty(type = cls)
        bpy.types.Scene.odc_splint_index = bpy.props.IntProperty(name = "Working Splint Index", min=0, default=0, update=index_update)
  
        cls.name = bpy.props.StringProperty(name="Splint Name",default="")
        cls.model = bpy.props.StringProperty(name="Splint Model",default="")
        cls.bone = bpy.props.StringProperty(name="Bone",default="")
        cls.refractory = bpy.props.StringProperty(name="Rrefractory model",default="")
        cls.axis = bpy.props.StringProperty(name="Splint Insertion",default="")
        cls.margin = bpy.props.StringProperty(name="Splint Bez",default="")
        cls.splint = bpy.props.StringProperty(name="Splint Restoration",default="")
        cls.falloff = bpy.props.StringProperty(name="falloff mesh",default="")
        cls.plane = bpy.props.StringProperty(name="Occlusal Plane",default="")
        cls.cut = bpy.props.StringProperty(name="Cut Surface",default="")
        
        #tooth names used to repopulate lists above before saving
        cls.tooth_string = bpy.props.StringProperty(name="teeth in splint names separated by : or \n",default="")
        cls.implant_string = bpy.props.StringProperty(name="implants in splint names separated by : or \n",default="")
    
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.odc_splints
        del bpy.types.Scene.odc_splint_index
            
    def load_components_from_string(self,scene):
        print('no longer loading components')
        #tooth_list = self.tooth_string.split(sep=":")
        #for name in tooth_list:
        #    tooth = scene.odc_teeth.get(name)
        #    if tooth and tooth not in self.teeth:
        #        self.teeth.append(tooth)
    
        #imp_list = self.implant_string.split(sep=":")
        #for name in imp_list:
        #    implant = scene.odc_implants.get(name)
        #    if implant and implant not in self.implants:
        #        self.implants.append(implant)
                
    def save_components_to_string(self):
        print(self.tooth_string)
        print(self.implant_string)
        
        #names = [tooth.name for tooth in self.teeth]
        #names.sort()
        #self.tooth_string = ":".join(names)
        
        #i_names = [implant.name for implant in self.implants]
        #i_names.sort()
        #self.implant_string = ":".join(i_names)
                
    def add_tooth(self,tooth):
        name = tooth.name
        if len(self.tooth_string):
            tooth_list = self.tooth_string.split(sep=":")
            if name not in tooth_list:
                tooth_list.append(name)
                tooth_list.sort()
                self.tooth_string = ":".join(tooth_list)
                self.teeth.append(tooth)           
     
    def cleanup(self):
        print('not implemented')
        
class SplintRestorationAdd(bpy.types.Operator):
    '''Be sure to have an object selected to build the splint on!'''
    bl_idname = 'opendental.add_splint'
    bl_label = "Append Splint"
    bl_options = {'REGISTER','UNDO'}
    
    name = bpy.props.StringProperty(name="Splint Name",default="_Splint")  
    link_active = bpy.props.BoolProperty(name="Link",description = "Link active object as base model for splint", default = True)
    def invoke(self, context, event): 
        
        
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}
    
    def execute(self, context):

        my_item = context.scene.odc_splints.add()        
        my_item.name = self.name
        
        if self.link_active:
            if context.object:
                my_item.model = context.object.name
            elif context.selected_objects:
                my_item.model = context.selected_objects[0].name
                
        return {'FINISHED'}
                                         
class OPENDENTAL_OT_add_tooth_restoration(bpy.types.Operator):
    '''Adds a new tooth to the scene'''
    bl_idname = 'opendental.add_tooth_restoration'
    bl_label = "New Tooth Restoration"
    bl_options = {'REGISTER','UNDO'}
    
    #We will select a tooth to work on
    ob_list = bpy.props.EnumProperty(name="Tooth to work on", description="A list of all teeth to chose from", items=teeth_enum, default='0')
    name = bpy.props.StringProperty(name="Tooth Number",default="")
    rest_type = bpy.props.EnumProperty(name="Restoration Type", description="The type of restoration for this tooth", items=rest_enum, default='0')
    
    #in_bridge = bpy.props.BoolProperty(name="Incude in Bridge", default = False)
    #abutment = bpy.props.BoolProperty(name="Abutment", description="If Pontic Uncheck", default = True)   
    
    def invoke(self, context, event): 
        #context.window_manager.invoke_search_popup(self)
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}
    
    def execute(self, context):

        if not self.properties.name: #eg, it was invoked
            self.properties.name = str(teeth[int(self.properties.ob_list)])
            
        if self.properties.name in [tooth.name for tooth in context.scene.odc_teeth]:
            self.report({'ERROR'},'That tooth is already planned!  No duplicates allowed')
            return {'CANCELLED'}
            
        my_item = bpy.context.scene.odc_teeth.add()
        indx = int(self.properties.ob_list)
        
        print(indx)
        
        
        #my_item.abutment = self.properties.abutment
        my_item.name = self.properties.name
        my_item.rest_type = self.properties.rest_type
        
        #reimport to get new value?
        #import odc       
        #if not odc.odc_restricted_registration:  #TODO global var persisten
        #    from . import crown, implant
        #    crown.post_register2()
        #    implant.post_register2()
        #    odc.odc_restricted_registration = True
        return {'FINISHED'}


class ImplantRestorationAdd(bpy.types.Operator):
    '''Adds a new implant to the scene'''
    bl_idname = 'opendental.add_implant_restoration'
    bl_label = "New Implant Placement"
    bl_options = {'REGISTER','UNDO'}
    
    #We will select a tooth to work on
    ob_list = bpy.props.EnumProperty(name="Implant space to restore", description="A list of all teeth to chose from", items=teeth_enum, default='0')
    name = bpy.props.StringProperty(name="Tooth Number",default="")
    rest_type = bpy.props.EnumProperty(name="Restoration Type", description="The type of restoration for this tooth", items=rest_enum, default='0')
    
    #in_bridge = bpy.props.BoolProperty(name="Incude in Bridge", default = False)
    #abutment = bpy.props.BoolProperty(name="Abutment", description="If Pontic Uncheck", default = True)   
    
    def invoke(self, context, event): 
        #context.window_manager.invoke_search_popup(self)
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}
    
    def execute(self, context):

        my_item = bpy.context.scene.odc_implants.add()
        indx = int(self.properties.ob_list)   
        print(indx)
        
        if not self.properties.name: #eg, it was invoked
            self.properties.name = str(teeth[int(self.properties.ob_list)])
        #my_item.abutment = self.properties.abutment
        my_item.name = self.properties.name
        my_item.rest_type = self.properties.rest_type
        
        #my_item.in_bridge = self.properties.in_bridge
        #import odc
        #if not odc.odc_restricted_registration:
           # from . import crown, implant
            #crown.post_register2()
           # implant.post_register2()
            #odc.odc_restricted_registration = True
        return {'FINISHED'}
    
class ToothRestorationRemove(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.remove_tooth_restoration'
    bl_label = "Remove Tooth Restoration"
    
    def execute(self, context):

        j = bpy.context.scene.odc_tooth_index
        bpy.context.scene.odc_teeth.remove(j)
            
        return {'FINISHED'}
    
class SplintRestorationRemove(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.remove_splint'
    bl_label = "Remove Splint Restoration"
    
    def execute(self, context):

        j = bpy.context.scene.odc_splint_index
        bpy.context.scene.odc_splints.remove(j)
            
        return {'FINISHED'}
    
class ImplantRestorationRemove(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.remove_implant_restoration'
    bl_label = "Remove Implant Restoration"
    
    def execute(self, context):

        j = bpy.context.scene.odc_implant_index
        bpy.context.scene.odc_implants.remove(j)
            
        return {'FINISHED'}
    
class BridgeRestorationRemove(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.remove_bridge_restoration'
    bl_label = "Remove Bridge Restoration"
    
    def execute(self, context):

        j = bpy.context.scene.odc_bridge_index
        bpy.context.scene.odc_bridges.remove(j)
            
        return {'FINISHED'}
    
#class OPENDENTAL_OT_activate(bpy.types.Operator):
#    '''Adds a new tooth to the scene'''
#    bl_idname = 'opendental.activate'
#    bl_label = "Activate Opendental"
#    
#    def execute(self, context):
        
#        import odc
#        if not odc.odc_restricted_registration:
#            from . import crown, implant
#            crown.post_register2()
#            implant.post_register2()
#            load_post_method("dummy")
#            odc.odc_restricted_registration = True
#        return {'FINISHED'}
    
        
def register():
    bpy.utils.register_class(ODCProps)
    bpy.utils.register_class(ODCSettings)    
    bpy.utils.register_class(ToothRestoration)
    bpy.utils.register_class(ImplantRestoration)
    bpy.utils.register_class(BridgeRestoration)
    bpy.utils.register_class(SplintRestoration)
    
    #functions to add new class instances into collections
    bpy.utils.register_class(OPENDENTAL_OT_add_tooth_restoration)
    bpy.utils.register_class(ImplantRestorationAdd)
    bpy.utils.register_class(BridgeRestorationRemove)
    bpy.utils.register_class(ImplantRestorationRemove)
    bpy.utils.register_class(ToothRestorationRemove)
    bpy.utils.register_class(SplintRestorationAdd)
    bpy.utils.register_class(SplintRestorationRemove)
    
    #activation function
    #bpy.utils.register_class(OPENDENTAL_OT_activate)
    
def unregister():

    #bpy.utils.unregister_class(ODCProps)
    ODCProps.unregister()
    ODCSettings.unregister()
    
    
    ToothRestoration.unregister()
    ImplantRestoration.unregister()
    BridgeRestoration.unregister()
    SplintRestoration.unregister()
    
    #functions to add remove class isntances into collections
    bpy.utils.unregister_class(OPENDENTAL_OT_add_tooth_restoration)
    bpy.utils.unregister_class(ImplantRestorationAdd)
    bpy.utils.unregister_class(BridgeRestorationRemove)
    bpy.utils.unregister_class(ImplantRestorationRemove)
    bpy.utils.unregister_class(ToothRestorationRemove)
    bpy.utils.unregister_class(SplintRestorationAdd)
    bpy.utils.unregister_class(SplintRestorationRemove)
    '''
if __name__ == "__main__":
    register()
    '''