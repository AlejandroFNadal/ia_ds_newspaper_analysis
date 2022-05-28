import base64
import io
import json
import os
import datetime
import requests
from bs4 import BeautifulSoup
import boto3
    
def pull_image(event, context):
    #s3 arn
    s3_arn = 'arn:aws:s3:::clarin-image-bucket'
    # get today's date
    today = datetime.datetime.today()
    # url from clarin is:
    clarin_url= ' https://www.clarin.com/tapa-diario-clarin-hoy.html?h='
    #adding date at the end of url in format dd-mm-yyyy
    clarin_url = clarin_url + today.strftime("%d-%m-%Y")
    # using requests to get url, save html to a string
    html = requests.get(clarin_url).text
    
    # using beautifulsoup to parse html
    soup = BeautifulSoup(html, 'html.parser')
    # find the figure tag with class 'img-container'
    img_container = soup.find('img', class_='img-responsive')
    print(img_container)
    # obtain url
    img_url = img_container['src']
    # get image from url and save it to a s3 bucket called image_clarin_bucket with name today's date
    img_data = requests.get(img_url).content
    # create a file object
    img_file = io.BytesIO(img_data)
    # create a binary image file
    img_binary = img_file.getvalue()
    # save img_binary to s3
    s3 = boto3.client('s3')
    s3.put_object(Bucket='clarin-image-bucket', Key=f"front_pages/{today.strftime('%d-%m-%Y')}.webp", Body=img_binary)
    # return the url of the image
    body = {
        "s3_url": s3_arn + '/' + today.strftime("%d-%m-%Y")
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response