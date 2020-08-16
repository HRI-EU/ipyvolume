"""The widgets module of ipvyolume."""

from __future__ import absolute_import

__all__ = ['Mesh', 'Scatter', 'Volume', 'Figure', 'Voxel', 'quickquiver', 'quickscatter', 'quickvolshow', 'observed_array']

import logging
import warnings

import numpy as np
import ipywidgets as widgets  # we should not have widgets under two names
import ipywebrtc
import pythreejs
import traitlets
from scipy import ndimage

from traitlets import Unicode, Integer
from traittypes import Array

import ipyvolume
import ipyvolume as ipv  # we should not have ipyvolume under two names either
import ipyvolume._version
from ipyvolume.traittypes import Image
from ipyvolume.serialize import (
    array_cube_tile_serialization,
    array_serialization,
    array_sequence_serialization,
    color_serialization,
    texture_serialization,
)
from ipyvolume.transferfunction import TransferFunction
from ipyvolume.utils import debounced, grid_slice, reduce_size
import math

_last_figure = None
logger = logging.getLogger("ipyvolume")
semver_range_frontend = "~" + ipyvolume._version.__version_js__


@widgets.register
class Mesh(widgets.Widget):
    _view_name = Unicode('MeshView').tag(sync=True)
    _view_module = Unicode('ipyvolume').tag(sync=True)
    _model_name = Unicode('MeshModel').tag(sync=True)
    _model_module = Unicode('ipyvolume').tag(sync=True)
    _view_module_version = Unicode(semver_range_frontend).tag(sync=True)
    _model_module_version = Unicode(semver_range_frontend).tag(sync=True)
    x = Array(default_value=None).tag(sync=True, **array_sequence_serialization)
    y = Array(default_value=None).tag(sync=True, **array_sequence_serialization)
    z = Array(default_value=None).tag(sync=True, **array_sequence_serialization)
    u = Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization)
    v = Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization)
    triangles = Array(default_value=None, allow_none=True).tag(sync=True, **array_serialization)
    lines = Array(default_value=None, allow_none=True).tag(sync=True, **array_serialization)
    texture = traitlets.Union(
        [
            traitlets.Instance(ipywebrtc.MediaStream),
            Unicode(),
            traitlets.List(Unicode, [], allow_none=True),
            Image(default_value=None, allow_none=True),
            traitlets.List(Image(default_value=None, allow_none=True)),
        ]
    ).tag(sync=True, **texture_serialization)

    sequence_index = Integer(default_value=0).tag(sync=True)
    color = Array(default_value="red", allow_none=True).tag(sync=True, **color_serialization)
    visible = traitlets.CBool(default_value=True).tag(sync=True)

    lighting_model = traitlets.Enum(values=['DEFAULT', 'LAMBERT', 'PHONG', 'PHYSICAL'], default_value='DEFAULT').tag(sync=True)
    opacity = traitlets.CFloat(1).tag(sync=True)
    emissive_intensity = traitlets.CFloat(1).tag(sync=True)
    specular_color = Array(default_value="white", allow_none=True).tag(sync=True, **color_serialization)
    shininess = traitlets.CFloat(1).tag(sync=True)
    roughness = traitlets.CFloat(0).tag(sync=True)
    metalness = traitlets.CFloat(0).tag(sync=True)
    cast_shadow = traitlets.CBool(default_value=True).tag(sync=True)
    receive_shadow = traitlets.CBool(default_value=True).tag(sync=True)
    flat_shading = traitlets.CBool(default_value=True).tag(sync=True)
    material = traitlets.Instance(
        pythreejs.ShaderMaterial, help='A :any:`pythreejs.ShaderMaterial` that is used for the mesh'
    ).tag(sync=True, **widgets.widget_serialization)

    @traitlets.default('material')
    def _default_material(self):
        return pythreejs.ShaderMaterial(side=pythreejs.enums.Side.DoubleSide)

    line_material = traitlets.Instance(
        pythreejs.ShaderMaterial, help='A :any:`pythreejs.ShaderMaterial` that is used for the lines/wireframe'
    ).tag(sync=True, **widgets.widget_serialization)

    @traitlets.default('line_material')
    def _default_line_material(self):
        return pythreejs.ShaderMaterial()

