import os
import sys
import time
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from lxml import etree
from visualize import visualize_bounding_box

	

def horizontal_grid_augment(annot_path,imgs_path,combine_img_number,desired_augment_number=None,min_width=False,custom_reshape=None,im_save_path=None,xml_save_path=None):

	"""
	combine_img_number=number of images to combine horizontally.
	min_width=if True, all the images are resized to the mininum existing image width.Default-their original widths are adjusted with height.
	desired_augment_number-how many gridlike images to generate,cannot exceed the number of original images.
	decrease_width_size=how many times to decrease the width before saving.
	min_width  and custom reshape are mutually exclusive. If one is True, the other is None, and if custom reshape is None, the other should be False.
	
	custom reshape reshapes the individual images all to the same width, height and not the full image.
	"""

	new_xml_dir_path= im_save_path if im_save_path!=None else os.path.join(os.path.dirname(annot_path),"grid_horizontal_xmls") 
	new_img_dir_path= xml_save_path if xml_save_path!=None else os.path.join(os.path.dirname(annot_path),"grid_horizontal_images")


	if not os.path.exists(new_img_dir_path):
		os.makedirs(new_img_dir_path)

	if not os.path.exists(new_xml_dir_path):
		os.makedirs(new_xml_dir_path)

	image_names=[im for im in os.listdir(imgs_path)]
	
	new_images_list=[]
	new_annots_list=[]
	iter_num=sum_images//combine_img_number if desired_augment_number==None else desired_augment_number


	for index, _ in enumerate(range(iter_num)):
		
		img_list=[]
		annot_names=[]
		# print("Loop",index+1)

		for _ in range(combine_img_number): 

			
			ind=np.random.randint(0,len(image_names))
			img=image_names[ind]

			img_full_path=os.path.join(imgs_path,img)
			img_list.append(Image.open(img_full_path))

			annot=os.path.splitext(img)[0]+".xml"
			annot_names.append(annot)

							
		if min_width: #resize based on the minimum width, height of the image in the batch(3-5).
			
			min_height = min(im.height for im in img_list)
			min_width=min(im.width for im in img_list)

			im_list_resize = [im.resize((min_width, min_height),resample=Image.BICUBIC)
				for im in img_list]				  
		
		
		elif custom_reshape!=None: # resize individual images based on custom size. e.g.(500,500).

			min_height=custom_reshape[1]
		
			im_list_resize = [im.resize((custom_reshape),resample=Image.BICUBIC) for im in img_list]

		else: #resize based on mininum height, and adjsuting the widths accordingly.

			min_height = min(im.height for im in img_list)
			im_list_resize = [im.resize((int(im.width * min_height /im.height),min_height),resample=Image.BICUBIC)
						  for im in img_list]


		size_diff=[(i.size[0]/j.size[0],i.size[1]/j.size[1]) for i,j in zip(img_list,im_list_resize)] #both width and height are resized by the same amount.
		total_width = sum(im.width for im in im_list_resize)
				
		new_image=Image.new('RGB', (total_width, min_height))
		
		np_image = np.array(new_image) # to do np_image.shape[2] later.

		new_image_name="grid_augment"+str(index+1)+".jpg"
		
		new_img_path=os.path.join(new_img_dir_path,new_image_name)

		
		write_xml=XML_Writer(new_image_name,new_img_path,new_image.width,new_image.height,np_image.shape[2])
		r=write_xml.create_tag()

		x_position=0

		for i, (img,annot) in enumerate(zip(im_list_resize,annot_names)): # the first one need to be the

			new_image.paste(img,(x_position,0))
			x_position+=img.width
			
		 
			full_path=os.path.join(annot_path,annot)
			tree=ET.parse(full_path)
			root=tree.getroot()


			for object in root.iter("object"): 
					
				voc_list=[]

				name=str(object.find("name").text)		
				box= object.find("bndbox")

				xmin=int(box.find("xmin").text)
				ymin=int(box.find("ymin").text)
				xmax=int(box.find("xmax").text)
				ymax=int(box.find("ymax").text)
				
				#resize bounding boxes of resize images before shifting.
				
				xmin=int(xmin/size_diff[i][0])
				xmax=int(xmax/size_diff[i][0])
				ymin=int(ymin/size_diff[i][1])
				ymax=int(ymax/size_diff[i][1])
				#sys.exit()

				shift=x_position-img.width
				
				write_xml.add_object(r,xmin+shift,ymin,xmax+shift,ymax,name)
	
		
		if (index+1)%20==0:
			print("{} images horizontally transformed.".format(index+1))

		new_images_list.append(new_image)
		new_annots_list.append(r)

				
		new_image.save(new_img_path)
		write_xml.save_xml(r,new_xml_dir_path,new_image_name)

	print("{} images and {} annotations have been horizontally transformed.".format(len(new_images_list),len(new_annots_list)))
	return new_img_dir_path,new_xml_dir_path



