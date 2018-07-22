import numpy as np

# Common maps
# E.g. ortho_map defines an orthogonal neighborhood
ortho_map = ((1,0),  (0,-1), (-1,0), (0,1))
diag_map  = ((1,-1), (-1,-1),(-1,1), (1,1))

def _value_to_class(class_dict, value):
    # TODO: This should be more general, and not assume
    #   the underlying datatype is array-like-1D
    if tuple(value) in class_dict.keys():
        return class_dict[tuple(value)]
    else:
        return 0


def _class_to_map(nbhd_offsets, value, default=ortho_map):
    # e.g. _class_to_map(contiguities, 3)
    # where contiguities = { 3 : ortho_map + diag_map, ... }
    # returns contiguities[3]
    # This is used to identify the x and y offsets used in the contiguities and adjacencies
    if value in nbhd_offsets.keys():
        return nbhd_offsets[value]
    else:
        return default


def _get_adacent_pixels(x, y, w, h, nbhd_map = ortho_map, wrap = False):
    # Returns only valid pixels; order of pixels not guaranteed
    # E.g. adjacent_pixels(0,0,3,4) = [(1,0),(0,3),(0,2),(0,1)]
    # E.g. adjacent_pixles(0,0,0,0, wrap=False) = [(1,0),(0,1)]
    adj_pixels = []
    for offset_x, offset_y in nbhd_map:
        if wrap:
            adj_pixels.append(((x+offset_x) % w, (y+offset_y) % h))
        else:
            if 0 <= x + offset_x < w and 0 <= y + offset_y < h:
                adj_pixels.append((x+offset_x, y + offset_y))
    
    return adj_pixels


class RegionMapper:
    def __init__(self,
                 image,                 # 2D Numpy Array
                 class_dict,            # Dict of (value) --> Int >= 1
                 contiguities   = {},   # Dict of class int --> map (like ortho_map)
                 adjacencies    = {},   # Dict of class int --> map (like ortho map)
                 sparse         = True,
                 wrap           = False):
        
        width, height = image.shape[:2]
        
        assert(len(image.shape) == 3), "image should be np array shaped (width, height, number_of_channels_in_image)"
        
        ####
        # Create self._image:
        ####
        # rgb-image (w,h,3) to class-image (w,h)
        self._image = np.zeros((width, height))
        for ii in range(width):
         for jj in range(height):
            self._image[ii, jj] = _value_to_class(class_dict, image[ii,jj])
        
        ####
        # Cut up into regions:
        ####
        ## Some variables we will be using:
        # A list of all regions
        self._regions = []
        if sparse:
            self._region_at_pixel = dict()
        else:
            self._region_at_pixel = np.zeros((width, height))
        # _regions_with_class:
        # E.g. _regions_with_class[2] = [1,4,3] # Regions 1, 4, and 3 the ones with class 3
        self._regions_with_class = dict()
        
        ##The busy work:
        # Region number we are working with
        region = 0
        # A map of all pixels that have or have not been recorded
        rec = np.zeros((width, height), dtype=np.bool)
        for x in range(width):
         for y in range(height):
            if rec[x,y] == False:
                # An unexplored region! Time to check it out!
                region_class = self._image[x,y] # Let's get its class number, make sure it's not empty
                if not region_class == 0:
                    list_of_pixels_in_region = []   # ... and set up a list to fill with all these pixels!
                    
                    ##Fill up list_of_pixels_in_region using BFS
                    # contig_map: A list of what we consider "contigous" pixels. e.g. ((1,0),(-1,0)) only considers those left-right of us.
                    contig_map = _class_to_map(nbhd_offsets = contiguities, value = region_class)
                    # pixels_under_consideration: Every pixel we are looking at but have not computed yet.
                    pixels_under_consideration = [(x,y)]
                    rec[x,y] = True
                    #print("Hey!", x, y, region_class)
                    while len(pixels_under_consideration) > 0:
                        
                        #print(pixels_under_consideration)
                        #input()
                        xi, yi = pixels_under_consideration.pop() # Takes the first element from pixels_under_consideration
                        list_of_pixels_in_region.append((xi, yi)) # = [..., (x,y)]
                        self._region_at_pixel[xi, yi] = region
                        # For each adjacent pixel, if it's the same class, add it to the list of pixels we're going to explore
                        for xJ, yJ in _get_adacent_pixels(x=xi, y=yi, w=width, h=height, nbhd_map = contig_map):
                           if self._image[xJ, yJ] == region_class and rec[xJ, yJ] == False:
                               pixels_under_consideration.append((xJ, yJ))
                               rec[xJ, yJ] = True
                    
                    self._regions.append((region_class, list_of_pixels_in_region))
                    
                    if not (region_class) in self._regions_with_class.keys():
                        self._regions_with_class[region_class] = [region]
                    else:
                        self._regions_with_class[region_class].append(region)
                    
                    region += 1
        
    def region_at_pixel(self,x,y):
        if self._image[x,y] == 0:
            return -1
        else:
            return self._region_at_pixel[x,y]
    
    def regions(self, region_id):
        return self._regions[region_id]
    
    def regions_with_class(self,class_number):
        return self._regions_with_class[class_number]
    
    def adjacent_regions(self,region_id):
        pass

    
'''
RegionMapper init e.g.
    image        = np.swapaxes(np.array(PIL.Image.open("test.png")), 0, 1)
        # axes 0 and 1 represent x and y, respectively
    class_dict   = { (255,0,0) : 1, (0,255,0) : 2, (0,0,255) : 3 }
    contiguities = { 1 : ortho_map + diag_map, 3 : diag_map }
        # Here, it is implicit that class 2 (green) is ortho only
    adjacencies  = {}
        # Here, it is implicit that regions are only adjacent
        #   if they are orthogonally touching.
    sparse      = True
        # Underlying datatypes assume most elements do not belong to a class
    wrap        = True
        # Set true, so array is a torus, therefore grid edges touch.
'''