@widgets.register
class Scatter(widgets.Widget):
    _view_name = Unicode('ScatterView').tag(sync=True)
    _view_module = Unicode('ipyvolume').tag(sync=True)
    _model_name = Unicode('ScatterModel').tag(sync=True)
    _model_module = Unicode('ipyvolume').tag(sync=True)
    _view_module_version = Unicode(semver_range_frontend).tag(sync=True)
    _model_module_version = Unicode(semver_range_frontend).tag(sync=True)
    x = Array(default_value=None).tag(sync=True, **array_sequence_serialization)
    y = Array(default_value=None).tag(sync=True, **array_sequence_serialization)
    z = Array(default_value=None).tag(sync=True, **array_sequence_serialization)
    vx = Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization)
    vy = Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization)
    vz = Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization)
    selected = Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization)
    sequence_index = Integer(default_value=0).tag(sync=True)
    size = traitlets.Union(
        [
            Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization),
            traitlets.Float().tag(sync=True),
        ],
        default_value=5,
    ).tag(sync=True)
    size_selected = traitlets.Union(
        [
            Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization),
            traitlets.Float().tag(sync=True),
        ],
        default_value=7,
    ).tag(sync=True)
    size_marker = traitlets.Union(
        [
            Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization),
            traitlets.Float().tag(sync=True),
        ],
        default_value=1,
    ).tag(sync=True)
    voxel_data = Array(default_value=None, allow_none=True).tag(sync=True, **array_sequence_serialization)
    color = Array(default_value="red", allow_none=True).tag(sync=True, **color_serialization)
    color_selected = traitlets.Union(
        [Array(default_value=None, allow_none=True).tag(sync=True, **color_serialization), Unicode().tag(sync=True)],
        default_value="green",
    ).tag(sync=True)
    geo = traitlets.Unicode('diamond').tag(sync=True)
    connected = traitlets.CBool(default_value=False).tag(sync=True)
    visible = traitlets.CBool(default_value=True).tag(sync=True)
    use_instanced = traitlets.CBool(default_value=True).tag(sync=True)
    lighting_model = traitlets.Enum(values=['DEFAULT', 'PHYSICAL'], default_value='DEFAULT').tag(sync=True)
    opacity = traitlets.CFloat(1).tag(sync=True)
    specular_color = Array(default_value="white", allow_none=True).tag(sync=True, **color_serialization)
    shininess = traitlets.CFloat(1).tag(sync=True)
    emissive_intensity = traitlets.CFloat(1).tag(sync=True)
    roughness = traitlets.CFloat(0).tag(sync=True)
    metalness = traitlets.CFloat(0).tag(sync=True)
    cast_shadow = traitlets.CBool(default_value=False).tag(sync=True)
    receive_shadow = traitlets.CBool(default_value=False).tag(sync=True)
    pause_update = traitlets.CBool(default_value=False).tag(sync=True)
    scale_factor = traitlets.CFloat(1).tag(sync=True)
    pos_offset_x = traitlets.CFloat(0).tag(sync=True)
    pos_offset_y = traitlets.CFloat(0).tag(sync=True)
    pos_offset_z = traitlets.CFloat(0).tag(sync=True)

    texture = traitlets.Union(
        [
            traitlets.Instance(ipywebrtc.MediaStream),
            Unicode(),
            traitlets.List(Unicode, [], allow_none=True),
            Image(default_value=None, allow_none=True),
            traitlets.List(Image(default_value=None, allow_none=True)),
        ]
    ).tag(sync=True, **texture_serialization)

    material = traitlets.Instance(
        pythreejs.ShaderMaterial, help='A :any:`pythreejs.ShaderMaterial` that is used for the mesh'
    ).tag(sync=True, **widgets.widget_serialization)

    @traitlets.default('material')
    def _default_material(self):
        return pythreejs.ShaderMaterial()

    line_material = traitlets.Instance(
        pythreejs.ShaderMaterial, help='A :any:`pythreejs.ShaderMaterial` that is used for the lines/wireframe'
    ).tag(sync=True, **widgets.widget_serialization)

    @traitlets.default('line_material')
    def _default_line_material(self):
        return pythreejs.ShaderMaterial()

