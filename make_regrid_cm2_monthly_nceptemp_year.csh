#!/bin/csh

#foreach year (2007 2008 2009 2010 2011 2012)
#foreach year (2006 2005 2004 2003 2002 2001 2000 1999 1998 1997 1996 1995 1994 1993 1992 1991 1990)
#foreach year ( 1989 1988 1987 1986 1985 1984 1983 1982 )
foreach year ( 2016 )

set sst_outfile = taircm21_ncepmonthly_${year}.nc 
set year2 = ${year}

\rm -f ${sst_outfile} tmp1.nc tmp2.nc

ferret <<!
!sp dmget /archive/x1y/archive/CM2.1R_ECDA_v4.1_48m1440p_ps2dpuv_ispd/history/ensm/19990101.ocean_month.ensm.nc
!use "/archive/x1y/archive/CM2.1R_ECDA_v4.1_48m1440p_ps2dpuv_ispd/history/ensm/19990101.ocean_month.ensm.nc"
!sp dmget /archive/snz/fms/oda_data/sst/weekly/sstcm2_daily_19490101_20101003.nc
!use "/archive/snz/fms/oda_data/sst/weekly/sstcm2_daily_19490101_20101003.nc"
use "/archive/nmme/NMME/INPUTS/ncep2_am2/NCEP2_AM2.${year}.nc"
set memory/size=600
!#let sst1 = sst[d=2,gx=geolon_t[d=1],gy=geolat_t[d=1],t=3-may-2010:3-oct-2010]
!let sst = sst1[d=2,gx=temp[d=1]@ASN,gy=temp[d=1]@ASN]
!let sst = sst1[d=2,gx=temp[d=1],gy=temp[d=1]]
!let sst2 = IF abs(temp[d=1,z=0,l=1]) LT  100 THEN sst1[d=2,gxy=temp[d=1,l=1,z=0]]
!let sst2 = IF abs(sst[d=1,l=1]) LT  100 THEN temp[d=2,gxy=sst[d=1,l=1]]
!define a monthly asix 
DEFINE AXIS/CALENDAR=JULIAN/T=15-jan-${year}:15-jun-${year}:1/npoint=6/UNIT=month  tmonth
let temp_month = temp[gt=tmonth@AVE]
!let sst_mask = IF abs(temp[d=1,z=0]) LT  100 THEN 1
!let sst2 = sst1[d=2,gx=temp[d=1,z=0],gy=temp[d=1,z=0]]*sst_mask[gt=sst1[d=2]]
save/clobber/file=tmp1.nc temp_month
exit
!
rm -f ferret*.jnl*

ncrename -v TEMP_MONTH,temp tmp1.nc
ncrename -v TMONTH,t tmp1.nc

ncrename -d TMONTH,t tmp1.nc

ncrcat -O -v temp tmp1.nc ${sst_outfile}

# clean up
\rm -f tmp[12].nc

end
