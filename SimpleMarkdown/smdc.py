import json
import sys
import os
import shlex
def getdefaultfile(target):
    try:
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),target),'r',encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        sys.stderr.write(f"Warning: default file {target} not found.\n")
    except UnicodeDecodeError:
        sys.stderr.write(f"Warning: default file {target} are changed to unsupport encoding.\n")
_styles = {'pure':'!pure'}
try:
    with open('styles_index.json','r',encoding='utf-8') as f:
        _styles = json.load(f)
    for i in _styles:
        _styles[i] = eval(_styles[i])
except FileNotFoundError:
    sys.stderr.write("Styles index loading failed.\n")
except UnicodeDecodeError:
    sys.stderr.write("Style index has wrong encoding.\n")
if 'pure' not in _styles:
    _styles['pure'] = '!pure'
_style = {"style":"built-in","data":_styles.get("default",_styles['pure'])}
if not _style['data']:
    _style = {"style":"built-in","data":_styles['pure']}
descript_style = '''# Styles
Use `-style=xxx` to set the style.
You can use a CSS file in the current working directory, or one of the program's built‑in styles.

## Built‑in Styles
- `default` — Normal markdown style.
- `pure` — No styling, raw HTML only.
- `document` — Document‑like style.
- `tech` — Technical‑focused style.'''
file_clear_back = lambda source:".".join(source.split(".")[:-1]) or source
def parse_html(html):
    pass
