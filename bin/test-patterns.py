#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
from lxml import etree
from subprocess import *
import sys
import codecs

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

if len(sys.argv) != 3:
    print "Usage:\ntest-patterns.py patterndb.xml pdbtool"
    sys.exit(1)

xml_doc = etree.parse(sys.argv[1])

def get_value(base, path):
    ret = None
    res = base.xpath(path)

    if len(res) == 1:
        ret = res[0]
    elif len(res) > 1:
        ret = []
        for r in res:
            try:
                ret.append(r.value)
            except AttributeError:
                ret.append(r.data)
    return ret

res = xml_doc.xpath('/patterndb/ruleset/rules/rule[count(examples/example)>0]')

ok = True

for p in res:
    values = {}
    rule_id = get_value(p, '@id')
    class_name = get_value(p, '@class')

    print "Testing %s" % rule_id

    for test in p.xpath('examples/example'):
        message = get_value(test, 'test_message/text()') or ""
        program = get_value(test, 'test_message/@program') or ""

        print " Example (%s) '%s'" % (program, message)

        pp = Popen([sys.argv[2], "match", "-p", sys.argv[1], "-M", message, "-P", program], stdout=PIPE)
        pp.wait()
        out = pp.stdout.read().strip().split('\n')
        exit_code = pp.returncode

        if exit_code != 0:
            print " No Match"
            ok = False
            continue

        for detail in out:
            (n,v) = detail.split('=', 1)
            values[n] = v

        if values['.classifier.rule_id'] != rule_id:
            print "  Rule_id does not match %s %s" % (values['.classifier.rule_id'], rule_id)
            ok = False
        if values['.classifier.class'] != class_name:
            print "  Class does not match %s %s" % (values['.classifier.class'], class_name)
            ok = False

        for v in test.xpath('test_values/test_value'):
            name = get_value(v, '@name')
            value = get_value(v, 'text()')

            try:
                if values[name] != value:
                    print "  Value mismatch (%s) value='%s', expected='%s'" % (name, values[name], value)
                    ok = False
            except KeyError:
                    print "  Excepted value is not available '%s'" % (name)
                    ok = False

sys.exit(not ok)
