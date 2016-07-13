#!/usr/bin/env python

import subprocess as p
import datetime
import os
import os.path
import glob

try:
    import pyferret
except ImportError:
    print "You must module load pyferret"
    exit(1)   

def mymain():

	#sets time variables, used in generation of NetCDFs, plots, and file names	

	print 'Please answer the following question to plot global air temperature for the current and last calendar year...'
	today = raw_input("Enter desired end date (mmyyyy): ")

	date = datetime.datetime.strptime('25' + today, '%d%m%Y')
	month = date.strftime('%m')
	month_abrev = date.strftime('%b')
	month_abrev_low = month_abrev.lower()
	year = date.strftime('%Y')
	year_abrev = date.strftime('%y')
	year_prev = str(int(year)-1)
	year_prev_abrev = year_prev[-2:]
	timeline = str(int(month)+11)


	atmos_outfile = "taircm21_ncepmonthly_" + year + ".nc"
	atmos_outfile_prev = "taircm21_ncepmonthly_" + year_prev + ".nc"
	atmos_outfile_combo = "taircm21_ncepmonthly_" + year_prev_abrev + year_abrev + ".nc"

	print 'Generating plots with available data from ', year_prev, '/', year, '...'

	#makes des file using XLY's make_des program to create file with locations of all relevant atmos netCDF's
	
	d ="." #the local directory

	finput = "/archive/x1y/FMS/c3/CM2.1_ECDA/CM2.1R_ECDA_v3.1_1960_pfl_auto/gfdl.ncrc3-intel-prod-openmp/history/tmp/*.atmos_month.ensm.nc"
	child = p.Popen(["dmget", finput],cwd=d)
	myout, myerr = child.communicate()
	cmd = ["/home/atw/util/make_des"]
	outputfile='ecda_v31_atmos_auto.des'
	flist = glob.glob(finput)
	[cmd.append(item) for item in flist]
	chd = p.Popen(cmd, stdout=p.PIPE, stderr=p.PIPE)
	# then when you "communicate", you will be returned three things, an return code (which we talked about before), and the contents of the pipes:
	myout, myerr = chd.communicate()
	print myerr
	#great, now the contents that you'd like to be written to a file is in the variable myout as a string
	#we will open, attempt the write and this syntax will close the file if all goes well.
	with open(outputfile,'w') as F:
	    F.write(myout)


	#lines 44-99 replace Xiaosong's csh script and make one NetCDF file in the local dir with two calendar years worth of daily SST data averaged monthly

	

	pyferret.start(quiet=True)
	os.remove("ferret.jnl")

	if os.path.isfile("tmp1.nc"):
		os.remove("tmp1.nc")

	if os.path.isfile(atmos_outfile_combo):
		os.remove(atmos_outfile_combo)

	if month == "01":

		#Janurary is a special case that can only consider atmos data from the previous year, and so the file naming convention for the desired data file is unique
		#Looks for files in Seth's directory, /net2/sdu/..., to avoid dmgetting the archive if possible

        	file_loc = '/archive/nmme/NMME/INPUTS/ncep2_am2/NCEP2_AM2.' + year + '.nc'
		file_loc_alt = '/net2/sdu/NMME/NCEP2_AM2/NetCDF/NCEP2_AM2.' + year + '.nc'

		if os.path.isfile(file_loc_alt):
			cmd1 = 'use ' + file_loc_alt
		else:	
			print 'dmgetting archived data files (this may take a while)'
			child = p.Popen(["dmget", file_loc],cwd=d)
        		child.communicate()
			cmd1 = 'use ' + file_loc
			
	
	else:

		#All other months obey this file naming convention for their data files
		#Looks for files in Seth's directory, /net2/sdu/..., to avoid dmgetting the archive if possible

        	file_loc = '/archive/nmme/NMME/INPUTS/ncep2_am2/NCEP2_AM2.' + year + '.nc'
		file_loc_alt = '/net2/sdu/NMME/NCEP2_AM2/NetCDF/NCEP2_AM2.' + year + '.nc'

		if os.path.isfile(file_loc_alt):
			cmd1 = 'use ' + file_loc_alt
		else:
			print 'dmgetting archived data files (this may take a while)'	        	
			child = p.Popen(["dmget", file_loc],cwd=d)
	        	child.communicate()
			cmd1 = 'use ' + file_loc

	#The following sets the necessary parameters in pyferret	

	cmd2 = 'set memory/size=600'
	cmd3 = 'DEFINE AXIS/CALENDAR=JULIAN/T=15-jan-' + year + ':15-' + month_abrev_low + '-' + year + ':1/npoint=' + month + '/UNIT=month tmonth'
	cmd4 = 'let temp_month = temp[gt=tmonth@AVE]'
	cmd5 = 'save/clobber/file=tmp1.nc temp_month'

	(errval, errmsg) = pyferret.run(cmd1)
	(errval, errmsg) = pyferret.run(cmd2)
	(errval, errmsg) = pyferret.run(cmd3)
	(errval, errmsg) = pyferret.run(cmd4)
	(errval, errmsg) = pyferret.run(cmd5)

	#Using the command shell, data files are concatenated in the local directory. The new NetCDF file containing averaged SST data from both calendar years will be here

	child = p.Popen(["ncrename","-v", "TEMP_MONTH,temp", "tmp1.nc"],cwd=d)
	child.communicate()
	child = p.Popen(["ncrename","-v", "TMONTH,t", "tmp1.nc"],cwd=d)
	child.communicate() 
	child = p.Popen(["ncrename","-d", "TMONTH,t", "tmp1.nc"],cwd=d)
	child.communicate() 
	child = p.Popen(["ncrcat","-O","-v","temp", "tmp1.nc", atmos_outfile],cwd=d)
	child.communicate()
   	child = p.Popen(["ncrcat", "/home/x1y/gfdl/ecda_operational/sst/" + atmos_outfile_prev, atmos_outfile, atmos_outfile_combo],cwd=d)
	child.communicate()

	returnCode = child.returncode

	os.remove("tmp1.nc")

	#the following automates the pyferret plot generation and saves a png image file in the local dir

	filename = 'tair_amo_' + month + '_' + year + '.png'

	header()
	
	cmd7 = "use " + atmos_outfile_combo
	cmd8 = "let temp2 = temp[d=2,gxy=temp[d=1],gt=temp[d=1]@asn]"
	cmd9 = "let err1 = temp[d=1,k=24] - temp2[k=24]" ###possibily timline here

	cmd11 = 'sha/lev=(0.,5.0,0.5) var1[l=1:' + timeline + '@ave]^0.5'
	cmd12 = 'go land'
	cmd13 = 'FRAME/FILE=' + filename

	(errval, errmsg) = pyferret.run(cmd7)
	(errval, errmsg) = pyferret.run(cmd8)
	(errval, errmsg) = pyferret.run(cmd9)

	body()

	(errval, errmsg) = pyferret.run(cmd11)
	(errval, errmsg) = pyferret.run(cmd12)
	(errval, errmsg) = pyferret.run(cmd13)

	print 'Plot image file for SST RMSE ', year_prev, '/', year, ' since ', month_abrev,' is located in the local directory (if data was available) and is named: ', filename
	print 'If no plots generated, please see script comments to find necessary input files.'


