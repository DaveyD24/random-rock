import bpy
from .random_rock import generate_rocks

bl_info = {
    "name": "Random Rock",
    "author": "Davey Dyer",
    "version": (1, 0, 0),
    "category": "Object",
}

class RANDOMROCK_OT_generate_rocks(bpy.types.Operator):
    bl_idname = "randomrock.generate_rocks"
    bl_label = "Generate Random Rocks"

    def execute(self, context):
        generate_rocks()
        return {'FINISHED'}

class RANOMROCK_OT_panel(bpy.types.Panel):
    bl_idname = "RANDOMROCK_OT_panel"
    bl_label = "Random Rock"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "My Tools"

    def draw(self, context):
        self.layout.operator(
            "randomrock.generate_rocks",
            text="Generate Random Rocks"
        )

def register():
    bpy.utils.register_class(RANDOMROCK_OT_generate_rocks)
    bpy.utils.register_class(RANOMROCK_OT_panel)

def unregister():
    bpy.utils.unregister_class(RANOMROCK_OT_panel)
    bpy.utils.unregister_class(RANDOMROCK_OT_generate_rocks)

if __name__ == "__main__":
    register()