class observed_array(np.ndarray):
    callback_obj=None
    callback_func=None
    def __new__(cls, *args, **kwargs):
        return super(observed_array, cls).__new__(cls, *args, **kwargs)
    def set_callback(self, cb_obj, cb_fcn):
        self.callback_obj = cb_obj    
        self.callback_func = cb_fcn
    def __getitem__(self, key):
        retval = super(observed_array, self).__getitem__(key)
        if self.callback_func and self.callback_obj and (isinstance(key, int) or (isinstance(key, tuple) and not isinstance(key[0], int))): # or (isinstance(key, tuple) and key[0] == -1 and key[1] == -1 and key[2] == -1)
            #print("{} {}".format(key, type(key)))
            self.callback_func(self.callback_obj)
        return retval
    def __setitem__(self,key,value):
        retval = super(observed_array, self).__setitem__(key, value)
        self.callback_func(self.callback_obj)
        return retval

@widgets.register
class Voxel(Scatter):
    def vox_cb(self, obj, *args, **kwargs):
        #print("Voxel Callback Compute x,y,z")
        coords = Voxel.d_to_xyz(obj.d, center=True)
        # print(coords[:,0])
        # print(coords[:,1])
        # print(coords[:,2])
        obj.pause_update = True
        # nl = obj.d.ravel().tolist()
        # obj.voxel_data = list(filter((0).__ne__, nl))
        obj.voxel_data = list(filter(lambda a: a !=0, obj.d.ravel().tolist()))
        #print(obj.voxel_data)
        obj.x=coords[:,0].tolist()
        obj.y=coords[:,1].tolist()
        obj.z=coords[:,2].tolist()
        # print("-------------------------")
        # print(obj.x)
        # print(obj.y)
        # print(obj.z)
        #print(obj.d)
        #print(obj.voxel_data)
        obj.pause_update = False
        #print("Finished x y z update") 
    
    d_param = observed_array([1,1,1])

    @property
    def d(self):
        return self.d_param
    @d.setter
    def d(self, value):
        self.d_param=observed_array(value.shape)
        np.copyto(self.d_param, value)
        self.d_param.set_callback(self, self.vox_cb)

    @staticmethod
    def d_to_xyz(d, center=True):
        boxes = None
        boxes = np.array(np.nonzero(d)).transpose()
        boxes = boxes.astype(np.float)

        # set model into origin
        if center and boxes.size > 0:
            for i in range(3): 
                boxes[:,i] = boxes[:,i] - boxes[:,i].min()
                boxes[:,i] = boxes[:,i] - boxes[:,i].max()/2

        return boxes


