Arisia Pocket Program Workflow
==============================

Introduction
------------

This document describes a workflow that I used to produce the Pocket
Program for Arisia 2008-2017, plus two Worldcons (Renovation in 2011, and
Sasquan in 2015). The scripts were completely rewritten for 2015, so
hopefully all the tweaking that has to happen is confined to the
configuration file.

The very brief synopsis is: I get a programming database report in
.csv (comma-separated value) format. I run this through some python
scripts, which generate an XML file. I link this into an InDesign
document, and they magically turn into a book.

The same scripts can produce html for the website, and plain text for
sanity checking and proof-reading. In addition, there are some
analysis and reporting tools.

The guidance given here is very specific to the way I work, for this
convention. If you're not me, and especially if you're doing this for a
different convention, there should be enough detail here so you can
figure out how to adapt.


Prerequisites
-------------

Of course you need InDesign (for layout), Illustrator (for the maps),
and Photoshop (for the cover artwork), and a Windows box or Mac to run
them on. (Or you could run Scribus, Inkscape, and Gimp; let me know how
that goes.)

On native Windows, I use Cygwin's python. However, I've recently
switched to running Windows 7 in a virtual machine on Ubuntu Linux. I
run all the python scripts in Linux, and import the generated files into
InDesign in the VM. (This is not insane!) See
http://www.prtfl.io/muellerwolfram/blog/2013/1/23/how-to-use-photoshop-in-ubuntu
for hints about how to set this up.

If you want to dive deep into the code, you need to know (or be willing to
learn) python. It also helps to have a basic understanding of XML, XHTML,
Unicode, UTF-8, and Windows-1252.

conguide
~~~~~~~~

Get my ``conguide`` package by running ``pip install conguide``.

(``pip`` should come with your python installation, but you might need
to install it separately?)

To upgrade, run ``pip install --upgrade conguide``.

Setup
-----

It's best to start with a copy of last year's files - the InDesign files
for the book and grids, the Illustrator files for the maps, and the
conguide configuration file.

``conguide.cfg`` has a bunch of things that need to be configured once,
at the start of the project - convention name, active days, rooms. In
addition, there are some things that may need to be tweaked as you go
along.


Data Sources
------------