def vertical_grid_augment(annot_path,imgs_path,combine_img_number,desired_augment_number=None,custom_reshape=None,min_height=False,im_save_path=None,xml_save_path=None):

	"""
	As vertical transformation is mostly applied to horiztonally combined images, which have bigger lengths and a standard height.
	it is much recommended to apply custom reshape(especially with smaller size) and images already have standard height.
	Main transformations is recommended with horizontal grid_augment, unless vertical is assigned to not-combined images.
	
	Height and custom_reshape are mutually exclusive. Provide either one or the other.
	
	For vertical augmentation, if applied to horiztonal images, min_height makes sense only when horizontally there has not been custom_reshape or min_width. 
	Custom_reshape is not much recommended if the images have been horizontally transformed.
	"""

	new_xml_dir_path= xml_save_path if im_save_path!=None else os.path.join(os.path.dirname(annot_path),"grid_vertical_xmls") 
	new_img_dir_path= im_save_path  if xml_save_path!=None else os.path.join(os.path.dirname(annot_path),"grid_vertical_images")


	if not os.path.exists(new_img_dir_path):
		os.makedirs(new_img_dir_path)

	if not os.path.exists(new_xml_dir_path):
		os.makedirs(new_xml_dir_path)
	
	new_images_list=[]
	new_annots_list=[]
	image_names=[im for im in os.listdir(imgs_path)]

	
	iter_num=sum_images//combine_img_number if desired_augment_number==None else desired_augment_number

	
	for index, _ in enumerate(range(iter_num)):
		
		img_list=[]
		annot_names=[]

		for _ in range(combine_img_number):

			ind=np.random.randint(0,len(image_names))
			img=image_names[ind]

			img_full_path=os.path.join(imgs_path,img)
			img_list.append(Image.open(img_full_path))

			annot=os.path.splitext(img)[0]+".xml"
			annot_names.append(annot)
			
		#resize the weights based on the mininum height.

		if min_height: #makes it square like.
			
			min_width = min(im.width for im in img_list)
			min_height=min(im.height for im in img_list)
			im_list_resize = [im.resize((min_width, min_height),resample=Image.BICUBIC)
						  for im in img_list]
		

		elif custom_reshape!=None: # with custom sizes.

			min_width=custom_reshape[0]
			im_list_resize = [im.resize((custom_reshape),resample=Image.BICUBIC) for im in img_list]

		else: #takes effect when height differ.

			
			min_width = min(im.width for im in img_list)
			im_list_resize = [im.resize((min_width, int(im.height * min_width / im.width)),resample=Image.BICUBIC)
					  for im in img_list]



		size_diff=[(i.size[0]/j.size[0],i.size[1]/j.size[1]) for i,j in zip(img_list,im_list_resize)]


		total_height = sum(im.height for im in im_list_resize)
		
		new_image=Image.new('RGB', (min_width, total_height))
		
		np_image = np.array(new_image) # for depth

		new_image_name="grid_augment"+str(index+1)+".jpg"
		
		new_img_path=os.path.join(new_img_dir_path,new_image_name)

		
		write_xml=XML_Writer(new_image_name,new_img_path,new_image.width,new_image.height,np_image.shape[2])
		r=write_xml.create_tag()

		y_position=0

		for i, (img,annot) in enumerate(zip(im_list_resize,annot_names)): 

			new_image.paste(img,(0,y_position))
			y_position+=img.height
			
		 
			full_path=os.path.join(annot_path,annot)
			tree=ET.parse(full_path)
			root=tree.getroot()


			for object in root.iter("object"): 
					
				voc_list=[]

				name=str(object.find("name").text)		
				box= object.find("bndbox")


				xmin=int(box.find("xmin").text)
				ymin=int(box.find("ymin").text)
				xmax=int(box.find("xmax").text)
				ymax=int(box.find("ymax").text)
				
				#resize based on new width and height.
				
				xmin=int(xmin/size_diff[i][0])
				xmax=int(xmax/size_diff[i][0])
				ymin=int(ymin/size_diff[i][1])
				ymax=int(ymax/size_diff[i][1])
									
				shift=y_position-img.height
				write_xml.add_object(r,xmin,ymin+shift,xmax,ymax+shift,name)
		
		
		if (index+1)%20==0:
			print("{} images vertically transformed.".format(index+1))
			
		new_images_list.append(new_image)
		new_annots_list.append(r)		

		new_image.save(new_img_path)
	
		write_xml.save_xml(r,new_xml_dir_path,new_image_name)

	print("{} images and {} annotations have been  vertically combined.".format(len(new_images_list),len(new_annots_list)))

	return new_img_dir_path,new_xml_dir_path


