import pyzbar.pyzbar as pyzbar
from PIL import Image
import shutil
import logging
import os
import datetime
import requests
# For Telegram Integration
from config import telegram_token, project_matters_id

# Lasted edited 23rd Dec 19 Krish
# Start time
start_time = datetime.datetime.now()

# Directories
root_dir = os.getcwd()
raw_image_dir = root_dir + "\\" + 'images'
scanned_image_dir = root_dir + "\\" + 'scannedPhoto'

# Log initialisation
logging.basicConfig(filename='barcodeReader_error.log',level=logging.DEBUG)

# Counters initialisation
compressed_count = 0
failed_compression = 0
total_can_read_count = 0
total_cannot_read_count = 0
# Pass an PIL Image object into this function
def decode(im):
	# Find barcodes and QR codes
	decodedObjects = pyzbar.decode(im)
	# Print results
	for obj in decodedObjects:
		print('Type : ', obj.type)
		print('Data : ', obj.data, '\n')

		if obj.type != 'QRCODE' or 'www' in str(obj.data):
			decodedObjects.remove(obj)

	return decodedObjects

def compress(im):
	# Formula designed to maintain original aspect ratio
	target_width = 720
	wpercent = target_width/im.size[0]
	target_height = int(float(im.size[1])*float(wpercent))
	im = im.resize((target_width, target_height), Image.ANTIALIAS)
	return im

for imageFolder in os.listdir(raw_image_dir):
	# Reset count to 0 each time we open a new imageFolder but first tally the total count.
	can_read_count = 0
	cannot_read_count = 0

	imageFolder_dir = raw_image_dir + "\\" + imageFolder
	number_of_images = len(os.listdir(imageFolder_dir))
	print(f'Opening {imageFolder} right now and it has {number_of_images} images...\n\n')
	# Time to start iterating through each image within the imageFolder
	for image in os.listdir(imageFolder_dir):
		image_dir = imageFolder_dir + "\\" + image
		try:
			im = Image.open(image_dir)
		except IOError as e:
			logging.error(e)
		# Decode the PIL image with PyZbar
		results = decode(im)
		print(results)
		# enumerate takes in two parameters. The first is a list, the second is a counter which defaults to zero
		for index, decodedData in enumerate(results):
			barcodeItems = str(decodedData.data)
			print(f'****{barcodeItems} is the {index} barcode******\n')
		# If PIL Image has been successfully decoded!
		if results:
			print(
				f"\n{image} able to read barcode... appending into array\n")
			can_read_count = can_read_count + 1
		else:
			print(
				f"\n{image} is unable to read barcode... appending into non-readable array\n")
			cannot_read_count = cannot_read_count + 1
		# Splits the image's name to retrieve the order information "EG. 2019xxxx Shopee Orders"
		stringParts = image.split('_')
		orderFile_name = stringParts[1].strip()

		if 'shopee' in orderFile_name.lower():
			print(f'This is a Shopee file {orderFile_name}')
		if 'lazada' in orderFile_name.lower():
			print(f'This is a Lazada file {orderFile_name}')

		# scanned_image_dir is ./scannedPhoto
		canReadPath = scanned_image_dir + "\\" + str(orderFile_name) + "\\CAN READ\\"
		print(canReadPath)
		cannotReadPath = scanned_image_dir + "\\" + str(orderFile_name) + "\\CANNOT READ\\"

		# Tries to open the file order file directory. 
		# If unable to open due to error 'FileNotFoundError', it will create the folder with the order file name.
		try:
			tryOpen = os.listdir(scanned_image_dir + "\\" + str(orderFile_name))
			print("Order file directory detected, not creating..")

		except FileNotFoundError as e:
			print("File directory not created.. Creating file for " +
					str(orderFile_name))
			os.mkdir(scanned_image_dir + "\\" + str(orderFile_name))
			os.mkdir(canReadPath)
			os.mkdir(cannotReadPath)
			logging.error(e)

		# Compresses this image.
		try:
			im = compress(im)
			compressed_count = compressed_count + 1
		except Exception as e:
			failed_compression = failed_compression + 1
			logging.error(e)

		# We can further reduce the quality but we have achieved sufficient compression anyways
		# If barcode has been read, save in canread folder
		if results:
			barcode = results[0][0]
			dir = canReadPath + "\\" + " " + orderFile_name + "-" + str(barcode)
			print(f'Saving image with barcode {barcode} in {dir}\n\n')
			im.save(canReadPath + "\\" + orderFile_name + '-' + str(barcode) + '.jpg', quality=95)
		else:
			im.save(cannotReadPath + "\\" + orderFile_name +'.jpg', quality=95)

	if can_read_count + cannot_read_count == number_of_images:
		for i in range(100):
			try:
				# os.remove(imageFolder_dir)
				shutil.rmtree(imageFolder_dir)

				print('Deleted the folder, moving on to the next folder.')
				break
			except Exception as e:
				print('Failed to delete, trying again.')
				logging.error(e)
			finally:
				if i == 99:
					print('Stupid file does not want to get lost')
					pass
	
	total_can_read_count = total_can_read_count + can_read_count
	total_cannot_read_count = total_cannot_read_count + cannot_read_count

end_time = datetime.datetime.now()

try:
	text = f'barcodeReaderV2 has some good news for you!\n\nImages taken: {total_can_read_count+total_cannot_read_count}\
		\n\nImages read: {total_can_read_count}\
		\n\nImages not read: {total_cannot_read_count}\
		\n\nPercentage read: {round((total_can_read_count/(total_can_read_count+total_cannot_read_count))*100, 2)}%\
		\n\nImages compressed: {compressed_count}\
		\n\nCompressions failed: {failed_compression}\
		\n\nPercentage Compressed: {round((compressed_count/(compressed_count+failed_compression))*100, 2)}%\
		\n\nTime elapsed: {end_time-start_time})'
except Exception as e:
	logging.error(e)
	text = 'barcodeReaderV2 ran but it seems like there are no new images today.'

print(text)
requests.post(
    f'https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={project_matters_id}&disable_notification=True&text={text}')    
    