@widgets.register
class Volume(widgets.Widget):
    """Widget class representing a volume (rendering) using three.js."""

    _view_name = Unicode('VolumeView').tag(sync=True)
    _view_module = Unicode('ipyvolume').tag(sync=True)
    _model_name = Unicode('VolumeModel').tag(sync=True)
    _model_module = Unicode('ipyvolume').tag(sync=True)
    _view_module_version = Unicode(semver_range_frontend).tag(sync=True)
    _model_module_version = Unicode(semver_range_frontend).tag(sync=True)

    data = Array(default_value=None, allow_none=True).tag(sync=True, **array_cube_tile_serialization)
    data_original = Array(default_value=None, allow_none=True)
    data_max_shape = traitlets.CInt(None, allow_none=True)  # TODO: allow this to be a list
    data_min = traitlets.CFloat(0).tag(sync=True)
    data_max = traitlets.CFloat(1).tag(sync=True)
    show_min = traitlets.CFloat(0).tag(sync=True)
    show_max = traitlets.CFloat(1).tag(sync=True)
    clamp_min = traitlets.CBool(False).tag(sync=True)
    clamp_max = traitlets.CBool(False).tag(sync=True)
    opacity_scale = traitlets.CFloat(1.0).tag(sync=True)
    brightness = traitlets.CFloat(1.0).tag(sync=True)
    tf = traitlets.Instance(TransferFunction, allow_none=True).tag(sync=True, **widgets.widget_serialization)
    ray_steps = traitlets.CInt(
        None,
        allow_none=True,
        help='defines the length of the ray (1/ray_steps) for each step, in normalized coordintes.',
    ).tag(sync=True)

    rendering_method = traitlets.Enum(values=['NORMAL', 'MAX_INTENSITY'], default_value='NORMAL').tag(sync=True)
    lighting = traitlets.Bool(True).tag(sync=True)

    extent = traitlets.Any().tag(sync=True)
    extent_original = traitlets.Any()

    def __init__(self, **kwargs):
        super(Volume, self).__init__(**kwargs)
        self._update_data()
        self.observe(self.update_data, ['data_original', 'data_max_shape'])

    def _listen_to(self, fig):
        fig.observe(self.update_data, ['xlim', 'ylim', 'zlim'])

    @debounced(method=True)
    def update_data(self, change=None):
        self._update_data()

    def _update_data(self):
        if self.data_original is None:
            return
        if all([k <= self.data_max_shape for k in self.data_original.shape]):
            self.data = self.data_original
            self.extent = self.extent_original
            return
        current_figure = ipv.gcf()
        xlim = current_figure.xlim
        ylim = current_figure.ylim
        zlim = current_figure.zlim
        shape = self.data_original.shape
        ex = self.extent_original
        viewx, xt = grid_slice(ex[0][0], ex[0][1], shape[2], *xlim)
        viewy, yt = grid_slice(ex[1][0], ex[1][1], shape[1], *ylim)
        viewz, zt = grid_slice(ex[2][0], ex[2][1], shape[0], *zlim)
        view = [slice(*viewz), slice(*viewy), slice(*viewx)]
        data_view = self.data_original[view]
        extent = [xt, yt, zt]
        data_view, extent = reduce_size(data_view, self.data_max_shape, extent)
        self.data = np.array(data_view)
        self.extent = extent

    
