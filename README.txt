
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
  * schema @ NV pair names should only contain alphanumeric characters: [_\.a-zA-Z0-9]+
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

Combining schemas
=================

Since our aim is to keep schemas as clean as possible, avoiding the addition
of newer and newer name-value pairs to a generic schema in order to support
a given application should be avoided if possible.

Therefore our idea is to make it possible to combine schemas when extracting
fields from a single message. The best way to understand this is to use a
concrete example.

Firewall events are usually comprised of:
  * an IP tuple (protocol, addresses, ports)
  * a verdict (ACCEPT or DROP)

However there are related events that should also be interpreted as firewall
events, however they'd add further fields into the mix, not that strictly
part of our original "Firewall events":

  * a NAT translation (IP tuple before and after the translation)

Of course the IP tuple _before_ the translation is the same as the IP tuple
in our original firewall event, however the tuple after the translation is
certainly different.

What can we do with the NAT information?

The simplest solution would be to shove those NAT fields into the firewall
event, thus it could carry this kind of information as well. The problem is
that, quite possibly, the set of these name-value pairs would be
ever-expanding.

The solution is to create multiple, distinct schamas and allow them to be
combined.

E.g. given the SIEM-like event format that combines IP tuple, a verdict and
NAT information, we create 3 schemas:
  * flowevt: to contain the base IP tuple
  * secevt: to contain the verdict
  * natevt: to contain the NAT tuple

Combining basically means the following:
  * the message will get 3 tags (identifying 3 schemas)
  * the different information will be filled into fields defined by either
    of the schemas

Storing messages
================

It is not strictly the scope of this document how the parsed messages will
get stored in persistent storage, however it is useful to know define what
we think are viable possibilities in representing the structured data that
patterndb produces.

  * per-schema SQL tables (slow but readable):
    * each message gets a unique ID (given by syslog-ng)
    * each schema gets its own SQL table, structure:  message ID + schema fields
    * query:
      * fetch by schema:
         SELECT * FROM schema;
      * fetch by a combination of 3 schemas:
         SELECT * FROM schema1, schema2, schema3 WHERE schema1.id = schema2.id AND schema2.id = schema3.id;

  * less generic SQL table (fast, but less readable)
    * a given combination of (possibly independent) schemas are stored in
      a single SQL table
    * each name-value pair gets a type-specific field (i1, i2, i3 for
      integers, s1, s2, s3 for strings)
    * schema names are stored in the table as a multi-attribute-field
    * query:
      * fetch by schema:
        SELECT * FROM table WHERE schema LIKE '%schema%'


Ruleset/rule organization
=========================

TBD

Identifying patterns
====================

ID vs. UUID discussion

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
