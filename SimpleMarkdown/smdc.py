import json
import sys
import os
import shlex
# TODO: 实现
is_html_elem = lambda i:'a'<=i.lower()<='z' or '0' <= i <= '9' or i == '-'
def parse_html(html):
    res = {"element":'body','attribute':{},'body':[]}
    curr = [res]
    i = 0
    while i < len(html):
        if html[i] == '<':
            if html[i+1] == '/':
                check = curr[-1]['element']
                i += 2
                start = i
                if 'a'<=html[i].lower()<='z':
                    i+=1
                else:
                    sys.stderr.write(f"illegal tag start character '{html[i]}' at extension loading.\n")
                    sys.stderr.flush()
                    sys.exit(-1)
                while is_html_elem(html[i]):
                    i += 1
                if check != html[start:i]:
                    sys.stderr.write(f"unmatched html tag: expected </{check}>, got </{html[start:i]}> at extension loading.\n")
                    sys.stderr.flush()
                    sys.exit(-1)
                while html[i] in '\t\n\f\r ':
                    i += 1
                if html[i]!='>':
                    sys.stderr.write(f"illegal html tag.\n")
                    sys.stderr.flush()
                    sys.exit(-1)
                i+=1
                curr.pop()
            else:
                elem = {"element":None,'attribute':{},'body':[]}
                i += 1
                start = i
                if 'a'<=html[i].lower()<='z':
                    i+=1
                else:
                    sys.stderr.write(f"illegal tag start character '{html[i]}' at extension loading.\n")
                    sys.stderr.flush()
                    sys.exit(-1)
                while is_html_elem(html[i]):
                    i += 1
                elem['element'] = html[start:i]
                while html[i] not in '/>':
                    check = i
                    while html[i] in '\t\n\f\r ':
                        i += 1
                    start = i
                    if 'a'<=html[i].lower()<='z' or html[i] in '_:':
                        i+=1
                    else:
                        sys.stderr.write(f"illegal attribute start character '{html[i]}' at extension loading.\n")
                        sys.stderr.flush()
                        sys.exit(-1)
                    while is_html_elem(html[i]) or html[i] in '_:.':
                        i += 1
                    key = html[start:i].lower()
                    if key in elem:
                        sys.stderr.write(f"repeat attribute name '{key}' at extension loading.\n")
                        sys.stderr.flush()
                        sys.exit(-1)
                    while html[i] in '\t\n\f\r ':
                        i += 1
                    if html[i] == '=':
                        i += 1
                        while html[i] in '\t\n\f\r ':
                            i += 1
                        if html[i] == '"' or html[i] == "'":
                            temp = html[i]
                            i += 1
                            start = i
                            while html[i] != temp:
                                i += 1
                            elem['attribute'][key] = html[start:i]
                            i += 1
                        else:
                            start = i
                            while html[i] not in '\t\n\f\r >/':
                                i += 1
                            elem['attribute'][key] = html[start:i]
                    else:
                        elem['attribute'][key] = True
                    if i == check:
                        sys.stderr.write("parser unmoved for unknown reason (maybe illegal input) at extension loading.\n")
                        sys.stderr.flush()
                        sys.exit(-1)
                if html[i] == '>':
                    curr[-1]['body'].append(elem)
                    curr.append(elem)
                    i += 1
                elif html[i:i+2] == '/>':
                    curr[-1]['body'].append(elem)
                    i += 2
                else:
                    sys.stderr.write("illegal html tag.")
                    sys.stderr.flush()
                    sys.exit(-1)
        else:
            if curr[-1]['body'] and isinstance(curr[-1]['body'][-1],str):
                curr[-1]['body'][-1] += html[i]
            else:
                curr[-1]['body'].append(html[i])
            i += 1
    return res['body']
def extension_init(ext,typ=None):
    if typ is exec:
        res = ext.copy()
        res['function'] = parse_html(res['function'])
        return res
    else:
        res = {}
        for i,j in ext:
            res[i] = extension_init(j)
        return res
def getdefaultfile(target):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),target),'r',encoding='utf-8') as f:
        return f.read()
_style = 'default'
_styles = {
    "pure":"!pure",
    "default":getdefaultfile("default.css"),
    "document":getdefaultfile("document.css"),
    "tech":getdefaultfile("tech.css"),
}
_style = {"style":"built-in","data":_styles[_style]}
descript_style = '''# Styles
Use `-style=xxx` to set the style.
You can use a CSS file in the current working directory, or one of the program's built‑in styles.

## Built‑in Styles
- `default` — Normal markdown style.
- `pure` — No styling, raw HTML only.
- `document` — Document‑like style.
- `tech` — Technical‑focused style.'''
def parser_options(options,extensions):
    global _style
    encoding = 'utf-8'
    for i in options:
        if i.startswith('-load-extension='):
            with open(i[17:],"r",encoding='utf-8') as f:
                ext = json.load(f)
            if not isinstance(ext,dict):
                sys.stderr.write("Error: type not json object at extension parser.")
                sys.exit(-1)
            if "function" in ext and 'args' in ext:
                if i.endswith('.json'):
                    temp = i[:-5]
                elif ext.endswith('.ext'):
                    temp = i[:-4]
                elif ext.endswith('.lib'):
                    temp = i[:-4]
                else:
                    temp = i
                extensions[temp] = extension_init(ext,exec)
            elif not(extensions.keys() & ext.keys()):
                extensions.update(extension_init(ext))
        elif i.startswith('-style='):
            _style = i[7:]
            if _style not in _styles:
                with open(_style,'r',encoding='utf-8') as f:
                    _style = {"style":"user","data":f.read()}
            else:
                _style = {"style":"built-in","data":_styles[_style]}
        elif i.startswith('-help='):
            opt = i[6:]
            if opt == 'style':
                sys.stderr.write(descript_style)
        elif i.startswith('-make='):
            with open(i[6:],"r",encoding=encoding) as f:
                encoding = parser_options(shlex.split(f.read()),extensions)
    return encoding
