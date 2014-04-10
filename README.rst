======
 Loop
======

Overview
========

Loop monitors a directory for changes and executes the supplied command.

The current directory is recursively monitored for changes (modification and creation). If such a change occurs the command supplied is executed. Files are ignored by a custom pattern-list and a .gitignore file (if found).


Usage
=====

 loop ls -la
