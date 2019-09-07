#! /usr/bin/env python
"""
Generates Inkscape SVG file containing box components needed to
laser cut a tabbed construction box taking kerf and clearance into account

Copyright (C) 2011 elliot white

Changelog:
19/12/2014 Paul Hutchison:
 - Ability to generate 6, 5, 4, 3 or 2-panel cutouts
 - Ability to also generate evenly spaced dividers within the box
   including tabbed joints to box sides and slots to slot into each other

23/06/2015 by Paul Hutchison:
 - Updated for Inkscape's 0.91 breaking change (unittouu)

v0.93 - 15/8/2016 by Paul Hutchison:
 - Added Hairline option and fixed open box height bug

v0.94 - 05/01/2017 by Paul Hutchison:
 - Added option for keying dividers into walls/floor/none

This program is ugly software: you can clean it up yourself and/or mock it
under the unpublished terms of common civility.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
__version__ = "0.94"  # please report bugs, suggestions etc at
# https://github.com/paulh-rnd/TabbedBoxMaker ###

import math
import os

import inkex
import simplestyle

try:
    # This is the typing library for local dev.   Can be ignored in production.  :)
    from typing import Tuple
except ImportError:
    pass

inkex.localize()

DEFAULT_LINE_THICKNESS = 1  # default unless overridden by settings


def log(text):
    if 'SCHROFF_LOG' in os.environ:
        f = open(os.environ.get('SCHROFF_LOG'), 'a')
        f.write(text + "\n")


def draw_lines(xy_string):  # Draw lines from a list
    name = 'part'
    style = {'stroke'      : '#000000',
             'stroke-width': str(DEFAULT_LINE_THICKNESS),
             'fill'        : 'none'}
    drw = {'style'                         : simplestyle.formatStyle(style),
           inkex.addNS('label', 'inkscape'): name, 'd': xy_string}
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), drw)
    return


# jslee - shamelessly adapted from sample code on below Inkscape wiki page 2015-07-28
# http://wiki.inkscape.org/wiki/index.php/Generating_objects_from_extensions
def draw_circle(r, cx, cy):
    log("putting circle at ({},{})".format(cx, cy))

    style = {'stroke'      : '#000000',
             'stroke-width': str(DEFAULT_LINE_THICKNESS),
             'fill'        : 'none'}

    ell_attribs = {'style'                         : simplestyle.formatStyle(style),
                   inkex.addNS('cx', 'sodipodi')   : str(cx),
                   inkex.addNS('cy', 'sodipodi')   : str(cy),
                   inkex.addNS('rx', 'sodipodi')   : str(r),
                   inkex.addNS('ry', 'sodipodi')   : str(r),
                   inkex.addNS('start', 'sodipodi'): str(0),
                   inkex.addNS('end', 'sodipodi')  : str(2 * math.pi),
                   inkex.addNS('open', 'sodipodi') : 'true',
                   # all ellipse sectors we will draw are open
                   inkex.addNS('type', 'sodipodi') : 'arc',
                   'transform'                     : ''}
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), ell_attribs)


def side(root_coord, start_offset_coord, end_offset_coord, tab_vec, length, direction,
         is_tab, is_divider, num_dividers, div_spacing, div_offset):
    # type: (Tuple[int, int], Tuple[int, int], Tuple[int, int], int, int, Tuple[int, int], bool, bool, int, int, int) -> str

    rx, ry = root_coord

    sox, soy = start_offset_coord

    eox, eoy = end_offset_coord

    dir_x, dir_y = direction

    divs = int(length / nom_tab)  # divisions
    if not divs % 2:
        divs -= 1  # make divs odd
    divs = float(divs)
    tabs = (divs - 1) / 2  # tabs for side

    if equal_tabs:
        gap_width = tab_width = length / divs
    else:
        tab_width = nom_tab
        gap_width = (length - tabs * nom_tab) / (divs - tabs)

    if is_tab:  # kerf correction
        gap_width -= correction
        tab_width += correction
        first = correction / 2
    else:
        gap_width += correction
        tab_width -= correction
        first = -correction / 2

    first_vec = 0
    second_vec = tab_vec
    dirxN = 0 if dir_x else 1  # used to select operation on x or y
    diryN = 0 if dir_y else 1
    (Vx, Vy) = (rx + sox * thickness, ry + soy * thickness)
    s = 'M {},{} '.format(Vx, Vy)

    if dirxN:
        Vy = ry  # set correct line start
    if diryN:
        Vx = rx

    # generate line as tab or hole using:
    #   last co-ord:Vx,Vy ; tab dir:tab_vec  ; direction:dir_x,dir_y ; thickness:thickness
    #   divisions:divs ; gap width:gap_width ; tab width:tab_width

    for n in range(1, int(divs)):
        if ((n % 2) ^ (
                not is_tab)) and num_dividers > 0 and not is_divider:  # draw holes for
            # divider
            # joints in side walls
            w = gap_width if is_tab else tab_width
            if n == 1:
                w -= sox * thickness
            for m in range(1, int(num_dividers) + 1):
                Dx = Vx + -dir_y * div_spacing * m
                Dy = Vy + dir_x * div_spacing * m
                if n == 1:
                    Dx += sox * thickness
                h = 'M {},{} '.format(Dx, Dy)

                Dx = Dx + dir_x * w + dirxN * first_vec + first * dir_x
                Dy = Dy + dir_y * w + diryN * first_vec + first * dir_y
                h += 'L {},{} '.format(Dx, Dy)

                Dx += dirxN * second_vec
                Dy += diryN * second_vec
                h += 'L {},{} '.format(Dx, Dy)

                Dx = Dx - (dir_x * w + dirxN * first_vec + first * dir_x)
                Dy = Dy - (dir_y * w + diryN * first_vec + first * dir_y)
                h += 'L {},{} '.format(Dx, Dy)

                Dx -= dirxN * second_vec
                Dy -= diryN * second_vec
                h += 'L {},{} '.format(Dx, Dy)

                draw_lines(h)
        if n % 2:
            if n == 1 and num_dividers > 0 and is_divider:  # draw slots for dividers
                # to slot into each other
                for m in range(1, int(num_dividers) + 1):
                    Dx = Vx + -dir_y * (div_spacing * m + div_offset)
                    Dy = Vy + dir_x * (div_spacing * m - div_offset)
                    h = 'M {},{} '.format(Dx, Dy)

                    Dx = Dx + dir_x * (first + length / 2)
                    Dy = Dy + dir_y * (first + length / 2)
                    h += 'L {},{} '.format(Dx, Dy)

                    Dx = Dx + dirxN * thickness
                    Dy = Dy + diryN * thickness
                    h += 'L {},{} '.format(Dx, Dy)

                    Dx = Dx - dir_x * (first + length / 2)
                    Dy = Dy - dir_y * (first + length / 2)
                    h += 'L {},{} '.format(Dx, Dy)

                    Dx = Dx - dirxN * thickness
                    Dy = Dy - diryN * thickness
                    h += 'L {},{} '.format(Dx, Dy)

                    draw_lines(h)

            Vx = Vx + dir_x * gap_width + dirxN * first_vec + first * dir_x
            Vy = Vy + dir_y * gap_width + diryN * first_vec + first * dir_y
            s += 'L {},{} '.format(Vx, Vy)

            Vx = Vx + dirxN * second_vec
            Vy = Vy + diryN * second_vec
            s += 'L {},{} '.format(Vx, Vy)
        else:
            Vx = Vx + dir_x * tab_width + dirxN * first_vec
            Vy = Vy + dir_y * tab_width + diryN * first_vec
            s += 'L {},{} '.format(Vx, Vy)

            Vx = Vx + dirxN * second_vec
            Vy = Vy + diryN * second_vec
            s += 'L {},{} '.format(Vx, Vy)
        (second_vec, first_vec) = (-second_vec, -first_vec)  # swap tab direction
        first = 0

    # finish the line off
    s += 'L {},{} '.format(rx + eox * thickness + dir_x * length,
                           ry + eoy * thickness + dir_y * length)
    if is_tab and num_dividers > 0 and not is_divider:  # draw last for divider joints
        # in side walls
        for m in range(1, int(num_dividers) + 1):
            Dx = Vx
            Dy = Vy + dir_x * div_spacing * m
            h = 'M {},{} '.format(Dx, Dy)

            Dx = rx + eox * thickness + dir_x * length
            Dy = Dy + dir_y * tab_width + diryN * first_vec + first * dir_y
            h += 'L {},{} '.format(Dx, Dy)

            Dx = Dx + dirxN * second_vec
            Dy = Dy + diryN * second_vec
            h += 'L {},{} '.format(Dx, Dy)

            Dx = Vx
            Dy = Dy - (dir_y * tab_width + diryN * first_vec + first * dir_y)
            h += 'L {},{} '.format(Dx, Dy)

            Dx = Dx - dirxN * second_vec
            Dy = Dy - diryN * second_vec
            h += 'L {},{} '.format(Dx, Dy)

            draw_lines(h)
    return s


class BoxMaker(inkex.Effect):
    def __init__(self):
        # Call the base class constructor.
        # We are not using super because as of Inkscape 0.92 inkex.Effect is still an
        #   Old-Style python class that doesn't inherit from `object`
        inkex.Effect.__init__(self)
        # Define options
        self.OptionParser.add_option('--schroff', action='store', type='int',
                                     dest='schroff', default=0,
                                     help='Enable Schroff mode')
        self.OptionParser.add_option('--rail_height', action='store', type='float',
                                     dest='rail_height', default=10.0,
                                     help='Height of rail')
        self.OptionParser.add_option('--rail_mount_depth', action='store', type='float',
                                     dest='rail_mount_depth', default=17.4,
                                     help='Depth at which to place hole for rail mount '
                                          'bolt')
        self.OptionParser.add_option('--rail_mount_centre_offset', action='store',
                                     type='float',
                                     dest='rail_mount_centre_offset', default=0.0,
                                     help='How far toward row centreline to offset rail '
                                          'mount bolt (from rail centreline)')
        self.OptionParser.add_option('--rows', action='store', type='int',
                                     dest='rows', default=0,
                                     help='Number of Schroff rows')
        self.OptionParser.add_option('--hp', action='store', type='int',
                                     dest='hp', default=0,
                                     help='Width (TE/HP units) of Schroff rows')
        self.OptionParser.add_option('--row_spacing', action='store', type='float',
                                     dest='row_spacing', default=10.0,
                                     help='Height of rail')
        self.OptionParser.add_option('--unit', action='store', type='string',
                                     dest='unit', default='mm', help='Measure Units')
        self.OptionParser.add_option('--inside', action='store', type='int',
                                     dest='inside', default=0, help='Int/Ext Dimension')
        self.OptionParser.add_option('--length', action='store', type='float',
                                     dest='length', default=100, help='Length of Box')
        self.OptionParser.add_option('--width', action='store', type='float',
                                     dest='width', default=100, help='Width of Box')
        self.OptionParser.add_option('--depth', action='store', type='float',
                                     dest='height', default=100, help='Height of Box')
        self.OptionParser.add_option('--tab', action='store', type='float',
                                     dest='tab', default=25, help='Nominal Tab Width')
        self.OptionParser.add_option('--equal', action='store', type='int',
                                     dest='equal', default=0, help='Equal/Prop Tabs')
        self.OptionParser.add_option('--hairline', action='store', type='int',
                                     dest='hairline', default=0, help='Line Thickness')
        self.OptionParser.add_option('--thickness', action='store', type='float',
                                     dest='thickness', default=10,
                                     help='Thickness of Material')
        self.OptionParser.add_option('--kerf', action='store', type='float',
                                     dest='kerf', default=0.5, help='Kerf (width) of cut')
        self.OptionParser.add_option('--clearance', action='store', type='float',
                                     dest='clearance', default=0.01,
                                     help='Clearance of joints')
        self.OptionParser.add_option('--style', action='store', type='int',
                                     dest='style', default=25, help='Layout/Style')
        self.OptionParser.add_option('--spacing', action='store', type='float',
                                     dest='spacing', default=25, help='Part Spacing')
        self.OptionParser.add_option('--boxtype', action='store', type='int',
                                     dest='boxtype', default=25, help='Box type')
        self.OptionParser.add_option('--div_l', action='store', type='int',
                                     dest='div_l', default=25,
                                     help='Dividers (Length axis)')
        self.OptionParser.add_option('--div_w', action='store', type='int',
                                     dest='div_w', default=25,
                                     help='Dividers (Width axis)')
        self.OptionParser.add_option('--keydiv', action='store', type='int',
                                     dest='keydiv', default=3,
                                     help='Key dividers into walls/floor')

    def effect(self):
        global parent, nom_tab, equal_tabs, thickness, correction, div_x, div_y, \
            hairline, DEFAULT_LINE_THICKNESS, key_div_walls, key_div_floor

        # Get access to main SVG document element and get its dimensions.
        svg = self.document.getroot()

        # Get the attributes:
        width_doc = self.unittouu(svg.get('width'))
        height_doc = self.unittouu(svg.get('height'))

        # Create a new layer.
        layer = inkex.etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'newlayer')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        parent = self.current_layer

        # Get script's option values.
        hairline = self.options.hairline
        unit = self.options.unit
        inside = self.options.inside
        schroff = self.options.schroff

        # Set the line thickness
        if hairline:
            DEFAULT_LINE_THICKNESS = self.unittouu('0.002in')
        else:
            DEFAULT_LINE_THICKNESS = 1

        if schroff:
            hp = self.options.hp
            rows = self.options.rows
            rail_height = self.unittouu(str(self.options.rail_height) + unit)
            row_centre_spacing = self.unittouu(str(122.5) + unit)
            row_spacing = self.unittouu(str(self.options.row_spacing) + unit)
            rail_mount_depth = self.unittouu(str(self.options.rail_mount_depth) + unit)
            rail_mount_centre_offset = self.unittouu(
                str(self.options.rail_mount_centre_offset) + unit)
            rail_mount_radius = self.unittouu(str(2.5) + unit)

        # minimally different behaviour for schroffmaker.inx vs. boxmaker.inx
        # essentially schroffmaker.inx is just an alternate interface with different
        # default settings, some options removed, and a tiny amount of extra logic
        if schroff:
            # schroffmaker.inx
            x = self.unittouu(str(self.options.hp * 5.08) + unit)
            # 122.5mm vertical distance between mounting hole centres of 3U Schroff panels
            row_height = rows * (row_centre_spacing + rail_height)
            # rail spacing in between rows but never between rows and case panels
            row_spacing_total = (rows - 1) * row_spacing
            y = row_height + row_spacing_total
        else:
            # boxmaker.inx
            x = self.unittouu(str(self.options.length) + unit)
            y = self.unittouu(str(self.options.width) + unit)

        z = self.unittouu(str(self.options.height) + unit)
        thickness = self.unittouu(str(self.options.thickness) + unit)
        nom_tab = self.unittouu(str(self.options.tab) + unit)
        equal_tabs = self.options.equal
        kerf = self.unittouu(str(self.options.kerf) + unit)
        clearance = self.unittouu(str(self.options.clearance) + unit)
        layout = self.options.style
        spacing = self.unittouu(str(self.options.spacing) + unit)
        box_type = self.options.boxtype
        div_x = self.options.div_l
        div_y = self.options.div_w
        key_div_walls = 0 if self.options.keydiv == 3 or self.options.keydiv == 1 else 1
        key_div_floor = 0 if self.options.keydiv == 3 or self.options.keydiv == 2 else 1
        div_offset = key_div_walls * thickness

        if inside:  # if inside dimension selected correct values to outside dimension
            x += thickness * 2
            y += thickness * 2
            z += thickness * 2

        correction = kerf - clearance

        # check input values mainly to avoid python errors
        # TODO restrict values to *correct* solutions
        # TODO restrict divisions to logical values
        error = 0

        if min(x, y, z) == 0:
            inkex.errormsg('Error: Dimensions must be non zero')
            error = 1
        if max(x, y, z) > max(width_doc, height_doc) * 10:  # crude test
            inkex.errormsg('Error: Dimensions Too Large')
            error = 1
        if min(x, y, z) < 3 * nom_tab:
            inkex.errormsg('Error: Tab size too large')
            error = 1
        if nom_tab < thickness:
            inkex.errormsg('Error: Tab size too small')
            error = 1
        if thickness == 0:
            inkex.errormsg('Error: Thickness is zero')
            error = 1
        if thickness > min(x, y, z) / 3:  # crude test
            inkex.errormsg('Error: Material too thick')
            error = 1
        if correction > min(x, y, z) / 3:  # crude test
            inkex.errormsg('Error: Kerf/Clearance too large')
            error = 1
        if spacing > max(x, y, z) * 10:  # crude test
            inkex.errormsg('Error: Spacing too large')
            error = 1
        if spacing < kerf:
            inkex.errormsg('Error: Spacing too small')
            error = 1

        if error:
            exit()

        # layout format:
        #   (root_x), (root_y), X_length, Y_length, tabInfo, tabbed, pieceType
        #
        # root = (spacing,x,y,z) * values in multiples of dimension of top left corner
        # eg. (3, 1, 0, 1) means x position = 3*spacing + 1*x dimension + 1*z dimension
        #
        # tabInfo= <abcd> 0=holes 1=tabs
        # tabbed= <abcd> 0=no tabs 1=tabs on this side
        # (sides: a=top, b=right, c=bottom, d=left)
        #
        # pieceType: 1=XY, 2=XZ, 3=ZY
        # note first two pieces in each set are the x-divider template and y-divider
        # template respectively
        if box_type == 2:  # One side open (x,y)
            if layout == 1:  # Diagrammatic Layout
                pieces = [[(2, 0, 0, 1), (3, 0, 1, 1), x, z, 0b1010, 0b1101, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1111, 0b1110, 3],
                          [(2, 0, 0, 1), (2, 0, 0, 1), x, y, 0b0000, 0b1111, 1],
                          [(3, 1, 0, 1), (2, 0, 0, 1), z, y, 0b1111, 0b1011, 3],
                          [(4, 1, 0, 2), (2, 0, 0, 1), x, y, 0b0000, 0b0000, 1],
                          [(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1010, 0b0111, 2]]
            elif layout == 2:  # 3 Piece Layout
                pieces = [[(2, 0, 0, 1), (2, 0, 1, 0), x, z, 0b1010, 0b1101, 2],
                          [(1, 0, 0, 0), (1, 0, 0, 0), z, y, 0b1111, 0b1110, 3],
                          [(2, 0, 0, 1), (1, 0, 0, 0), x, y, 0b0000, 0b1111, 1]]
            elif layout == 3:  # Inline(compact) Layout
                pieces = [[(5, 2, 0, 2), (1, 0, 0, 0), x, z, 0b1111, 0b1101, 2],
                          [(3, 2, 0, 0), (1, 0, 0, 0), z, y, 0b0101, 0b1110, 3],
                          [(4, 2, 0, 1), (1, 0, 0, 0), z, y, 0b0101, 0b1011, 3],
                          [(2, 1, 0, 0), (1, 0, 0, 0), x, y, 0b0000, 0b1111, 1],
                          [(6, 3, 0, 2), (1, 0, 0, 0), x, z, 0b1111, 0b0111, 2]]
            elif layout == 4:  # Diagrammatic Layout with Alternate Tab Arrangement
                pieces = [[(2, 0, 0, 1), (3, 0, 1, 1), x, z, 0b1001, 0b1101, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1100, 0b1110, 3],
                          [(2, 0, 0, 1), (2, 0, 0, 1), x, y, 0b1100, 0b1111, 1],
                          [(3, 1, 0, 1), (2, 0, 0, 1), z, y, 0b0110, 0b1011, 3],
                          [(4, 1, 0, 2), (2, 0, 0, 1), x, y, 0b0110, 0b0000, 1],
                          [(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1100, 0b0111, 2]]
        elif box_type == 3:  # Two sides open (x,y and x,z)
            if layout == 1:  # Diagrammatic Layout
                pieces = [[(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1010, 0b0111, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1111, 0b1100, 3],
                          [(2, 0, 0, 1), (2, 0, 0, 1), x, y, 0b0010, 0b1101, 1],
                          [(3, 1, 0, 1), (2, 0, 0, 1), z, y, 0b1111, 0b1001, 3]]
            elif layout == 2:  # 3 Piece Layout
                pieces = [[(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1010, 0b0111, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1111, 0b1100, 3],
                          [(2, 0, 0, 1), (2, 0, 0, 1), x, y, 0b0010, 0b1101, 1]]
            elif layout == 3:  # Inline(compact) Layout
                pieces = [[(2, 2, 0, 2), (1, 0, 0, 0), x, z, 0b1010, 0b0111, 2],
                          [(3, 2, 0, 0), (1, 0, 0, 0), z, y, 0b1111, 0b1100, 3],
                          [(2, 1, 0, 0), (1, 0, 0, 0), x, y, 0b0010, 0b1101, 1],
                          [(4, 2, 0, 1), (1, 0, 0, 0), z, y, 0b1111, 0b1001, 3]]
            elif layout == 4:  # Diagrammatic Layout with Alternate Tab Arrangement
                pieces = [[(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1100, 0b0111, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1111, 0b1100, 3],
                          [(2, 0, 0, 1), (2, 0, 0, 1), x, y, 0b1110, 0b1101, 1],
                          [(3, 1, 0, 1), (2, 0, 0, 1), z, y, 0b0110, 0b1001, 3]]
        elif box_type == 4:  # Three sides open (x,y, x,z and z,y)
            if layout == 2:  # 3 Piece Layout
                pieces = [[(2, 2, 0, 0), (2, 0, 1, 0), x, z, 0b1111, 0b1001, 2],
                          [(1, 0, 0, 0), (1, 0, 0, 0), z, y, 0b1111, 0b0110, 3],
                          [(2, 2, 0, 0), (1, 0, 0, 0), x, y, 0b1100, 0b0011, 1]]
            else:
                pieces = [[(3, 3, 0, 0), (1, 0, 0, 0), x, z, 0b1110, 0b1001, 2],
                          [(1, 0, 0, 0), (1, 0, 0, 0), z, y, 0b1111, 0b0110, 3],
                          [(2, 2, 0, 0), (1, 0, 0, 0), x, y, 0b1100, 0b0011, 1]]
        elif box_type == 5:  # Opposite ends open (x,y)
            if layout == 1:  # Diagrammatic Layout
                pieces = [[(2, 0, 0, 1), (3, 0, 1, 1), x, z, 0b1010, 0b0101, 2],
                          [(3, 1, 0, 1), (2, 0, 0, 1), z, y, 0b1111, 0b1010, 3],
                          [(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1010, 0b0101, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1111, 0b1010, 3]]
            elif layout == 2:  # 2 Piece Layout
                pieces = [[(1, 0, 0, 1), (1, 0, 1, 1), x, z, 0b1010, 0b0101, 2],
                          [(2, 1, 0, 1), (1, 0, 0, 1), z, y, 0b1111, 0b1010, 3]]
            elif layout == 3:  # Inline(compact) Layout
                pieces = [[(1, 0, 0, 0), (1, 0, 0, 0), x, z, 0b1010, 0b0101, 2],
                          [(3, 2, 0, 0), (1, 0, 0, 0), z, y, 0b1111, 0b1010, 3],
                          [(2, 1, 0, 0), (1, 0, 0, 0), x, z, 0b1010, 0b0101, 2],
                          [(4, 2, 0, 1), (2, 0, 0, 0), z, y, 0b1111, 0b1010, 3]]
            elif layout == 4:  # Diagrammatic Layout with Alternate Tab Arrangement
                pieces = [[(2, 0, 0, 1), (3, 0, 1, 1), x, z, 0b1011, 0b0101, 2],
                          [(3, 1, 0, 1), (2, 0, 0, 1), z, y, 0b0111, 0b1010, 3],
                          [(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1110, 0b0101, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1101, 0b1010, 3]]
        elif box_type == 6:  # 2 panels jointed (x,y and z,y joined along y)
            pieces = [[(1, 0, 0, 0), (1, 0, 0, 0), x, y, 0b1011, 0b0100, 1],
                      [(2, 1, 0, 0), (1, 0, 0, 0), z, y, 0b1111, 0b0001, 3]]
        else:  # Fully enclosed
            if layout == 1:  # Diagrammatic Layout
                pieces = [[(2, 0, 0, 1), (3, 0, 1, 1), x, z, 0b1010, 0b1111, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1111, 0b1111, 3],
                          [(2, 0, 0, 1), (2, 0, 0, 1), x, y, 0b0000, 0b1111, 1],
                          [(3, 1, 0, 1), (2, 0, 0, 1), z, y, 0b1111, 0b1111, 3],
                          [(4, 1, 0, 2), (2, 0, 0, 1), x, y, 0b0000, 0b1111, 1],
                          [(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1010, 0b1111, 2]]
            elif layout == 2:  # 3 Piece Layout
                pieces = [[(2, 0, 0, 1), (2, 0, 1, 0), x, z, 0b1010, 0b1111, 2],
                          [(1, 0, 0, 0), (1, 0, 0, 0), z, y, 0b1111, 0b1111, 3],
                          [(2, 0, 0, 1), (1, 0, 0, 0), x, y, 0b0000, 0b1111, 1]]
            elif layout == 3:  # Inline(compact) Layout
                pieces = [[(5, 2, 0, 2), (1, 0, 0, 0), x, z, 0b1111, 0b1111, 2],
                          [(3, 2, 0, 0), (1, 0, 0, 0), z, y, 0b0101, 0b1111, 3],
                          [(6, 3, 0, 2), (1, 0, 0, 0), x, z, 0b1111, 0b1111, 2],
                          [(4, 2, 0, 1), (1, 0, 0, 0), z, y, 0b0101, 0b1111, 3],
                          [(2, 1, 0, 0), (1, 0, 0, 0), x, y, 0b0000, 0b1111, 1],
                          [(1, 0, 0, 0), (1, 0, 0, 0), x, y, 0b0000, 0b1111, 1]]
            elif layout == 4:  # Diagrammatic Layout with Alternate Tab Arrangement
                pieces = [[(2, 0, 0, 1), (3, 0, 1, 1), x, z, 0b1001, 0b1111, 2],
                          [(1, 0, 0, 0), (2, 0, 0, 1), z, y, 0b1100, 0b1111, 3],
                          [(2, 0, 0, 1), (2, 0, 0, 1), x, y, 0b1100, 0b1111, 1],
                          [(3, 1, 0, 1), (2, 0, 0, 1), z, y, 0b0110, 0b1111, 3],
                          [(4, 1, 0, 2), (2, 0, 0, 1), x, y, 0b0110, 0b1111, 1],
                          [(2, 0, 0, 1), (1, 0, 0, 0), x, z, 0b1100, 0b1111, 2]]

        for idx, piece in enumerate(pieces):  # generate and draw each piece of the box
            (xs, xx, xy, xz) = piece[0]
            (ys, yx, yy, yz) = piece[1]
            x_ = xs * spacing + xx * x + xy * y + xz * z  # root x co-ord for piece
            y_ = ys * spacing + yx * x + yy * y + yz * z  # root y co-ord for piece
            dx = piece[2]
            dy = piece[3]
            tabs = piece[4]
            a = tabs >> 3 & 1
            b = tabs >> 2 & 1
            c = tabs >> 1 & 1
            d = tabs & 1  # extract tab status for each side
            tabbed = piece[5]
            a_tabs = tabbed >> 3 & 1
            b_tabs = tabbed >> 2 & 1
            c_tabs = tabbed >> 1 & 1
            d_tabs = tabbed & 1  # extract tabbed flag for each side
            x_spacing = (x - thickness) / (div_y + 1)
            y_spacing = (y - thickness) / (div_x + 1)
            x_holes = 1 if piece[6] < 3 else 0   # 3 is a YZ piece
            y_holes = 1 if piece[6] != 2 else 0  # 2 is an XZ piece
            wall = 1 if piece[6] > 1 else 0
            floor = 1 if piece[6] == 1 else 0    # 1 is an XY piece
            rail_holes = 1 if piece[6] == 3 else 0

            if schroff and rail_holes:
                log("rail holes enabled on piece {} at ({}, {})".format(idx,
                                                                        x_ + thickness,
                                                                        y_ + thickness))
                log("abcd = ({},{},{},{})".format(a, b, c, d))
                log("dxdy = ({},{})".format(dx, dy))
                rhx_offset = rail_mount_depth + thickness
                if idx == 1:
                    rhx = x_ + rhx_offset
                elif idx == 3:
                    rhx = x_ - rhx_offset + dx
                else:
                    rhx = 0
                log("rhx_offset = {}, rhx= {}".format(rhx_offset, rhx))
                ry_start = y_ + (rail_height / 2) + thickness
                if rows == 1:
                    log("just one row this time, ry_start = {}".format(ry_start))
                    rh1y = ry_start + rail_mount_centre_offset
                    rh2y = rh1y + (row_centre_spacing - rail_mount_centre_offset)
                    draw_circle(rail_mount_radius, rhx, rh1y)
                    draw_circle(rail_mount_radius, rhx, rh2y)
                else:
                    for n in range(0, rows):
                        log("drawing row {}, ry_start = {}".format(n + 1, ry_start))
                        # if holes are offset (eg. Vector T-strut rails), they should
                        # be offset
                        # toward each other, ie. toward the centreline of the Schroff row
                        rh1y = ry_start + rail_mount_centre_offset
                        rh2y = rh1y + row_centre_spacing - rail_mount_centre_offset
                        draw_circle(rail_mount_radius, rhx, rh1y)
                        draw_circle(rail_mount_radius, rhx, rh2y)
                        ry_start += row_centre_spacing + row_spacing + rail_height

            # generate and draw the sides of each piece
            side_a = side(root_coord=(x_, y_),
                          start_offset_coord=(d, a),
                          end_offset_coord=(-b, a),
                          tab_vec=a_tabs * (-thickness if a else thickness),
                          length=dx,
                          direction=(1, 0),
                          is_tab=a,
                          is_divider=False,
                          num_dividers=(key_div_floor | wall) * (
                                  key_div_walls | floor) * div_x * y_holes * a_tabs,
                          div_spacing=y_spacing,
                          div_offset=div_offset)

            side_b = side(root_coord=(x_ + dx, y_),
                          start_offset_coord=(-b, a),
                          end_offset_coord=(-b, -c),
                          tab_vec=b_tabs * (thickness if b else -thickness),
                          length=dy,
                          direction=(0, 1),
                          is_tab=b,
                          is_divider=False,
                          num_dividers=(key_div_floor | wall) * (
                                  key_div_walls | floor) * div_y * x_holes * b_tabs,
                          div_spacing=x_spacing,
                          div_offset=div_offset)

            if a_tabs:
                side_c = side(root_coord=(x_ + dx, y_ + dy),
                              start_offset_coord=(-b, -c),
                              end_offset_coord=(d, -c),
                              tab_vec=c_tabs * (thickness if c else -thickness),
                              length=dx,
                              direction=(-1, 0),
                              is_tab=c,
                              is_divider=False,
                              num_dividers=0,
                              div_spacing=0,
                              div_offset=div_offset)
            else:
                side_c = side(root_coord=(x_ + dx, y_ + dy),
                              start_offset_coord=(-b, -c),
                              end_offset_coord=(d, -c),
                              tab_vec=c_tabs * (thickness if c else -thickness),
                              length=dx,
                              direction=(-1, 0),
                              is_tab=c,
                              is_divider=False,
                              num_dividers=(key_div_floor | wall) * (
                                      key_div_walls | floor) * div_x * y_holes *
                                           c_tabs,
                              div_spacing=y_spacing,
                              div_offset=div_offset)

            if b_tabs:
                side_d = side(root_coord=(x_, y_ + dy),
                              start_offset_coord=(d, -c),
                              end_offset_coord=(d, a),
                              tab_vec=d_tabs * (-thickness if d else thickness),
                              length=dy,
                              direction=(0, -1),
                              is_tab=d,
                              is_divider=False,
                              num_dividers=0,
                              div_spacing=0,
                              div_offset=div_offset)
            else:
                side_d = side(root_coord=(x_, y_ + dy),
                              start_offset_coord=(d, -c),
                              end_offset_coord=(d, a),
                              tab_vec=d_tabs * (-thickness if d else thickness),
                              length=dy,
                              direction=(0, -1),
                              is_tab=d,
                              is_divider=False,
                              num_dividers=(key_div_floor | wall) * (
                                      key_div_walls | floor) * div_y * x_holes *
                                           d_tabs,
                              div_spacing=x_spacing,
                              div_offset=div_offset)

            draw_lines(side_a)
            draw_lines(side_b)
            draw_lines(side_c)
            draw_lines(side_d)

            if idx == 0:
                if not key_div_walls:
                    a = 1
                    b = 1
                    c = 1
                    d = 1
                    a_tabs = 0
                    b_tabs = 0
                    c_tabs = 0
                    d_tabs = 0
                y_ = 4 * spacing + 1 * y + 2 * z  # root y co-ord for piece
                for n in range(0, div_x):  # generate x dividers
                    x_ = n * (spacing + x)  # root x co-ord for piece

                    side_a = side(root_coord=(x_, y_),
                                  start_offset_coord=(d, a),
                                  end_offset_coord=(-b, a),
                                  tab_vec=key_div_floor * a_tabs * (
                                      -thickness if a else thickness),
                                  length=dx,
                                  direction=(1, 0),
                                  is_tab=a,
                                  is_divider=True,
                                  num_dividers=0,
                                  div_spacing=0,
                                  div_offset=div_offset)

                    side_b = side(root_coord=(x_ + dx, y_),
                                  start_offset_coord=(-b, a),
                                  end_offset_coord=(-b, -c),
                                  tab_vec=key_div_walls * b_tabs * (
                                      thickness if key_div_walls * b else -thickness),
                                  length=dy,
                                  direction=(0, 1),
                                  is_tab=b,
                                  is_divider=True,
                                  num_dividers=div_y * x_holes,
                                  div_spacing=x_spacing,
                                  div_offset=div_offset)

                    side_c = side(root_coord=(x_ + dx, y_ + dy),
                                  start_offset_coord=(-b, -c),
                                  end_offset_coord=(d, -c),
                                  tab_vec=key_div_floor * c_tabs * (
                                      thickness if c else -thickness),
                                  length=dx,
                                  direction=(-1, 0),
                                  is_tab=c,
                                  is_divider=True,
                                  num_dividers=0,
                                  div_spacing=0,
                                  div_offset=div_offset)

                    side_d = side(root_coord=(x_, y_ + dy),
                                  start_offset_coord=(d, -c),
                                  end_offset_coord=(d, a),
                                  tab_vec=key_div_walls * d_tabs * (
                                      -thickness if d else thickness),
                                  length=dy,
                                  direction=(0, -1),
                                  is_tab=d,
                                  is_divider=True,
                                  num_dividers=0,
                                  div_spacing=0,
                                  div_offset=div_offset)

                    draw_lines(side_a)
                    draw_lines(side_b)
                    draw_lines(side_c)
                    draw_lines(side_d)
            elif idx == 1:
                y_ = 5 * spacing + 1 * y + 3 * z  # root y co-ord for piece
                for n in range(0, div_y):  # generate y dividers
                    x_ = n * (spacing + z)  # root x co-ord for piece

                    side_a = side(root_coord=(x_, y_),
                                  start_offset_coord=(d, a),
                                  end_offset_coord=(-b, a),
                                  tab_vec=key_div_walls * a_tabs * (
                                      -thickness if a else thickness),
                                  length=dx,
                                  direction=(1, 0),
                                  is_tab=a,
                                  is_divider=True,
                                  num_dividers=div_x * y_holes,
                                  div_spacing=y_spacing,
                                  div_offset=thickness)

                    side_b = side(root_coord=(x_ + dx, y_),
                                  start_offset_coord=(-b, a),
                                  end_offset_coord=(-b, -c),
                                  tab_vec=key_div_floor * b_tabs * (
                                      thickness if b else -thickness),
                                  length=dy,
                                  direction=(0, 1),
                                  is_tab=b,
                                  is_divider=True,
                                  num_dividers=0,
                                  div_spacing=0,
                                  div_offset=thickness)

                    side_c = side(root_coord=(x_ + dx, y_ + dy),
                                  start_offset_coord=(-b, -c),
                                  end_offset_coord=(d, -c),
                                  tab_vec=key_div_walls * c_tabs * (
                                      thickness if c else -thickness),
                                  length=dx,
                                  direction=(-1, 0),
                                  is_tab=c,
                                  is_divider=True,
                                  num_dividers=0,
                                  div_spacing=0,
                                  div_offset=thickness)

                    side_d = side(root_coord=(x_, y_ + dy),
                                  start_offset_coord=(d, -c),
                                  end_offset_coord=(d, a),
                                  tab_vec=key_div_floor * d_tabs * (
                                      -thickness if d else thickness),
                                  length=dy,
                                  direction=(0, -1),
                                  is_tab=d,
                                  is_divider=True,
                                  num_dividers=0,
                                  div_spacing=0,
                                  div_offset=thickness)

                    draw_lines(side_a)
                    draw_lines(side_b)
                    draw_lines(side_c)
                    draw_lines(side_d)


# Create effect instance and apply it.
effect = BoxMaker()
effect.affect()
