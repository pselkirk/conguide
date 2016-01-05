Changelog
=========

0.9.4 (2016-01-05)
------------------

Change
~~~~~~

- Add a config option to sort participants in schedule listing.
  Supported modes are strict sorting, and moderator-first.

- Restore support for uppercase rendering of fields in templates.

Fix
~~~

- Escape ampersand in xref xml output - participant names (group names) might
  have an ampersand, who knew?

- Implement the code behind '[session do not print]'.

0.9.3 (2015-12-30)
------------------

Change
~~~~~~

- If report commands are run without an output mode specified, default to
  all modes rather than none. (e.g. ``conguide all`` == ``conguide all -a``)

Fix
~~~

- Don't panic if duration field is empty.

0.9.2 (2015-12-17)
------------------

Fix
~~~

- Restore the way the InDesign doc expects to see the tracks in xml.

- Fix the config for bios templates.

- Fix a repeated-content bug in grid.

0.9.1 (2015-12-16)
------------------

First upload to PyPI.

New
~~~

- Add ``--version`` option.

Fix
~~~

- ``conguide all`` was causing repeated content due to repeated read of
  input files.

- Fix ``conguide grid -a`` exception.

- Fix ``bios`` to work at all (was reading the wrong csv file).

0.9.0 (2015-12-08)
------------------

Limited release for Arisia internal use.
