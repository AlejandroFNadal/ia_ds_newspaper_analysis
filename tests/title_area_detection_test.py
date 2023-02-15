import sys
sys.path.insert(0, '../lambda/newspaper-to-img-title')
from opencv_handler import local_detect_title

#list all files from data folder
import os
from os import listdir
from os.path import isfile, join
mypath = 'data'
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

# opening the file Labelled_ROI.json
import json
with open('Labelled_ROI.json') as json_file:
    # we get every key, remove everything from the key after ".jpg". For the correspondent value
    # we get region.x, region.y, region.width, region.height. These values are saved in a dict with the modified key
    # as key and the values as values
    data = json.load(json_file)
    labelled_data = {}
    for key in data:
        new_key = key.split('.jpg')[0]
        json_shape_attributes= data[key]['regions'][0]['shape_attributes']
        labelled_data[new_key] = {}
        labelled_data[new_key]['y_prime'] = [json_shape_attributes['x'], json_shape_attributes['y'], json_shape_attributes['width'], json_shape_attributes['height']]

# we iterate over all files
for file in onlyfiles:
    # we open the file
    with open(f'{mypath}/{file}', 'rb') as f:
        # we read the binary data
        img_data = f.read()
        # we detect the title
        img, x, y, x2, y2 = local_detect_title(img_data)
        # we save the detected title in a dict
        new_key = file.split('.jpg')[0]
        labelled_data[new_key]['y'] = [x, y, x2, y2]
# now we calculate the IoC, iterating over the dict
average_iou = 0
for key in labelled_data:
    # we calculate the area of union and intersection
    x1, y1, x2, y2 = labelled_data[key]['y']
    x1_prime, y1_prime, x2_prime, y2_prime = labelled_data[key]['y_prime']
    xA = max(x1, x1_prime)
    yA = max(y1, y1_prime)
    xB = min(x2, x2_prime)
    yB = min(y2, y2_prime)
    interArea = max(0, xB - xA ) * max(0, yB - yA )
    boxAArea = (x2 - x1) * (y2 - y1)
    boxBArea = (x2_prime - x1_prime) * (y2_prime - y1_prime)
    iou = interArea / float(boxAArea + boxBArea - interArea)
    # we save the IoC in the dict
    labelled_data[key]['IoC'] = iou
    # we add the IoC to the average
    average_iou += iou
# we calculate the average IoC
average_iou /= len(labelled_data)
print(f'Average IoC: {average_iou}')



        