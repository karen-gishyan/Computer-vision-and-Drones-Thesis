import pandas as pd
from plot import plot


path="C:\\Users\\gishy\\OneDrive - University of Bath\\Bath Thesis\\Bath Thesis\\results\\csvs\\yolov3_result_352s.csv"
df=pd.read_csv(path)



map_05_indices=[10,25,40,55,70,85]
f1_indices=[11,26,41,56,71,86]
total_loss=[5,20,35,50,65,80]


names=["No Augmentation","Blending Sequence","Blurring Sequence","Geometric Sequence","(3x4) Grid Sequence","(3x5) Grid Sequence with Transfer Learning"]


if __name__=="__main__":


	# for i in map_05_indices:
	# 	print(max(df.iloc[:,i]))


	for index,name in enumerate(df.columns):
		print(index,name)

	plot(df,map_05_indices,names,title="mAP 0.5: Yolo version 3",rolling_mean_windows_size=3,xlabel="Epochs",ylabel="Percentage",percentage=True)		
	plot(df,f1_indices,names,title="F1 score: Yolo version 3",rolling_mean_windows_size=3,xlabel="Epochs",ylabel="Percentage",percentage=True)
	plot(df,total_loss,names,title="Total Training Loss: Yolo version 3",rolling_mean_windows_size=3,xlabel="Epochs",ylabel="Value")
	
