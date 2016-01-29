'''
Created on Sep 5, 2015

@author: Patrick
'''

import bpy
import bgl
import blf
import time
import odcutils
import bridge_methods

from textbox import TextBox
from bpy.app.handlers import persistent

#Module Level globals

#for now, just a help box and the
help_display_box = None


#the app handlers are different for each situation
crown_help_app_handle = None
crown_help_draw_handle = None

implant_help_app_handle = None
implant_help_draw_handle = None

bridge_help_app_handle = None
bridge_help_draw_handle = None

guide_help_app_handle = None
guide_help_draw_handle = None


def update_help_box(help_text):
    global help_display_box
    if help_text != help_display_box.raw_text:
        help_display_box.raw_text = help_text
        help_display_box.format_and_wrap_text()
        help_display_box.fit_box_width_to_text_lines()
        help_display_box.snap_to_corner(bpy.context, corner = [0,1])
        
def crown_help_parser(scene):
    if not hasattr(scene, 'odc_props'):
        print('no ODC')
        return

    selections = odcutils.tooth_selection(bpy.context)  #weird, how do I specify better arguments?
    sel_names = [item.name for item in selections]
    help_text = 'Crown Help Wizard \n\n'
    
    if len(selections) == 0:
        help_text += 'No teeth in project! "Plan Multiple" to get started'
        update_help_box(help_text)
        return
    
    if not (bpy.context.scene.odc_props.master and 
            bpy.context.scene.odc_props.master in bpy.data.objects):
        help_text += 'Select and Set a Master Model!'
        update_help_box(help_text)
        return
    

    
    help_text += 'Selected Unit: ' + ', '.join(sel_names) + '\n'
    
    for tooth in selections:
        help_text += tooth_help_text(tooth)
        
    update_help_box(help_text)
        
    

def implant_help_parser(scene):
    if not hasattr(scene, 'odc_props'):
        print('no ODC')
        return

    selections = odcutils.implant_selection(bpy.context)  #weird, how do I specify better arguments?
    sel_names = [item.name for item in selections]

    global help_display_box
    help_text = 'Implant Help Wizard \n'
    help_text += 'Selected Unit: ' + ', '.join(sel_names) + '\n'
    
    for implant in selections:
        help_text += implant_help_text(implant)
        
    if help_text != help_display_box.raw_text:
        help_display_box.raw_text = help_text
        help_display_box.format_and_wrap_text()
        help_display_box.fit_box_width_to_text_lines()
        help_display_box.fit_box_height_to_text_lines()
        help_display_box.snap_to_corner(bpy.context, corner = [0,1])

def bridge_help_parser(scene):
    if not hasattr(scene, 'odc_props'):
        print('no ODC')
        return

    global help_display_box
    help_text = 'Bridge Help Wizard \n'
    
    
    if len(scene.odc_bridges) == 0:
        help_text += 'Need to plan a bridge \n'
        help_text += 'Select multiple single units and "Units to Bridge"'
        
        return help_text
    
    bridges = bridge_methods.active_spanning_restoration(bpy.context)
    
    for bridge in bridges:
        help_text += bridge_help_text(bridge)
      
    if help_text != help_display_box.raw_text:
        help_display_box.raw_text = help_text
        help_display_box.format_and_wrap_text()
        help_display_box.fit_box_width_to_text_lines()
        help_display_box.fit_box_height_to_text_lines()
        help_display_box.snap_to_corner(bpy.context, corner = [0,1])
        
def guide_help_parser(scene):
    if not hasattr(scene, 'odc_props'):
        print('no ODC')
        return
    
    global help_display_box
    help_text = 'Surgical Guide Help Wizard \n'    
    help_text += 'Coming Soon!!!'   
    if help_text != help_display_box.raw_text:
        help_display_box.raw_text = help_text
        help_display_box.format_and_wrap_text()
        help_display_box.fit_box_width_to_text_lines() 
        
