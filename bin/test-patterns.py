#!/usr/bin/python

import sys, os
sys.path.append('/usr/lib/python%s/site-packages/oldxml' % sys.version[:3])

import xml
from xml.dom import ext
from xml.dom.ext.reader import PyExpat
from xml import xpath
from xml.dom.minidom import *
from subprocess import *

if len(sys.argv) != 3:
    print "Usage:\ntest-patterns.py patterndb.xml pdbtool"
    sys.exit(1)

reader = PyExpat.Reader()
xml_doc = reader.fromUri(sys.argv[1])

xml_doc = parse(sys.argv[1])

def get_value(base, path):
    ret = None
    res = xpath.Evaluate(path, base)

    if len(res) == 1:
        try:
            ret = res[0].value
        except AttributeError:
            ret = res[0].data
    elif len(res) > 1:
        ret = []
        for r in res:
            try:
                ret.append(r.value)
            except AttributeError:
                ret.append(r.data)
            
    return ret

res = xpath.Evaluate('/patterndb/ruleset/rules/rule[count(examples/example)>0]', xml_doc.documentElement)

ok = True

for p in res:
    values = {}
    rule_id = get_value(p, '@id')
    class_name = get_value(p, '@class')

    print "Testing %s" % rule_id

    for test in xpath.Evaluate('examples/example', p):
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

        for v in xpath.Evaluate('test_values/test_value', test):
            name = get_value(v, '@name')
            value = get_value(v, 'text()')

            try:
                if values[name] != value:
                    print "  Value missmatch (%s) value='%s', expected='%s'" % (name, values[name], value)
                    ok = False
            except KeyError:
                    print "  Excepted value is not available '%s'" % (name)
                    ok = False


sys.exit(not ok)
