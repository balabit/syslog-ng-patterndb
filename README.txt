
Introduction
============

db-parser() is a feature of syslog-ng that lets users classify messages and
to extract free-form human readable information into structured name-value
pairs.

db-parser() uses a database of log patterns, described in a set of external
XML files, read by syslog-ng upon startup.

The aim of this document is to describe how these pattern files should be
constructed in order to make them useful for the general syslog-ng user.
This is not a patterndb documentation, the documentation of patterndb can
be found in the syslog-ng Administrator's Guide at:

http://www.balabit.com/support/documentation/

Applying patterndb
==================

Since the db-parser() feature can be used in a multitude of ways, this
section describes how we assumed db-parser() is used by our average
syslog-ng user.

This section is not necessarily a simple reading, it is just a concise
summary which you can probably only understand once you understand the
patterndb structure and features.

  * all incoming syslog messages go through a patterndb, as their first step
    of processing
  * patterndb is used to:
    * identify the event, assign the same ID to all variations of the same
      message
    * extract information into name-value pairs
    * associate one or more tags to the message
  * once patterndb identified the message, further processing is performed
    based on
    * "tags" are used for filtering
    * name-value pairs are used to write structured information

The key in the usability of patterndb is the way names for tags and
name-value pairs are chosen, and the meat of this policy is to describe the
rules governing naming.

Schemas & Tags
==============

The same message can be interpreted multiple ways and each interpretation
possibly has a distinct set of important attributes.

For example the SSH login message looks like this:

Accepted publickey for bazsi from 192.168.1.1 port 1156 ssh2
         ^^^^^^^^^     ^^^^^      ^^^^^^^^^^^      ^^^^ ^^^^

The marked portions are candidates to be included in name-value pairs. There
are multiple possible interpretations of the log message above, but for the
sake of the example, let's name two:

  * it is a login event
  * it describes a TCP session established to the host computer, processed
    by our SSH daemon

As a login event, the important portions of the message is:
  * username: bazsi
  * client_ip: 192.168.1.1
  * info: ssh2, publickey

As a TCP session, the important portions are:
  * application: ssh
  * client_ip: 192.168.1.1
  * client_port: 1156
  * server_ip: 0.0.0.0 (not in the message)
  * server_port: 22    (not in the actual message)

Although the examples might be a bit weird, the point is that there might
even be information associated with a log message which is not actually
written into the message and the two interpretations differ in the set
of name-value pairs that are important in understanding the event.

From now on, the "interpretation of an event" is called "schema", which is
comprised of:
  * a set of name-value pairs that can be or must be defined in order to
    evaluate the event
  * a tag that marks that a given message is interpreted in this schema

The following conventions are used:
  * the name of the schema is used as the prefix of the name-value pairs
  * the name of the schema and the tag are the same

This means that with the samples above the "login" schema would use the
following names for name-value pairs:
  * login.username
  * login.client_ip
  * login.info

Likewise, my TCP example would use:
  * tcpsession.application
  * tcpsession.client_ip
  * tcpsession.client_port
  * tcpsession.server_ip
  * tcpsession.server_port

Additional rules:
  * schema & NV pair names should relate to the event type that it describes
  * schema & NV pair names are case-sensitive
  * schema @ NV pair names should only contain alphanumeric characters (a-zA-Z0-9)
  * only one dot should be present in NV pair names, which separates the
    schema prefix from the attribute name

Describing schemas
==================

syslog-ng has no limits on how name-value pairs or tags are named, the
schema concept only exists as a set of conventions, we as the patterndb
maintainers adhere to.

For now, schemas are going to be described in a text file named SCHEMAS.txt
next to this document, but a more formal description and even a validation
tool might be created in the future.

In order to accept a pattern ruleset the schema it is using must be
described in the SCHEMAS.txt file.

Schemas are developed in the public of the syslog-ng mailing list (though
the venue of communication might change in the future).

It is important to realize that it is not trivial to decide whether a schema
with the given set of name-value pairs contain everything that a given
interpretation needs. Therefore the development of schemas is more like a
process: it starts with a given set of applications at first and might
evolve as new and new applications get covered. Once over the critical mass,
new applications are not expected to change the schema.

Since the proliferation of schemas should be strongly avoided, we define the
state of our commitment to a given schema:
  * experimental: completely experimental, changes are to be expected, only
    a small set of applications are covered (or only 1)
  * testing: a number of applications got covered, but more testing is
    needed
  * stable: we commit to this schema, changes can only be incremental (e.g.
    additional NV pairs)

Of course it doesn't mean that individual syslog-ng users couldn't define
their own schemas for in-house applications, syslog-ng would work with those
just as well, but we strongly suggest that even in-house patterns use the
same naming structure as described here in this document.

Files & directories
===================

The layout of this package is:
  /
    +--appgroup1/
       application1.xml
       application2.xml
       ...
    +--appgroup2/
       application3.xml
       application4.xml
       ...

Applications are grouped by their respective function and each application
gets a single file that lists all the patterns of that application.

NOTE: pdbtool doesn't yet handle recursive directory structures, but I plan
to add that as soon as possible.

Deploying this package
======================

Patterndb files are XML files that can be installed into a syslog-ng
installation under the path:

/etc/syslog-ng/patterndb.d

The files in this directory are read and merged by update-patterndb which
generates a file named /var/lib/syslog-ng/patterndb.xml, which is read by
syslog-ng's db-parser() statement.

The aim of this package is to be directly deployable in
/etc/syslog-ng/patterndb.d by extracting the distribution.