@widgets.register
class Figure(ipywebrtc.MediaStream):
    """Widget class representing a volume (rendering) using three.js."""

    _view_name = Unicode('FigureView').tag(sync=True)
    _view_module = Unicode('ipyvolume').tag(sync=True)
    _model_name = Unicode('FigureModel').tag(sync=True)
    _model_module = Unicode('ipyvolume').tag(sync=True)
    _view_module_version = Unicode(semver_range_frontend).tag(sync=True)
    _model_module_version = Unicode(semver_range_frontend).tag(sync=True)

    eye_separation = traitlets.CFloat(6.4).tag(sync=True)

    scatters = traitlets.List(traitlets.Instance(Scatter), [], allow_none=False).tag(
        sync=True, **widgets.widget_serialization
    )
    meshes = traitlets.List(traitlets.Instance(Mesh), [], allow_none=False).tag(
        sync=True, **widgets.widget_serialization
    )
    volumes = traitlets.List(traitlets.Instance(Volume), [], allow_none=False).tag(
        sync=True, **widgets.widget_serialization
    )
    
    #lights = traitlets.List(traitlets.Instance(Light), [], allow_none=False).tag(
    #    sync=True, **widgets.widget_serialization
    #)
    lights = traitlets.List(traitlets.Instance(pythreejs.Light), [], allow_none=False).tag(
        sync=True, **widgets.widget_serialization
    )

    animation = traitlets.Float(1000.0).tag(sync=True)
    animation_exponent = traitlets.Float(1.0).tag(sync=True)

    ambient_coefficient = traitlets.Float(0.5).tag(sync=True)
    diffuse_coefficient = traitlets.Float(0.8).tag(sync=True)
    specular_coefficient = traitlets.Float(0.5).tag(sync=True)
    specular_exponent = traitlets.Float(5).tag(sync=True)

    stereo = traitlets.Bool(False).tag(sync=True)

    camera_control = traitlets.Unicode(default_value='trackball').tag(sync=True)
    camera_fov = traitlets.CFloat(45, min=0.1, max=179.9).tag(sync=True)
    camera_center = traitlets.List(traitlets.CFloat(), default_value=[0, 0, 0]).tag(sync=True)
    # Tuple(traitlets.CFloat(0), traitlets.CFloat(0), traitlets.CFloat(0)).tag(sync=True)

    camera = traitlets.Instance(
        pythreejs.Camera, allow_none=True, help='A :any:`pythreejs.Camera` instance to control the camera'
    ).tag(sync=True, **widgets.widget_serialization)

    enable_shadows = traitlets.Bool(False).tag(sync=True)

    @traitlets.default('camera')
    def _default_camera(self):
        # see https://github.com/maartenbreddels/ipyvolume/pull/40 for an explanation
        z = 2 * np.tan(45.0 / 2.0 * np.pi / 180) / np.tan(self.camera_fov / 2.0 * np.pi / 180)
        return pythreejs.PerspectiveCamera(fov=self.camera_fov, position=(0, 0, z), width=400, height=500)

    scene = traitlets.Instance(pythreejs.Scene, allow_none=True).tag(sync=True, **widgets.widget_serialization)

    @traitlets.default('scene')
    def _default_scene(self):
        # could be removed when https://github.com/jovyan/pythreejs/issues/176 is solved
        # the default for pythreejs is white, which leads the volume rendering pass to make everything white
        return pythreejs.Scene(background=None)

    width = traitlets.CInt(500).tag(sync=True)
    height = traitlets.CInt(400).tag(sync=True)
    displayscale = traitlets.CFloat(1).tag(sync=True)
    pixel_ratio = traitlets.Float(
        None,
        allow_none=True,
        help='Pixel ratio of the WebGL canvas (2 on retina screens). Set to 1 for better performance, but less crisp'
        'edges. If set to None it will use the browser\'s window.devicePixelRatio.'
    ).tag(sync=True)
    capture_fps = traitlets.CFloat(None, allow_none=True).tag(sync=True)
    cube_resolution = traitlets.CInt(512).tag(sync=True)

    show = traitlets.Unicode("Volume").tag(sync=True)  # for debugging

    xlim = traitlets.List(traitlets.CFloat(), default_value=[0, 1], minlen=2, maxlen=2).tag(sync=True)
    ylim = traitlets.List(traitlets.CFloat(), default_value=[0, 1], minlen=2, maxlen=2).tag(sync=True)
    zlim = traitlets.List(traitlets.CFloat(), default_value=[0, 1], minlen=2, maxlen=2).tag(sync=True)

    matrix_projection = traitlets.List(
        traitlets.CFloat(), default_value=[0] * 16, allow_none=True, minlen=16, maxlen=16
    ).tag(sync=True)
    matrix_world = traitlets.List(
        traitlets.CFloat(), default_value=[0] * 16, allow_none=True, minlen=16, maxlen=16
    ).tag(sync=True)

    xlabel = traitlets.Unicode("x").tag(sync=True)
    ylabel = traitlets.Unicode("y").tag(sync=True)
    zlabel = traitlets.Unicode("z").tag(sync=True)

    style = traitlets.Dict(default_value=ipyvolume.styles.default).tag(sync=True)

    render_continuous = traitlets.Bool(False).tag(sync=True)
    selector = traitlets.Unicode(default_value='lasso').tag(sync=True)
    selection_mode = traitlets.Unicode(default_value='replace').tag(sync=True)
    mouse_mode = traitlets.Unicode(default_value='normal').tag(sync=True)
    panorama_mode = traitlets.Enum(values=['no', '360', '180'], default_value='no').tag(sync=True)

    # xlim = traitlets.Tuple(traitlets.CFloat(0), traitlets.CFloat(1)).tag(sync=True)
    # y#lim = traitlets.Tuple(traitlets.CFloat(0), traitlets.CFloat(1)).tag(sync=True)
    # zlim = traitlets.Tuple(traitlets.CFloat(0), traitlets.CFloat(1)).tag(sync=True)

    def __init__(self, **kwargs):
        super(Figure, self).__init__(**kwargs)
        self._screenshot_handlers = widgets.CallbackDispatcher()
        self._selection_handlers = widgets.CallbackDispatcher()
        self.on_msg(self._handle_custom_msg)

    def __enter__(self):
        """Set this figure as the current in the pylab API.

        Example:
        >>> f1 = ipv.figure(1)
        >>> f2 = ipv.figure(2)
        >>> with f1:
        >>>  ipv.scatter(x, y, z)
        >>> assert ipv.gcf() is f2
        """
        self._previous_figure = ipv.gcf()
        ipv.figure(self)

    def __exit__(self, type, value, traceback):
        ipv.figure(self._previous_figure)
        del self._previous_figure

    def screenshot(self, width=None, height=None, mime_type='image/png'):
        self.send({'msg': 'screenshot', 'width': width, 'height': height, 'mime_type': mime_type})

    def on_screenshot(self, callback, remove=False):
        self._screenshot_handlers.register_callback(callback, remove=remove)

    def _handle_custom_msg(self, content, buffers):
        if content.get('event', '') == 'screenshot':
            self._screenshot_handlers(content['data'])
        elif content.get('event', '') == 'selection':
            self._selection_handlers(content['data'])

    def on_selection(self, callback, remove=False):
        self._selection_handlers.register_callback(callback, remove=remove)

    def project(self, x, y, z):
        W = np.matrix(self.matrix_world).reshape((4, 4)).T
        P = np.matrix(self.matrix_projection).reshape((4, 4)).T
        M = np.dot(P, W)
        x = np.asarray(x)
        vertices = np.array([x, y, z, np.ones(x.shape)])
        screen_h = np.tensordot(M, vertices, axes=(1, 0))
        xy = screen_h[:2] / screen_h[3]
        return xy


