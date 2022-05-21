import base64
import io
import json
import os
import cv2


    
def detect_title(event, context):
    print('OpenCV version:')
    print(cv2.cv2.version.opencv_version)

    body = {
        "opencv_version": cv2.cv2.version.opencv_version
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response