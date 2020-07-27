import os
import imageio
import imgaug as ia
from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage
from imgaug import augmenters as iaa 
from collections import defaultdict
from PIL import Image
import numpy as np
from skimage import io as sk_io
ia.seed(1)
import torch


def separate_file(directory,sep_file="txt"):
	
	"""
	sep file takes txt, jpg.
	"""

	folder_name="Seperated image1" if sep_file=="jpg" else "Seperated txt1"  
	new_dir=os.path.join(os.path.split(directory)[0],folder_name)
	if not os.path.exists(new_dir):
		os.makedirs(new_dir)

	count=0
	for file in os.listdir(directory):
		if sep_file=="txt":
			if file.endswith(".txt"):	

				with open(os.path.join(directory,file),"rt") as lines:
					with open(os.path.join(new_dir,file),"wt") as stream:
						for line in lines:
							stream.write(line)
				

 	
		if sep_file=="jpg":
			if file.endswith(".jpg"):
				path=os.path.join(new_dir,file)

				img = Image.open(os.path.join(directory,file))
				img=img.save(path)



def conversion(txt_file_directory,image_directory):
	"""
	Takes images and annotations from different folders, applies transformation to both the image
	and annotation, and saves both. 
	"""

	# go one level back.
	img_save_dir=os.path.join(os.path.split(image_directory)[0],"yolo_annotations_transformed_images_2000_5c") 
	txt_sav_dir=os.path.join(os.path.split(txt_file_directory)[0],"yolo_annotations_transformed_annotations_2000_5c")
	
	if not os.path.exists(img_save_dir) and not os.path.exists(txt_sav_dir):
		os.makedirs(img_save_dir)
		os.makedirs(txt_sav_dir)

    # sepereted directories is good to make sure we loop simultanouesly.
	iterable= zip(os.listdir(image_directory),os.listdir(txt_file_directory)) 
	
	count=0
	for img,txt in iterable:
		bb_list=[]
		l=[]
		label_list=[]

		"""
		the img and txt have need to match exactly.
		"""
		if img.endswith(".jpg") and txt.endswith(".txt") and img.strip(".jpg")== txt.strip(".txt"):

			image = imageio.imread(os.path.join(image_directory,img))

			file=open(os.path.join(txt_file_directory,txt))
			for line in file.readlines():	

				"""
				read from the yolo format, convert to pascal voc, which matches the bounding box requirements of 
				imgaug's BoundingBox class.
				"""
			
				label=int(line.split()[0])

				# create a list, then remove the class label.
				new_line=line.split()[1:] 
			
				xmin = max(float(new_line[0]) - float(new_line[2]) / 2, 0)
				xmax = min(float(new_line[0]) + float(new_line[2]) / 2, 1)
				ymin = max(float(new_line[1]) - float(new_line[3]) / 2, 0)
				ymax = min(float(new_line[1]) + float(new_line[3]) / 2, 1)

				xmin = round(float(image.shape[1] * xmin))
				xmax = round(float(image.shape[1] * xmax))
				ymin = round(float(image.shape[0] * ymin))
				ymax = round(float(image.shape[0] * ymax))
								
				bb=BoundingBox(x1=xmin, x2=xmax, y1=ymin, y2=ymax)
				bb_list.append(bb)
				label_list.append(label)
	
			bbs = BoundingBoxesOnImage(bb_list,shape=image.shape)
			
			seq = iaa.Sequential([
				iaa.GammaContrast(1.5),
				iaa.AdditiveGaussianNoise(scale=(10, 60)),
				iaa.Affine(rotate=(-30, 30))])

			image_aug, bbs_aug = seq(image=image, bounding_boxes=bbs)

			for i in range(len(bbs.bounding_boxes)):
				
				"""
				Convert the  voc bounding box format back to yolo format.
				"""
				after=bbs_aug.bounding_boxes[i]
				xcen = float((after.x1 + after.x2)) / 2 / image.shape[1]
				ycen = float((after.y1 + after.y2)) / 2 / image.shape[0]

				w = float((after.x2 - after.x1)) / image.shape[1]
				h = float((after.y2 - after.y1)) / image.shape[0]

				l1=[label,xcen, ycen, w, h] 

				l.append(l1)

			label_array=np.array(label_list)
			yolo_array=np.array(l)
			
			yolo_array[:,0]=np.array(list(map(lambda x: int(x),label_array)))

			# if does not exists, creates then saves.
			with open(os.path.join(txt_sav_dir,txt),"wt", encoding='ascii') as stream: 		
				#print("Reached")
				# format types for all columns.
				fmt= '%d', '%1.7f', '%1.7f', '%1.7f','%1.7f' 
				np.savetxt(stream, yolo_array, fmt=fmt)
				#print("Saved")
			
			#save images.
			file_path = os.path.join(img_save_dir, img)
			sk_io.imsave(file_path, image_aug)
			#ia.imshow(image_aug)

			count+=1
			print("{} annotations and images have been transformed!!".format(count))
			# if count==2:
			# 	break


img_path="C:\\Users\\gishy\\OneDrive - University of Bath\\Bath Thesis\\Bath Thesis\\VisDrone2019-DET-train\\Annotations-All Categories\\experiment"
txt_path="C:\\Users\\gishy\\OneDrive - University of Bath\\Bath Thesis\\Bath Thesis\\VisDrone2019-DET-train\\Annotations-All Categories\\experiment2"

if __name__=="__main__":		
	conversion(txt_path,img_path)



