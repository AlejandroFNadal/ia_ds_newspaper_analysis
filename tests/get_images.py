import sys
sys.path.insert(0, '../lambda/newspaper-to-img-title')
from pull_image import pull_image_no_context
# This script downloads directly from the web one image from every month of the year since 1966

# we generate all march 3rd dates from 1966 to 2020 in format YYYY-MM-DD
dates = [f'{year}-03-03' for year in range(1966, 2021)]
# we download the image for each date
for date in dates:
    img_binary = pull_image_no_context(date)
    # we save the image in the images folder
    with open(f'data/{date}.webp', 'wb') as f:
        f.write(img_binary)
