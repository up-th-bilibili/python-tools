import decimal
import fractions
import numbers
import sys
try:
    import numpy
except ImportError:
    numpy = False
    sys.stderr.write('Warning: can\'t use numpy.\n')
big = '京垓秭穰沟涧正载极'
_small2cn = lambda prefix,left,right:prefix+chinese_number(left)+"点"+''.join(right)
_number_to_chinese_string_storege = ([],[])
def register_type(typ,behavier):
    if typ in _number_to_chinese_string_storege[0]:
        _number_to_chinese_string_storege[1][_number_to_chinese_string_storege[0].index(typ)] = behavier
    else:
        _number_to_chinese_string_storege[0].append(typ)
        _number_to_chinese_string_storege[1].append(behavier)
def getregisted(typ):
    if typ in _number_to_chinese_string_storege[0]:
        return _number_to_chinese_string_storege[1][_number_to_chinese_string_storege[0].index(typ)]
    raise TypeError('unregisted type.')
def are_registed(typ):
    return typ in _number_to_chinese_string_storege[0]
def _decsm2str(dec):
    dt = dec.as_tuple()
    if (dt[2]+len(dt[1])) > len(big)*4+16:
        raise ValueError(f'number size are greater than 10**{len(big)*4+16} or smaller than -(10**{len(big)*4+16}).')
    hi,lo = '',''
    if (dt[2]+len(dt[1]))<0:
        hi = '0'
        lo = '0'*(-dt[2]-len(dt[1]))
    for i in range(len(dt[1])):
        if i+dt[2]<0:
            hi += str(dt[1][i])
        else:
            lo += str(dt[1][i])
    i += 1
    while i<(dt[2]+len(dt[1])):
        hi += '0'
        i += 1
    return _small2cn('负'*dt[0],hi,lo)
def _int2cn(number):
    if number == '0':
        return '零'
    cl = 0
    while cl < len(number) and number[cl] == '0':
        cl += 1
    if cl and cl-1:
        number = number[cl-1:]
    if len(number) > len(big)*4+16:
        raise ValueError(f'number size are greater than 10**{len(big)*4+16} or smaller than -(10**{len(big)*4-16}).')
    if len(number) > 16:
        lower = (lambda i:_int2cn(i) if i !='0'*16 else '')(number[-16:])
        higher = [number[i*(i>0):i+4] for i in range(len(number)-4,-4,-4)]
        higher = list(map(_int2cn,higher))
        for i in range(len(higher)):
            if not higher[i] == '零':
                higher[i] = higher[i]+big[i]
            elif i and higher[i-1] == '零':
                higher[i] = ''
        higher.reverse()
        return ''.join(higher)+lower
    if len(number) > 4:
        return (lambda i,j:_int2cn(i[:j*-4])+'万亿'[j-1]+(_int2cn(i[j*-4:]) if i[j*-4:] !='0'*j*4 else ''))(number,((len(number)+7)>>3))
    def setting(res,idx,i,table):
        if idx >= 0:
            dgt = '0123456789'.index(number[idx])
            if (dgt or ((not res) or res[-1] != '零')) and ((dgt-1) or (i!=2 or idx)):
                res.append(table[dgt])
            if i > 1 and dgt:
                res.append('十百千'[i-2])
    res = []
    for i in range(4,0,-1):
        setting(res,len(number)-i,i,'零一两三四五六七八九' if i == 4 else '零一二三四五六七八九')
    while res and res[-1] == '零':
        res.pop()
    return ''.join(res)
def _rtn2cn(number):
    try:
        if not number.numerator:
            return '零'
        den = number.denominator
        num = number.numerator
        if abs(den) == 1:
            return chinese_number(num*den)
        if num < 0:
            num = num*-1
            den = den*-1
    except (TypeError,ValueError,AttributeError,NotImplementedError):
        den = number.denominator
        num = number.numerator
    return chinese_number(den)+"分之"+chinese_number(num)
def chinese_number(number):
    if isinstance(number,bool):
        return '假真'[number]
    if isinstance(number,numbers.Integral) or (numpy and isinstance(number,numpy.integer)):
        number = str(number)
    if isinstance(number,(bytes,bytearray)):
        number = number.decode()
    if isinstance(number,numbers.Rational):
        return _rtn2cn(number)
    if isinstance(number,numbers.Real):
        if isinstance(number,float):
            number = repr(number)
        elif hasattr(number, "numerator") and hasattr(number, "denominator"):
            return _rtn2cn(number)
        elif are_registed(type(number)):
            number = getregisted(type(number))(number)
        elif hasattr(number,'__decimal__'):
            number = number.__decimal__()
        elif hasattr(number,'__float__'):
            number = number.__float__().__repr__()
        raise TypeError
    if isinstance(number,decimal.Decimal):
        return _decsm2str(number)
    if not isinstance(number,str):
        raise TypeError
    if not number:
        raise ValueError('Empty string.')
    prefix = ''
    if number[0] == '-':
        number = number[1:]
        prefix = '负'
    elif number[0] == '+':
        number = number[1:]
        prefix = '正'
    cl = 0
    while cl >= len(number) - 2 and number[cl] == '0':
        cl += 1
    number = number[cl:]
    if '/' in number:
        number = number.split('/')
        if len(number) != 2:
            raise ValueError('Incorrect fraction format. Too many slashs.')
        return prefix+chinese_number(number[1])+"分之"+chinese_number(number[0])
    if '.' in number:
        number = number.split('.')
        if len(number) != 2:
            raise ValueError('Incorrect decimal format. Too many dot.')
        for i in number:
            if not('0' <= i <= '9'):
                raise ValueError('Inlegal DEC number.')
        for i in range(10):
            number[1] = number[1].replace(chr(i+48),'零一二三四五六七八九'[i])
        return _small2cn(prefix,number[0],number[1])
    for i in number:
        if not('0' <= i <= '9'):
            raise ValueError('Inlegal DEC number.')
    return _int2cn(number)
if __name__ == '__main__':
    assert chinese_number('12345') == '一万两千三百四十五'
    assert chinese_number(10) == '十'
    assert chinese_number('10010') == '一万零一十'
    assert chinese_number('3.14159265358979323846264338') == '三点一四一五九二六五三五八九七九三二三八四六二六四三三八'
    try:
        chinese_number('1/2/3')
        assert False
    except ValueError:
        assert True
    try:
        chinese_number(None)
        assert False
    except TypeError:
        assert True
