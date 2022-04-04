import tkinter as tk


def cp_projections():
    return ['AlbersEqualArea', 'AzimuthalEquidistant', 'EckertI', 'EckertII', 'EckertIII', 'EckertIV', 'EckertV', 'EckertVI', 'EqualEarth', 'EquidistantConic', 'EuroPP', 'Geostationary', 'Globe', 'Gnomonic', 'InterruptedGoodeHomolosine', 'LambertAzimuthalEqualArea', 'LambertConformal', 'LambertCylindrical', 'Mercator', 'Miller', 'Mollweide', 'NearsidePerspective', 'NorthPolarStereo', 'OSGB', 'OSNI', 'Orthographic', 'PlateCarree', 'Robinson', 'RotatedGeodetic', 'RotatedPole', 'Sinusoidal', 'SouthPolarStereo', 'Stereographic', 'TransverseMercator']

def dropdown(Window, column, row, options):
    def show():
        myLabel = tk.Label(Window,  text=clicked.get()).pack()

    clicked = tk.StringVar()
    clicked.set(options[0])

    drop = tk.OptionMenu(Window, clicked, *options)
    drop.pack()

    button = tk.Button(Window, text="Projections", command=show).pack()