def splint_help_parser(scene):
    if not hasattr(scene, 'odc_props'):
        print('no ODC')
        return
    
    global help_display_box
    help_text = 'Surgical Guide Help Wizard \n'    
    help_text += 'Coming Soon!!!'   
    if help_text != help_display_box.raw_text:
        help_display_box.raw_text = help_text
        help_display_box.format_and_wrap_text()
        help_display_box.fit_box_width_to_text_lines()       
    
def pontic_help_text(tooth):
    msg = 'Pontic Crown Steps: ' + tooth.name + '\n'
    msg += '1. Set Prep: '
    if tooth.prep_model and tooth.prep_model in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += '\nOptional:  Use "Set Prep" to mark gingiva for tissue pontics \n'
    
    msg += '2. Insertion Axis: '   
    if tooth.axis and tooth.axis in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += 'Please define insertion axis \n'
        
    msg += '5. Full Contour:'
    if tooth.contour in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += 'Please "Get Crown Form" to pick a tooth shape \n'
    
    msg += '6. Extra: \n'
    msg += 'Use "Pontic From Crown" to change pontic shape'
        
    return msg
    
def crown_help_text(tooth):
    
    msg = 'Simple Crown Steps: ' + tooth.name + '\n'
    msg += '1. Set Prep: '
    if tooth.prep_model and tooth.prep_model in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += '  Please select prep model or prep geometry \n'
    
    msg += '2. Insertion Axis: '   
    if tooth.axis and tooth.axis in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += 'Please define insertion axis \n'
        
    msg += '3. Margin Marking: '
    if tooth.margin and tooth.margin in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += 'Please mark margin \n'

    msg += '4. Margin Acceptance: '
    if tooth.margin in bpy.data.objects and tooth.pmargin in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += 'Please refine (optional) and accept (mandatory) margin\n'
    
    msg += '5. Full Contour:'
    if tooth.contour in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += 'Please "Get Crown Form" to pick a tooth shape \n'
        
    msg += '6. Intaglio: ' 
    if tooth.intaglio and tooth.intaglio in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += 'Please Calc Intaglio\n'
         
    msg += '7. Solid Restoration'
    if tooth.solid and tooth.solid in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += '\n Please Make Solid Restoration and then export to format of your choice!'
        
    return msg

def tooth_help_text(tooth):
    if tooth.rest_type == '1':
        msg = pontic_help_text(tooth)
    else:
        msg = crown_help_text(tooth)
        
    return msg
def implant_help_text(implant):
        
    msg = 'Simple Implant Steps: ' + implant.name + '\n'
    msg += '1. Place Implant: '
    if implant.implant and implant.implant in bpy.data.objects:
        msg += 'DONE \n'
    else:
        msg += '  Place 3d cursor at apex location and "Place Implant"'
    
    msg += '2. Inner Cylinder: '   
    if implant.inner and implant.inner in bpy.data.objects:
        msg += 'DONE '
        Cyl = bpy.data.objects[implant.inner]
        V = Cyl.dimensions
        width = '{0:.{1}f}'.format(V[0], 2)
        msg += "\n    Hole Diameter: " + width + "mm \n" 
    
    else:
        msg += 'Needed to make holes in surgical guide\n'
        
    msg += '3. Outer Cylinder: '
    if implant.outer and implant.outer in bpy.data.objects:
        
        if implant.implant and implant.implant in bpy.data.objects:
            msg += 'DONE:'
            Imp = bpy.data.objects[implant.implant]
            Cyl = bpy.data.objects[implant.outer]
            v1 = Imp.matrix_world.to_translation()
            v2 = Cyl.matrix_world.to_translation()
            V = v2 - v1
            depth = '{0:.{1}f}'.format(V.length, 2)        
            msg += "\n    Cylinder Depth: " + depth + "mm" + '\n'
        else:
            msg += 'DONE \n'
    else:
        msg += 'Needed for depth control.  Ideally do after guide base has been designed \n'
         
    return msg


