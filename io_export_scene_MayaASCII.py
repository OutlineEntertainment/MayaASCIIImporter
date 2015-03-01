import bpy
from bpy.props import *
import os.path
from bpy_extras.io_utils import ExportHelper
from math import degrees, radians

bl_info = {
    "name": "Maya ASCII (*.ma) Exporter",
    "author": "Outline Entertainment",
    "version": (1, 0),
    "blender": (2, 73, 0),
    "location": "File > Export",
    "description": "An export script for Maya ASCII (.ma) files. It can be used to export tracking data.",
    "warning": "Still WIP",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

class ExportMayaASCII(bpy.types.Operator, ExportHelper):
    bl_idname = "export.mayaascii"
    bl_label = "Export Maya ASCII (*.ma)"
    bl_options = {'REGISTER', 'UNDO'}
    
    sscale = FloatProperty (name ="sscale", default = 1, description="Scene Scale Multiplier")
    enumber = IntProperty (name ="enumber", default = 50, description="Max. Number of Empties to be Exported")
    anim_empties = BoolProperty (name ="anim_empties", default = False, description="Animate Empties")
    
    filename_ext = ".ma"
    filter_glob = StringProperty(default="*.ma", options={'HIDDEN'})

    @classmethod    
    def poll(cls, context):
        return context.active_object != None and bpy.context.scene.camera != None    

    def execute(self, context):
        self.exportTracking(self.filepath)
        return {'FINISHED'}
        
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row()
        row.prop(self,'sscale','Scene Scale')
        row = col.row()
        row.separator()
        row = col.row()
        row.prop(self,'enumber','Max. Number of Empties')
        row = col.row()
        row.prop(self,'anim_empties','Animate Empties')
    
    def exportTracking(self, filename):
        print("Exporting...")
        scene = bpy.context.scene
        try:
            expCamObj = bpy.context.object
            test = bpy.data.cameras[expCamObj.data.name].lens
        except:
            expCamObj = bpy.context.scene.camera
        expCamera = expCamObj.data
        enumber = self.enumber
        sscale = self.sscale*100
        anim_empties = self.anim_empties
        oframe = scene.frame_current
        start_frame = scene.frame_start
        end_frame = scene.frame_end
        
        hasmedia = True
        try:
            media_start_frame = scene.active_clip.frame_start-1 #starts at one hitfilm expexts 0 based
            media_end_frame = scene.active_clip.frame_duration #even tho 0 based looks to 1 based last frame in xml so leave
        except:
            hasmedia = False
            media_start_frame = start_frame #starts at one hitfilm expexts 0 based
            media_end_frame = end_frame #even tho 0 based looks to 1 based last frame in xml so leave  
        
        scene.frame_set(scene.frame_start)
        
        num_frames = end_frame+1 - start_frame
        flength = end_frame+1 - start_frame
        res_x = bpy.context.scene.render.resolution_x
        res_y = bpy.context.scene.render.resolution_y
        resasp = res_x/res_y
        aspect = res_x*scene.render.pixel_aspect_x / float(res_y*scene.render.pixel_aspect_y)
        
        t = {}
        
        #header
        t['header'] = []
        t['header'].append('//Maya ASCII 2010 scene\n\nrequires maya "2010";\n')
        
        #fps
        if bpy.context.scene.render.fps < 25:
            fps = 'film'
        elif bpy.context.scene.render.fps < 30:
            fps = 'pal'
        else:
            fps = 'ntsc'
        t['header'].append('currentUnit -l centimeter -a degree -t %s;\n'%(fps))
        
        #resolution
        t['header'].append('select -ne defaultResolution;\n')
        t['header'].append('    setAttr ".w" %s;\n'%(res_x))
        t['header'].append('    setAttr ".h" %s;\n'%(res_y))
        t['header'].append('    setAttr ".dar" %s;\n'%(resasp))
        t['header'].append('    setAttr ".ldar" yes;\n\n')
        
        #camera
        c = 1.25
        aperturex = min(c,c*aspect)
        aperturey = min(c,c/aspect)  
        t['header'].append('createNode transform -n "%s";\n'%(expCamObj.name))
        t['header'].append('createNode camera -n "%sShape" -p "%s";\n'%(expCamObj.name,expCamObj.name))
        t['header'].append('    setAttr -k off ".v";\n')
        t['header'].append('    setAttr ".cap" -type "double2" %s %s;\n'%(aperturex,aperturey))  
        t['header'].append('    setAttr ".ff" 3;\n')#filmfit
        #nearClipPlane 0.001(pfhoe reference)
        t['header'].append('    setAttr ".ncp" %f;\n'%(expCamera.clip_start*sscale))
        #farClipPlane 1000(pfhoe reference)
        t['header'].append('    setAttr ".fcp" %f;\n'%(expCamera.clip_end*sscale))
        #focusDistance 5(pfhoe reference)       
        t['header'].append('    setAttr ".fd" %f;\n'%(expCamera.dof_distance*sscale))
        #centerOfInterest 5(pfhoe reference)     
        t['header'].append('    setAttr ".coi" %f;\n'%(expCamera.dof_distance*sscale))
        #orthographicWidth 10(pfhoe reference)     
        t['header'].append('    setAttr ".ow" 10;\n')
        #displayResolution        
        t['header'].append('    setAttr ".dr" yes;\n')
        
        #empties
        tracker=[]
        tracker_data=[] 
        
        idx = 1
        for o in bpy.context.selected_objects:
            if o.type=='EMPTY':
                tracker.append(o)
                tracker_data.append(['']*9)
                idx+=1
            if idx>enumber: break
        
        #animation
        c_fl =''
        c_v =''
        c_tx =''
        c_ty =''
        c_tz =''
        c_rx =''
        c_ry =''
        c_rz =''
        for frame in range(start_frame, end_frame+1):
            scene.frame_set(frame)
            obj = expCamObj
            
            x = bpy.data.objects[expCamObj.name].location[0]*sscale
            y = bpy.data.objects[expCamObj.name].location[2]*sscale
            z = bpy.data.objects[expCamObj.name].location[1]*sscale*-1
            
            rx = degrees(bpy.data.objects[expCamObj.name].rotation_euler[0])-90
            ry = degrees(-bpy.data.objects[expCamObj.name].rotation_euler[2])*-1
            rz = degrees(bpy.data.objects[expCamObj.name].rotation_euler[1])
            
            c_fl+=(' %s %s'%(frame,expCamera.lens))
            c_v+=(' %s 1'%(frame))
            c_tx+=(' %s %s'%(frame,x))
            c_ty+=(' %s %s'%(frame,y))
            c_tz+=(' %s %s'%(frame,z))
            c_rx+=(' %s %s'%(frame,rx))
            c_ry+=(' %s %s'%(frame,ry))
            c_rz+=(' %s %s'%(frame,rz))
            if anim_empties or scene.frame_current == scene.frame_start:
                idx = 1
                for o in tracker:
                    x = bpy.data.objects[o.name].location[0]*sscale
                    y = bpy.data.objects[o.name].location[2]*sscale
                    z = bpy.data.objects[o.name].location[1]*sscale*-1
                    
                    if anim_empties:
                        rx = degrees(bpy.data.objects[o.name].rotation_euler[0])-90
                        ry = degrees(-bpy.data.objects[o.name].rotation_euler[2])*-1
                        rz = degrees(bpy.data.objects[o.name].rotation_euler[1])
                    
                        sx = bpy.data.objects[o.name].scale[0]*sscale
                        sy = bpy.data.objects[o.name].scale[2]*sscale
                        sz = bpy.data.objects[o.name].scale[1]*sscale
                        
                        tracker_data[idx-1][0]+=(' %s %s'%(frame,x))
                        tracker_data[idx-1][1]+=(' %s %s'%(frame,y))
                        tracker_data[idx-1][2]+=(' %s %s'%(frame,z))
                        tracker_data[idx-1][3]+=(' %s %s'%(frame,rx))
                        tracker_data[idx-1][4]+=(' %s %s'%(frame,ry))
                        tracker_data[idx-1][5]+=(' %s %s'%(frame,rz))
                        tracker_data[idx-1][6]+=(' %s %s'%(frame,sx))
                        tracker_data[idx-1][7]+=(' %s %s'%(frame,sy))
                        tracker_data[idx-1][8]+=(' %s %s'%(frame,sz))
                    else:
                        tracker_data[idx-1][0]+=(' %s'%(x))
                        tracker_data[idx-1][1]+=(' %s'%(y))
                        tracker_data[idx-1][2]+=(' %s'%(z))
                    idx+=1
                
        #camera animation lines   
        t['anim']=[]
        t['anim'].append('createNode animCurveTU -n "%s_focalLength";\n'%(expCamObj.name))
        t['anim'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,c_fl))

        t['anim'].append('createNode animCurveTU -n "%s_visibility";\n'%(expCamObj.name))
        t['anim'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,c_v))
        
        t['anim'].append('createNode animCurveTL -n "%s_translateX";\n'%(expCamObj.name))
        t['anim'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,c_tx))
            
        t['anim'].append('createNode animCurveTL -n "%s_translateY";\n'%(expCamObj.name))
        t['anim'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,c_ty)) #invert
                
        t['anim'].append('createNode animCurveTL -n "%s_translateZ";\n'%(expCamObj.name))
        t['anim'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,c_tz))
        
        t['anim'].append('createNode animCurveTA -n "%s_rotateX";\n'%(expCamObj.name))
        t['anim'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,c_rx))
        
        t['anim'].append('createNode animCurveTA -n "%s_rotateY";\n'%(expCamObj.name))
        t['anim'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,c_ry)) #invert
        
        t['anim'].append('createNode animCurveTA -n "%s_rotateZ";\n'%(expCamObj.name))
        t['anim'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,c_rz))
        
        #cam_footer
        t['cam_footer']=[]
        t['cam_footer'].append('connectAttr "%s_focalLength.o" "%sShape.fl";\n'%(expCamObj.name,expCamObj.name))
        t['cam_footer'].append('connectAttr "%s_visibility.o" "%sShape.v";\n'%(expCamObj.name,expCamObj.name))
        t['cam_footer'].append('connectAttr "%s_translateX.o" "%s.tx";\n'%(expCamObj.name,expCamObj.name))
        t['cam_footer'].append('connectAttr "%s_translateY.o" "%s.ty";\n'%(expCamObj.name,expCamObj.name))
        t['cam_footer'].append('connectAttr "%s_translateZ.o" "%s.tz";\n'%(expCamObj.name,expCamObj.name))
        t['cam_footer'].append('connectAttr "%s_rotateX.o" "%s.rx";\n'%(expCamObj.name,expCamObj.name))
        t['cam_footer'].append('connectAttr "%s_rotateY.o" "%s.ry";\n'%(expCamObj.name,expCamObj.name))
        t['cam_footer'].append('connectAttr "%s_rotateZ.o" "%s.rz";\n'%(expCamObj.name,expCamObj.name))
        
        #point animation lines
        t['point'] = [] 
        idx = 1
        for o in tracker:
            t['point'].append('createNode transform -n "Track_%s";\n'%idx)
            if anim_empties:
                t['point'].append('createNode locator -n "Point_%s" -p "Track_%s";\n'%(idx,idx))
                t['point'].append(' setAttr -k off ".v";\n')
                tracker_data[idx-1][0]+=(' %s %s'%(frame,x))
                tracker_data[idx-1][1]+=(' %s %s'%(frame,y))
                tracker_data[idx-1][2]+=(' %s %s'%(frame,z))
                tracker_data[idx-1][3]+=(' %s %s'%(frame,rx))
                tracker_data[idx-1][4]+=(' %s %s'%(frame,ry))
                tracker_data[idx-1][5]+=(' %s %s'%(frame,rz))
                tracker_data[idx-1][6]+=(' %s %s'%(frame,sx))
                tracker_data[idx-1][7]+=(' %s %s'%(frame,sy))
                tracker_data[idx-1][8]+=(' %s %s'%(frame,sz))
                t['point'].append('createNode animCurveTU -n "Track_%s_tx";\n'%idx)
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][0]))
                t['point'].append('createNode animCurveTU -n "Track_%s_ty";\n'%idx)
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][1]))
                t['point'].append('createNode animCurveTU -n "Track_%s_tz";\n'%idx)
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][2]))
                
                t['point'].append('createNode animCurveTU -n "Track_%s_rx";\n'%idx)
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][3]))
                t['point'].append('createNode animCurveTU -n "Track_%s_ry";\n'%idx)
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][4]))
                t['point'].append('createNode animCurveTU -n "Track_%s_rz";\n')
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][5]))
                
                t['point'].append('createNode animCurveTU -n "Track_%s_sx";\n'%idx)
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][6]))
                t['point'].append('createNode animCurveTU -n "Track_%s_sy";\n'%idx)
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][7]))
                t['point'].append('createNode animCurveTU -n "Track_%s_sz";\n'%idx)
                t['point'].append('  setAttr -s %s ".ktv[%s:%s]"%s;\n'%(num_frames,start_frame,end_frame,tracker_data[idx-1][8]))
                
                t['point'].append('connectAttr "Track_%s_tx.o" "Track_%s.tx";\n'%(idx,idx))
                t['point'].append('connectAttr "Track_%s_ty.o" "Track_%s.ty";\n'%(idx,idx))
                t['point'].append('connectAttr "Track_%s_tz.o" "Track_%s.tz";\n'%(idx,idx))
                
                t['point'].append('connectAttr "Track_%s_rx.o" "Track_%s.rx";\n'%(idx,idx))
                t['point'].append('connectAttr "Track_%s_ry.o" "Track_%s.ry";\n'%(idx,idx))
                t['point'].append('connectAttr "Track_%s_rz.o" "Track_%s.rz";\n'%(idx,idx))
                
                t['point'].append('connectAttr "Track_%s_sx.o" "Track_%s.sx";\n'%(idx,idx))
                t['point'].append('connectAttr "Track_%s_sy.o" "Track_%s.sy";\n'%(idx,idx))
                t['point'].append('connectAttr "Track_%s_sz.o" "Track_%s.sz";\n'%(idx,idx))
            else:
                t['point'].append(' setAttr ".t" -type "double3" %s %s %s;\n'%(tracker_data[idx-1][0],tracker_data[idx-1][1],tracker_data[idx-1][2]))
                t['point'].append('createNode locator -n "Point_%s" -p "Track_%s";\n'%(idx,idx))
                t['point'].append(' setAttr -k off ".v";\n')
            idx+=1
        
        #footer
        t['footer']=[]
        t['footer'].append('playbackOptions -min %s -max %s;\n'%(start_frame,end_frame))
        
        #write
        if not filename.endswith('.ma'):
            filename += '.ma'
        mafile = open(filename, 'w')
        
        for line in t['header']:
            mafile.write(line)

        for line in t['anim']:
            mafile.write(line)      
            
        for line in t['cam_footer']:
            mafile.write(line)  
            
        for line in t['point']:
            mafile.write(line)  
            
        for line in t['footer']:
            mafile.write(line)
            
        del t
        self.report({'INFO'}, 'Successfully exported.')
        scene.frame_set(oframe)

def menu_func(self, context):
    self.layout.operator(ExportMayaASCII.bl_idname, text="Maya ASCII (*.ma)")


def register():
    bpy.utils.register_class(ExportMayaASCII)
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    bpy.utils.unregister_class(ExportMayaASCII)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()