def extension_init(ext,typ=None):
    if typ is exec:
        res = ext.copy()
        res['function'] = parse_html(res['function'])
        return res
    else:
        res = {}
        for i,j in ext.items():
            res[i] = extension_init(j,exec)
        return res
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
                temp = file_clear_back(i[17:])
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
HTML_SPECIAL = {
    '&':'&amp;',
    '>':'&gt;',
    '<':'&lt;',
    '"':'&quot;'
}
HTML_SPECIAL_TRANS = str.maketrans(HTML_SPECIAL)
html_string = lambda string:string.translate(HTML_SPECIAL_TRANS)
html_attribute_from_dict = lambda dct:' '.join(key if value is True else (f'{key}="{html_string(value)}"') for key,value in dct.items() if value not in (False, None))
def smd_to_html(smd,extensions,_rec_shift=0):
    ESCAPE_TABLE = {'*','\\','`','~','#','[',']','{','}','^','='}
    MAPPING_TABLE = {
        '\n':''
    }
    i = 0
    result = []
    stack = []
    expect = []
    extra = []
    smd = smd+'\n'
    smd_size = len(smd)-1
    def check_match(expect):
        if isinstance(expect,str):
            return len(expect)*smd.startswith(expect,i)
        for exp in expect:
            if exp is None:
                continue
            if smd.startswith(exp,i):
                return len(exp)
        return False
    def important_hint_decl(expect,stack,extra,result,cond):
        if cond == 2:
            if stack and stack[-1]['type'] == 'html_end' and stack[-1]['name'] == 'strong':
                nonlocal i
                i -= 1
                return
            result.pop()
            expect.append(['**','*'])
            stack.append({'type':'html_end','name':'em'})
            extra.append(important_hint_decl)
            expect.append('**')
            result.append({'type':'html_begin','name':'strong','attribute':{}})
            stack.append({'type':'html_end','name':'strong'})
            extra.append(None)
    while i < smd_size:
        cond = expect and check_match(expect[-1])
        if cond:
            i += cond
            expect.pop()
            result.append(stack.pop())
            decl = extra.pop()
            if decl is not None:
                decl(expect,stack,extra,result,cond)
        elif smd[i] == '\n':
            next_newline = smd.find('\n',i+1)
            if next_newline-i==4 and smd.startswith('\n---',i):
                result.append({'type':'string','data':'\n'})
                result.append({'type':'html_self_closed','name':'hr','attribute':{}})
                i=next_newline
            elif not any(not smd[i].isspace() for i in range(i+1,next_newline-1)):
                if result and result[0] != {'type':'html_begin','name':'p','attribute':{}}:
                    result.insert(0,{'type':'html_begin','name':'p','attribute':{}})
                result.append({'type':'html_end','name':'p'})
                result.append({'type':'string','data':'\n'})
                result.append({'type':'html_begin','name':'p','attribute':{}})
                i = next_newline
            elif next_newline-i>=4 and smd.startswith('\n```',i):
                if not result or result[-1]!={'type':'string','data':'\n'}:
                    result.append({'type':'string','data':'\n'})
                result.append({'type':'html_begin','name':'details','attribute':{'open':True}})
                result.append({'type':'string','data':'\n'})
                result.append({'type':'html_begin','name':'summary','attribute':{}})
                result.append({'type':'html_begin','name':'strong','attribute':{}})
                result.append({'type':'string','data':smd[i+4:next_newline] or 'code'})
                result.append({'type':'html_end','name':'strong'})
                result.append({'type':'html_end','name':'summary'})
                result.append({'type':'string','data':'\n'})
                result.append({'type':'html_begin','name':'pre','attribute':{}})
                result.append({'type':'html_begin','name':'code','attribute':({} if next_newline-i==4 else {'class':f'language-{smd[i+4:next_newline]}'})})
                start = next_newline+1
                i = next_newline
                while i < smd_size and not(next_newline-i>=4 and smd.startswith('\n```',i)):
                    if next_newline-i>=5 and smd.startswith('\n\\```',i):
                        result.append({'type':'string_range','range':[start,i]})
                        result.append({'type':'string','data':smd[i+2:next_newline]})
                        start=next_newline+1
                    i=next_newline
                    next_newline = smd.find('\n',i+1)
                result.append({'type':'string_range','range':[start,i]})
                result.append({'type':'string','data':'\n'})
                result.append({'type':'html_end','name':'code'})
                result.append({'type':'html_end','name':'pre'})
                result.append({'type':'string','data':'\n'})
                result.append({'type':'html_end','name':'details'})
                i = next_newline
            else:
                if not(result and((result[-1]['type'] == 'html_end' and result[-1]['name'] == 'code')or(result[-1]['type'] == 'html_self_closed' and result[-1]['name'] == 'hr'))):
                    result.append({'type':'html_self_closed','name':'br','attribute':{}})
                i += 1
            result.append({'type':'string','data':'\n'})
        elif smd.startswith('**',i):
            expect.append('**')
            result.append({'type':'html_begin','name':'strong','attribute':{}})
            stack.append({'type':'html_end','name':'strong'})
            extra.append(None)
            i+=2
        elif smd[i] == '*':
            expect.append(['**','*'])
            result.append({'type':'html_begin','name':'em','attribute':{}})
            stack.append({'type':'html_end','name':'em'})
            extra.append(important_hint_decl)
            i+=1
        elif smd[i] == '`':
            result.append({'type':'html_begin','name':'code','attribute':{}})
            while smd[i] != '`' and smd[i] != '\n':
                i += 1
            if smd[i] != '`':
                sys.stderr.write('unclosed single-line code.')
            result.append({'type':'html_end','name':'code'})
            i += 1
        elif smd.startswith('==',i):
            expect.append('==')
            result.append({'type':'html_begin','name':'mark','attribute':{}})
            stack.append({'type':'html_end','name':'mark'})
            extra.append(None)
            i+=2
        elif smd[i] == '~':
            expect.append('~')
            result.append({'type':'html_begin','name':'del','attribute':{}})
            stack.append({'type':'html_end','name':'del'})
            extra.append(None)
            i+=1
        else:
            if smd[i] == '\\':
                i += 1
                if smd[i] in ESCAPE_TABLE:
                    result.append({'type':'string','data':smd[i]})
                    i+=1
                elif smd[i] in MAPPING_TABLE:
                    result.append({'type':'string','data':MAPPING_TABLE[smd[i]]})
                    i+=1
                elif smd[i] == 'u':
                    data = smd[i+1:i+5]
                    if any(i not in '0123456789abcdefABCDEF' for i in data):
                        sys.stderr.write(f'Error: wrong unicode hex "{data}".')
                    else:
                        data = eval(f'"\\u{data}"')
                        result.append({'type':'string','data':data})
                    i += 5
                elif smd[i] == 'U':
                    result.append({'type':'string','data':smd[i]})
                continue
            if result and result[-1]['type'] == 'string_range':
                result[-1]['range'][1] += 1
            else:
                result.append({'type':'string_range','range':[i,i+1]})
            i += 1 #TODO:实现该分支
    if result and result[0] == {'type':'html_begin','name':'p','attribute':{}}:
        result.append({'type':'html_end','name':'p'})
    for i,j in enumerate(result):
        if j['type'] == 'string':
            result[i] = html_string(j['data'])
        elif j['type'] == 'html_begin':
            result[i] = f'<{j["name"]} {html_attribute_from_dict(j["attribute"])}>' if j['attribute'] else f'<{j["name"]}>'
        elif j['type'] == 'html_end':
            result[i] = f'</{j["name"]}>'
        elif j['type'] == 'html_self_closed':
            result[i] = f'<{j["name"]} {html_attribute_from_dict(j["attribute"])}/>' if j['attribute'] else f'<{j["name"]}/>'
        elif j['type'] == 'string_range':
            result[i] = html_string(smd[j['range'][0]:j['range'][1]])
    return ''.join(result)
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
            <title>{file_clear_back(source)}</title>\n\
            <meta charset="UTF-8">\n\
            <style>\n{_style["data"]}\n</style>\
            </head>\n\
            <body>\n{html}\n</body>\n</html>'
    with open(dest,'w',encoding='utf-8') as f:
        f.write(html)