Log into Zambia (http://zambia.arisia.org). Make sure you've got the
Staff View, not the Participant View; if you don't have staff access,
email programming@arisia.org. Go to the Available Reports tab, then go
to the ``Reports downloadable as CSVs`` link, and click on ``Report for
Pubs (CSV Version)`` and ``CSV - Biographies for publication``. Save the
results.

``pocketprogram.csv`` is the primary data file, with the full schedule.

``PubBio.csv`` is the program participant bios. It has the participants
in roughly alphabetical order, but gets it wrong often enough that
``conguide`` does its own sorting, with a bit of guidance from the
``[participant sort name]`` config section.

Important: Don't forget to back up the old data before overwriting!
The files download as ``pocketprogram.csv`` and ``PubBio.csv``. Run
``conguide backup`` to assign unique dated names to the csv files,
before downloading new csv files into your working directory. You will
want the old files to compare with (see next section).

(By contrast, Worldcon uses Grenadine, which produces date-stamped data
files. In that case, either update the file name in ``[input files]``,
or create a symbolic link and update that to point to the right file.)

Statistics and Other Interesting Data
-------------------------------------

``conguide changes``
  Show changes from the last data file, or between any two data files. If
  one argument is given, it will compare the named file to the default
  input file (``pocketprogram.csv``). If two arguments are given, it will
  compare the two named files.

``conguide count``
  Show what rooms are in use, how many items are scheduled each day,
  etc. This can be run against a single data file, or multiple data files,
  if you want to compare. For instance, I like to compare this time last
  year, when we went to press last year, and where we're at right now.
  If no argument is given, it will count the default input file
  (``pocketprogram.csv``). If two or more arguments are given, it will
  count the files in a tabular format.

``conguide featured``
  When run with ``--research``, this identifies likely candidates for the
  "Featured Events" list, formatted for easy insertion into the
  ``[featured sessions]`` config section.

``conguide problems``
  Find common problems in the data file.

``conguide dup``
  Find duplicated/repeated sessions. If space is very tight in the book,
  it may be helpful to replace sessions with "See #nnn for description."
  Output is formatted for easy insertion into the ``[schedule deduplicate]``
  config section.

``conguide overnight``
  Find "overnight" sessions - ones that will only show in a Late Night
  grid, e.g. starting at or after 1:30am and ending at or before 8:30am.

Generating the Pocket Program
-----------------------------

Run ``conguide all`` to generate the bulk of the book:

- schedule
- featured events
- track list
- participant cross-reference

This emits ``pocketprogram.xml``. For a variety of reasons, it's more
convenient to have all of the sections in one gigantic xml output file,
and to associate the major tags with different "stories" within the
book.

The XML file is already linked to the InDesign file. The Links window
will show a yellow triangle warning if the XML file has been updated and
needs to be re-imported -- just double-click on the yellow triangle and
wait for it to read and render the new data. WARNING: this will
overwrite any local edits in any linked sections.

To do a new import (because you have a new file, or you just want to
understand how I set it up), choose ``File`` > ``Import XML``, select
``pocketprogram.xml``, and select ``Show XML Import Options`` from the import
dialog. In the ``XML Import Options`` dialog, select ``Create Link``, and
un-select all the other options. Open the ``Structure`` window (``View`` >
``Structure``), and you will see the complete structure of the xml file.
Open the ``Tags`` window (``Window`` > ``Utilities`` > ``Tags``), and you will see all
the tags (xml element names) in the xml file. From either the
``Structure`` window or the ``Tags`` window, open the flyout menu, and select
``Map Tags to Styles``. Then choose the appropriate paragraph or character
style for each tag. Note that you can only choose one style per tag,
so e.g. ``ss-index`` and ``ss-room`` have character styles, but ``ss-title`` has
the paragraph style for the whole line. Note also that not all tags
will have an associated style (container tags generally won't). Now
drag the ``schedule`` tag from the ``Tags`` window to the schedule story (master
page A-Friday), then drag the ``schedule`` sub-tree from the ``Structure``
window into the schedule story. This should import the xml data into
the story, and apply all the paragraph and character styles.

Post-Import Cleanup
~~~~~~~~~~~~~~~~~~~

Obviously look for text that overflows the allotted pages, and add pages
as necessary.

Look for long title lines, or even titles that bump into the room
name. Select the title and room, and try to adjust the tracking, but
don't go beyond -30. A good rule of thumb is that, if only the level
(e.g. "(3E)") spills over, you can get it with tracking. Failing that,
break the line before the room (use shift-Enter to keep it as part of
the same paragraph), and tab the room over to the right margin.

Look for widows and orphans. Sometimes you can fix these by changing the
paragraph style to fully justified, if the last line is 5 characters or
less. Use this technique judiciously, because the paragraph can get very
cramped this way. If necessary, play with the size of the text frame. Also
look for hyphenation fails; especially try to avoid hyphenation in
participant names.

Finally, apply the appropriate master pages to the schedule pages. I
recently revived the old practice of putting a clock icon at the top of
each page. There are now 12 master pages for each day, called things like
"Friday 1" and "Friday 2". Apply the master page that matches the first
full session (the first title) on the page.


Grids
-----

Run ``conguide grid`` to generate the grids (if you want to do it
separately from ``conguide all``).

This emits ``grid.txt``, which is an InDesign tagged text file. (This is
the one piece of the book which I can't do in XML, and not for lack of
trying. Adobe's support for tables in its XML format does not include
a row height attribute, which makes it pretty worthless for me.)

To import the grid data, open ``Pocket Program Grid.indd``, click inside
one of the text frame, but outside the table (i.e. click on one of the
day headers), hit ctrl-A to select all text (including tables), then
hit ctrl-D to place 'grid.txt'. In the Place dialog, make sure
``Replace Selected Item`` is checked.

The table row heights are calculated based on the number of "major"
rooms (those with more than 5 scheduled sessions). Anything that's in
a "minor" room will show up in an extra row, with the room name in
red, and with the room name following the session title.

If you see a minor-room session, you need to move it to an unused cell
somewhere else in the table, ideally in the same time slot. Use ```Table`` >
``Unmerge Cells`` and ``Merge Cells`` to create a cell of the right size. In the
``Cell Styles`` window, select ``Grid text``. Copy the cell text (including the
room name) to the new cell. Re-merge any empty cells, with cell style
``Grid gray``. Finally, use ``Table`` > ``Delete`` > ``Row`` (or ctrl-Backspace) to
remove the now-unused "extra" row.

We don't actually print the tables for Friday Morning, anything Late
Night, or Monday Evening, so don't bother making them look nice, just
delete unused rows to make the table fit in its text frame.

Any sessions that fall entirely in one of the tables that we don't
print will have to get moved into a table that we do print. Friday
afternoon sessions can be moved into the Friday Evening table in the
same way as the "extra-row" sessions above. OTOH, sessions on the
Late Night tables can be consolidated into a single oversized cell
on the previous evening's table. See the "Overnight Movies" listings
in the example grids. Use ``conguide overnight`` to generate a list of
these sessions. (At present, this is a plain-text list, which you have
to manually copy into the grid, and apply paragraph styles.)

Any cell that displays a red dot in the corner has text that overflows
the cell ("overset text" in InDesign parlance). In some cases you can
just enable hyphenation for that cell (off by default in the ``Grid
text`` paragraph style). But in most cases, you'll need to copy the
text out to a text editor where you can actually see it all, and edit
it down as best you can.

There has been an explosion in the Gaming track (in Harbor I), with as
many as half a dozen games starting at the same time (therefore in the
same grid table cell). Coincidentally, the Minstrels were just added to
the program, with performances/jams in Harbor III (Art Show) and Harbor
Prefunction.  So I could grab one of those rooms to give Harbor I two
table rows. Even then, I had to remove the gaming system from all
session titles, aggressively edit the titles, and even merge cells in a
few cases.

Finally, go through the whole table and adjust line breaks as needed to
make titles look better. Try to find the natural phrase breaks. In
Readings and Autographs (when present), avoid having a line break in the
middle of a name (between first and last name) wherever possible. In
multi-session cells (Gaming and Fast Track), sessions are separated with
semicolons; try to arrange the line break after a semicolon if possible.

Depending on how many rooms are in use, you may need to adjust the
grouping labels (e.g. "Mezzanine (3W)") on the master page. However, the
grid is not visible on the master page, so you have to hack it a bit.
One approach is to copy the labels from the master page to a grid page
(say Friday Evening), make the adjustments there, then copy them back to
the master page. Another approach is to pull a temporary guide line down
to the start of a grouping, noting the precise value of the Y position
in the tool dialog.


Other content
-------------

Cover
~~~~~

We get some bit of GOH artwork from the Publications div head. This is
often last-minute, and may involve some scrounging among the scraps
not used by the Souvenir Book.

Artwork obviously has to fit a 4" x 10" cover (add a minimum 1/8"
bleed around all sides), or 8" x 10" for a wrap-around cover, and has
to look good in black & white.

The words "Arisia 2017" (or whichever year) and "Pocket Program" should
appear on the cover, in a font that complements the artwork. When laying
out the cover, don't forget to leave room for the bleed tab labels.

Maps
~~~~

The maps are created and edited in Illustrator. I've carefully
organized each one into 3 layers: ``Lines`` (walls), ``Hotel labels``
(room names, icons for bathrooms, escalators, and the like), and
``Arisia labels`` (how we're using each room, or locations of desks in
lobby and prefunction areas).

The maps are roughly but not obsessively to scale. There is a
``Westin-poster.ai`` that pulls together the maps into one cohesive hotel
map. Note that the Pocket Program has its own version of the overall
map, in the InDesign file. This allows us to move and tweak individual
maps to fit on the printed page.

Quick Reference
~~~~~~~~~~~~~~~

The QR is the what/when/where of the con, outside of the panel rooms.
Skip considers this the most important 2 pages that we publish.
There's a constant tension between adding more stuff (or more text)
and keeping it down to 2 pages of the book, or one poster-size page to
stick up at Info Desk.

Every line of the QR needs to be reviewed for relevance, location,
hours, and, in a few cases, phone numbers. We sometimes devote an
entire concom meeting to this (and inevitably uncover issues that need
to be dealt with). Recently, we've dumped the text into a Google doc for
large-scale review and updating.

Ads
~~~

We usually run an ad for next year's con on the back cover or inside
back cover. Occasionally we get ads for other conventions. However,
we're tight enough for space that the extra money isn't worth the
hassle.

Dealers list, Artists list
~~~~~~~~~~~~~~~~~~~~~~~~~~

We used to include one or both of these lists in the Pocket Program, but
we can't spare the pages anymore, and we don't have anyone pushing to
include them.


Deliverables
------------

PDF for printing
~~~~~~~~~~~~~~~~

In InDesign, export the book as PDF, using the ``Press Quality with
bleeds`` preset.

If that doesn't exist (because you didn't start with last year's book),
use the ``Press Quality`` preset, and check ``Crop Marks``, and set
``Bleed`` to at least 0.125" all around (or check ``Use Document Bleed
Settings``).

If the cover IS NOT wraparound (separate artwork for front and back
covers), you can include the covers in the same PDF as the interior
pages.

If the cover IS wraparound, you need to make a separate 8"x10" PDF of
the cover (including the inside cover), and only include the interior
pages in the book PDF. In my file, the cover pages are numbered i-iv, so
you can set the page range to 1-88.

Always check ``View PDF after Exporting``, and always sanity-check the
generated PDF.

Export the grids using the ``Smallest File Size`` preset. This prints on
ordinary copier paper, so the same PDF is used for printing and the website.

PDF for website
~~~~~~~~~~~~~~~

In InDesign, export the book as PDF, using the ``Smallest File Size``
preset, and check ``Spreads``. (I should probably create a derived
preset for this, but oh well.) This creates a PDF with 4"x10" cover
pages, and 8"x10" interior pages, which can be easily printed for review
or whatever.

HTML for website
~~~~~~~~~~~~~~~~

``conguide all -h`` generates html documents with cross-links: titles in
the grid, track list, featured list, and bios all link to session
descriptions in the schedule; and participant names in the schedule link
to the bios. Also, URLs and email addresses in the descriptions and the
bios are automatically turned into links.

By convention, the file names in ``[output files html]`` do not have the
``.html`` extension, because we drop them into Drupal as page names.

Guidebook
~~~~~~~~~

``conguide guidebook`` creates the three .csv files that Guidebook
needs. James van Zandt is responsible for liaising with guidebook.com and
getting the files into their system. I don't know anything about the
workflow beyond that.

Large Print
~~~~~~~~~~~

The Access team used to (maybe still does?) print the pocket program on
legal size paper (8.5"x14"). This is a 40% larger page, which is okay I
guess. Back when the book was only 8.5" tall, printing on legal made it
65% bigger.

For this, export the book as PDF, using the ``Smallest File Size``
preset, without the ``Spreads`` option. The PDF file name should include
the phrase "1up" or "1-up" to distinguish it.

Maps & Quick Reference for posters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rick likes to print posters to hang at Info Desk and/or around the con.

For the maps, there is a ``Westin-poster.ai`` that links to the
individual map files. In Illustrator, export that as PDF. (Note that
the Pocket Program has its own links to the map files; each one is laid
out to its particular page size (8.5"x11" or 8"x10")).

For the QR, open the website version of the book PDF (the one with
spreads and no crop marks) in Acrobat Pro, and extract the QR page as
a separate PDF (``Tools`` > ``Pages`` > ``Extract``). If you want to
pretty it up a little, remove the bleed tab: ``Tools`` > ``Content`` >
``Edit Object``, click on the bleed tab, and hit delete. You can also
remove the page numbers with the ``Edit Document Text`` tool.
