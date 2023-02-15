import base64
import io
import json
import os
import cv2
import boto3
import numpy as np

def local_detect_title(img_binary_data):
    # write the image to tmp
    img_file = io.BytesIO(img_binary_data)
    img_binary = img_file.getvalue()
    # read the image
    img = cv2.imdecode(np.frombuffer(img_binary, np.uint8), cv2.IMREAD_COLOR)
    
    ## removing 20% top
    height = img.shape[0]
    header_size = int(height/5)
    img = img[header_size:,:,:]
    ## detecting lines
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # we use canny because it highlights the borders and edges, improving the results of HoughLinesP
    edges = cv2.Canny(gray, 255, 255) 
    minLineLength = 150
    maxLineGap = 3
    lines = cv2.HoughLinesP(image=edges, rho=1, theta=np.pi/180.0, threshold=10, 
                        minLineLength = minLineLength, 
                        maxLineGap = maxLineGap)
    if lines == []:
        print(f'No lines found ')
    else:
        #remove lines by painting over them
        for elem in lines:
            for x1, y1, x2, y2 in elem:
                cv2.line(img, (x1,y1), (x2, y2), (255, 255,255), 3)
    ## remove main image looking for biggest areas
    gray_no_lines = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #black and white images work better for contour finding
    ret, thresh = cv2.threshold(gray_no_lines, 230, 255, cv2.THRESH_BINARY)
    # using the negative of the image gives better results
    contours, hier = cv2.findContours(~thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
    
    areas = [[index, cv2.contourArea(c)] for index, c in enumerate(contours)]
    #sorting the areas will allow us to eliminate the biggest ones choosing, in this case, two. The elimination is just painting a whole white rectangle on top of it
    sorted_areas = sorted(areas, key = lambda x: x[1], reverse=True)
    for i in range(0,2):
        x,y,w,h = cv2.boundingRect(contours[sorted_areas[i][0]])
        cv2.rectangle(img, (x,y), (x+w, y+h), (255,255,255),-1)
    likely_img_pos = contours[sorted_areas[0][0]] #saving just in case we need it later
    # get contours with biggest height
    gray_no_lines = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray_no_lines, 120, 255, cv2.THRESH_BINARY)
    #ret, thresh = cv2.threshold(cv2.cvtColor(newspaper_borders, cv2.COLOR_BGR2GRAY), 127, 255, cv2.THRESH_BINARY)
    contours, hier = cv2.findContours(~thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) #Important, external will give you only an external bounding box. Tree will give you every single
    heights = [[index, cv2.boundingRect(c)[3]] for index, c in enumerate(contours) if cv2.boundingRect(c)[3]> 2]
    heights_only = [elem[1] for elem in heights]
    if heights_only == []:
        return -1
    heights_only_np = np.array(heights_only)
    q3 = np.quantile(heights_only_np, 0.93)
    sorted_heights = sorted(heights, key = lambda x: x[1], reverse=True)
    #calculate average height
    avg_height = 0
    for pair in sorted_heights:
        avg_height +=pair[1]
    avg_height = avg_height/len(sorted_heights)

    #draw boxes for each letter
    # save the boxes
    letter_boxes = []
    for i in range(0,len(sorted_heights)):
        if sorted_heights[i][1] > q3:
            x,y,w,h = cv2.boundingRect(contours[sorted_heights[i][0]])
            letter_boxes.append([x,y,w,h])
    ## eliminate boxes inside boxes
    for coords in letter_boxes:
        x, y, w, h = coords
        i = 0
        for other_coords in letter_boxes:
            x2,y2,w2,h2 = other_coords
            if x < x2 and y < y2 and x+w > x2+w2 and y+h > y2+h2:
                letter_boxes[i] = [-1,-1,-1,-1]
            i+=1
    letter_boxes[:] = [elem for elem in letter_boxes if elem[0] != -1]
    #drop boxes with small areas now out of letter_boxes
    avg_area = 0
    areas = []
    for coords in letter_boxes:
        area = coords[2]*coords[3]
        avg_area += area
        areas.append(area)
    avg_area /= len(areas)
    areas_array = np.array(areas)
    std = np.std(areas_array)
    letter_boxes[:] = [coords for coords in letter_boxes if coords[2]*coords[3] > avg_area]
    
    line_boxes = []
    while letter_boxes != []:
        comp_box = letter_boxes[0]
        original_width = comp_box[2]
        original_height = comp_box[3]
        letter_boxes.pop(0)
        #create the new line box
        for coords in letter_boxes:
            # if vertical position + height is similar, then most likely belongs to the same phrase

            if abs(coords[1]+coords[3] - (comp_box[1]+comp_box[3])) < 10:

                #if the x of the possible added box is less than the x of our comp_box, it is at our left
                if coords[0] < comp_box[0]:

                    #space analysis
                    #if (coords[0]+coords[2] - comp_box[0]) < original_width + 20: # this might fail with spaces between words if the chosen letter is too small
                    comp_box[2] = coords[2] + (-(coords[0] + coords[2]) + comp_box[0]) + comp_box[2] #w new box + gap + w old box
                    comp_box[0] = coords[0] # correcting x
                    comp_box[1] =  min(coords[1], comp_box[1])# for capital letters, some might be taller than others.
                    comp_box[3] = max(coords[3],comp_box[3])
                if coords[0] > (comp_box[0]+ comp_box[2]): # the new possible box is at the right:

                    #print(comp_box, coords)
                    #if (coords[0] - (comp_box[0] + comp_box[2])) < original_width + 20: # space check:
                        #update comp_box
                        # new w is orignial w + extra w + gap
                    comp_box[2] += coords[2] + (coords[0] - (comp_box[0] + comp_box[2])) 
                    # x doesnt change
                    comp_box[1] = min(coords[1], comp_box[1]) #pick the smallest y and the heighest h
                    comp_box[3] = max(coords[3], comp_box[3])
        # eliminate all boxes in the same height
        letter_boxes[:] = [coords for coords in letter_boxes if abs((comp_box[1]+comp_box[3]) - (coords[1]+ coords[3])) > 10]

        # add new line to line_list
        line_boxes.append(comp_box)
    #eliminate smaller boxes in width (these would not be titles but stuff that has survived to all the filtering before
    # even if we eliminate some letter, it will still be obtained when we join all the lines
    avg_width = 0
    for coords in line_boxes:
        avg_width += coords[2]
    avg_width = avg_width / len(line_boxes)

    line_boxes[:] = [coords for coords in line_boxes if coords[2] >= avg_width*0.7]
    
    #combine boxes
    x, y, x2, y2 = line_boxes[0]
    x2 += x# we need the actual coordinates for the second point of the rectangle
    y2 += y 
    for coords in line_boxes:
        if coords[0] < x:
            x = coords[0]
        if coords[1] < y:
            y = coords[1]
        if coords[0] + coords[2] > x2:
            x2 = coords[0] + coords[2]
        if coords[1] + coords[3] > y2:
            y2 = coords[1] + coords[3]
    return [img, x,y,x2,y2]
    
def detect_title(event, context):
    #print('OpenCV version:')
    #print(cv2.cv2.version.opencv_version)
    # first we obtain the path to the image from the event
    img_path = event['Records'][0]['s3']['object']['key']
    print(f'Image Path: {img_path}')
    s3_arn = 'arn:aws:s3:::clarin-image-bucket'
    # we obtain the image from s3
    s3 = boto3.client('s3')
    img_data = s3.get_object(Bucket='clarin-image-bucket', Key=img_path)['Body'].read()
    
    
    img, x, y, x2, y2 = local_detect_title(img_data)
    #we extract the image, adding a bit of extra margin on the bottom for good measure
    title_img = img[y:(y2+20), x:x2]
    #write image in /tmp/
    image_name = img_path.split('/')[1]
    saved_to_disk = cv2.imwrite(f"/tmp/{image_name}", title_img)
    print(f"Imaged saved locally: {saved_to_disk}")
    # save image to s3 folder title
    s3.put_object(Bucket='clarin-image-bucket', Key=f"titles/{image_name}", Body=open(f"/tmp/{image_name}", 'rb'))
    return True