def bridge_help_text(bridge):
    msg = 'Bridge: ' + bridge.name + '\n'
    
    teeth = [bpy.context.scene.odc_teeth[nm] for nm in bridge.tooth_string.split(sep=":")]
    msg += 'There are %i tooth units' % len(teeth)
    msg += '\n'
    
    msg += '1.Full Contours:'
    all_contours = [tooth.contour not in bpy.data.objects for tooth in teeth]
    if any(all_contours):
        msg += '\n Not all Full Contours created. \n Please "Get Crown Form" for all units\n'
    else:
        msg += 'DONE \n'
    
    def has_margin(tooth):
        if tooth.rest_type == '1': return True
        if tooth.margin and tooth.margin in bpy.data.objects:
            return True
        return False
    
    msg += '2.Mark Margins:'
    all_margins = [not has_margin(tooth) for tooth in teeth]  
    if any(all_margins):
        msg += '\nNot all Margins Marked. \n Please "Mark Margin" for all units\n'
    else:
        msg += 'DONE \n'
        
    msg += '3.Accept Margins:'
    all_pmargins = [tooth.pmargin not in bpy.data.objects for tooth in teeth]
    if any(all_pmargins):
        msg += ' \nNot all Margins finalized. \n Please "Refine Margin" (optional)\nPlease "Accept Margin" (mandatory)\n'
    else:
        msg += 'DONE \n'
        
    msg += '4.Seat to Margin:'
    def is_seated(tooth):
        
        if tooth.contour not in bpy.data.objects: return False
        if tooth.rest_type == '1': return True #this is a pontic
        if tooth.margin not in bpy.data.objects: return False
        Crown = bpy.data.objects[tooth.contour]
        if 'Shrinkwrap' not in Crown.modifiers: return False
        return True
           
    all_seated = [not is_seated(tooth) for tooth in teeth]
    if any(all_seated):
        msg += ' \nNot all abutments seated. \n Please "Seat to Margin" \n'
    else:
        msg += 'DONE \n'
    
    
    def has_intaglio(tooth):
        if tooth.rest_type == '1': return True  #pontic
        if tooth.intaglio and tooth.intaglio in bpy.data.objects: return True
    
        return False
    msg += '5.Calculate Intaglio: '
    all_intags = [not has_intaglio(tooth) for tooth in teeth]
    if any(all_intags):
        msg += '\n Not all intalgios calculated. \n Please "Calculate Intaglio" for units abutments\n'
    else:
        msg += 'DONE \n'
    
    msg += '6. MORE HELP TO COME!!!'
    return msg

def guide_help_text(splint):
    msg = 'No help for guides :-('
    return msg


def odc_help_draw(dummy, context):
    '''
    same for all the help modules
    '''
    global help_display_box
    help_display_box.draw()


def clear_help_handlers():
    
    global crown_help_app_handle
    global crown_help_draw_handle        
    if crown_help_draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(crown_help_draw_handle, 'WINDOW')
        crown_help_draw_handle = None
            
        bpy.app.handlers.scene_update_pre.remove(crown_help_parser)
        crown_help_app_handle = None
        
    global implant_help_app_handle
    global implant_help_draw_handle        
    if implant_help_draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(implant_help_draw_handle, 'WINDOW')
        implant_help_draw_handle = None
            
        bpy.app.handlers.scene_update_pre.remove(implant_help_parser)
        implant_help_app_handle = None
    
    global bridge_help_app_handle
    global bridge_help_draw_handle        
    if bridge_help_draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(bridge_help_draw_handle, 'WINDOW')
        bridge_help_draw_handle = None
            
        bpy.app.handlers.scene_update_pre.remove(bridge_help_parser)
        bridge_help_app_handle = None

    global guide_help_app_handle
    global guide_help_draw_handle        
    if guide_help_draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(guide_help_draw_handle, 'WINDOW')
        guide_help_draw_handle = None
            
        bpy.app.handlers.scene_update_pre.remove(guide_help_parser)
        guide_help_app_handle = None
    
     
