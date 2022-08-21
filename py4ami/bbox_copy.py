"""bounding box"""

import math
from pyamiimage.ami_util import AmiUtil


class BBox:
    """bounding box 2array of 2arrays, based on integers
    """

    X = "x"
    Y = "y"
    WIDTH = "width"
    HEIGHT = "height"

    # indexes for convenience
    MIN = 0
    MAX = 1

    def __init__(self, xy_ranges=None, swap_minmax=False):
        """
        Must have a valid bbox
        Still haven'tb worked out logic of default boxes (must include None's)
        as [0.0],[0.0] is valid
        :param xy_ranges: [[x1, x2], [y1, y2]] will be set to integers
        """
        self.xy_ranges = [[], []]
        self.swap_minmax = swap_minmax
        if xy_ranges is not None:
            self.set_ranges(xy_ranges)

    def copy(self):
        """creqtes new BBox as copy of self
        :return: copy of bbox xy_ranges
        """
        bbox = BBox(self.xy_ranges)
        bbox.swap_minmax = self.swap_minmax

        return bbox

    @classmethod
    def create_from_numpy_array(cls, nparray):
        coords = nparray.tolist()
        bbox = BBox(xy_ranges=[[coords[0], coords[2]], [coords[1], coords[3]]])
        return bbox

    @classmethod
    def create_from_xy_w_h(cls, xy, width, height):
        """
        create from xy, width height
        all inputs must be floats
        :param xy: origin a [float, float]
        :param width:
        :param height:
        :return:
        """
        assert type(xy[0]) is float or type(xy[0]) is int, f"found {type(xy[0])}"
        assert type(xy[1]) is float or type(xy[1]) is int, f"found {type(xy[1])}"
        assert type(width) is float or type(width) is int, f"found {type(width)}"
        assert type(height) is float or type(height) is int, f"found {type(height)}"

        try:
            xy_ranges = [[float(xy[0]), float(xy[0]) + float(width)], [float(xy[1]), float(xy[1]) + float(height)]]
        except Exception as e:
            raise ValueError(f"cannot create bbox from {xy},{width},{height}, {e}")
        return BBox(xy_ranges=xy_ranges)

    @classmethod
    def create_from_points(cls, points_list, tolerance=0.001):
        """make bounding box if 4 points can be aligned in a rectangle within tolerance
        choose low/low and high/high ; don't use othe values except as True/False
        :param points_list: reqyires len=4
        :param tolerance: must be aligned within tolerance; default 0.001
        :return: BBox [lowx,  lowy] [highx, highy] => [[lowx, highx], [lowy, highy]] or None
        """
        if not points_list:
            return None
        if not points_list or len(points_list) != 4:
            return None
        high_high = cls._find_low_low_high_high(points_list, 1, tolerance)
        low_low = cls._find_low_low_high_high(points_list, -1, tolerance)
        bbox = None
        if low_low and high_high:
            bbox = BBox(xy_ranges=[
                [low_low[0], high_high[0]],
                [low_low[1], high_high[1]]
            ])
        return bbox

    def set_ranges(self, xy_ranges):
        if xy_ranges is None:
            raise ValueError("no lists given")
        if len(xy_ranges) != 2:
            raise ValueError("must be 2 lists of lists")
        if xy_ranges[0] is not None and len(xy_ranges[0]) == 0:
            xy_ranges[0] = None
        if xy_ranges[0] is not None and len(xy_ranges[0]) != 2:
            raise ValueError(f"range {xy_ranges[0]} must be None or 2-tuple")
        if xy_ranges[1] is not None and len(xy_ranges[1]) == 0:
            xy_ranges[1] = None
        if xy_ranges[1] is not None and len(xy_ranges[1]) != 2:
            raise ValueError(f"range {xy_ranges[1]} must be None or 2-tuple")
        self.set_xrange(xy_ranges[0])
        self.set_yrange(xy_ranges[1])

    def get_ranges(self):
        """gets ranges as [xrange, yrange]"""
        return self.xy_ranges

    def set_xrange(self, rrange):
        self.set_range(0, rrange)

    def get_xrange(self):
        return self.xy_ranges[0]

    def get_width(self):
        """get width
        :return: width or None if x range invalid or not set"""
        if self.get_xrange() is None or len(self.get_xrange()) == 0:
            return None
        assert self.get_xrange() is not None
        assert len(self.get_xrange()) == 2, f"xrange, got {len(self.get_xrange())}"
        return self.get_xrange()[1] - self.get_xrange()[0]

    def set_yrange(self, rrange):
        self.set_range(1, rrange)

    def get_yrange(self):
        return self.xy_ranges[1]

    def get_height(self):
        if self.get_yrange() is None or len(self.get_yrange()) == 0:
            return None
        return self.get_yrange()[1] - self.get_yrange()[0] if len(self.get_yrange()) == 2 else None

    def set_range(self, index, rrange):
        if index != 0 and index != 1:
            raise ValueError(f"bad tuple index {index}")
        if rrange is None:
            self.xy_ranges[index] = None
            return
        val0 = int(rrange[0])
        val1 = int(rrange[1])
        # This may cause problem for vertical text
        # if val1 < val0:
        #     if self.swap_minmax:
        #         val1, val0 = val0, val1
        #     else:
        #         raise ValueError(f"ranges must be increasing {val0} !<= {val1}")
        self.xy_ranges[index] = [val0, val1]
        self.xy_ranges[index] = [val0, val1]

    def __str__(self):
        return str(self.xy_ranges)

    def __repr__(self):
        return str(self.xy_ranges)

    def intersect(self, bbox):
        """
        inclusive intersection of boxes (AND)
        if any fields are empty returns None
        DOES NOT CHANGE self
        :param bbox:
        :return: new Bbox (max(min) ... (min(max)) or None if any  errors
        """
        bbox1 = None
        if bbox is not None:
            xrange = self.intersect_range(self.get_xrange(), bbox.get_xrange())
            yrange = self.intersect_range(self.get_yrange(), bbox.get_yrange())
            bbox1 = BBox([xrange, yrange]) if xrange and yrange else None
            # print(f"self {self} bbox {bbox} => {bbox1}")
        return bbox1

    def union(self, bbox):
        """
        inclusive merging of boxes (OR)
        if any fields are empty returns None
        DOES NOT CHANGE self

        :param bbox:
        :return: new Bbox (min(min) ... (max(max)) or None if any  errors
        """
        bbox1 = None
        if bbox is not None:
            xrange = self.union_range(self.get_xrange(), bbox.get_xrange())
            yrange = self.union_range(self.get_yrange(), bbox.get_yrange())
            bbox1 = BBox((xrange, yrange))
        return bbox1

    @classmethod
    def intersect_range(cls, range0, range1):
        """intersects 2 range tuples"""
        if len(range0) != 2 or len(range1) != 2:
            return None
        min_coord = max(range0[cls.MIN], range1[cls.MIN])
        max_coord = min(range0[cls.MAX], range1[cls.MAX])
        if max_coord < min_coord:
            return None
        return [min_coord, max_coord]

    @classmethod
    def union_range(cls, range0, range1):
        """intersects 2 range tuples"""
        rrange = []
        if len(range0) == 2 and len(range1) == 2:
            rrange = [min(range0[0], range1[0]), max(range0[1], range1[1])]
        return rrange

    def add_coordinate(self, xy_tuple):
        assert xy_tuple is not None, f"xy_tuple must have coordinates"
        self.add_to_range(0, self.get_xrange(), xy_tuple[0])
        self.add_to_range(1, self.get_yrange(), xy_tuple[1])

    def add_to_range(self, index, rrange, coord):
        """if coord outside range , expand range

        :param index: 0 or  =1 for axis
        :param rrange: x or y range
        :param coord: x or y coord
        :return: None (changes range)
        """
        if index != 0 and index != 1:
            raise ValueError(f"bad index {index}")
        if len(rrange) != 2:
            rrange = [None, None]
        if rrange[0] is None or coord < rrange[0]:
            rrange[0] = coord
        if rrange[1] is None or coord > rrange[1]:
            rrange[1] = coord
        self.xy_ranges[index] = rrange
        return rrange

    @classmethod
    def create_box(cls, xy, width, height):
        if xy is None or width is None or height is None:
            raise ValueError("All params must be not None")
        width = int(width)
        height = int(height)
        if len(xy) != 2:
            raise ValueError("xy must be an array of 2 values")
        if width < 0 or height < 0:
            raise ValueError("width and height must be non negative")
        xrange = ([xy(0), xy[0] + width])
        yrange = [xy(1), xy[1] + int(height)]
        bbox = BBox.create_from_ranges(xrange, yrange)
        return bbox

    def expand_by_margin(self, margin):
        """
        if margin is scalar, apply to both axes
        if margin is 2-tuple, apply to x and y separately
        if margin is negative applies only if current range is >- 2*margin + 1
        i
        :param margin: scalar dx or tuple (dx, dy)
        :return: None
        """

        if not isinstance(margin, list):
            margin = [margin, margin]
        self.change_range(0, margin[0])
        self.change_range(1, margin[1])

    def change_range(self, index, margin):
        """
        change range by margin

        :param index: 0 for X 1 for Y
        :param margin:
        :return:
        """
        if index != 0 and index != 1:
            raise ValueError(f"Bad index for range {index}")
        rr = self.xy_ranges[index]
        rr[0] -= margin
        rr[1] += margin
        # range cannot be <= 0
        if rr[0] >= rr[1]:
            mid = (rr[0] + rr[1]) / 2
            rr[0] = int(mid - 0.5)
            rr[1] = int(mid + 0.5)
        self.xy_ranges[index] = rr

    @classmethod
    def create_from_ranges(cls, xr, yr):
        """
        create from 2 2-arrays
        :param xr: 2-list of range
        :param yr: 2-list of range
        :return:
        """
        bbox = BBox()
        bbox.set_xrange(xr)
        bbox.set_yrange(yr)
        return bbox

    def is_valid(self):
        """
        both ranges must be present and non-negative
        :return:
        """
        if self.xy_ranges is None or len(self.xy_ranges) != 2:
            return False
        if self.xy_ranges[0] is None or self.xy_ranges[1] is None:
            return False
        try:
            ok = self.get_width() >= 0 and self.get_height() >= 0
            return ok
        except Exception:
            return False

    def set_invalid(self):
        """set xy_ranges to None"""
        self.xy_ranges = None

    @classmethod
    def get_width_height(cls, bbox):
        """
        TODO MOVED

        :param bbox: tuple of tuples ((x0,x1), (y0,y1))
        :return: (width, height) tuple
        """
        """
        needs to have its own class
        """
        width = bbox[0][1] - bbox[0][0]
        height = bbox[1][1] - bbox[1][0]
        return width, height

    @classmethod
    def fits_within(cls, bbox, bbox_gauge):
        """
        does bbox fit within self (relative coordinates)

        Will this parcel fir the letter box?


        TODO MOVED

        :param bbox: tuple of tuples ((x0,x1), (y0,y1))
        :param bbox_gauge: tuple of (width, height) that bbox must fit in
        :return: true if fits in rectangle
        """
        """
        needs to have its own class
        """
        width, height = bbox.get_width_height()
        return width < bbox_gauge[0] and height < bbox_gauge[1]

    def min_dimension(self):
        """
        gets minimum of height and width
        :return: min(height, width)
        """
        return min(self.get_width(), self.get_height())

    def max_dimension(self):
        """
        gets maximum of height and width
        :return: max(height, width)
        """
        return max(self.get_width(), self.get_height())

    def get_point_pair(self):
        """
        BBox stores the location as ranges of x and y values:
        [[x1, x2], [y1, y2]]
        sometimes it is necessary to work with points instead:
        [(y1, x1), (y2, x2)]
        :returns: list of 2 tuples
        """
        return [(self.get_yrange()[0], self.get_xrange()[0]),
                (self.get_yrange()[1], self.get_xrange()[1])]
        # remember that the indexing is in terms of rows and columns
        # hence x(columns) y(rows) values are flipped when returning point pair

    # @classmethod
    # def plot_bbox_on(cls, image, bbox):
    #     """
    #     Plots bbox on an image
    #     :param: image
    #     :type: numpy array
    #     :param: bbox
    #     :type: BBox or list
    #     :returns: fig, ax
    #     """
    #     from skimage import draw
    #     pixel_value = 200  # 0 is black
    #     # bbox can either be BBox object or in form of [[a, b][c, d]]
    #
    #     # if type(bbox) == BBox:
    #     #     assert bbox.is_valid()
    #     # elif type(bbox) == list:
    #     #     bbox = BBox(bbox)
    #     #     assert bbox.is_valid()
    #     # else:
    #     #     # the bbox passed is not invalid
    #     #     return None
    #
    #     point_pair = bbox.get_point_pair()
    #     if point_pair[0][0] > image.shape[0] or point_pair[0][1] > image.shape[1]:
    #         # if the starting point is outside the image, ignore bbox
    #         return image
    #
    #     try:
    #         row, col = draw.rectangle_perimeter(start=point_pair[0], end=point_pair[1])
    #         image[row, col] = pixel_value
    #     except IndexError:
    #         point_pair = BBox.fit_point_pair_within_image(image, point_pair)
    #         row, col = draw.rectangle_perimeter(start=point_pair[0], end=point_pair[1])
    #         image[row, col] = pixel_value
    #
    #     return image

    @classmethod
    def fit_point_pair_within_image(cls, image, point_pair):
        max_row = image.shape[0]
        max_col = image.shape[1]
        bbox_row = point_pair[1][0]
        bbox_col = point_pair[1][1]
        if bbox_row >= max_row - 1:
            bbox_row = max_row - 2
        if bbox_col >= max_col - 1:
            bbox_col = max_col - 2
        point_pair[1] = (bbox_row, bbox_col)
        return point_pair

    @classmethod
    def create_from_corners(cls, xy1, xy2):
        if xy1 is None or xy2 is None:
            return None
        if len(xy1) != 2 or len(xy2) != 2:
            return None
        xrange = [xy1[0], xy2[0]] if xy2[0] > xy1[0] else [xy2[0], xy1[0]]
        yrange = [xy1[1], xy2[1]] if xy2[1] > xy1[1] else [xy2[1], xy1[1]]
        bbox = BBox(xy_ranges=[xrange, yrange])
        return bbox

    @property
    def centroid(self):
        return [
            (self.get_xrange()[0] + self.get_xrange()[1]) / 2,
            (self.get_yrange()[0] + self.get_yrange()[1]) / 2
        ]

    def contains_point(self, point):
        """does point lie within xy_ranges inclusive
        :param point: 2D numeric array [x, y] or 2-tuple
        :return: False if point is None or self is invalid or point lies outside
        """
        if not BBox.validate_point(point) or not self.is_valid():
            return False
        if point[0] < self.xy_ranges[0][0] or point[0] > self.xy_ranges[0][1]:
            return False
        if point[1] < self.xy_ranges[1][0] or point[1] > self.xy_ranges[1][1]:
            return False
        return True

    def contains_geom_object(self, geom_object):
        """does object fit within self (inclusive coords)

        :param geom_object: 2-float array or BBox
        :return: None returns False
        """

        if not geom_object:
            return False
        if AmiUtil.is_point(geom_object):
            return (self.get_xrange()[0] <= geom_object[0] <= self.get_xrange()[1] and
                    self.get_yrange()[0] <= geom_object[1] <= self.get_yrange()[1])
        if type(geom_object) is BBox:
            if (geom_object.get_xrange()[0] >= self.get_xrange()[0] and
                    geom_object.get_xrange()[1] <= self.get_xrange()[1] and
                    geom_object.get_yrange()[0] >= self.get_yrange()[0] and
                    geom_object.get_yrange()[1] <= self.get_yrange()[1]):
                return True
            return False
        return False

    @classmethod
    def validate_point(cls, point):
        if point is None or len(point) != 2:
            return False
        return AmiUtil.is_number(point[0]) and AmiUtil.is_number(point[1])

    @classmethod
    def _find_low_low_high_high(cls, points_list, sign, tolerance=0.001):
        """
        :param points_list: list of 4 points [x,y]
        :param sign: 1 for high_high or -1 for low_low
        :param tolerance: default 0.001
        :return: point with lowestx, lowesty (sign=-1) or highest, higest (sign=1)
        """
        point = None
        if points_list and len(points_list) == 4:
            for p in points_list:
                if point is None:
                    point = p
                else:
                    if cls._is_movable(p[0], point[0], tolerance, sign) and cls._is_movable(p[1], point[1], tolerance,
                                                                                            sign):
                        point = p
        return point

    @classmethod
    def _is_movable(cls, coord_new, coord_old, tolerance, sign):
        if abs(coord_new - coord_old) < tolerance:
            return True
        if math.copysign(1, coord_new - coord_old) == sign:
            return True

    @classmethod
    def assert_xy_ranges(cls, bbox, target_ranges):
        """asserts that bbox has given xy_ranges (main equality test)
        :param bbox: Bbox
        :param target_ranges: 2-D array of floats [[x0,x1], y0,y1]]
        :except: throws variaous exceptions
        """
        if not bbox:
            if not target_ranges:
                # expected None
                return
            else:
                raise ValueError("parameter/s are None")
        if not bbox.is_valid():
            raise ValueError("Bad bbox {bbox}")
        assert bbox.xy_ranges == target_ranges, f"bbox_xy_ranges {bbox.xy_ranges}, target_ranges {target_ranges}"

    def extract_edges_in_box(self, ami_edges):
        # TODO extend to OR and AND and maybe XOR
        """extract any edges which have at least one node in bbox
        :param ami_edges:
        :return: list of extracted edges
        """

        new_ami_edges = []
        for ami_edge in ami_edges:
            bbox = ami_edge.get_or_create_bbox()
            if bbox.get_width() < 2 or bbox.get_height() < 2:
                continue
            start_node = ami_edge.get_start_ami_node()
            end_node = ami_edge.get_end_ami_node()
            start_xy = start_node.centroid_xy
            end_xy = end_node.centroid_xy
            if (self.contains_geom_object(start_xy) or
                    self.contains_geom_object(end_xy)):
                new_ami_edges.append(ami_edge)
        return new_ami_edges

    @property
    def width(self):
        return self.xy_ranges[0][1] - self.xy_ranges[0][0]

    @property
    def height(self):
        return self.xy_ranges[1][1] - self.xy_ranges[1][0]


"""If you looking for the overlap between two real-valued bounded intervals, then this is quite nice:

def overlap(start1, end1, start2, end2):
    how much does the range (start1, end1) overlap with (start2, end2)
    return max(max((end2-start1), 0) - max((end2-end1), 0) - max((start2-start1), 0), 0)
I couldn't find this online anywhere so I came up with this and I'm posting here."""
