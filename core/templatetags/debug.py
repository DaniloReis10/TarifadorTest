from django import template

register = template.Library()


@register.simple_tag
def pdb(data):
    print(dir(data))
    import ipdb; ipdb.set_trace()
