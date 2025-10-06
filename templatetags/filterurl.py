from django import template 
register = template.Library()

from findyourshoe.models import Foot


@register.simple_tag 
def generate_filter_url(form):
    url = '?'
    data = {}
    
    for group in form:
        for field in group:
            obj = dict(field.data)
                
            if obj['name'] == 'model__prices':
                for subobj in obj['subwidgets']:
                    subobj = dict(subobj)
                    if subobj['name'] not in data:
                        data[subobj['name']] = []
                    value = subobj['value']
                    data[subobj['name']].append(value)
                    
            elif 'type' in obj and obj['type'] == 'checkbox' and obj['selected'] == True:
                if obj['name'] not in data:
                    data[obj['name']] = []
                if obj['name'] != 'brands':
                    value = str(obj['value'])
                    data[obj['name']].append(int(value))
                else:
                    data[obj['name']].append(obj['value'])
                
    for key in data:
        for value in (data[key]):
            if value == None:
                value = ''
            url = url + f'{key}={value}&'
            
    return url


@register.simple_tag
def sort_set(form):
    obj = dict(form.data)
    sort = ''
    if 'sort' in obj:
        sort = obj['sort'][0]
    return sort


@register.simple_tag
def get_foot(session):
    print(f"SESSION: ", session)
    foot = {
        'length': session['foot']['length'],
        'width': session['foot']['width'],
        'circumference': session['foot']['circumference']
    }
    return foot


@register.simple_tag
def has_foot(request):
    try:
        foot = Foot.objects.get(user=request.user)
        return 'My results'
    except:
        pass