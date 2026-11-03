"""Replaces outdated persona images, then re-audits the site.

fix.py      backs up and replaces every image both classifiers call outdated
design_tool redraws an image with the approved persona (stand-in for a design tool)
reaudit.py  crawls and classifies the fixed site and writes the handoff and reports
"""
