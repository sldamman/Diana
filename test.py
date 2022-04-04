import matplotlib.rcsetup as rcsetup
import cartopy.crs as ccrs
import cartopy as cp
import io, projections, numpy as np
import tkinter as tk
import PIL
import matplotlib.pyplot as plt
import xarray as xr

import numpy as np
import matplotlib.pyplot as plt
import cartopy as cp
import os
from netCDF4 import Dataset
from PIL import Image

plotpath = "/nird/projects/NS9600K/brittsc/WRF_output_Stian/plots/"


class WRF_Output:
    def __init__(self, output_file, plotpath):
        self.data = Dataset(output_file)
        self.plotpath = plotpath
        self.lat = self.data.variables['XLAT'][1, :, :]
        self.lon = lon = self.data.variables['XLONG'][1, :, :]
        self.R = 287
        self.date, self.start_hour = self.data.variables['XTIME'].units[
            14:24], self.data.variables['XTIME'].units[25:27]

    def pressure(self, time, loc):
        return self.data.variables['PB'][time, :, loc[0], loc[1]] + self.data.variables['P'][time, :, loc[0], loc[1]]

    def temperature(self, time, loc):
        theta = 300 + self.data.variables['T'][time, :, loc[0], loc[1]]
        return theta * (self.pressure(time, loc) / 1000) ** (2 / 7)

    def write_variables_to_file(self, file):
        with open('variables.txt', 'w') as f:
            for var, name in zip(self.data.variables.values(), self.data.variables.keys()):
                try:
                    des = str(var.description)
                except AttributeError:
                    des = ' '
                try:
                    dim = str(var.dimensions)
                except AttributeError:
                    dim = ' '
                try:
                    shp = str(var.shape)
                except AttributeError:
                    shp = ' '
                try:
                    unit = str(var.units)
                except AttributeError:
                    unit = ' '
                f.write(f'{name:22s}{unit:20s}{dim:60s}{shp:20s}{des:85s}')
                f.write('\n')
                f.write(u'\u2500' * 205)
                f.write('\n')

    def area_plot(self, var, start_time, height=0, only_andoya=True, levels=None, title='map.png', end_time=None, loc=None):
        '''
        Plot horizontal map using Lambert Conformal projection of WRF simulation over Andoya.
        Parameters:
        -----------
        WRF_output  - path to data file containing WRF model simulation data
        var         - 3 or 4 dimensional variable to plot
        time        - timestep at which to plot data
        height      - model altitude level to plot at, default is 0
        only_andoya - whether to plot full model area or only Andoya specifically, default True
        levels - specify min/max range and number of bins for colorbar (tuple), default is None
        '''

        if only_andoya:
            min_lat = 75.5
            max_lat = 81.2
            min_lon = 6.97
            max_lon = 32.33

        else:
            min_lat = np.amin(self.lat)
            max_lat = np.amax(self.lat)
            min_lon = np.amin(self.lon)
            max_lon = np.amax(self.lon)

        #Create map instance
        proj = cp.crs.LambertConformal(central_latitude=(
            min_lat + max_lat)/2, central_longitude=(max_lon + min_lon)/2)

        PC = cp.crs.PlateCarree()
        fig = plt.figure(figsize=(10, 10))
        map = fig.add_subplot(projection=proj)
        map.coastlines()
        map.set_extent([min_lon, max_lon, min_lat, max_lat], crs=PC)

        if len(self.data.variables[var].shape) == 3:
            if levels is not None:
                plot = map.contourf(
                    self.lon, self.lat, self.data.variables[var][start_time, :, :], 10, transform=PC, levels=levels)
            else:
                plot = map.contourf(
                    self.lon, self.lat, self.data.variables[var][start_time, :, :], 10, transform=PC)

        if len(self.data.variables[var].shape) == 4:
            if levels is not None:
                plot = map.contourf(
                    self.lon, self.lat, self.data.variables[var][start_time, height, :, :], 10, transform=PC, levels=levels)
            else:
                plot = map.contourf(
                    self.lon, self.lat, self.data.variables[var][start_time, height, :, :], 10, transform=PC)

        #Find and set date and time as title
        hour = int(self.start_hour) + start_time
        plt.title(self.date + ' ' + str(hour) + ':00:00 ' +
                  var + ' height=' + str(height))
        plt.colorbar(plot, orientation='horizontal')
        plt.savefig(plotpath + title)

    def number_conc_profile(self, var, start_time, end_time, loc=(78.9, 11.9), only_andoya=True, levels=None, title=None, height=None, per_liter=False):
        lat, lon = loc
        mid_time = int((start_time + end_time) / 2)
        PH = self.data.variables["PH"][mid_time, :, lat, lon]
        PHB = self.data.variables["PHB"][mid_time, :, lat, lon]
        H = (PH + PHB) / 9.81
        NC = np.mean(
            self.data.variables[var][start_time: end_time + 1, :, lat, lon], 0)
        unit = 'm$^{-3}$'

        if per_liter:
            density = self.pressure(start_time, loc) / \
                (self.R * self.temperature(start_time, loc))
            NC = NC * density / 1000
            unit = 'L$^{-1}$'

        # Create the figure and add axes
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
        ax.plot(NC, H[1:])

        start_hour = start_time + 12
        end_hour = end_time + 12

        ax.set_title(self.date + ' ' + str(start_hour) +
                     ':00-' + str(end_hour) + ':00 ' + var)
        ax.set_xlabel(f'number concentration [{unit}]')
        ax.set_ylabel('Altitude [m]')
        if title is None:
            plt.savefig(plotpath + var + '_' + self.date + '_' +
                        str(start_hour) + '-' + str(end_hour) + '.png')
        else:
            plt.savefig(plotpath + title)

    def time_animation(self, var, plotter, height=0, loc=(78.9, 11.9), step_interval=1, n_frames=37, binsize=2, anim_title='animation', duration=200, levels=None):
        frames = []
        for frame in range(n_frames):
            frame_name = f'{frame}.png'
            t = frame * step_interval
            plotter(var, height=height, start_time=t, end_time=t+binsize,
                    loc=loc, only_andoya=True, levels=levels, title=frame_name)
            frames.append(Image.open(self.plotpath + frame_name))
            plt.close()
            os.remove(plotpath + frame_name)

        frames[0].save(plotpath + anim_title + '.gif', format='GIF',
                       append_images=frames[1:], save_all=True, duration=duration, loop=1)

    def create_animation(self, var, time=0, height=0, only_andoya=True, levels=None, time_plot=True):
        #Create pngs by calling plot method
        frames = []
        if time_plot:
            for t in range(37):
                frame_name = f'{t}.png'
                self.area_plot(var, t, height, only_andoya,
                               levels, title=frame_name)
                frames.append(Image.open(plotpath + frame_name))
                plt.close()
                os.remove(plotpath + frame_name)
                title = f'{var}_time_animation.gif'
        else:
            #create height animation
            for h in range(57):
                frame_name = f'{h}.png'
                self.area_plot(var, time, 3*h, only_andoya,
                               levels, title=frame_name)
                frames.append(Image.open(plotpath + frame_name))
                plt.close()
                os.remove(plotpath + frame_name)
                title = f'{var}_height_animation.gif'

        frames[0].save(plotpath + title, format='GIF',
                       append_images=frames[1:], save_all=True, duration=200, loop=0)

    def cross_section(self, var, time=0):
        pass


