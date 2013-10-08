#coding: utf-8

__doc__ = """
This script place extracted unstructured .cab files properly according to their .manifest
Useful when analyzing Microsoft .msu files.

2010-09-18
"""

import os, sys, re
from xml.dom.minidom import parseString

target_dir = r"D:\downloads\IE9beta\tmp\IE9-neutral.Downloaded\Windows6.1-KB982861-x86"

def xml2attr(str_xml):
    """
    return a `dict` of attributes from a line of xml `str`
    
    >>> xml2attr(r'  <file name="urlmon.dll" destinationPath="$(runtime.system32)\" sourceName="urlmon.dll" sourcePath=".\" importPath="$(build.nttree)\"></file>')
    {u'sourceName': 'urlmon.dll', u'sourcePath': '.\\', u'destinationPath': '$(runtime.system32)\\', u'name': 'urlmon.dll', u'importPath': '$(build.nttree)\\'}
    
    """
    r={}
    r=dict(parseString(str_xml).firstChild.attributes)
    for x in r:
        r[x]=str(r[x].value)
    return r

def manifest2path(manifest_io):
    r=[]
    l=re.findall(r'<file name.*>', manifest_io.read())
    for i in range(len(l)):
        l_attr = xml2attr(l[i]+'</file>') #closing xml node
        r.append( (l_attr['sourcePath']+l_attr['sourceName'], l_attr.get('destinationPath', '')+l_attr['name']) )
    return r


def extract_cab(cab_path):
    cab_path = os.path.abspath(cab_path)
    cab_path_1 = cab_path+'_tmp'
    cab_path_2 = cab_path[:-4]
    os.system('mkdir "' + cab_path_1 + '"')
    os.system(r'expand -F:* "' + cab_path + '" "' + cab_path_1 + '"')
    os.system('mkdir "' + cab_path[:-4] + '"')
    manifests = filter(os.path.isdir, map(lambda x:os.path.join(cab_path_1, x), os.listdir(cab_path_1)))
    moves = []
    for x in manifests:
        r=manifest2path(open(x+'.manifest'))
        for y in r:
            os.system('echo F|xcopy "' + os.path.abspath(os.path.join(cab_path_1, x, y[0])) + '" "' + \
                os.path.abspath(os.path.join(cab_path_2, y[1])) + '" /Y')
    
if '__main__' == __name__:
    if len(sys.argv)>1:
        extract_cab(sys.argv[1])
    else:
        print __doc__