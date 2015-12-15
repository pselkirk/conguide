Arisia Pocket Program Workflow
==============================

Introduction
------------

This document describes a workflow that I used to produce the Pocket
Program for Arisia 2008-2015, plus two Worldcons (Renovation in 2011, and
Sasquan in 2015). The scripts have been completely rewritten for 2015, so
hopefully all the tweaking that has to happen is confined to the
configuration file.

The very brief synopsis is: I get a programming database report in
.csv (comma-separated value) format. I run this through some python
scripts, which generate an XML file. I link this into an InDesign
document, and they magically turn into a book.

The same scripts can produce html for the website, and plain text for
sanity checking and proof-reading. In addition, there are some
analysis and reporting tools.


Prerequisites
-------------

Of course you need InDesign, Illustrator (for the maps), and Photoshop
(for the cover artwork), and a Windows box or Mac to run them on.

(Or you could run Scribus, Inkscape, and Gimp; let me know how that goes.)

On native Windows, I use Cygwin's python. However, I've recently switched
to running Windows 7 in a virtual machine on Ubuntu Linux. I run all the
python scripts in Linux, and import the generated files into InDesign in
the VM. (This is not insane!) See
http://www.prtfl.io/muellerwolfram/blog/2013/1/23/how-to-use-photoshop-in-ubuntu
for hints about how to set this up.

If you want to dive deep into the code, you need to know (or be willing to
learn) python. It also helps to have a basic understanding of xml, xhtml,
Unicode, UTF-8, and Windows-1252.


Setup
-----

conguide.cfg has a bunch of things that need to be configured once, at
the start of the project - convention name, active days, rooms. In
addition, there are some things that may need to be tweaked as you go
along.


Data Sources
------------

``pocketprogram.csv`` - This is the primary data file, the result of
running a database report.

Log into Zambia (zambia.arisia.org). Make sure you've got the Staff View,
not the Participant View; if you don't have staff access, email
programming@arisia.org. Go to the Available Reports tab, then go to the
"Reports downloadable as CSVs" link, and click on "Report for Pubs (CSV
Version)" and "CSV - Biographies for publication". Save the results.

Important: Don't forget to back up the old data before overwriting!
``conguide backup`` assigns unique dated names to the csv files.


Statistics and Other Interesting Data
-------------------------------------

``conguide changes`` - Show changes from the last data dump, or between
any two data dumps.

``conguide count`` - Show what rooms are in use, how many items are
scheduled each day, etc. This can be run against a single data dump, or
multiple data dumps, if you want to compare.

``conguide featured`` - When run with ``--research``, this identifies
likely candidates for the "Featured Events" list, formatted for easy
insertion into the ``[featured]`` section of conguide.cfg.


Generating the Output Files
---------------------------

Run ``conguide all`` to generate the bulk of the book:
- schedule
- featured events
- track list
- participant cross-reference

This emits pocketprogram.xml. For a variety of reasons, it's more
convenient to have all of these in one gigantic xml output file, and
to associate the major tags with different "stories" within the book.

The XML file is already linked to the InDesign file. The Links window
will show a yellow triangle warning if the XML file has been updated
and needs to be re-imported. To re-import, click on pocketprogram.xml
in the Links window, then click on the Update Link icon at the bottom
(or use the flyout menu).