class OPENDENTAL_OT_help_start_crown(bpy.types.Operator):
    '''
    Will add a floating text box and some GUI features which attempt
    to help the user decide what to do next....
    '''
    bl_idname='opendental.start_crown_help'
    bl_label="Crown Helper Wizard"

    @classmethod
    def poll(cls, context):
        if not hasattr(context.scene, 'odc_props'):
            return False
        return True
    
    def execute(self, context):
        #add a textbox to display information.  attach it to this
        #add a persisetent callback on scene update
        #which monitors the status of the ODC
        
        #clear previous handlers
        clear_help_handlers()
        global crown_help_app_handle
        crown_help_app_handle = bpy.app.handlers.scene_update_pre.append(crown_help_parser)
        
        global help_display_box
        if help_display_box != None:
            del help_display_box
        help_text = 'Open Dental Crown Help Wizard \n'
        selections = odcutils.tooth_selection(bpy.context)  #weird, how do I specify better arguments?
        sel_names = [item.name for item in selections]
        help_text += 'Selected Units: ' + ', '.join(sel_names) + '\n'
        help_text += 'Next Step: ' + 'TBA'
        
        help_display_box = TextBox(context,500,500,300,100,10,20, help_text)
        help_display_box.snap_to_corner(context, corner = [0,1])
        
        global crown_help_draw_handle
        crown_help_draw_handle = bpy.types.SpaceView3D.draw_handler_add(odc_help_draw, (self, context), 'WINDOW', 'POST_PIXEL')
        
        
        return {'FINISHED'}
 
class OPENDENTAL_OT_help_start_implant(bpy.types.Operator):
    '''
    Will add a floating text box and some GUI features which attempt
    to help the user decide what to do next....
    '''
    bl_idname='opendental.start_implant_help'
    bl_label="Implant Helper Wizard"

    @classmethod
    def poll(cls, context):
        if not hasattr(context.scene, 'odc_props'):
            return False
        return True
    
    def execute(self, context):
        #add a textbox to display information.  attach it to this
        #add a persisetent callback on scene update
        #which monitors the status of the ODC
        
        #clear previous handlers
        clear_help_handlers()
        global implant_help_app_handle
        implant_help_app_handle = bpy.app.handlers.scene_update_pre.append(implant_help_parser)
        
        global help_display_box
        if help_display_box != None:
            del help_display_box
        help_text = 'Open Dental Implant Help Wizard \n'
        selections = odcutils.implant_selection(bpy.context)  #weird, how do I specify better arguments?
        sel_names = [item.name for item in selections]
        help_text += 'Selected Implants: ' + ', '.join(sel_names) + '\n'
        help_text += 'Next Step: ' + 'TBA'
        
        help_display_box = TextBox(context,500,500,300,100,10,20, help_text)
        help_display_box.snap_to_corner(context, corner = [0,1])
        
        global implant_help_draw_handle
        implant_help_draw_handle = bpy.types.SpaceView3D.draw_handler_add(odc_help_draw, (self, context), 'WINDOW', 'POST_PIXEL')    
        return {'FINISHED'}

class OPENDENTAL_OT_help_start_bridge(bpy.types.Operator):
    '''
    Will add a floating text box and some GUI features which attempt
    to help the user decide what to do next....
    '''
    bl_idname='opendental.start_bridge_help'
    bl_label="Bridge Helper Wizard"

    @classmethod
    def poll(cls, context):
        if not hasattr(context.scene, 'odc_props'):
            return False
        return True
    
    def execute(self, context):
        #add a textbox to display information.  attach it to this
        #add a persisetent callback on scene update
        #which monitors the status of the ODC
        
        #clear previous handlers
        clear_help_handlers()
        global bridge_help_app_handle
        bridge_help_app_handle = bpy.app.handlers.scene_update_pre.append(bridge_help_parser)
        
        global help_display_box
        if help_display_box != None:
            del help_display_box
        help_text = 'Open Dental Bridge Help Wizard \n'
        help_text += 'Next Step: ' + 'TBA'
        
        help_display_box = TextBox(context,500,500,300,100,10,20, help_text)
        help_display_box.snap_to_corner(context, corner = [0,1])
        
        global bridge_help_draw_handle
        bridge_help_draw_handle = bpy.types.SpaceView3D.draw_handler_add(odc_help_draw, (self, context), 'WINDOW', 'POST_PIXEL')    
        return {'FINISHED'}
    
