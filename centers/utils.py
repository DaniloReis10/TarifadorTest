def get_company_choices(org, company_set=None):
    choices = []
    if not org:
        return choices
    if company_set is None:
        company_set = org.company_set
    for company in company_set.active().only('organization', 'slug', 'name'):
        choices.append((company.slug, company.name))
    return choices


def get_center_choices(company):
    choices = []
    if not company:
        return choices
    for center in company.center_set.all():
        choices.append((center.id, center.name))
    return choices


def get_sector_choices(center):
    choices = []
    if not center:
        return choices
    for sector in center.sector_set.all():
        choices.append((sector.id, sector.name))
    return choices


def make_price(value):
    """
        Função para formatar preço no formato: 999.999,99
        Ex.:
            9999.9 -> 9.999,90
            200000 -> 200.000,00
    """
    value = f'{float(value):,.2f}'
    return value.replace(',', 'v').replace('.', ',').replace('v', '.')


def make_price_adm(value):
    """
        Função para formatar preço no formato: 999.999,99
        Ex.:
            9999.9 -> 9.999,90
            200000 -> 200.000,00
    """
    value = f'{float(value):,.4f}'
    return value.replace(',', 'v').replace('.', ',').replace('v', '.')