def header():
	
	#the following clears data from previously running pyferrets, establishes base parameters, and loads ensemble data

	com1 = 'cancel data/all'
	com2 = 'def sym print_opt $1"0"'
	com3 = 'set mem/size=240'
	com4 = 'use ecda_v31_atmos_auto.des'

	(errval, errmsg) = pyferret.run(com1)
	(errval, errmsg) = pyferret.run(com2)
	(errval, errmsg) = pyferret.run(com3)
	(errval, errmsg) = pyferret.run(com4)

def body():
	
	#the following calculates, lists, and plots RMSE. This method depends on functions computed in the main method

	com5 = 'let var1 = err1^2; let rms10 = var1[x=@ave,y=60s:60n@ave]^0.5' 
	com6 = 'set win 1'
	com7 = 'set viewport upper' 
	com8 = 'plot/vl=0.0:1.5:0.1/line=1 rms10' 
	com9 = 'let var1 = err1^2;'
	com10 = 'let rms1 = var1[k=24,x=@ave,y=60s:60n@ave]^0.5'
	com11 = 'list rms10' 
	com12 = 'plot/ov/line=1/DASH rms1'
	com13 = 'set viewport lower'
	com14 = 'set region/y=80s:80n'
	com15 = 'set viewport lower'
	com16 = 'set region/y=30s:30n'

	(errval, errmsg) = pyferret.run(com5)
	(errval, errmsg) = pyferret.run(com6)
	(errval, errmsg) = pyferret.run(com7)
	(errval, errmsg) = pyferret.run(com8)
	(errval, errmsg) = pyferret.run(com9)
	(errval, errmsg) = pyferret.run(com10)
	(errval, errmsg) = pyferret.run(com11)
	(errval, errmsg) = pyferret.run(com12)
	(errval, errmsg) = pyferret.run(com13)
	(errval, errmsg) = pyferret.run(com14)
	(errval, errmsg) = pyferret.run(com15)
	(errval, errmsg) = pyferret.run(com16)

if __name__=="__main__":
    mymain()