class OPENDENTAL_OT_help_start_guide(bpy.types.Operator):
    '''
    Will add a floating text box and some GUI features which attempt
    to help the user decide what to do next....
    '''
    bl_idname='opendental.start_guide_help'
    bl_label="Guide Helper Wizard"

    @classmethod
    def poll(cls, context):
        if not hasattr(context.scene, 'odc_props'):
            return False
        return True
    
    def execute(self, context):
        #add a textbox to display information.  attach it to this
        #add a persisetent callback on scene update
        #which monitors the status of the ODC
        
        #clear previous handlers
        clear_help_handlers()
        global guide_help_app_handle
        guide_help_app_handle = bpy.app.handlers.scene_update_pre.append(guide_help_parser)
        
        global help_display_box
        if help_display_box != None:
            del help_display_box
        help_text = 'Open Dental Guide Help Wizard \n'
        help_text += 'Next Step: ' + 'TBA'
        
        help_display_box = TextBox(context,500,500,300,100,10,20, help_text)
        help_display_box.snap_to_corner(context, corner = [0,1])
        
        global guide_help_draw_handle
        guide_help_draw_handle = bpy.types.SpaceView3D.draw_handler_add(odc_help_draw, (self, context), 'WINDOW', 'POST_PIXEL')    
        return {'FINISHED'}
     
class OPENDENTAL_OT_help_stop(bpy.types.Operator):
    '''
    Remove Floating Help Box
    '''
    bl_idname='opendental.stop_help'
    bl_label="Open Dental Stop Helper Wizard"

    @classmethod
    def poll(cls, context):
        if not hasattr(context.scene, 'odc_props'):
            return False
        return True
    
    def execute(self, context):

        clear_help_handlers()
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_crown_report(bpy.types.Operator):
    '''
    Will add a text object to the .blend file which tells
    the information about all the units being designed and 
    their details.
    '''
    bl_idname='opendental.crown_report'
    bl_label="Crown and Bridge Report"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        if not hasattr(context.scene, 'odc_props'):
            return False
        condition_1 = len(context.scene.odc_teeth) > 0
        return condition_1
    
    def execute(self,context):

        sce = context.scene
        if 'Crown Report' in bpy.data.texts:
            Report = bpy.data.texts['Crown Report']
            Report.clear()
        else:
            Report = bpy.data.texts.new("Crown Report")
    
    
        Report.write("Open Dental CAD Crown Project Report")
        Report.write("\n")
        Report.write('Date and Time: ')
        Report.write(time.asctime())
        Report.write("\n")
    
        Report.write("There is/are %i crown(s)" % len(sce.odc_teeth))
        Report.write("\n")
        Report.write("_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _")
        Report.write("\n")
        Report.write("\n")
    
        for tooth in sce.odc_teeth:
            Report.write('Tooth #%i' % int(tooth.name))
            Report.write("\n")
            for pair in tooth.items():
                Report.write(str(pair))
                Report.write("\n")
            
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OPENDENTAL_OT_crown_report)
    bpy.utils.register_class(OPENDENTAL_OT_help_start_crown)
    bpy.utils.register_class(OPENDENTAL_OT_help_start_implant)
    bpy.utils.register_class(OPENDENTAL_OT_help_start_bridge)
    bpy.utils.register_class(OPENDENTAL_OT_help_start_guide)
    bpy.utils.register_class(OPENDENTAL_OT_help_stop)
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_crown_report)
    bpy.utils.unregister_class(OPENDENTAL_OT_help_start_crown)
    bpy.utils.unregister_class(OPENDENTAL_OT_help_start_implant)
    bpy.utils.unregister_class(OPENDENTAL_OT_help_start_bridge)
    bpy.utils.unregister_class(OPENDENTAL_OT_help_start_guide)
    bpy.utils.unregister_class(OPENDENTAL_OT_help_stop)
    
    
    clear_help_handlers()
    
if __name__ == "__main__":
    register()