import bpy
from bpy.types import Panel, Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper


class RENDER_main_panel(Panel):
    bl_idname = "RENDER_main_panel"
    bl_label = "Render settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("freestyle_render_set_param_op.operator", icon="RENDER_STILL")


class FREESTYLE_RENDER_set_param_op(Operator):
    bl_label = "Set freestyle"
    bl_idname = "freestyle_render_set_param_op.operator"

    def execute(self, context):
        bpy.context.scene.render.use_freestyle = True
        view_layer = bpy.context.scene.view_layers["ViewLayer"]
        view_layer.use_freestyle = True
        freestyle_settings = view_layer.freestyle_settings
        freestyle_settings.crease_angle = 1.74533  # 100° in radian
        # bpy.ops.scene.freestyle_lineset_remove()
        while len(freestyle_settings.linesets) != 2:
            if len(freestyle_settings.linesets) > 2:
                bpy.ops.scene.freestyle_lineset_remove()
            else:
                bpy.ops.scene.freestyle_lineset_add()
        default_lineset = freestyle_settings.linesets[0]
        default_lineset.name = "Default"
        default_lineset.select_silhouette = True
        default_lineset.select_crease = False
        default_lineset.select_border = False
        default_lineset.select_edge_mark = True
        default_lineset.select_external_contour = True

        crease_angle_lineset = freestyle_settings.linesets[1]
        crease_angle_lineset.name = "Crease angle"
        crease_angle_lineset.select_silhouette = False
        crease_angle_lineset.select_crease = True
        crease_angle_lineset.select_border = False
        crease_angle_lineset.select_edge_mark = False
        crease_angle_lineset.select_external_contour = False
        bpy.ops.scene.freestyle_alpha_modifier_add(type="CREASE_ANGLE")
        crease_angle_lineset.linestyle.name = "Crease angle"
        crease_angle_lineset.linestyle.alpha_modifiers[
            "Crease Angle"
        ].angle_min = 1.39626  # 80° in radian
        crease_angle_lineset.linestyle.alpha_modifiers[
            "Crease Angle"
        ].angle_max = 1.74533  # 100° in radian

        return {"FINISHED"}


class DISPLAY_COLOR_main_panel(Panel):
    bl_idname = "DISPLAY_COLOR_main_panel"
    bl_label = "Viewport display color"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick tools"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "display_color_reset_everything.operator", icon="DECORATE_OVERRIDE"
        )


class DISPLAY_COLOR_reset_everything(Operator):
    bl_label = "Reset"
    bl_idname = "display_color_reset_everything.operator"

    def execute(self, context):
        for mesh in [obj for obj in bpy.data.objects if obj.type == "MESH"]:
            for slot in mesh.material_slots:
                material = slot.material
                print("Mesh", mesh.name, "slot", slot, "material", material)
                background_node = material.node_tree.nodes.get("Background", None)
                if background_node:
                    material.diffuse_color = background_node.inputs[
                        "Color"
                    ].default_value
        return {"FINISHED"}


class ARMATURE_NAME_REMAP_PT_main_panel(Panel):
    bl_label = "Armature rename"
    bl_idname = "ARMATURE_NAME_REMAP_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick tools"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature_name_min_maj.myop_operator", icon="SMALL_CAPS")
        layout.separator()
        layout.operator("armature_name_export.myop_operator", icon="EXPORT")
        layout.operator("armature_name_remap.myop_operator", icon="IMPORT")


class ARMATURE_NAME_MIN_MAJ_OT_my_op(Operator):
    bl_label = "Upper '_l' and '_r'"
    bl_idname = "armature_name_min_maj.myop_operator"

    def execute(self, context):
        active = bpy.context.active_object
        if active.type != "ARMATURE":
            self.report({"ERROR_INVALID_CONTEXT"}, "Active object is not an armature.")
        else:
            nbr = 0
            for b in active.data.bones:
                if "_l" in b.name or "_r" in b.name:
                    new_name = b.name.replace("_l", "_L").replace("_r", "_R")
                    b.name = new_name
                    nbr += 1
            self.report({"INFO"}, str(nbr) + " bones renamed")
        return {"FINISHED"}


class ARMATURE_NAME_EXPORT_OT_my_op(Operator, ExportHelper):
    bl_label = "Extract bones name"
    bl_idname = "armature_name_export.myop_operator"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".txt"

    def execute(self, context):
        active = bpy.context.active_object
        if active.type != "ARMATURE":
            self.report({"ERROR_INVALID_CONTEXT"}, "Active object is not an armature.")
        else:
            bones_name = [b.name + ":" for b in active.data.bones]
            bones_name.sort()
            formated_bones_name = "\n".join(bones_name)
            with open(self.filepath, "w") as fd:
                fd.write(formated_bones_name)
            self.report({"INFO"}, "Please, complete " + self.filepath)
        return {"FINISHED"}


class ARMATURE_NAME_REMAP_OT_my_op(Operator, ImportHelper):
    bl_label = "Remap bones name"
    bl_idname = "armature_name_remap.myop_operator"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".txt"

    def execute(self, context):
        self.report({"INFO"}, "Load from : " + self.filepath)
        lines = []

        with open(self.filepath) as fd:
            lines = [line.strip() for line in fd]
        translate = self.getTranslation(lines)
        self.remap(translate)

        return {"FINISHED"}

    def getTranslation(self, lines):
        tr = {}
        for line in lines:
            if len(line.split(":")) == 2:
                old, new = line.split(":")
                old = old.strip()
                new = new.strip()
                if new != "":
                    tr[old] = new
                    self.report({"INFO"}, old + " : " + tr[old])
        return tr

    def remap(self, translate_dict):
        nbr = 0
        active = bpy.context.active_object
        for old, new in translate_dict.items():
            bone = active.data.bones.get(old, None)
            if bone:
                bone.name = new
                nbr += 1
        self.report({"INFO"}, "Change " + str(nbr) + " bones name")


classes = [
    ARMATURE_NAME_EXPORT_OT_my_op,
    ARMATURE_NAME_REMAP_PT_main_panel,
    ARMATURE_NAME_REMAP_OT_my_op,
    ARMATURE_NAME_MIN_MAJ_OT_my_op,
    DISPLAY_COLOR_main_panel,
    DISPLAY_COLOR_reset_everything,
    RENDER_main_panel,
    FREESTYLE_RENDER_set_param_op,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
