import bpy
import functools
import numpy
import os
from pathlib import Path
from tempfile import TemporaryDirectory

def mesh_from_tri(name: str, vertices, triangles):
    vertices = numpy.asarray(vertices, dtype=float)
    triangles = numpy.asarray(triangles, dtype=int)
    assert vertices.ndim == 2 and triangles.ndim == 2 and vertices.shape[1] == 3 and triangles.shape[1] == 3

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], triangles)
    return bpy.data.objects.new(name, mesh)

def add_vertex_colors(obj, name: str, colors):
    colors = numpy.asarray(colors, dtype=float)
    assert colors.ndim == 2 and colors.shape[1] == 4

    attr = obj.data.color_attributes.new(name=name, type='FLOAT_COLOR', domain='POINT')
    for i, color in enumerate(colors):
        attr.data[i].color = color
    return attr

def add_vertex_colors_and_material(obj, name: str, colors):
    color_attr = add_vertex_colors(obj, name, colors)

    # Generate a new material. The material comes preloaded with a
    # 'Principled BSDF' shader node and an output node.
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    shader = material.node_tree.nodes['Principled BSDF']

    # Create an input node and attach the input to the shader.
    vertex_colors = material.node_tree.nodes.new('ShaderNodeVertexColor')
    vertex_colors.layer_name = color_attr.name
    material.node_tree.links.new(vertex_colors.outputs[0], shader.inputs[0])

    obj.data.materials.append(material)
    return color_attr, material

def _ensure_filename(f):
    @functools.wraps(f)
    def wrapper(output, *args, **kwargs):
        try:
            output = os.fspath(output)
        except TypeError:
            pass
        else:
            return f(output, *args, **kwargs)
        with TemporaryDirectory() as tmpdir:
            tmpfile = Path(tmpdir) / 'out.png'
            f(str(tmpfile), *args, **kwargs)
            with open(tmpfile, 'rb') as src:
                output.write(src.read())
    return wrapper

@_ensure_filename
def render_tri(
        output: str,
        vertices,
        triangles,
        *,
        colors=None,
        camera_rotation = (0.7, 0.0, 0.8),
        camera_distance = 5.0,
        camera_focal_length = 35., # mm
        light_distance = 5.0,
        light_energy = 300, # Watt
        renderer: str = 'CYCLES',
        resolution_x: int = 800,
        resolution_y: int = 600):

    import mathutils

    scene = bpy.context.scene

    # Clear the scene.
    for c in scene.collection.children:
        scene.collection.children.unlink(c)

    # Add a mesh.
    mesh = mesh_from_tri('mesh', vertices, triangles)
    if colors:
        add_vertex_colors_and_material(mesh, 'Col', colors)
    scene.collection.objects.link(mesh)

    ## Add a camera.
    camera_data = bpy.data.cameras.new('camera')
    camera_data.lens = camera_focal_length
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    camera.location = [0, 0, 0]
    camera.rotation_euler = camera_rotation
    camera.location = camera.rotation_euler.to_matrix() @ mathutils.Vector([0, 0, camera_distance])
    scene.collection.objects.link(camera)
    scene.camera = camera

    # Add a light source.
    light = bpy.data.lights.new(name='light', type='POINT')
    light.energy = light_energy
    light = bpy.data.objects.new(name=light.name, object_data=light)
    light.location = (0, 0, light_distance)
    scene.collection.objects.link(light)

    # Render.
    bpy.context.view_layer.cycles.use_denoising = False
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.filepath = output
    bpy.ops.render.render(write_still = True)
