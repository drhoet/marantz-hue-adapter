import numpy as np
from mayavi import mlab
from scipy.interpolate import splprep, splev
from traits.api import HasTraits, Instance, Button, on_trait_change, Float
from traitsui.api import View, Item, HSplit, Group, VGroup

from mayavi.core.ui.api import MlabSceneModel, SceneEditor

################################################################################
# Remark: I used this script to find a good frequency -> xy values mapping.
# I generated, as carefully as I could, all xy values the app would send to the
# lamp. I did this by SLOOOOOOOWLY sliding through the slider, and printing out
# all xy values I received, in order. I made 3 of those files, which are ofc a
# bit different due to the speed I used not being constant, as I'm not a robot.
# I then used this script to perfect a B-spline interpolation. On the screen,
# you can input a value for the smoothing factor s and recalculate + redraw the
# interpolated function. I found a value of 0.001 for s to be good.
# The xy values are then printed to the console, for frequencies 87.5 -> 108.00.
# These values are copied in the MarantzFmRadioLightAdapter, since I didn't
# want to add the dependency to scipy there.
#
# I executed this script in Enthought Canopy Version: 1.7.4.3348 (64 bit).
# Required packages:
# - numpy 1.10.4-1
# - mayavi 4.4.3-10
# - vtk 6.3.0-4
# - scipy 0.17.1-1
# - traits 4.5.0-1
# - traitsui 5.1.0-1

def read_file(filename):
    linenb = 0
    data = [[], [], []]
    for line in open(filename, 'r'):
        fields = line[1:-2].split(',')
        data[0].append(linenb)
        data[1].append(float(fields[0]))
        data[2].append(float(fields[1]))
        linenb = linenb + 1
    return np.array(data)

class MyDialog(HasTraits):
    
    p0 = read_file('testGO0.txt')
    p1 = read_file('testGO1.txt')
    p2 = read_file('testGO2.txt')
    new_u = x = y = None

    scene1 = Instance(MlabSceneModel, ())
    scene2 = Instance(MlabSceneModel, ())

    button1 = Button('Redraw')
    button2 = Button('Redraw')
    buttonSave = Button('Save')
    
    s1 = Float
    s2 = Float

    @on_trait_change('button1')
    def redraw_scene1(self):
        self.redraw_scene(self.scene1, self.s1)

    @on_trait_change('button2')
    def redraw_scene2(self):
        self.redraw_scene(self.scene2, self.s2)

    @on_trait_change('buttonSave')
    def save(self):
        f = open('outputGO.txt', 'w')
        f.write('freq = [\n')
        for i in range(0, len(self.new_u)):
            f.write(' [%s,%s],\n' % (self.x[i], self.y[i]))
        f.write(']')
        f.close()

    def redraw_scene(self, scene, s):
        mlab.clf(figure=scene.mayavi_scene)
        mlab.plot3d(np.divide(self.p0[0], 100), self.p0[1], self.p0[2], tube_radius=0.005, color=(1, 0, 0), figure=scene.mayavi_scene)
        mlab.plot3d(np.divide(self.p1[0], 100), self.p1[1], self.p1[2], tube_radius=0.005, color=(0, 1, 0), figure=scene.mayavi_scene)
        mlab.plot3d(np.divide(self.p2[0], 100), self.p2[1], self.p2[2], tube_radius=0.005, color=(0, 0, 1), figure=scene.mayavi_scene)

        tck, u = splprep([self.p1[1], self.p1[2]], u=np.linspace(87.50, 108.00, len(self.p1[0])), s=s, k=3)
        self.new_u = np.linspace(87.50, 108.00, 411)
        self.x, self.y = splev(self.new_u, tck, ext=2)
        mlab.plot3d(np.divide(self.new_u, 100), self.x, self.y, tube_radius=0.005, color=(1, 1, 1), figure=scene.mayavi_scene)
        

    # The layout of the dialog created
    view = View(VGroup(
                    HSplit(
                        Group(
                            Item('scene1', editor=SceneEditor(), height=250,
                                    width=300),
                            'button1',
                            's1',
                            show_labels=False,
                        ),
                        Group(
                            Item('scene2',
                                    editor=SceneEditor(), height=250,
                                    width=300, show_label=False),
                            'button2',
                            's2',
                            show_labels=False,
                        )
                    ),
                    'buttonSave',
                    show_labels=False
                ),
                resizable=True,
                )

m = MyDialog()
m.configure_traits()