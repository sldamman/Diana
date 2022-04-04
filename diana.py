import matplotlib.pyplot as plt, numpy as np, cartopy as cp, PIL
import cartopy.crs as ccrs, tkinter as tk, io, time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from projections import cp_projections
import xarray as xr


class DianaProgram:
    def __init__(self, size=(1200, 700), title='Diana v0.1'):
        self.width, self.height = size
        self.Window = tk.Tk()
        self.Window.title(title)
        self.Window.geometry(str(self.width) + 'x' + str(self.height))
        self.Window.columnconfigure(1, minsize=2/3*self.width)
        self.dpi = 1/plt.rcParams['figure.dpi']
        self.leftcolumn = tk.Frame(self.Window, width=20, height=self.window_height, bg='grey')
        self.rightcolumn = tk.Frame(self.Window, height = self.window_height)

        self.coast = 1
        self.stock_img = -1
        self.gridlines = 1
        self.tissot = -1
        self.all_projections = cp_projections()
        self.proj = 'Robinson'
        self.var_to_plot = None
        self.coordinates = [-180, 180, -90, 90]
        self.timestep = 0
        self.heightstep = 0
        self.plotlevels = 10
        self.cmap = 'coolwarm'

        self.set_map_extent()
        self._drawCoastlinesButton = tk.Button(
            self.leftcolumn, text='Coastlines', command=self.update_coast, padx=30, pady=5, bg='grey').pack(fill=tk.X)#.grid(column=0, row=2)
        self._drawStockImg = tk.Button(
            self.leftcolumn, text='Background', command=self.update_stock_img, padx=30, pady=5, bg='grey').pack(fill=tk.X)#.grid(column=0, row=3)
        self._drawGrid = tk.Button(
            self.leftcolumn, text='Grid', command=self.update_gridlines, padx=30, pady=5, bg='grey').pack(fill=tk.X)  # .grid(column=0, row=4)
        self._drawTissot = tk.Button(
            self.leftcolumn, text='Tissot', command=self.update_tissot, padx=30, pady=5, bg='grey').pack(fill=tk.X)  # .grid(column=0, row=5)
        self.dropdown_projections()
        
        tk.Label(self.leftcolumn, text=' ', bg='grey').pack(fill=tk.X)
        self._getForecastButton = tk.Button(self.leftcolumn, text='Load forecast', command=self.load_arome, padx=30, pady=5, bg='red')
        self._getForecastButton.pack(fill=tk.X)  # .grid(column=0, row=5)

        self.leftcolumn.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
    
    def load_arome(self):
        url = 'https://thredds.met.no/thredds/dodsC/mepslatest/meps_det_vc_2_5km_latest.nc'
        self.forecast = xr.open_dataset(url)
        self.variables = [name for name in self.forecast.variables.keys()]
        self.dropdown_arome()
        self.lat = self.forecast.variables['latitude'][0, :]
        self.lon = lon = self.forecast.variables['longitude'][0, :]
        self._getForecastButton["state"] = tk.DISABLED
        self.aromeExtentButton = tk.Button(self.leftcolumn, text='Use AROME extent', command=self.set_arome_extent, pady=5, padx=30).pack(fill=tk.X, side=tk.BOTTOM)
        
        plotLevelFrame = tk.Frame(self.leftcolumn)
        levelExplain = tk.Label(plotLevelFrame, text='Resolution: ', anchor='w')
        levelExplain.pack(side=tk.LEFT, fill=tk.X)
        self.inputPlotLevels = tk.Entry(plotLevelFrame, width=4)
        self.inputPlotLevels.bind('<Return>', self.update_plot_levels)
        self.inputPlotLevels.pack(side=tk.RIGHT, fill=tk.X)
        plotLevelFrame.pack(fill=tk.X)

        cmapFrame = tk.Frame(self.leftcolumn)
        cmapExplain = tk.Label(cmapFrame, text='Colormap: ', anchor='w')
        cmapExplain.pack(side=tk.LEFT, fill=tk.X)
        self.cmapInput = tk.Entry(cmapFrame, width=4)
        self.cmapInput.bind('<Return>', self.update_cmap)
        self.cmapInput.pack(side=tk.RIGHT, fill=tk.X)
        cmapFrame.pack(fill=tk.X)

    def update_plot_levels(self, _):
        self.plotlevels = int(self.inputPlotLevels.get())
        self.map()

    def update_cmap(self, _):
        self.cmap = self.cmapInput.get()
        self.map()

    def set_arome_extent(self):
        self.arome_min_lat, self.arome_max_lat = np.amin(self.lat), np.amax(self.lat)
        self.arome_min_lon, self.arome_max_lon = np.amin(self.lon), np.amax(self.lon)
        self.coordinates = [self.arome_min_lon, self.arome_max_lon, self.arome_min_lat, self.arome_max_lat]
        self.map()

    def plot_variable(self):
        self.var_to_plot = self.click_arome.get()
        self.map()


    def dropdown_arome(self):
        self.options = [var for var in self.variables if len(
            self.forecast.variables[var].shape) >= 3]
        self.click_arome = tk.StringVar()
        self.click_arome.set(self.options[0])
        drop_arome = tk.OptionMenu(self.leftcolumn, self.click_arome, *self.options)
        drop_arome.pack(fill=tk.X)
        drop_aromeButton = tk.Button(self.leftcolumn, text='Plot variable', command=self.plot_variable, padx=10, pady=5)
        drop_aromeButton.pack(fill=tk.X)


    def dropdown_projections(self):
        self.click = tk.StringVar()
        self.click.set(self.all_projections[0])
        self.drop = tk.OptionMenu(self.leftcolumn, self.click, *self.all_projections)
        self.drop.pack(fill=tk.X)
        self.dropButton = tk.Button(self.leftcolumn, text='Project', command=self.update_projection, padx=30, pady=5)
        self.dropButton.pack(fill=tk.X)
    
    def map(self):
        plt.clf()
        try:
            self.plotframe.destroy()
        except:
            pass

        projection = getattr(ccrs, self.proj)

        fig = plt.Figure(figsize=(3/3 * self.window_width * self.dpi, self.window_height * self.dpi))
        map = fig.add_subplot(111, projection=projection())
        fig.tight_layout(pad=0, h_pad=None, w_pad=None, rect=None)

        if self.coast > 0:
            map.coastlines()
        if self.stock_img > 0:
            map.background_img()
        if self.gridlines > 0:
            map.gridlines()
        if self.tissot > 0:
            map.tissot()

        map.set_extent(self.coordinates, crs=ccrs.PlateCarree())

        if self.var_to_plot is not None:
            if len(self.forecast.variables[self.var_to_plot][1]) > 3:
                self.contour = map.pcolormesh(
                self.lon, self.lat, self.forecast.variables[self.var_to_plot][self.timestep, self.heightstep, 0, :],
                levels=self.plotlevels, transform=ccrs.PlateCarree(), alpha=0.5, cmap=self.cmap)
                self.cbar = fig.colorbar(self.contour, ax=map, orientation='horizontal', location='top')
            else:
                self.contour = map.pcolormesh(
                self.lon, self.lat, self.forecast.variables[self.var_to_plot][self.timestep, 0, 0, :],
                levels=self.plotlevels, transform=ccrs.PlateCarree(), alpha=0.5, cmap=self.cmap)
                self.cbar = fig.colorbar(self.contour, ax=map, orientation='horizontal', location='top')

        self.plotframe = tk.Frame(self.Window)
        self.plotframe.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = FigureCanvasTkAgg(fig, master=self.plotframe)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, side=tk.TOP, expand=True)
        NavigationToolbar2Tk(self.canvas, self.plotframe).pack(side=tk.BOTTOM)


    def set_map_extent(self):
        self.coordFrame = tk.Frame(self.leftcolumn)
        self.expFrame = tk.Frame(self.coordFrame)
        self.inputFrame = tk.Frame(self.coordFrame, width=4)

        text1 = tk.Label(self.expFrame, text='Min latitude:', anchor='w')
        text1.pack(side=tk.BOTTOM, pady=4)

        text2 = tk.Label(self.expFrame, text='Max latitude:', anchor='w')
        text2.pack(side=tk.BOTTOM, pady=4)

        text3 = tk.Label(self.expFrame, text='Min longitude:', anchor='w')
        text3.pack(side=tk.BOTTOM, pady=4)

        text4 = tk.Label(self.expFrame, text='Max longitude:', anchor='w')
        text4.pack(side=tk.BOTTOM, pady=4)

        self.input_min_lat = tk.Entry(self.inputFrame, width=4)
        self.input_min_lat.bind('<Return>', self.update_minlat)
        self.input_min_lat.pack(side=tk.BOTTOM, fill=tk.X)

        self.input_max_lat = tk.Entry(self.inputFrame, width=4)
        self.input_max_lat.bind('<Return>', self.update_maxlat)
        self.input_max_lat.pack(side=tk.BOTTOM, fill=tk.X)

        self.input_min_lon = tk.Entry(self.inputFrame, width=4)
        self.input_min_lon.bind('<Return>', self.update_minlon)
        self.input_min_lon.pack(side=tk.BOTTOM, fill=tk.X)

        self.input_max_lon = tk.Entry(self.inputFrame, width=4)
        self.input_max_lon.bind('<Return>', self.update_maxlon)
        self.input_max_lon.pack(side=tk.BOTTOM, fill=tk.X)

        self.inputFrame.pack(side=tk.RIGHT)
        self.expFrame.pack(side=tk.LEFT)
        self.coordFrame.pack(side=tk.BOTTOM, fill=tk.X)

    def update_minlon(self, _):
        self.coordinates[0] = float(self.input_min_lon.get())
        self.map()

    def update_maxlon(self, _):
        self.coordinates[1] = float(self.input_max_lon.get())
        self.map()

    def update_minlat(self, _):
        self.coordinates[2] = float(self.input_min_lat.get())
        self.map()

    def update_maxlat(self, _):
        self.coordinates[3] = float(self.input_max_lat.get())
        self.map()

    @property
    def window_height(self):
        return self.Window.winfo_height()
    @property
    def window_width(self):
        return self.Window.winfo_width()

    def from_plot_to_PIL(self, fig):
        buf = io.BytesIO()
        fig.savefig(buf)
        buf.seek(0)
        img = PIL.Image.open(buf)
        return img

    def run(self):
        self.map()
        self.Window.mainloop()

    def update_coast(self):
        self.coast *= -1
        self.map()

    def update_stock_img(self):
        self.stock_img *= -1
        self.map()

    def update_gridlines(self):
        self.gridlines *= -1
        self.map()

    def update_tissot(self):
        self.tissot *= -1
        self.map()

    def update_projection(self):
        self.proj = self.click.get()
        self.map()


diana = DianaProgram().run()










