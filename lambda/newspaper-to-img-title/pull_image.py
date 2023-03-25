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
    # get date from event
    date = event['Records'][0]['eventTime'].split('T')[0]
    print("Date of event: " + date)
    s3_arn = 'arn:aws:s3:::clarin-image-bucket'
    # generate datetime object from date string
    today = datetime.datetime.strptime(date, '%Y-%m-%d')
    # substract 1 from today
    today = today - datetime.timedelta(days=1)
    today_inverted = today.strftime('%d-%m-%Y')
    # url from clarin is:
    clarin_url= f'https://www.clarin.com/buscar-tapa-{today_inverted}.html'
    print("Url to get image from: " + clarin_url)
    # using requests to get url, save html to a string
    img_url = requests.get(clarin_url).json()['tapa_imagen']
    print("Image url: " + img_url)
    # I realized that it is not necessary to use beatiful soup because the image url also comes in a json response
    # but I kept it for future reference

    # using beautifulsoup to parse html
    # soup = BeautifulSoup(html, 'html.parser')
    # find the figure tag with class 'img-container'
    #img_container = soup.find('img', class_='img-responsive')
    #print(img_container)
    # obtain url
    #img_url = img_container['src']


    # get image from url and save it to a s3 bucket called image_clarin_bucket with name today's date
    img_data = requests.get(img_url).content
    # create a file object
    img_file = io.BytesIO(img_data)
    # create a binary image file
    img_binary = img_file.getvalue()
    # save img_binary to s3
    s3 = boto3.client('s3')
    s3.put_object(Bucket='clarin-image-bucket', Key=f"front_pages/{today}.webp", Body=img_binary)
    
    
    return 0