milbrandt_output_file = '/nird/projects/NS9600K/brittsc/WRF_output_Stian/Milbrandt/wrfout_d01_2019-11-11_12:00:00'
morrison_output_file = '/nird/projects/NS9600K/brittsc/WRF_output_Stian/Morrison/wrfout_d02_2019-11-11_12:00:00'

Milbrandt = WRF_Output(milbrandt_output_file, plotpath)
Morrison = WRF_Output(morrison_output_file, plotpath)


#area_plot(wrf_output_file, 'SST', 30, height=100, only_andoya=False, levels=np.linspace(260, 280, 30))
#Milbrandt.number_conc_profile('QNICE', start_time=10, end_time=30, loc=(78.9,11.9))
#Milbrandt.time_animation('QNICE', Milbrandt.number_conc_profile, n_frames=35, binsize=2, anim_title='QNICE_anim')
#Milbrandt.time_animation('QNCLOUD', Milbrandt.number_conc_profile, n_frames=35, binsize=2, anim_title='QNICE_anim')
#Milbrandt.time_animation('QNICE', Milbrandt.area_plot, n_frames=37, anim_title='QNICE_anim_area', levels=np.linspace(0, 2000, 20))

#Milbrandt.number_conc_profile('QNICE', start_time=0, end_time=5, loc=(78.924,11.909), per_liter=True)

#create_animation(wrf_output_file, 'CLDFRA', time_plot=False, time=15, only_andoya=False, levels=np.linspace(0, 1, 10))