def mosaic_augment(annot_path,imgs_path,size=(3,4),
	desired_total_horizontal_images=10,total_images=15,mininum_horizontal_width=False,custom_horizontal_reshape=None):
	
	# the more the desired_total_horizontal_images, the more the variation in total images.
	#Perfecr squares can be generated by passing (n,n) tuple to custom_horizontal_reshape. (352,353) or (1080,1080W)

	new_xml_dir_path=os.path.join(os.path.dirname(annot_path),"grid_mosaic_xmls")
	new_img_dir_path=os.path.join(os.path.dirname(imgs_path),"grid_mosaic_images")

	if not os.path.exists(new_img_dir_path):
		os.makedirs(new_img_dir_path)

	if not os.path.exists(new_xml_dir_path):
		os.makedirs(new_xml_dir_path)


	horiz_im_dir_path,horiz_xml_dir_path=horizontal_grid_augment(annot_path,imgs_path,combine_img_number=size[0],
		desired_augment_number=desired_total_horizontal_images,min_width=mininum_horizontal_width,custom_reshape=custom_horizontal_reshape)

	vertical_grid_augment(horiz_xml_dir_path,horiz_im_dir_path,combine_img_number=size[1],
		xml_save_path=new_xml_dir_path,im_save_path=new_img_dir_path,desired_augment_number=total_images)


class XML_Writer:


	def __init__(self,file_name,img_path,img_width,img_height,img_depth):
		
		self.file_name=file_name
		self.img_path=img_path
		self.img_width=img_width
		self.img_height=img_height
		self.img_depth=img_depth

	def create_tag(self):

		self.root = etree.Element('annotation')

		self.folder=etree.SubElement(self.root,'folder').text='annotations'
		self.filename=etree.SubElement(self.root,"filename").text="{}".format(self.file_name)
		self.path=etree.SubElement(self.root,"path").text="{}".format(self.img_path)
		self.source=etree.SubElement(self.root,"source")		
		self.database=etree.SubElement(self.source,"database").text='Visdrone Dataset'
		self.size=etree.SubElement(self.root,"size")
		self.width=etree.SubElement(self.size,"width").text="{}".format(self.img_width)
		self.height=etree.SubElement(self.size,"height").text="{}".format(self.img_height)
		self.depth=etree.SubElement(self.size,"depth").text="{}".format(self.img_depth)
		self.segmented=etree.SubElement(self.root,"segmented").text="0"

		return self.root


	def add_object(self,root,xmin,ymin,xmax,ymax,name):
		
		

		self.obj = etree.Element('object')
		self.name=etree.SubElement(self.obj,'name').text="{}".format(name)
		self.pose=etree.SubElement(self.obj,'pose').text="Unspecified"
		self.truncated=etree.SubElement(self.obj,'truncated').text="0"
		self.diff=etree.SubElement(self.obj,'difficult').text="0"
		self.bnd=etree.SubElement(self.obj,'bndbox')
		self.xmin=etree.SubElement(self.bnd,"xmin").text="{}".format(xmin)
		self.ymin=etree.SubElement(self.bnd,"ymin").text="{}".format(ymin)
		self.xmax=etree.SubElement(self.bnd,"xmax").text="{}".format(xmax)
		self.ymax=etree.SubElement(self.bnd,"ymax").text="{}".format(ymax)

		
		root.append(self.obj)
		

	def save_xml(self,root,new_xml_dir_path,img_name):

		s = etree.tostring(root, pretty_print=True)

		name=os.path.splitext(img_name)[0]+".xml"
		save_path=os.path.join(new_xml_dir_path,name)

		with open(save_path,"wb") as file:
			file.write(s)


if __name__ == '__main__':

	
	#path to original images and annotations.

	annot_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\own images\\combined\\train_labels_xml"
	images_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\own images\\combined\\train_images"
	
	start=time.time()
	
	#horizontal_grid_augment(annot_path,images_path,3,desired_augment_number=3)#,custom_reshape=(352,352# #35 seconds running time with 700 imags.
	#vertical_grid_augment(annot_path,images_path,4,desired_augment_number=10)#, running time-45 seconds.
	mosaic_augment(annot_path,images_path,size=(3,4),desired_total_horizontal_images=110,total_images=110)#custom_horizontal_reshape=(352,352)	
	print("Running Time is: %.3f seconds." % (time.time()-start))
		
	#path to new xmls and images.
	annot_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\own images\\combined\\grid_mosaic_xmls"
	images_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\own images\\combined\\grid_mosaic_images"

	#applies to transformed annotations.
	hname="h_images_with_bounding_boxes"
	vname="v_images_with_bounding_boxes"
	mname="m_images_with_bounding_boxes"
	visualize_bounding_box(annot_path,images_path,name=mname)


