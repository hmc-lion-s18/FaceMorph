#!/usr/bin/env python
#Most of this code is clone from learn opencv github repo
import sys
#import triangles
import cv2
import numpy as np
import features

def rect_contains(rect, point) :
    '''checks if a points is contains within the bounds
    of a rectangle plane'''

    if point[0] < rect[0] :
        return False
    elif point[1] < rect[1] :
        return False
    elif point[0] > rect[2] :
        return False
    elif point[1] > rect[3] :
        return False
    return True

def draw_delaunay(subdiv,dictionary1, r) :
    '''uses a brute force method to find which points fall under delaunay triangulation
    constraints'''

    trianglePoints =[]
    triangleList = subdiv.getTriangleList()
    
    for t in triangleList :
        pt1 = (int(t[0]), int(t[1]))
        pt2 = (int(t[2]), int(t[3]))
        pt3 = (int(t[4]), int(t[5]))
        if rect_contains(r, pt1) and rect_contains(r, pt2) and rect_contains(r, pt3) :
            trianglePoints.append((dictionary1[pt1],dictionary1[pt2],dictionary1[pt3]))
    

    return trianglePoints

def makeDelaunay(image, listOfPoints):

    '''the input is an image file read in by opencv and a list of average points
    the output is the final triangulation points in a list of tuples
    '''
    size = image.shape
    rect = (0, 0, size[0], size[0])
    # Create an instance of Subdiv2D.
    subdiv = cv2.Subdiv2D(rect);

    # Make a points list and a searchable dictionary. 
    theList= listOfPoints
    points=[(int(x[0]),int(x[1])) for x in theList] #making a tuple of points
    
    #the following line might still need some testing
    dictionary={x[0]:x[1] for x in list(zip(points,range(len(points))))}
   
    # Insert points into subdiv
    for p in points :
        subdiv.insert(p)
        
    # Make a delaunay triangulation list.
    return draw_delaunay(subdiv,dictionary, rect)


# Read points from text file
def readPoints(path) :
    # Create an array of points.
    # points = []
    # # Read points
    # with open(path) as file :
    #     for line in file :
    #         x, y = line.split()
    #         points.append((int(x), int(y)))

    return points

# Apply affine transform calculated using srcTri and dstTri to src and
# output an image of size.
def applyAffineTransform(src, srcTri, dstTri, size) :
    
    # Given a pair of triangles, find the affine transform.
    warpMat = cv2.getAffineTransform( np.float32(srcTri), np.float32(dstTri) )
    
    # Apply the Affine Transform just found to the src image
    dst = cv2.warpAffine( src, warpMat, (size[0], size[1]), None, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101 )

    return dst


# Warps and alpha blends triangular regions from img1 and img2 to img
def morphTriangle(img1, img2, img, t1, t2, t, alpha) :

    # Find bounding rectangle for each triangle
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))
    r = cv2.boundingRect(np.float32([t]))


    # Offset points by left top corner of the respective rectangles
    t1Rect = []
    t2Rect = []
    tRect = []


    for i in range(0, 3):
        tRect.append(((t[i][0] - r[0]),(t[i][1] - r[1])))
        t1Rect.append(((t1[i][0] - r1[0]),(t1[i][1] - r1[1])))
        t2Rect.append(((t2[i][0] - r2[0]),(t2[i][1] - r2[1])))


    # Get mask by filling triangle
    mask = np.zeros((r[3], r[2], 3), dtype = np.float32)
    cv2.fillConvexPoly(mask, np.int32(tRect), (1.0, 1.0, 1.0), 16, 0)

    # Apply warpImage to small rectangular patches
    img1Rect = img1[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]
    img2Rect = img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]]

    size = (r[2], r[3])
    warpImage1 = applyAffineTransform(img1Rect, t1Rect, tRect, size)
    warpImage2 = applyAffineTransform(img2Rect, t2Rect, tRect, size)

    # Alpha blend rectangular patches
    imgRect = (1.0 - alpha) * warpImage1 + alpha * warpImage2

    # Copy triangular region of the rectangular patch to the output image
    img[r[1]:r[1]+r[3], r[0]:r[0]+r[2]] = img[r[1]:r[1]+r[3], r[0]:r[0]+r[2]] * ( 1 - mask ) + imgRect * mask


if __name__ == '__main__' :

    filename1 = 'kobe_bryant.jpg'
    filename2 = 'donald_trump.jpg'
    userInput = input("Input a morphing rate between 0 and 1:")
    alpha = float(userInput)
    # Read images
    img1 = cv2.imread(filename1)
    img2 = cv2.imread(filename2)

    img1 = cv2.resize(img1,(600,800))
    img2 = cv2.resize(img2,(600,800))

    size1 = img1.shape
    size2 = img2.shape

    if(size1[0]==size2[0] and size1[1]==size2[1]):
        print("Hey")
    features = features.makeCorrespondence("shape_predictor_68_face_landmarks.dat",img1,img2)
    # Convert Mat to float data type
    img1 = np.float32(img1)
    img2 = np.float32(img2)

    # Read array of corresponding points
    # points1 = readPoints(filename1 + '.txt')
    # points2 = readPoints(filename2 + '.txt')
    #features = features.makeCorrespondence("shape_predictor_68_face_landmarks.dat",img1,img2)
    points1 = features[3]
    points2 = features[4]
    points = []

    # Compute weighted average point coordinates
    for i in range(0, len(points1)):
        x = ( 1 - alpha ) * points1[i][0] + alpha * points2[i][0]
        y = ( 1 - alpha ) * points1[i][1] + alpha * points2[i][1]
        points.append((x,y))
    # Allocate space for final output
    imgMorph = np.zeros(img1.shape, dtype = img1.dtype)

    trianglePoints = makeDelaunay(img2, points)
    for i in range(len(trianglePoints)):

        x,y,z = trianglePoints[i]
        
        x = int(x)
        y = int(y)
        z = int(z)
        
        t1 = [points1[x], points1[y], points1[z]]
        t2 = [points2[x], points2[y], points2[z]]
        t = [ points[x], points[y], points[z] ]

        # Morph one triangle at a time.
        morphTriangle(img1, img2, imgMorph, t1, t2, t, alpha)

    cv2.imshow("Morphed Face", np.uint8(imgMorph))
    cv2.waitKey(0)
