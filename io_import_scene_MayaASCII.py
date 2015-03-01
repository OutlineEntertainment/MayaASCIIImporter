import bpy
from bpy.props import *
import os.path
from bpy_extras.io_utils import ImportHelper
from math import degrees, radians

bl_info = {
    "name": "Maya ASCII (*.ma) Importer",
    "author": "Outline Entertainment",
    "version": (1, 0),
    "blender": (2, 72, 0),
    "location": "File > Import",
    "description": "An import script for Maya ASCII (.ma) files. It was primarily designed for the ones generated by Autodesk MatchMover.",
    "warning": "Only tested with files from Autodesk MatchMover.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

class ImportMayaASCII(bpy.types.Operator, ImportHelper):
    bl_idname = "import.mayaascii"
    bl_label = "Import Maya ASCII (*.ma)"
    bl_options = {'REGISTER', 'UNDO'}
    
    enumber = IntProperty (name ="enumber", default = 50, description="Number of Empties to be Imported")
    sscale = FloatProperty (name ="sscale", default = 1, description="Scene Scale Multiplier")
    egroup = StringProperty (name ="egroup", default = "Tracks", description="Name of the Group Created for Imported Empties")
    ename = StringProperty (name ="ename", default = "Track", description="Name (Prefix) for Imported Empties")
    include_empties = BoolProperty(
        name="Empties",
        description="Import Empties",
        default=True,
        )
    include_camera = BoolProperty(
        name="Camera",
        description="Import Camera",
        default=True,
        )
    include_bg = BoolProperty(
        name="BGClip",
        description="Import Movie Clip",
        default=True,
        )
    var_fl = BoolProperty(
        name="Variable Focallength",
        description="Use keyframes on the focallength.",
        default=False,
        )
    flip_taxis = BoolProperty(
        name="Translation",
        description="Flip Z/Y Translation Axis",
        default=True,
        )
    flip_raxis = BoolProperty(
        name="Rotation",
        description="Flip Z/Y Rotation Axis",
        default=True,
        )
    invert_x = BoolProperty(
        name="X",
        description="Invert X Axis",
        default=False,
        )
    invert_y = BoolProperty(
        name="Y",
        description="Invert Y Axis",
        default=True,
        )
    invert_z = BoolProperty(
        name="Z",
        description="Invert Z Axis",
        default=False,
        )
    invert_rx = BoolProperty(
        name="X",
        description="Invert X Rotation",
        default=False,
        )
    invert_ry = BoolProperty(
        name="Y",
        description="Invert Y Rotation",
        default=True,
        )
    invert_rz = BoolProperty(
        name="Z",
        description="Invert Z Rotation",
        default=False,
        )
    clear_scene = BoolProperty(
        name="Clear Scene",
        description="Delete every object in the scene, before importing.",
        default=False,
        )
    imported_tracknumbers = BoolProperty(
        name="Use Track Numbers Defined in File",
        description="Use the track numbers defined in the Maya ASCII file for counting and naming the according empties.",
        default=False,
        )
    xadd = FloatProperty (name ="xadd", default = 90, description="X Rotation Offset (Eulers)")
    yadd = FloatProperty (name ="yadd", default = 0, description="Y Rotation Offset (Eulers)")
    zadd = FloatProperty (name ="zadd", default = 0, description="Z Rotation Offset (Eulers)")
    
    filename_ext = ".ma"
    filter_glob = StringProperty(default="*.ma", options={'HIDDEN'})
    
    def execute(self, context):
        self.importTracking(self.filepath)
        return {'FINISHED'}
        
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row()
        row.label('Include:')
        row = col.row()
        row.prop(self, 'clear_scene')
        row = col.row()
        row.prop(self, 'include_camera')
        row.prop(self, 'include_empties')
        row.prop(self, 'include_bg')
        row = col.row()
        row.prop(self, 'var_fl')
        row = col.row()
        row.separator()
        row = col.row()
        row.prop(self,'sscale','Scene Scale')
        row = col.row()
        row.separator()
        row = col.row()
        row.prop(self,'enumber','Max. Number of Empties')
        row = col.row()
        row.prop(self, 'imported_tracknumbers')
        row = col.row()
        row.separator()
        row = col.row()
        row.prop(self,'egroup','Group')
        row = col.row()
        row.prop(self,'ename','Name')
        row = col.row()
        row.separator()
        row = col.row()
        row.label('Flip Axis:')
        row = col.row()
        row.prop(self, 'flip_taxis')
        row.prop(self, 'flip_raxis')
        row = col.row()
        row.separator()
        row = col.row()
        row.label('Invert Axis:')
        row = col.row()
        row.prop(self, 'invert_x')
        row.prop(self, 'invert_y')
        row.prop(self, 'invert_z')
        row = col.row()
        row.separator()
        row = col.row()
        row.label('Invert Rotation:')
        row = col.row()
        row.prop(self, 'invert_rx')
        row.prop(self, 'invert_ry')
        row.prop(self, 'invert_rz')
        row = col.row()
        row.separator()
        row = col.row()
        row.label('Rotation Offset (Eulers):')
        row = col.row()
        row.prop(self,'xadd','X')
        row.prop(self,'yadd','Y')
        row.prop(self,'zadd','Z')
    
    def importTracking(self, filename):
        print("Importing...")
        include_camera = self.include_camera
        include_empties = self.include_empties
        include_bg = self.include_bg
        enumber = self.enumber
        newCamera = bpy.context.active_object
        clipname = ""
        camname = ""
        trackn = 0
        scene = bpy.context.scene
        oframe = scene.frame_current
        framesSet = False
        
        if self.clear_scene:
            bpy.ops.object.select_all(action = 'SELECT')
            bpy.ops.object.delete()
        
        if include_empties:
            bpy.ops.group.create(name=self.egroup)
            
        invert_x=self.sscale
        invert_y=self.sscale
        invert_z=self.sscale
        invert_rx=1
        invert_ry=1
        invert_rz=1
        
        if self.flip_taxis:
            if self.invert_x:
                invert_x = -1 * self.sscale
            if self.invert_y:
                invert_z = -1 * self.sscale  
            if self.invert_z:
                invert_y = -1 * self.sscale
            txaxis = 0
            tyaxis = 2
            tzaxis = 1
        else:
            if self.invert_x:
                invert_x = -1 * self.sscale
            if self.invert_y:
                invert_y = -1 * self.sscale
            if self.invert_z:
                invert_z = -1 * self.sscale
            txaxis = 0
            tyaxis = 1
            tzaxis = 2
        
        if self.flip_raxis:
            if self.invert_rx:
                invert_rx = -1
            if self.invert_ry:
                invert_rz = -1  
            if self.invert_rz:
                invert_ry = -1
            rxaxis = 0
            ryaxis = 2
            rzaxis = 1
        else:
            if self.invert_rx:
                invert_rx = -1
            if self.invert_ry:
                invert_ry = -1  
            if self.invert_rz:
                invert_rz = -1
            rxaxis = 0
            ryaxis = 1
            rzaxis = 2
        
        mode = 0
        file = open(filename, 'r')
        for line in file:
            words = line.split()
            if len(words) == 0 or words[0].startswith('//'):
                pass
            
            elif mode == 0 and words[0] == 'currentUnit' and words[1] == '-l' and words[3] == '-a' and words[5] == '-t':
                if words[2] == 'centimeter':
                    invert_x=invert_x*0.01
                    invert_y=invert_y*0.01
                    invert_z=invert_z*0.01
                if words[6] == 'film':
                    bpy.context.scene.render.fps = 24
                elif words[6] == 'pal':
                    bpy.context.scene.render.fps = 25
                elif words[6] == 'ntsc':
                    bpy.context.scene.render.fps = 30
            
            elif mode == 0 and words[0] == 'select' and words[1] == '-ne' and words[2] == 'defaultResolution;': #get Resolution
                mode = -2
            
            elif mode < 0 and words[0] == 'setAttr' and words[1] == '".w"': #get Width
                bpy.context.scene.render.resolution_x = int((words[2])[:-1])
                mode = mode + 1
            
            elif mode < 0 and words[0] == 'setAttr' and words[1] == '".h"': #get Height
                bpy.context.scene.render.resolution_y = int((words[2])[:-1])
                mode = mode + 1
                                
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'camera' and words[2] == '-n' and words[4] == '-p': #create Camera
                if include_camera:
                    camname = words[5]
                    camname = camname[1:-2]
                    bpy.ops.object.camera_add(location=(0, 0, 0), rotation=(0, 0, 0))
                    newCamera = bpy.context.active_object
                    newCamera.name = camname
                    bpy.context.scene.camera = newCamera
                
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'imagePlane' and words[2] == '-n': #get Clipname
                if include_bg:
                    clipname = words[3]
                    clipname = clipname[1:-2]
                mode = 1
                
            elif mode == 1 and words[0] == 'setAttr' and words[1] == '".imn"' and words[2] == '-type' and words[3] == '"string"': #get Clipfile
                if include_bg:
                    try:
                        clippath = line[32:-3]
                        clipfile = os.path.basename(clippath)
                        clippath = clippath[:-len(clipfile)]
                        clippath = clippath.replace("/", r"\\")
                        bpy.ops.clip.open(directory=clippath, files=[{"name":clipname, "name":clipfile}])
                    except:
                        print("Unable to load bg clip.")
                    
                mode = 0
            
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'animCurveTU' and words[2] == '-n' and words[3] == '"'+clipname+'_frameExtension";':
                mode = 2
                
            elif mode == 2 and words[0] == 'setAttr' and words[1] == '-s' and words[2] == '2' and words[3] == '".ktv[0:1]"': #get Start and Endframe
                scene.frame_start = int(words[4])
                scene.frame_end = int(words[6])
                framesSet = True
                mode = 0
                
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'animCurveTU' and words[2] == '-n' and words[3] == '"'+camname+'_focalLength";':
                if include_camera:
                    mode = 3
            
            elif mode == 3 and words[0] == 'setAttr' and words[1] == '-s': #get Focal Length
                if self.var_fl:
                    for x in range(1, int(float(words[2]))):
                        bpy.data.cameras[newCamera.data.name].lens = float(words[(x*2)+3])
                        newCamera.data.keyframe_insert(data_path='lens', frame=x)
                        scene.frame_set(x)
                else:
                    bpy.data.cameras[newCamera.data.name].lens = float(words[5])
                
                mode = 0
            
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'animCurveTL' and words[2] == '-n' and words[3] == '"'+camname+'_translateX";':
                if include_camera:
                    mode = 4
            
            elif mode == 4 and words[0] == 'setAttr' and words[1] == '-s': #get X-Pos
                for x in range(1, int(float(words[2]))):
                    bpy.data.objects[newCamera.name].location[txaxis] = float(words[(x*2)+3])*invert_x
                    newCamera.keyframe_insert(data_path='location', frame=x, index=txaxis)
                mode = 0
            
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'animCurveTL' and words[2] == '-n' and words[3] == '"'+camname+'_translateY";':
                if include_camera:
                    mode = 5
            
            elif mode == 5 and words[0] == 'setAttr' and words[1] == '-s': #get Y-Pos
                for x in range(1, int(float(words[2]))):
                    bpy.data.objects[newCamera.name].location[tyaxis] = float(words[(x*2)+3])*invert_y
                    newCamera.keyframe_insert(data_path='location', frame=x, index=tyaxis)
                mode = 0
            
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'animCurveTL' and words[2] == '-n' and words[3] == '"'+camname+'_translateZ";':
                if include_camera:
                    mode = 6
            
            elif mode == 6 and words[0] == 'setAttr' and words[1] == '-s': #get Z-Pos
                for x in range(1, int(float(words[2]))):
                    bpy.data.objects[newCamera.name].location[tzaxis] = float(words[(x*2)+3])*invert_z
                    newCamera.keyframe_insert(data_path='location', frame=x, index=tzaxis)
                mode = 0
            
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'animCurveTA' and words[2] == '-n' and words[3] == '"'+camname+'_rotateX";':
                if include_camera:
                    mode = 7
            
            elif mode == 7 and words[0] == 'setAttr' and words[1] == '-s': #get X-Rot
                for x in range(1, int(float(words[2]))):
                    bpy.data.objects[newCamera.name].rotation_euler[rxaxis] = radians(float(words[(x*2)+3])+self.xadd)*invert_rx
                    newCamera.keyframe_insert(data_path='rotation_euler', frame=x, index=rxaxis)
                mode = 0
            
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'animCurveTA' and words[2] == '-n' and words[3] == '"'+camname+'_rotateY";':
                if include_camera:
                    mode = 8
            
            elif mode == 8 and words[0] == 'setAttr' and words[1] == '-s': #get Y-Rot
                for x in range(1, int(float(words[2]))):
                    bpy.data.objects[newCamera.name].rotation_euler[ryaxis] = radians(float(words[(x*2)+3])+self.yadd)*invert_ry
                    newCamera.keyframe_insert(data_path='rotation_euler', frame=x, index=ryaxis)
                mode = 0
            
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'animCurveTA' and words[2] == '-n' and words[3] == '"'+camname+'_rotateZ";':
                if include_camera:
                    mode = 9
            
            elif mode == 9 and words[0] == 'setAttr' and words[1] == '-s': #get Z-Rot
                for x in range(1, int(float(words[2]))):
                    bpy.data.objects[newCamera.name].rotation_euler[rzaxis] = radians(float(words[(x*2)+3])+self.zadd)*invert_rz
                    newCamera.keyframe_insert(data_path='rotation_euler', frame=x, index=rzaxis)
                mode = 0
            
            elif mode == 0 and words[0] == 'createNode' and words[1] == 'locator' and words[2] == '-n': #get Track Number
                if include_empties:
                    if self.imported_tracknumbers:
                        try:
                            trackn = int(line[len(line[:-7]):-3])
                            if trackn <= enumber:
                                mode = 10
                        except:
                            try:
                                trackn = int(line[len(line[:-6]):-3])
                                if trackn <= enumber:
                                    mode = 10
                            except:
                                try:
                                    trackn = int(line[len(line[:-5]):-3])
                                    if trackn <= enumber:
                                        mode = 10
                                except:
                                    try:
                                        trackn = int(line[len(line[:-4]):-3])
                                        if trackn <= enumber:
                                            mode = 10
                                    except:
                                        print("Unable to load 1 marker.")
                    else:
                        if trackn <= enumber:
                            mode = 10
            
            elif mode == 10 and words[0] == 'setAttr' and words[1] == '".t"' and words[2] == '-type': #get Trackers
                try:
                    if self.flip_taxis:
                        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(float(words[4])*invert_x, float((words[6])[:-2])*invert_z, float(words[5])*invert_y))
                    else:
                        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(float(words[4])*invert_x, float(words[5])*invert_y, float((words[5])[:-2])*invert_z))
                    
                    trackobj = bpy.context.active_object
                    trackobj.name = self.ename + '.' + str(trackn).zfill(4)
                    bpy.ops.object.group_link(group=self.egroup)
                    bpy.ops.object.select_all(action = 'DESELECT')
                    if not self.imported_tracknumbers:
                        trackn = trackn + 1
                    
                except:
                    print("Unable to load 1 marker.")
                    
                mode = 0
                
            elif words[0] == 'playbackOptions' and words[1] == '-min' and words[3] == '-max':
                if not framesSet:
                    scene.frame_start = int(words[2])
                    scene.frame_end = int((words[4])[:-1])
            else:
                pass
            
        scene.frame_set(oframe)
        self.report({'INFO'}, 'Successfully imported.')

            
def menu_func(self, context):
    self.layout.operator(ImportMayaASCII.bl_idname, text="Maya ASCII (*.ma)")


def register():
    bpy.utils.register_class(ImportMayaASCII)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_class(ImportMayaASCII)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()