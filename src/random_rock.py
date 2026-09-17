import bpy
import bmesh
from mathutils import Vector, Euler
import math
import random

SUBD_LEVELS = 5
DISPLACE_STRENGTH = 0.25
DISPLACE_SCALE = 0.5

#Adjust for low poly
RATIO = 0.004

SLANT_POS = (-0.1, -0.3, 1.4)
SLANT_ANGLE = (0.45, 0, 0.34)

IMAGE_PATH = "//image/footprint.png"

LARGE_SCALE = (12, 24)
MEDIUM_SCALE = (5, 8)
Y_DISTANCE = 0.25

def clear_objects() -> None:
    for obj in list(bpy.data.objects):
        if obj.get("spawned_from_script"):
            bpy.data.objects.remove(obj, do_unlink=True)

def create_rock(location: Vector, rotation: Euler, scale: float, do_slant=False) -> bpy.types.Object:
    
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj["spawned_from_script"] = True

    subd_mod = obj.modifiers.new(
        name="Subdivision Surface",
        type="SUBSURF"
    )
    subd_mod.levels = SUBD_LEVELS
    subd_mod.render_levels = SUBD_LEVELS

    displace_mod = obj.modifiers.new(
        name="Displace",
        type="DISPLACE"
    )

    texture = bpy.data.textures.new(
        name="Displace Texture",
        type="VORONOI"
    )
    displace_mod.texture = texture

    displace_mod.strength = DISPLACE_STRENGTH
    displace_mod.mid_level = DISPLACE_STRENGTH
    displace_mod.texture.noise_scale = DISPLACE_SCALE

    decimate_mod = obj.modifiers.new(
        name="Decimate",
        type="DECIMATE"
    )
    decimate_mod.ratio = RATIO
    
    #Apply so bisection will happen on the newly formed mesh
    apply_modifiers(obj)
    
    obj.location = location
    obj.rotation_euler = rotation
    
    #If creating launchable surface
    if do_slant:
        slant(obj, rotation, scale)
    
    obj.scale = Vector((scale, scale, scale))
    
    slice_off_bottom_half(obj)
    
    return obj

def bisect(bm: bmesh.types.BMesh, pos: tuple, normal: tuple, inner: bool, outer: bool) -> tuple:
    
    bisect_result = bmesh.ops.bisect_plane(
        bm,
        geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
        plane_co=pos,
        plane_no=normal,
        clear_inner=inner,
        clear_outer=outer
    )

    edges = [element for element in bisect_result["geom_cut"] if isinstance(element, bmesh.types.BMEdge)]

    fill_result = bmesh.ops.edgenet_fill(
        bm,
        edges=edges
    )
    
    return (bm, fill_result)


def slice_off_bottom_half(obj: bpy.types.Object) -> None:
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    bm = bisect(bm, (0,0,0), (0,0,1), True, False)[0]
    
    bm.to_mesh(obj.data)
    bm.free()

def slant(obj: bpy.types.Object, rotation: Euler, scale: float) -> None:
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    bisection = bisect(bm, SLANT_POS, SLANT_ANGLE, False, True)
    bm = bisection[0]
    
    new_face = bisection[1]["faces"][0]
    vertices = [v.co.copy() for v in new_face.verts]
    
    mesh = bpy.data.meshes.new("SlantPlane")
    mesh.from_pydata(
        vertices,
        [],
        [list(range(len(vertices)))]
    )
    mesh.update()
    
    generate_uvs(mesh)
    
    plane = bpy.data.objects.new("SlantPlane", mesh)
    plane["spawned_from_script"] = True
    plane.rotation_euler = rotation
    
    #Avoid z-index fighting
    plane.location.z += 0.001
    
    plane.scale = Vector((scale, scale, scale))
    
    add_texture(plane)
    
    bpy.context.collection.objects.link(plane)
    bm.to_mesh(obj.data)
    bm.free()
    
def generate_uvs(mesh: bmesh.types.BMesh) -> None:
    bm_uv = bmesh.new()
    bm_uv.from_mesh(mesh)

    uv_layer = bm_uv.loops.layers.uv.new()

    scale = 1.5
    for face in bm_uv.faces:
        for loop in face.loops:
            u = 0.5 + loop.vert.co.x * scale
            v = 0.5 + loop.vert.co.y * scale

            #Rotate 270 degrees
            loop[uv_layer].uv = (
                v,
                1 - u
            )

    bm_uv.to_mesh(mesh)
    bm_uv.free()
    
def add_texture(obj: bpy.types.Object) -> None:
    material = bpy.data.materials.new("RockMaterial")
    
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    bsdf_node = nodes.get("Principled BSDF")
    
    texture_node = nodes.new("ShaderNodeTexImage")
    texture_node.image = bpy.data.images.load(IMAGE_PATH)
    
    links.new(texture_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
    links.new(texture_node.outputs["Color"], bsdf_node.inputs["Base Color"])
    
    material.surface_render_method = "DITHERED"
    
    obj.data.materials.append(material)

def random_euler() -> Euler:
    return Euler((0, 0, math.radians(random.randint(0, 360))))

def apply_modifiers(obj) -> None:
    for modifier in list(obj.modifiers):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)

if __name__ == "__main__":
    
    clear_objects()

    large_scale = random.randint(*LARGE_SCALE) / 10
    medium_scale = random.randint(*MEDIUM_SCALE) / 10
    
    #Big slanted rock
    big_rock = create_rock(Vector((0,0,0)), random_euler(), large_scale, do_slant=True)
    
    y_offset = large_scale + (medium_scale / 2) - Y_DISTANCE
    x_offset_l = random.randint(-int(large_scale), int(large_scale)) / 2
    x_offset_r = random.randint(-int(large_scale), int(large_scale)) / 2
    
    #Medium unslanted rocks
    medium_rock_left = create_rock(Vector((x_offset_l, -y_offset, 0)), random_euler(), medium_scale)
    medium_rock_right = create_rock(Vector((x_offset_r, y_offset, 0)), random_euler(), medium_scale)
