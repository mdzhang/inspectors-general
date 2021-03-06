#!/usr/bin/env python

import datetime
import logging
import os
import re

from utils import utils, inspector

# https://www.sigtarp.gov
archive = 2009

# options:
#   standard since/year options for a year range to fetch from.
#
# Notes for IG's web team:
#

REPORT_URLS = [
  ("semiannual_report", "https://www.sigtarp.gov/pages/quarterly.aspx"),
  ("audit", "https://www.sigtarp.gov/pages/audit.aspx"),
  ("audit", "https://www.sigtarp.gov/pages/auditrc.aspx"),
  ("audit", "https://www.sigtarp.gov/pages/engmem.aspx"),
]

LINK_RE = re.compile("^([A-Za-z ]+) \\(([A-Z][a-z]+ [0-9]+, [0-9]+)\\)$")

def run(options):
  year_range = inspector.year_range(options, archive)

  # Pull the reports
  for report_type, report_url in REPORT_URLS:
    doc = utils.beautifulsoup_from_url(report_url)
    results =  doc.select("td.mainInner div.ms-WPBody > div > ul > li")

    if not results:
      raise inspector.NoReportsFoundError("SIGTARP (%s)" % report_url)

    for result in results:
      report = report_from(result, report_type, year_range)
      if report:
        inspector.save_report(report)

def report_from(result, report_type, year_range):
  result_link = result.find("a")
  title = result_link.text

  report_url = result_link.get('href')
  report_filename = report_url.split("/")[-1]
  report_id, extension = os.path.splitext(report_filename)

  published_on_text = result.select("div.custom_date")[0].text.lstrip("-")
  if published_on_text == "":
    match = LINK_RE.match(result_link.text.strip())
    published_on_text = match.group(2)
    title = result.find("div", class_="groupheader").text.strip()
  published_on = datetime.datetime.strptime(published_on_text, '%B %d, %Y')

  if published_on.year not in year_range:
    logging.debug("[%s] Skipping, not in requested range." % report_url)
    return

  report = {
    'inspector': 'sigtarp',
    'inspector_url': "https://www.sigtarp.gov",
    'agency': 'sigtarp',
    'agency_name': "Special Inspector General for the Troubled Asset Relief Program",
    'type': report_type,
    'report_id': report_id,
    'url': report_url,
    'title': title,
    'published_on': datetime.datetime.strftime(published_on, "%Y-%m-%d"),
  }

  return report

utils.run(run) if (__name__ == "__main__") else None
