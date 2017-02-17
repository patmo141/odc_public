#----------------------------------------------------------
# File __init__.py
#----------------------------------------------------------
 
#    Addon info
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    'name': "Open Dental CAD for Blender",
    'author': "Patrick R. Moore",
    'version': (1,0,2),
    'blender': (2, 7, 6),
    'api': 59393,
    'location': "3D View -> Tool Shelf",
    'description': "Dental CAD Tool Package",
    'warning': "",
    'wiki_url': "",
    'tracker_url': "",
    'category': '3D View'}


#we need to add the odc subdirectory to be searched for imports
#http://stackoverflow.com/questions/918154/relative-paths-in-python
import sys, os, platform, inspect, imp
sys.path.append(os.path.join(os.path.dirname(__file__)))
print(os.path.join(os.path.dirname(__file__)))

''' 
if "bpy" in locals():
    import imp
    
    imp.reload(classes)
    imp.reload(odcutils)
    imp.reload(crown)
    imp.reload(margin)
    imp.reload(bridge)
    imp.reload(panel)
    print("Reloaded multifiles")
    
else:
    from . import classes, odcutils, crown, margin, bridge, panel
    print("Imported multifiles")
''' 
import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.app.handlers import persistent
#from . 

import odcutils

def update_brackets(self,context):
    settings = odcutils.get_settings()
    libpath = settings.ortho_lib
    assets = odcutils.obj_list_from_lib(libpath)
    return [(asset,asset, asset) for asset in assets]

#addon preferences
class ODCAddonPreferences(AddonPreferences):
    bl_idname = __name__

    addons = bpy.context.user_preferences.addons
    
    folderpath = os.path.dirname(os.path.abspath(__file__))
    print('SETTINGS FOLDERPATH')
    print(folderpath)
    data_folder =os.path.join(folderpath,'data\\')
    
    
    #addons_folder = bpy.utils.script_paths('addons')[0]
    #data_folder =os.path.join(addons_folder,'odc_public','data')
    def_tooth_lib = os.path.join(data_folder,"odc_tooth_library.blend")
    def_mat_lib = os.path.join(data_folder,"odc_materials.blend")
    def_imp_lib = os.path.join(data_folder,"odc_implants_leone.blend")
    def_drill_lib = os.path.join(data_folder,"odc_drill_lib.blend")
    def_ortho_lib = os.path.join(data_folder,"odc_bracket_library.blend")
    
    #enums
    behavior_modes=['LIST','ACTIVE','ACTIVE_SELECTED']
    behavior_enum = []
    for index, item in enumerate(behavior_modes):
        behavior_enum.append((str(index), behavior_modes[index], str(index)))
        
    workflow_modes=['SINGLE','MULTIPLE_LINEAR','MULTIPLE_PARALLEL']
    workflow_enum = []
    for index, item in enumerate(workflow_modes):
        workflow_enum.append((str(index), workflow_modes[index], str(index)))
    
    
              
    #real properties
    tooth_lib = bpy.props.StringProperty(
        name="Tooth Library",
        default=def_tooth_lib,
        #default = '',
        subtype='FILE_PATH')
    
    mat_lib = bpy.props.StringProperty(
        name="Material Library",
        default=def_mat_lib,
        #default = '',
        subtype='FILE_PATH')
    
    imp_lib = bpy.props.StringProperty(
        name="Implant Library",
        default=def_imp_lib,
        #default = '',
        subtype='FILE_PATH')
    
    drill_lib = bpy.props.StringProperty(
        name="Drill Library",
        default=def_drill_lib,
        #default = '',
        subtype='FILE_PATH')
    
    ortho_lib = bpy.props.StringProperty(
        name="Bracket Library",
        default=def_ortho_lib,
        #default = '',
        subtype='FILE_PATH')
 
    debug = IntProperty(
            name="Debug Level",
            default=1,
            min = 0,
            max = 4,
            )
    
    behavior = EnumProperty(
            name = "Behavior Mode",
            description = "",
            items = behavior_enum,
            default = '2',
            )


    workflow = EnumProperty(
            items = workflow_enum,
            name = "Workflow Mode",
            description = "SINGLE: for single units, LINEAR: do each tooth start to finish, MULTI_PARALLELS: Do all teeth at each step",
            default = '0')
    
    #Ortho Settings
    bgauge_override = BoolProperty(name="Override Edge Height",
            default=False,
            description = "Use manual gauge height instead of default bracket prescription")
    
    bracket_gauge = FloatProperty(name="Gauge Height",
            default=4,
            min = .5,
            max = 7,
            unit = 'LENGTH',
            description = "Manual gauge height to override the default library prescription")
    
    bracket = EnumProperty(
            items = update_brackets,
            name = "Choose Bracket")
  
    #behavior_mode = EnumProperty(name="How Active Tooth is determined by operator", description="'LIST' is more predictable, 'ACTIVE' more like blender, 'ACTIVE_SELECTED' is for advanced users", items=behavior_enum, default='0')

    def draw(self, context):
        layout = self.layout
        layout.label(text="Open Dental CAD Preferences and Settings")
        layout.prop(self, "mat_lib")
        layout.prop(self, "tooth_lib")
        layout.prop(self, "imp_lib")
        layout.prop(self, "drill_lib")
        layout.prop(self, "ortho_lib")
        layout.prop(self, "behavior")
        layout.prop(self, "workflow")
        layout.prop(self, "debug")