def smd_to_html(smd,extensions):
    ESCAPE_TABLE = {'*','\\','`','^','#'}
    i = 0
    expect = []
    stack = []
    extra = []
    result = ''
    def text_handle():
        nonlocal i,smd,result
        if smd[i] == '\\':
            i += 1
            if i >= len(smd):
                sys.stderr.write("Error: parser over bound.\n")
                sys.stderr.flush()
                sys.exit(-1)
            if smd[i] in ESCAPE_TABLE:
                result += smd[i]
            else:
                sys.stderr.write(f"Warning: unexpected character {smd[i]}.\n")
                result += smd[i]
            i += 1
        else:
            result += smd[i]
            i += 1
    while i < len(smd):
        if expect and smd[i:i+len(expect[-1])] == expect[-1]:
            i += len(expect.pop())
            result += stack.pop()
            extra_temp = extra.pop()
            if extra_temp is not None:
                # extra_temp must be None or callable
                extra_temp(expect,stack,extra)
        elif smd[i] == '\n':
            curr = i+1
            while i < len(smd) and smd[i] in '\t\n\f\r ':
                i += 1
            if i < len(smd) and smd[i].isdigit():
                while smd[i].isdigit():
                    i += 1
                if smd[i] == '.':
                    result+='\n<ol>\n<li>'
                    while True:
                        i += 1
                        while i < len(smd) and smd[i] in '\t\n\f\r ':
                            i += 1
                        while i < len(smd) and smd[i] != '\n':
                            text_handle()
                        result+='</li>'
                        curr = i
                        while i < len(smd) and smd[i] in '\t\n\f\r ':
                            i += 1
                        if i >= len(smd) or not smd[i].isdigit():
                            result += '\n</ol>'
                            i = curr
                            break
                        while smd[i].isdigit():
                            i += 1
                        if smd[i] != '.':
                            result += '\n</ol>'
                            i = curr
                            break
                        result += '\n<li>'
                else:
                    i = curr
                    result += '\n'
            elif i < len(smd) and smd[i] == '-':
                result+='\n<ul>\n<li>'
                while True:
                    i += 1
                    while i < len(smd) and smd[i] in '\t\n\f\r ':
                        i += 1
                    while i < len(smd) and smd[i] != '\n':
                        text_handle()
                    result+='</li>'
                    curr = i
                    while i < len(smd) and smd[i] in '\t\n\f\r ':
                        i += 1
                    if i >= len(smd) or smd[i] != '-':
                        result += '\n</ul>'
                        i = curr
                        break
                    result += '\n<li>'
            else:
                i = curr
                result += '\n'
        elif smd[i:i+3] == '  \n':
            result += '<br/>'
            i += 2
        elif smd[i:i+2] in {'**','^^'}:
            result += '<strong>'
            expect.append(smd[i:i+2])
            stack.append('</strong>')
            extra.append(None)
            i += 2
        elif smd[i] in '*^':
            result += '<em>'
            expect.append(smd[i])
            stack.append('</em>')
            extra.append(None)
            i += 1
        elif smd[i] == '#':
            start = i
            while i < len(smd) and smd[i] == '#':
                i += 1
            start = i - start
            result += f'<h{start}>'
            while smd[i] in '\t\n\f\r ':
                i += 1
            while i < len(smd) and smd[i] != '\n':
                text_handle()
            result += f'</h{start}>'
        elif smd[i] == '`':
            result += '<code>'
            expect.append('`')
            stack.append('</code>')
            extra.append(None)
            i += 1
        else:
            text_handle()
    if stack:
        sys.stderr.write("Warning: unclosed labels.\n")
    # unclosed labels handle (unstandard behavior).
    while stack:
        result += stack.pop()
    return result
if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: python smdc.py source-file target-file [options]\n")
        sys.exit(-1)
    source = sys.argv[1]
    dest = sys.argv[2]
    extensions = {}
    encoding = parser_options(sys.argv[3:],extensions)
    if source == '-ignore' or dest == '-ignore':
        sys.exit(0)
    with open(source,"r",encoding=encoding) as f:
        smd_data = f.read()
    html = smd_to_html(smd_data,extensions)
    if _style['data'] != '!pure':
        html = f'<!DOCTYPE html>\n<html>\n\
            <head>\n\
            <title>{".".join(source.split(".")[:-1]) or source}</title>\n\
            <meta charset="UTF-8">\n\
            <style>\n{_style["data"]}\n</style>\
            </head>\n\
            <body>\n{html}\n</body>\n</html>'
    with open(dest,'w',encoding='utf-8') as f:
        f.write(html)
