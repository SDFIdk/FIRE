# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Fire
                                 A QGIS plugin
 FikspunktRegister Plugin (Processing funcs)
                              -------------------
        begin                : 2019-12-02
        copyright            : (C) 2019 by Septima
        email                : kontakt@septima.dk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Septima'
__date__ = '2019-12-02'
__copyright__ = '(C) 2019 by Septima'


def classFactory(iface):  # pylint: disable=invalid-name
    from .fire_plugin import FirePlugin
    return FirePlugin()
