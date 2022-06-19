import base64
import io
import json
import os
import pytesseract
import boto3
from PIL import Image
from unidecode import unidecode
import datetime
try:
    if os.getenv('AWS_EXECUTION_ENV') is not None:
        os.environ['LD_LIBRARY_PATH'] = '/opt/lib'
        os.environ['TESSDATA_PREFIX'] = '/opt/tessdata'
        pytesseract.pytesseract.tesseract_cmd = '/opt/tesseract'
except Exception as e:
    print(e)
def ocr(event, context):
    print('Dynamo Table Name')
    print(os.getenv('TABLE_WORDS'))
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
    img_path = event['Records'][0]['s3']['object']['key']
    print('Image path: ' + img_path)
    s3_arn = 'arn:aws:s3:::clarin-image-bucket'
    s3 = boto3.client('s3')
    img_data = s3.get_object(Bucket='clarin-image-bucket', Key=img_path)['Body'].read()
    image = io.BytesIO(img_data)
    # open the image and convert it to a PIL image object from a webp format
    image_for_ocr = Image.open(image)
    text = pytesseract.image_to_string(image_for_ocr, config="--psm 1 --oem 2", lang="spa")
    print('Text of title is: ' + text)
    # convert puntuation to spaces
    for letter in text:
        if letter in '.,;:!?':
            text = text.replace(letter, ' ')
    # importing stopwords
    stopword_file = open('stopwords_sp.txt', 'r')
    stopwords = []
    for line in stopword_file:
        stopwords.append(unidecode(line[:-1]))
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_WORDS'])
    # removing stopwords
    text = text.lower()
    text = text.split()
    text = [unidecode(word) for word in text]
    # also remove words only made from numbers and punctuation
    text = [word for word in text if word not in stopwords and word.isalpha()]
    # structure of the table
    # "word_example":{
    #    "dates":[19-02-2000, 24-02-2000,...],
    #    "month_year":[
    #       "02-2000":2,
    #       "03-2000":3,],
    #   "year":[
    #      "2000":2,
    #     "2001":3,],
    #   "another_word"...
    # }
    # for every element of text, we check if it is a key in the table
    # if it is, in the field 'date' we append the current date
    # in the field month_year we check if the current month_year exists, if it 
    # does, we add one to the value. If it doesnt, we create a new entry with 
    #month_year and we set the value to 1
    # in the field year we check if the value already exists, if it does, we add one to the value, if it doesnt, we create a new entry
    print('final text: ' + str(text))
    for word in text:
        response = table.get_item(
            Key={
                'word': word
            }
        )
        if 'Item' in response:
            item = response['Item']
            if 'dates' in item:
                item['dates'].append(str(datetime.datetime.now().date()))
            else:
                item['dates'] = [str(datetime.datetime.now().date())]
            if 'month_year' in item:
                if str(datetime.datetime.now().month) + '-' + str(datetime.datetime.now().year) in item['month_year']:
                    item['month_year'][str(datetime.datetime.now().month) + '-' + str(datetime.datetime.now().year)] += 1
                else:
                    item['month_year'][str(datetime.datetime.now().month) + '-' + str(datetime.datetime.now().year)] = 1
            else:
                item['month_year'] = {str(datetime.datetime.now().month) + '-' + str(datetime.datetime.now().year): 1}
            if 'year' in item:
                if str(datetime.datetime.now().year) in item['year']:
                    item['year'][str(datetime.datetime.now().year)] += 1
                else:
                    item['year'][str(datetime.datetime.now().year)] = 1
        else:
            item = {
                'word': word,
                'dates': [str(datetime.datetime.now().date())],
                'month_year': {str(datetime.datetime.now().month) + '-' + str(datetime.datetime.now().year): 1},
                'year': {str(datetime.datetime.now().year): 1}
            }
        #write item to db
        table.put_item(
            Item=item
        )
    return 0