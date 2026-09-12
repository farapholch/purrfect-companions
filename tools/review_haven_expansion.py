#!/usr/bin/env python3
"""Cutaway of the north village; diagnostic block colors, not a Minecraft render."""
import render_world as r
r.VANILLA.update({'clay':(154,165,177),'smoker':(91,85,77),'crafting_table':(150,110,61)})
r.render_topdown(r.build_voxels(),r._custom_colors(),'/tmp/cathaven-expansion-map.png',ymax=-58,area=((-38,28),(-23,5)),scale=12)
