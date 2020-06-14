import bpy
import os
from odcutils import get_settings


class SCENE_UL_odc_teeth(bpy.types.UIList):
    # The draw_item function is called for each item of the collection that is visible in the list.
    #   data is the RNA object containing the collection,
    #   item is the current drawn item of the collection,
    #   icon is the "computed" icon for the item (as an integer, because some objects like materials or textures
    #   have custom icons ID, which are not available as enum items).
    #   active_data is the RNA object containing the active property for the collection (i.e. integer pointing to the
    #   active item of the collection).
    #   active_propname is the name of the active property (use 'getattr(active_data, active_propname)').
    #   index is index of the current item in the collection.
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        sce = data
        tooth = item
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # You should always start your row layout by a label (icon + text), this will also make the row easily
            # selectable in the list!
            # We use icon_value of label, as our given icon is an integer value, not an enum ID.
            layout.label(text=tooth.name)
            # And now we can add other UI stuff...
            # Here, we add nodes info if this material uses (old!) shading nodes.

        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value="NODE")


class SCENE_UL_odc_implants(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        sce = data
        implant = item
        if self.layout_type in {"DEFAULT", "COMPACT"}:

            layout.label(text=implant.name)

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value="NODE")


class SCENE_UL_odc_bridges(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        sce = data
        bridge = item
        if self.layout_type in {"DEFAULT", "COMPACT"}:

            layout.label(text=bridge.name)

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value="NODE")


class SCENE_UL_odc_splints(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        sce = data
        splint = item
        if self.layout_type in {"DEFAULT", "COMPACT"}:

            layout.label(text=splint.name)

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value="NODE")

class UNDERCUTS_props(bpy.types.PropertyGroup):

    Models = ["Preview", "Solid"]
    items = []
    for i in range(len(Models)):
        item = (str(Models[i]), str(Models[i]), str(""), int(i))
        items.append(item)

    Modelsprop: bpy.props.EnumProperty(items=items, description="", default="Solid")

class BASE_props(bpy.types.PropertyGroup):

    Models = ["Solid", "Hollow"]
    items = []
    for i in range(len(Models)):
        item = (str(Models[i]), str(Models[i]), str(""), int(i))
        items.append(item)

    Modelsprop: bpy.props.EnumProperty(items=items, description="", default="Solid")

class UNDERCUTS_view_props(bpy.types.PropertyGroup):

    colors = ["No color selected", "Violet", "Blue", "Pink", "Green"]
    items = []
    for i in range(len(colors)):
        item = (str(colors[i]), str(colors[i]), str(""), int(i))
        items.append(item)

    colorprop: bpy.props.EnumProperty(items=items, description="", default="No color selected")

    survey_quaternion : bpy.props.FloatVectorProperty(name="survey_q", description="stors the surveing quaternion rotation", size=4, subtype='QUATERNION')