To do a new import (because you have a new file, or you just want to
understand how I set it up), choose File > Import XML, select
pocketprogram.xml, and select Show XML Import Options from the import
dialog. In the XML Import Options dialog, select Create Link, and
un-select all the other options. Open the Structure window (View >
Structure), and you will see the complete structure of the xml file.
Open the Tags window (Window > Utilities > Tags), and you will see all
the tags (xml element names) in the xml file. From either the
Structure window or the Tags window, open the flyout menu, and select
Map Tags to Styles. Then choose the appropriate paragraph or character
style for each tag. Note that you can only choose one style per tag,
so e.g. ss-index and ss-room have character styles, but ss-title has
the paragraph style for the whole line. Note also that not all tags
will have an associated style (container tags generally won't). Now
drag the "schedule" tag from the Tags window to schedule story (master
page A-Friday), then drag the "schedule" sub-tree from the Structure
window into the schedule story. This should import the xml data into
the story, and apply all the paragraph and character styles.

Post-Import Cleanup
~~~~~~~~~~~~~~~~~~~

Look for long title lines, or even titles that bump into the room
name. First select the title and room, and try to adjust the tracking,
but don't go beyond -50. Failing that, break the line before the room
(use shift-Enter to keep it as part of the same paragraph), and tab
the room over to the right margin. If there's an icon next to the
desription, cut and paste it onto the line with the room, so that it
stays adjacent to the session number.

Look for widows and orphans. Occasionally you can fix these by
changing the paragraph style to fully justified. If necessary, play
with the size of the text frame. Also look for hyphenation fails;
especially try to avoid hyphenation in participant names.

Fix the day dividers. When the day changes, instead of just the time,
there's a divider with the time and day, e.g. "12:00am SATURDAY". The
text is fine, but you need to adjust the horizontal line. In the
Paragraph Rules dialog, changed the Weight to 2pt, and the Left Indent
to 1.125" for Saturday, and 1" for Sunday and Monday.

Apply the appropriate master pages to the schedule pages. I just
revived the old practice of putting a clock icon at the top of each
page. There are now 12 master pages for each day, called things like
"Friday 1" and "Friday 2". Apply the master page that matches the
first session on the page. You may choose to make it the first title
(the first full session), but be consistent.


Grids
-----

Run ``conguide grid`` to generate the grids.

This emits grid.txt, which is an InDesign tagged text file. (This is
the one piece of the book which I can't do in XML, and not for lack of
trying. Adobe's support for tables in its XML format does not include
a row height attribute, which makes it pretty worthless for me.)

To import the grid data, open 'Pocket Program Grid.indd', click inside
one of the text frame, but outside the table (i.e. click on one of the
day headers), hit ctrl-A to select all text (including tables), then
hit ctrl-D to place 'grid.txt'. In the Place dialog, make sure
"Replace Selected Item" is checked.

The table row heights are calculated based on the number of "major"
rooms (those with more than 5 scheduled sessions). Anything that's in
a "minor" room will show up in an extra row, with the room name in
red, and with the room name following the session title. For some
reason, when a table overflows its text frame by having extra rows,
InDesign displays a lot of blank pages after that table, so you need
to work on one table at a time, resolving all the extra rows.

If you see a minor-room session, you need to move it to an unused cell
somewhere else in the table, ideally in the same time slot. Use Table >
Unmerge Cells and Merge Cells to create a cell of the right size.
Use Table > Cell Options > Strokes and Fills to set the fill color to
'Paper'. Copy the cell text (including the room name) to the new cell,
then use Table > Delete > Row (or ctrl-Backspace) to remove the
now-unused "extra" row.

We don't actually print the tables for Friday Morning, anything Early
Morning, or Monday Evening, so don't bother making them look nice,
just delete unused rows to make the table fit in its text frame.

Any sessions that fall entirely in one of the tables that we don't
print will have to get moved into a table that we do print. Friday
afternoon sessions can be moved into the Friday Evening table in the
same way as the "extra-row" sessions above. OTOH, sessions on the
Early Morning tables can be consolidated into a single oversized cell
on the previous evening's table. See the "Overnight Movies" listings
in the example grids.

Any cell that displays a red dot in the corner has text that overflows
the cell ("overset text" in InDesign parlance). In some cases you can
just enable hyphenation for that cell (off by default in the "Grid
text" paragraph style). But in most cases, you'll need to copy the
text out to a text editor where you can actually see it all, and edit
it down as best you can.

Finally, go through the whole table and adjust line breaks as needed
to make titles look better. Try to find the natural phrase breaks.  In
Readings and Autographs, avoid having a line break in the middle of a
name (between first and last name) wherever possible. In multi-session
cells (mostly games and Fast Track), sessions are separated with
semicolons; try to arrange the line break after a semicolon if
possible.

Depending on how many rooms are in use, you may need to adjust the
grouping labels on the master page. However, the grid is not visible
on the master page, so you have to hack it a bit. On approach is to
copy the labels from the master page to a grid page (say Friday
Evening), make the adjustments there, then copy them back to the
master page. Another approach is to pull a temporary guide line down
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

The words "Arisia 2014" and "Pocket Program" should appear on the
cover, in a font that complements the artwork. When laying out the
cover, don't forget to leave room for the bleed tab labels.

Maps
~~~~

The maps are created and edited in Illustrator. I've carefully
organized each one into 3 layers: ``Lines`` (i.e. walls), ``Hotel labels``
(room names, icons for bathrooms, escalators, and the like), and
``Arisia labels`` (how we're using each room, or locations of desks in
lobbies).

The maps are roughly but not obsessively to scale. There is
Westin-poster.ai that pulls together the maps into one cohesive hotel
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
to be dealt with).

Ads
~~~

Dealers list, Artists list
~~~~~~~~~~~~~~~~~~~~~~~~~~


Other deliverables
------------------

html for website

GuideBook

large print

maps & quick ref for posters

text for braille

