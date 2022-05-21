import base64
import io
import json
import os
import pytesseract
from PIL import Image
try:
    if os.getenv('AWS_EXECUTION_ENV') is not None:
        os.environ['LD_LIBRARY_PATH'] = '/opt/lib'
        os.environ['TESSDATA_PREFIX'] = '/opt/tessdata'
        pytesseract.pytesseract.tesseract_cmd = '/opt/tesseract'
except Exception as e:
    print(e)
def ocr(event, context):
    print('Checking Tesseract')
    if os.path.exists('/opt'):
        print('Opt exists')
        print(os.listdir('/opt'))
        if os.path.exists('/opt/tesseract'):
            print('opt tesseract exists')
        else:
            print('opt tesseract doesnt exist')
    else:
        print('Opt doesnt exist')
    request_body = json.loads(event['body'])
    image = io.BytesIO(base64.b64decode(request_body['image']))

    text = pytesseract.image_to_string(Image.open(image), lang="spa")

    body = {
        "text": text
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response