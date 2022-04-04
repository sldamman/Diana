import matplotlib.pyplot as plt, numpy as np, cartopy as cp, netCDF4, PIL
import cartopy.crs as ccrs, tkinter as tk, io, time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from projections import cp_projections
import xarray as xr

#url = 'https://thredds.met.no/thredds/dodsC/mepslatest/meps_det_vc_2_5km_latest.nc'
#data = xr.open_dataset(url)

a = (range(67), range(1), range(1), range(32000))

print(len(a[2]))