def volshow(*args, **kwargs):
    """Deprecated: please use ipyvolume.quickvolshow or use the ipyvolume.pylab interface."""
    warnings.warn(
        "Please use ipyvolume.quickvolshow or use the ipyvolume.pylab interface", DeprecationWarning, stacklevel=2
    )
    return quickvolshow(*args, **kwargs)


def quickquiver(x, y, z, u, v, w, **kwargs):
    ipv.figure()
    ipv.quiver(x, y, z, u, v, w, **kwargs)
    return ipv.gcc()


def quickscatter(x, y, z, **kwargs):
    ipv.figure()
    ipv.scatter(x, y, z, **kwargs)
    return ipv.gcc()


def quickvolshow(
    data,
    lighting=False,
    data_min=None,
    data_max=None,
    max_shape=256,
    level=[0.1, 0.5, 0.9],
    opacity=[0.01, 0.05, 0.1],
    level_width=0.1,
    extent=None,
    memorder='C',
    **kwargs
):
    """Visualize a 3d array using volume rendering.

    :param data: 3d numpy array
    :param lighting: boolean, to use lighting or not, if set to false, lighting parameters will be overriden
    :param data_min: minimum value to consider for data, if None, computed using np.nanmin
    :param data_max: maximum value to consider for data, if None, computed using np.nanmax
    :param int max_shape: maximum shape for the 3d cube, if larger, the data is reduced by skipping/slicing (data[::N]),
                          set to None to disable.
    :param extent: list of [[xmin, xmax], [ymin, ymax], [zmin, zmax]] values that define the bounds of the volume,
                   otherwise the viewport is used
    :param level: level(s) for the where the opacity in the volume peaks, maximum sequence of length 3
    :param opacity: opacity(ies) for each level, scalar or sequence of max length 3
    :param level_width: width of the (gaussian) bumps where the opacity peaks, scalar or sequence of max length 3
    :param kwargs: extra argument passed to Volume and default transfer function
    :return:

    """
    ipv.figure()
    ipv.volshow(
        data,
        lighting=lighting,
        data_min=data_min,
        data_max=data_max,
        max_shape=max_shape,
        level=level,
        opacity=opacity,
        level_width=level_width,
        extent=extent,
        memorder=memorder,
        **kwargs
    )
    return ipv.gcc()


def scatter(x, y, z, color=(1, 0, 0), s=0.01):
    global _last_figure
    fig = _last_figure
    if fig is None:
        fig = volshow(None)
    fig.scatter = Scatter(x=x, y=y, z=z, color=color, size=s)
    fig.volume.scatter = fig.scatter
    return fig


# add all help strings to the __doc__ for the api docstrings
for name, cls in list(vars().items()):
    try:
        if issubclass(cls, traitlets.HasTraits):
            for trait_name, trait in cls.class_traits().items():
                if 'help' in trait.metadata:
                    trait.__doc__ = trait.metadata['help']
    except TypeError:
        pass