class OPENDENTAL_OT_addon_prefs_odc(Operator):
    """Display example preferences"""
    bl_idname = "opendental.odc_addon_pref"
    bl_label = "ODC Preferences Display"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences

        info = ("Path: %s, Number: %d, Boolean %r" %
                (addon_prefs.filepath, addon_prefs.number, addon_prefs.boolean))

        self.report({'INFO'}, info)
        print(info)

        return {'FINISHED'}

@persistent   
def load_post_method(dummy):
    print('loaded bridges')
    #make all the bridges reload their teeth.
    odcutils.scene_verification(bpy.context.scene, debug=True)
    for bridge in bpy.context.scene.odc_bridges:
        print(bridge.tooth_string)
        #bridge.load_components_from_string(bpy.context.scene)
    
    print('loaded splints')
    for splint in bpy.context.scene.odc_splints:
        print(splint.tooth_string)
        #splint.load_components_from_string(bpy.context.scene)
@persistent    
def save_pre_method(dummy):
    print('prepared bridges for save')
    odcutils.scene_verification(bpy.context.scene, debug = True)
    for bridge in bpy.context.scene.odc_bridges:
        bridge.save_components_to_string()
    print('prepared splints for save')
    for splint in bpy.context.scene.odc_splints:
        splint.save_components_to_string()

@persistent
def pause_playback(scene):
    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_play()
        scene.frame_set(scene.frame_current - 1) #prevent replaying
        print('REACHED THE END')
@persistent
def stop_playback(scene):
    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=False)
        scene.frame_set(scene.frame_current - 1) #prevent replaying
        print('REACHED THE END')

# or restore frames:
@persistent
def stop_playback_restore(scene):
    if scene.frame_current == scene.frame_end + 1:
        bpy.ops.screen.animation_cancel(restore_frame=True)
        print('REACHED THE END')
                               
def register():
    #bpy.utils.register_module(__name__)
    #import the relevant modules
    #from . 
    
    
    
    import classes, odcutils, crown, margin, bridge, splint, implant, panel, help, flexible_tooth, bracket_placement, denture_base, occlusion, ortho # , odcmenus, bgl_utils
        
    #register them
    classes.register()
    odcutils.register()
    crown.register()
    implant.register()
    margin.register()
    bridge.register()
    splint.register()
    help.register()
    flexible_tooth.register()
    bracket_placement.register()
    denture_base.register()
    panel.register()
    occlusion.register()
    ortho.register()
    #odcmenus.register()
    #bgl_utils.register()
    

    found = False
    try:
        imp.find_module('Crypto')
        #found = True
    except ImportError:
        found = False
        #from . 
        
    if found:
        print('found the Crypto module, importing CDT files supported')
        import cdt
        cdt.register()
    else:
        print('The Crypto module was not found! CDT not supported')
    
    #register this module
    print('REGISERESTED THE ADDON PREFERENCES?')
    bpy.utils.register_class(ODCAddonPreferences)
    bpy.utils.register_class(OPENDENTAL_OT_addon_prefs_odc)
    
    bpy.app.handlers.load_post.append(load_post_method)
    bpy.app.handlers.save_pre.append(save_pre_method)
    bpy.app.handlers.frame_change_pre.append(pause_playback)
    
def unregister():
    #import the relevant modules
    from . import classes, odcutils, crown, margin, bridge, splint, panel, implant, flexible_tooth#, splint, panel, odcmenus, bgl_utils
    
    bpy.app.handlers.save_pre.remove(save_pre_method)
    bpy.app.handlers.load_post.remove(load_post_method)
    bpy.app.handlers.frame_change_pre.remove(pause_playback)
    
    bpy.utils.unregister_module(__name__)
    
    
    #unregister them
    classes.unregister()
    odcutils.unregister()
    crown.unregister()
    margin.unregister()
    implant.unregister()
    splint.unregister()
    bridge.unregister()
    panel.unregister()
    flexible_tooth.unregister()
    
    #odcmenus.unregister()
    #bgl_utils.unregister()
    
    if platform.system() == "Windows" and platform.release() in ['7','Vista']:
        from . import cdt
        cdt.unregister()
    #unregister this module
 
if __name__ == "__main__":
    register()