class VIEW3D_PT_ODCModels(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "Open Dental CAD"
    bl_label = "Model Operations"
    bl_context = ""

    def draw(self, context):
        sce = bpy.context.scene
        layout = self.layout

        addon_prefs = get_settings()

        """
        # Title and info icon :
        row = layout.row()
        row.label(text="Model Tools")
        row.operator(
            "wm.url_open", text="", icon="INFO"
        ).url = "https://github.com/patmo141/odc_public/wiki"
        """

        

        # Clean Model Button :
        row = layout.row()
        row.operator("opendental.clean_model", text="Clean Model", icon="BRUSH_DATA")

        layout.row().separator()
        # Model Base Button :
        row = layout.row()
        props = context.scene.BASE_props
        row.prop(props, "Modelsprop", text="Type")
        row.operator(
            "opendental.model_base_type_select", text="Model Base"
        )

        row = layout.row()
        if context.scene.base_trim_mode == False:
            row.operator("opendental.trim_base", text="Trim Base")
        elif context.scene.base_trim_mode == True:
            row.operator("opendental.trim_base_confirm", text="Confirm")
            
        layout.row().separator()
        # Model Remesh Button :
        row = layout.row()
        row.operator("opendental.remesh_model", text="Remesh Model", icon="VIEW_ORTHO")

        # Decimate Model Button :
        row = layout.row()
        row.operator(
            "opendental.decimate_model", text="Decimate Model", icon="MOD_DECIM"
        )
        layout.row().separator()
        layout.label(text="Survey undercut color:")
        row = layout.row(align=True)
        props = context.scene.UNDERCUTS_view_props
        row.prop(props, "colorprop", text="")
        row.operator("opendental.view_silhouette_survey", text="Survey Model Undercuts")

        row = layout.row()
        props = context.scene.UNDERCUTS_props
        # Modelsprop = props.Modelsprop
        row.prop(props, "Modelsprop", text="Select Algorithm")
        row.operator("opendental.view_blockout_undercuts", text="Create Blockout")
        """
        row = layout.row()
        col = row.column(align=True)

        col.operator("opendental.meta_scaffold_create", text="Decimate Surface")
        col.operator("opendental.meta_offset_surface", text="Meta Offset Surface")
        if context.object and context.object.type == "META":
            col.operator("object.convert", text="Convert Meta Surface to Mesh")

        col.operator("opendental.simple_offset_surface", text="Simple Offset")
        # col.operator("opendental.simple_base", text = "Simple Base")
        """



        # row = layout.row()
        # row.operator("opendental.view_blockout_undercuts", text = "Blockout Model Undercuts")

class VIEW3D_PT_ODCSettings(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "Open Dental CAD"
    bl_label = "ODC Control Panel"
    bl_context = ""

    def draw(self, context):
        sce = bpy.context.scene
        layout = self.layout

        # split = layout.split()

        row = layout.row()

        row.operator(
            "wm.url_open", text="Wiki", icon="INFO"
        ).url = "https://github.com/patmo141/odc_public/wiki"
        row.operator(
            "wm.url_open", text="Errors", icon="ERROR"
        ).url = "https://github.com/patmo141/odc_public/issues"
        row.operator(
            "wm.url_open", text="Forum", icon="QUESTION"
        ).url = "https://www.zohodiscussions.com/blenderdental#Forum/general/help"

        # if not odc.odc_restricted_registration:
        # row = layout.row()
        # row.operator("opendental.activate",text="Activate")
        # row = layout.row()
        # row.prop(context.user_preferences.addons['odc_public'].preferences,"tooth_lib")

        # row = layout.row()
        # row.prop(context.user_preferences.addons['odc_public'].preferences, "mat_lib")

        # row = layout.row()
        # row.prop(context.user_preferences.addons['odc_public'].preferences, "imp_lib")

        col = self.layout.column(align=True)
        # col.label(text="Trace Tools")
        row = col.row()
        row.prop(sce.odc_props, "show_teeth", text="Teeth", icon="LAYER_ACTIVE")
        row.prop(sce.odc_props, "show_implant", text="Implants", icon="LAYER_ACTIVE")
        row.prop(sce.odc_props, "show_bridge", text="Bridges", icon="LAYER_ACTIVE")
        row = col.row()
        row.prop(sce.odc_props, "show_splint", text="Splints", icon="LAYER_ACTIVE")
        row.prop(sce.odc_props, "show_ortho", text="Ortho", icon="LAYER_ACTIVE")


class VIEW3D_PT_ODCTeeth(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "Open Dental CAD"
    bl_label = "Tooth Restorations"
    bl_context = ""

    def draw(self, context):
        if not context.scene.odc_props.show_teeth:
            return
        sce = bpy.context.scene
        layout = self.layout

        # split = layout.split()

        row = layout.row()
        # row.operator("wm.url_open", text = "", icon="QUESTION").url = "https://sites.google.com/site/blenderdental/contributors"
        row.operator("opendental.start_crown_help", text="", icon="QUESTION")
        row.operator("opendental.stop_help", text="", icon="CANCEL")
        row = layout.row()
        row.template_list(
            "SCENE_UL_odc_teeth", "", sce, "odc_teeth", sce, "odc_tooth_index"
        )

        col = row.column(align=True)
        # col.operator("opendental.tooth_lib_refresh", text = "Update Tooth Lib")
        col.operator("opendental.add_tooth_restoration", text="Add a Tooth")
        col.operator("opendental.remove_tooth_restoration", text="Remove a Tooth")
        col.operator("opendental.plan_restorations", text="Plan Multiple")

        # row = layout.row()
        # row.operator("opendental.implant_inner_cylinder", text = "Implant Inner Cylinders")

        row = layout.row()
        row.operator("opendental.crown_report", text="Project Report")

        row = layout.row()
        row.operator("opendental.center_objects", text="Center Objects")

        row = layout.row()
        row.operator("opendental.set_master", text="Set Master")

        row = layout.row()
        row.operator("opendental.set_as_prep", text="Set Prep")

        row = layout.row()
        row.operator("opendental.set_opposing", text="Set Opposing")

        row = layout.row()
        row.operator("opendental.set_mesial", text="Set Mesial")

        row = layout.row()
        row.operator("opendental.set_distal", text="Set Distal")

        row = layout.row()
        row.operator("opendental.insertion_axis", text="Insertion Axis")

        row = layout.row()
        row.operator("opendental.mark_crown_margin", text="Mark Margin")

        row = layout.row()
        row.operator("opendental.refine_margin", text="Refine Margin")

        row = layout.row()
        row.operator("opendental.accept_margin", text="Accept Margin")

        row = layout.row()
        row.operator("opendental.get_crown_form", text="Get Crown From")

        if context.object and "LAPLACIANDEFORM" in [
            mod.type for mod in context.object.modifiers
        ]:
            row = layout.row()
            row.operator("opendental.flexitooth_keep", text="FlexiTooth Keep")
        else:
            row = layout.row()
            row.operator("opendental.flexitooth", text="FlexiTooth")

        if context.object and "LATTICE" in [
            mod.type for mod in context.object.modifiers
        ]:
            row = layout.row()
            row.operator("opendental.keep_shape", text="Lattice Deform Keep")
        else:
            row = layout.row()
            row.operator("opendental.lattice_deform", text="Lattice Deform Crown")

        row = layout.row()
        row.operator("opendental.seat_to_margin", text="Seat To Margin")

        row = layout.row()
        row.operator(
            "opendental.cervical_convergence", text="Angle Cervical Convergence"
        )

        row = layout.row()
        row.operator("opendental.grind_occlusion", text="Grind Occlusion")

        row = layout.row()
        row.operator("opendental.grind_contacts", text="Grind Contacts")

        row = layout.row()
        row.operator("opendental.calculate_inside", text="Calculate Intaglio")

        row = layout.row()
        row.operator("opendental.prep_from_crown", text="Artificial Intaglio")

        row = layout.row()
        row.operator("opendental.make_solid_restoration", text="Solid Restoration")

        # row = layout.row()
        # row.operator("opendetnal.lattice_deform", text = "Place/Replace Implant")


class VIEW3D_PT_ODCImplants(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "Open Dental CAD"
    bl_label = "Implant Restorations"
    bl_context = ""

    def draw(self, context):
        if not context.scene.odc_props.show_implant:
            return
        sce = bpy.context.scene
        layout = self.layout

        # split = layout.split()

        # row.label(text="By Patrick Moore and others...")
        # row.operator("wm.url_open", text = "", icon="QUESTION").url = "https://sites.google.com/site/blenderdental/contributors"
        row = layout.row()
        row.operator("opendental.start_implant_help", text="", icon="QUESTION")
        row.operator("opendental.stop_help", text="", icon="CANCEL")

        row = layout.row()
        row.label(text="Implant List:")
        row = layout.row()
        row.template_list(
            "SCENE_UL_odc_implants", "", sce, "odc_implants", sce, "odc_implant_index"
        )

        col = row.column(align=True)
        col.operator("opendental.add_implant_restoration", text="Add Implant")
        col.operator("opendental.remove_implant_restoration", text="Remove Implant")
        #col.operator("opendental.plan_restorations", text="Plan Multiple")
        col.label(text="Implant Library:")
        col.prop(context.scene.implant_lib_list, "Type")

        # if odc.odc_restricted_registration:
        row = layout.row()
        row.operator("opendental.place_implant", text="Place/Replace Implant")

        row = layout.row()
        row.operator("opendental.implant_from_crown", text="Place Implants From Crown")

        # else:
        # row = layout.row()
        # row.label(text = "Implant library not loaded :-(")
        #col = layout.column(align = True)
        #col.prop(context.scene, "splint_shell_thickness")
        #col.prop(context.scene, "splint_shell_offset")

        row = layout.row()
        row.label(text="Sleeve Parameters:")
        row = layout.row()
        row.prop(context.scene, "sleeve_diameter")
        row = layout.row()
        row.operator("opendental.place_guide_sleeve", text="Place Sleeve")
        row = layout.row()
        row.operator(
            "opendental.implant_inner_cylinder", text="Implant Inner Cylinders"
        )

        row = layout.row()
        row.label(text="Guide Platform Parameters:")
        row = layout.row()
        row.prop(context.scene, "platform_diameter")
        row = layout.row()
        row.prop(context.scene, "platform_height")
        row = layout.row()
        row.prop(context.scene, "platform_offset")
        row = layout.row()
        row.operator("opendental.implant_guide_cylinder", text="Place Guide Platform")

        row = layout.row()
        row.label(text="Splint Operators:")
        row = layout.row()
        row.operator("opendental.implant_guide_cylinder", text="Finalize Guide")
        row = layout.row()
        row.operator("opendental.implant_guide_cylinder", text="Update Guide")



class ImplantTypeListProperties(bpy.types.PropertyGroup):
    mode_options = [
        ("mesh.primitive_plane_add", "Plane", '', 'MESH_PLANE', 0),
        ("mesh.primitive_cube_add", "Cube", '', 'MESH_CUBE', 1)
    ]

    Type : bpy.props.EnumProperty(
        items=mode_options,
        description="implant library",
        default="mesh.primitive_plane_add",
        update=None #execute_operator
    )
def execute_operator(self, context):
    eval('bpy.ops.' + self.Type + '()')

class VIEW3D_PT_ODCBridges(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "Open Dental CAD"
    bl_label = "Bridge Restorations"
    bl_context = ""

    def draw(self, context):
        if not context.scene.odc_props.show_bridge:
            return
        sce = bpy.context.scene
        layout = self.layout

        # split = layout.split()

        # row = layout.row()
        # row.label(text="By Patrick Moore and others...")
        # row.operator("wm.url_open", text = "", icon="QUESTION").url = "https://sites.google.com/site/blenderdental/contributors"

        row = layout.row()
        row.label(text="Bridges")
        row = layout.row()
        row.operator("opendental.start_bridge_help", text="", icon="QUESTION")
        row.operator("opendental.stop_help", text="", icon="CANCEL")

        row = layout.row()
        row.template_list(
            "SCENE_UL_odc_bridges", "", sce, "odc_bridges", sce, "odc_bridge_index"
        )

        col = row.column(align=True)
        # col.operator("opendental.add_implant_restoration", text = "Add a Space")
        col.operator("opendental.remove_bridge_restoration", text="Remove a Bridge")
        # col.operator("opendental.plan_restorations", text = "Plan Multiple")

        row = layout.row()
        row.operator("opendental.draw_arch_curve", text="Draw Arch Curve")

        row = layout.row()
        row.operator("opendental.teeth_to_arch", text="Set Teeth on Curve")

        row = layout.row()
        row.operator("opendental.occlusal_scheme", text="Occlusal Setup to Curve")

        row = layout.row()
        row.operator("opendental.arch_plan_keep", text="Keep Arch Plan")

        row = layout.row()
        row.operator("opendental.define_bridge", text="Plan Selected Units as Bridge")

        # row = layout.row()
        # row.operator("opendental.make_prebridge", text = "Make Pre Bridge")

        # row = layout.row()
        # row.operator("opendental.bridge_individual", text = "Bridge Individual")

        row = layout.row()
        row.operator("opendental.bridge_boolean", text="Make Bridge Shell")

        row = layout.row()
        row.operator("opendental.solid_bridge", text="Join Intaglios to Shell")


class VIEW3D_PT_ODCSplints(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "Open Dental CAD"
    bl_label = "Splints"
    bl_context = ""

    # undercut_solver_mode_options = bpy.props.EnumProperty(items= (("opendental.view_blockout_undercuts", "Patrick's Method", "", 1), ("opendental.view_blockout_undercuts_issam", "Issam's Method", "", 2)), name="undercut_solvers")

    def draw(self, context):
        if not context.scene.odc_props.show_splint:
            return
        sce = bpy.context.scene
        layout = self.layout

        # split = layout.split()

        # row = layout.row()
        # row.label(text="By Patrick Moore and others...")
        # row.operator("wm.url_open", text = "", icon="QUESTION").url = "https://sites.google.com/site/blenderdental/contributors"

        row = layout.row()
        row.label(text="Splints")
        row = layout.row()
        row.operator(
            "wm.url_open", text="", icon="INFO"
        ).url = "https://github.com/patmo141/odc_public/wiki/Splint-Basics"
        row.operator("opendental.start_guide_help", text="", icon="QUESTION")
        row.operator("opendental.stop_help", text="", icon="CANCEL")
        row = layout.row()
        row.template_list(
            "SCENE_UL_odc_splints", "", sce, "odc_splints", sce, "odc_splint_index"
        )

        col = row.column(align=True)
        # col.operator("opendental.add_implant_restoration", text = "Add a Space")
        col.operator("opendental.add_splint", text="Start a Splint")
        col.operator("opendental.remove_splint", text="Remove Splint")

        # New row
        row = layout.row()
        if context.scene.splint_mode == "OBJECT":
            # Draw button
            row = layout.row()
            row.operator("opendental.splint_outline", text="Outline Area")
        if context.scene.splint_mode == "PAINT":
            # Draw button
            row = layout.row()
            row.operator("opendental.splint_outline", text="Exit Outline")
            # Draw button
            row = layout.row()
            row.operator("opendental.splint_outline_paint", text="Add Area")
            row = layout.row()
            row.operator("opendental.splint_outline_erase", text="Erase Area")

        col = layout.column(align = True)
        col.prop(context.scene, "splint_shell_thickness")
        col.prop(context.scene, "splint_shell_offset")

        layout.prop_search(context.scene, "splint_base_model", context.scene, "objects")
        
        # Make Button
        row = layout.row()
        row.operator("opendental.splint_make", text="Finalize Splint")


class VIEW3D_PT_ODCOrtho(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "Open Dental CAD"
    bl_label = "Orthodontics"
    bl_context = ""

    def draw(self, context):
        if not context.scene.odc_props.show_ortho:
            return
        sce = bpy.context.scene
        layout = self.layout

        addon_prefs = get_settings()

        row = layout.row()
        row.label(text="Orthodontics")
        row.operator(
            "wm.url_open", text="", icon="INFO"
        ).url = "https://github.com/patmo141/odc_public/wiki"

        layout.label(text="Brackets")

        row = layout.row()
        row.prop(addon_prefs, "ortho_lib", text="")
        row = layout.row()
        row.prop(addon_prefs, "bracket", text="Bracket")
        row = layout.row()
        row.prop(addon_prefs, "bgauge_override", text="")
        row.prop(addon_prefs, "bracket_gauge", text="")

        row = layout.row()
        row.operator("opendental.place_ortho_bracket", text="Place Bracket Guide")

        row = layout.row()
        row.operator("opendental.place_static_bracket", text="Place Bracket at Cursor")

        layout.label(text="Treatment Animation/Setup")
        row = layout.row()
        row.operator("opendental.show_max_teeth", text="Upper")
        row.operator("opendental.show_man_teeth", text="Lower")

        row = layout.row()
        row.operator("opendental.show_left_teeth", text="Left")
        row.operator("opendental.show_right_teeth", text="Right")

        row = layout.row()
        col = row.column(align=True)
        col.operator("opendental.add_bone_roots", "Add roots")
        if context.mode == "OBJECT":
            col.operator("opendental.adjust_bone_roots", "Adjust Roots")
        elif context.mode == "EDIT_ARMATURE" and context.object.type == "ARMATURE":
            col.operator("object.mode_set", "Finish Roots").mode = "OBJECT"

        col.operator("opendental.set_roots_parents", "Set Root Parents")

        if context.scene.frame_current != 0 and not any(
            [ob.animation_data for ob in context.scene.objects]
        ):
            row = layout.row()
            row.label("Initial position not captured!", icon="ERROR")
            row = layout.row()
            row.label("Set Frame to 0 and record initial position")
        else:
            row = layout.row()
            row.operator("opendental.set_treatment_keyframe", "Capture Positions")

        row = layout.row()
        row.prop(context.scene, "frame_current", text="")

        layout.label(text="Physics Simulation Tools")

        row = layout.row()
        col = row.column(align=True)
        col.operator("opendental.add_physics_scene", "Add Physics Scene")
        col.operator("opendental.physics_sim_setup", "Setup Physics Simulation")
        col.operator("opendental.add_forcefields", "Add Forcefields")

        col.operator("opendental.limit_physics_movements", "Limit Movement")
        col.operator("opendental.unlimit_physics_movements", "Unlimit Movement")
        col.operator("opendental.lock_physics_movements", "Lock Tooth")
        col.operator("opendental.unlock_physics_movements", "Unlock Tooth")

        layout.label(text="Simulation Timeline")
        row = layout.row()
        row.operator("screen.animation_play", icon="PLAY")
        row.prop(context.scene, "frame_current")
        row.operator("screen.frame_jump", icon="FILE_REFRESH").end = False

        # Big render button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("opendental.keep_simulation_results", "Keep Simulation")


class VIEW3D_PT_ODCDentures(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "Open Dental CAD"
    bl_label = "Dentures"
    bl_context = ""

    def draw(self, context):
        sce = bpy.context.scene
        layout = self.layout

        addon_prefs = get_settings()

        row = layout.row()
        row.label(text="Dentures")
        row.operator(
            "wm.url_open", text="", icon="INFO"
        ).url = "https://github.com/patmo141/odc_public/wiki"

        row = layout.row()
        col = row.column(align=True)
        # col.operator("opendental.add_implant_restoration", text = "Add a Space")
        col.operator(
            "opendental.meta_scaffold_create", text="Make Baseplate/Tray Scaffold"
        )

        col.operator("opendental.meta_custom_tray", text="Make Meta Custom Tray")
        col.operator("opendental.meta_offset_surface", text="Make Meta Baseplate")
        col.operator("opendental.meta_rim_from_curve", text="Make Meta Wax Rim")

        if context.object and context.object.type == "META":
            col.operator("object.convert", text="Convert Meta Baseplate to Mesh")

        col.operator(
            "opendental.denture_boolean_intaglio", text="Boolean with Master Cast"
        )




def register():
    bpy.utils.register_class(VIEW3D_PT_ODCModels)
    bpy.utils.register_class(SCENE_UL_odc_teeth)


    bpy.utils.register_class(SCENE_UL_odc_implants)
    #implant library list
    bpy.utils.register_class(ImplantTypeListProperties)
    bpy.types.Scene.implant_lib_list = bpy.props.PointerProperty(type=ImplantTypeListProperties)
    #implant sleeve diameter
    bpy.types.Scene.sleeve_diameter = bpy.props.StringProperty(name = "Diameter", description = "Set implant/sleeve diameter (mm).", default = "")
    #bpy.types.Scene.sleeve_height = bpy.props.StringProperty(name = "Height", description = "Set implant/sleeve diameter.", default = "")
    #implant splint/guide platform diameter and offset
    bpy.types.Scene.platform_diameter = bpy.props.StringProperty(name = "Diameter", description = "Set guide platform diameter (mm).", default = "")
    bpy.types.Scene.platform_height = bpy.props.StringProperty(name = "Height", description = "Set guide platform height (mm).", default = "")
    bpy.types.Scene.platform_offset = bpy.props.StringProperty(name = "Offset", description = "Set guide platform offset (mm).", default = "")

    bpy.utils.register_class(SCENE_UL_odc_bridges)
    bpy.utils.register_class(SCENE_UL_odc_splints)
    bpy.utils.register_class(VIEW3D_PT_ODCSettings)
    bpy.utils.register_class(VIEW3D_PT_ODCTeeth)
    bpy.utils.register_class(VIEW3D_PT_ODCImplants)
    bpy.utils.register_class(VIEW3D_PT_ODCBridges)
    bpy.utils.register_class(VIEW3D_PT_ODCSplints)
    bpy.utils.register_class(VIEW3D_PT_ODCOrtho)
    bpy.utils.register_class(VIEW3D_PT_ODCDentures)

    # bpy.utils.register_module(__name__)
    bpy.utils.register_class(UNDERCUTS_props)
    # Register UNDERCUTS_props
    bpy.types.Scene.UNDERCUTS_props = bpy.props.PointerProperty(type=UNDERCUTS_props)
    # Register model base props
    bpy.utils.register_class(BASE_props)
    bpy.types.Scene.BASE_props = bpy.props.PointerProperty(type=BASE_props)
    #register base trim mode state var
    bpy.types.Scene.base_trim_mode = bpy.props.BoolProperty(name="base_trim_mode", default=False)
    #register splint mode state var
    bpy.types.Scene.splint_mode = bpy.props.StringProperty(name="splint_mode", default="OBJECT") #other option is "PAINT" to unhide the add/erase buttons in weight paint mode
    #register splint thickness input
    bpy.types.Scene.splint_shell_thickness = bpy.props.StringProperty(name = "Thickness", description = "Set shell thickness in mm.", default = "3.0")
    #register splint offset input
    bpy.types.Scene.splint_shell_offset = bpy.props.StringProperty(name = "Offset", description = "Set shell offset from model in mm.", default = "0.5")
    #register splint base model selection
    bpy.types.Scene.splint_base_model = bpy.props.StringProperty(name = "Base Model", description = "Set the working dental model.")

    bpy.utils.register_class(UNDERCUTS_view_props)
    # Register UNDERCUTS_props
    bpy.types.Scene.UNDERCUTS_view_props = bpy.props.PointerProperty(
        type=UNDERCUTS_view_props
    )

    bpy.types.Scene.pre_surveyed = bpy.props.BoolProperty(name="bool_pre_survey", description="A bool property", default = False)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_ODCModels)
    bpy.utils.unregister_class(SCENE_UL_odc_teeth)
    bpy.utils.unregister_class(SCENE_UL_odc_implants)
    #implant library list
    del bpy.types.Scene.implant_lib_list
    bpy.utils.unregister_class(ImplantTypeListProperties)
    #implant sleeve diameter
    del bpy.types.Scene.sleeve_diameter
    #implant splint/guide platform diameter, height, offset
    del bpy.types.Scene.platform_diameter
    del bpy.types.Scene.platform_height
    del bpy.types.Scene.platform_offset

    bpy.utils.unregister_class(SCENE_UL_odc_bridges)
    bpy.utils.unregister_class(SCENE_UL_odc_splints)
    bpy.utils.unregister_class(VIEW3D_PT_ODCTeeth)
    bpy.utils.unregister_class(VIEW3D_PT_ODCImplants)
    bpy.utils.unregister_class(VIEW3D_PT_ODCBridges)
    bpy.utils.unregister_class(VIEW3D_PT_ODCSettings)
    bpy.utils.unregister_class(VIEW3D_PT_ODCBridges)
    bpy.utils.unregister_class(VIEW3D_PT_ODCSplints)
    bpy.utils.unregister_class(VIEW3D_PT_ODCOrtho)
    bpy.utils.unregister_class(VIEW3D_PT_ODCDentures)
    

    bpy.utils.unregister_class(UNDERCUTS_props)
    # delete UNDERCUTS_props  on unregister
    del bpy.types.Scene.UNDERCUTS_props
    # delete model base props
    del bpy.types.Scene.BASE_props
    del bpy.types.Scene.base_trim_mode
    # delete splint mode state var
    del bpy.types.Scene.splint_mode
    # delete splint thickness input
    del bpy.types.Scene.splint_shell_thickness
    # delete splint offset input
    del bpy.types.Scene.splint_shell_offset
    # delete splint base model selection
    del bpy.types.Scene.splint_base_model

    bpy.utils.unregister_class(UNDERCUTS_view_props)
    # $ delete UNDERCUTS_props  on unregister
    del bpy.types.Scene.UNDERCUTS_view_props

    del bpy.types.Scene.pre_surveyed


if __name__ == "__main__":
    register()
