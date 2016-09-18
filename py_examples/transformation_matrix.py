'''
Created on Aug 18, 2016

@author: Patrick
'''
import bpy
from mathutils import Vector, Matrix



###################################################
#########    ROTATION PART OF MATRIX  #############
###################################################


#how to make a transformation matrix from reference 
#vectors X and Y.  Z will be calculated from X and Y
#Y will be made touarantee X and Y are orthogonal
X = Vector((3,6,1))   #change these valuse
Y_user = Vector((8,0,-1))  #change these valuse

#convert to unit vectors
X.normalize()
Y_user.normalize()

Z = X.cross(Y_user)
Y = Z.cross(X)
          
#rotation matrix from principal axes
T = Matrix.Identity(3)  #make the columns of matrix U, V, W
T[0][0], T[0][1], T[0][2]  = X[0] ,Y[0],  Z[0]
T[1][0], T[1][1], T[1][2]  = X[1], Y[1],  Z[1]
T[2][0] ,T[2][1], T[2][2]  = X[2], Y[2],  Z[2]

Rotation_Matrix = T.to_4x4()



###################################################
#########    LOCATION PART OF MATRIX  #############
###################################################

#location is stored in the 4th colum of the
#world matrix
location = Vector((1,2,3))
T = Matrix.Identity(4)

T[0][3] = location[0]
T[1][3] = location[1]
T[2][3] = location[2]