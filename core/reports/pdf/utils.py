# project
from phonecalls.constants import VC1, VC2, VC3, LOCAL, LDN, LDI


def get_tj_calltype_title(calltype):
    if calltype == VC1:
        return 'Operação de acesso externo à rede \npara telefones móveis local (VC1)'
    elif calltype == VC2:
        return 'Operação de acesso externo à rede \npara telefones móveis na mesma região (VC2)'
    elif calltype == VC3:
        return 'Operação de acesso externo à rede \npara telefones móveis em outra área (VC3)'
    elif calltype == LOCAL:
        return 'Operação de acesso externo à rede \npara telefones fixo para ligações locais'
    elif calltype == LDN:
        return 'Operação de acesso externo à rede \npara ligações de longa distância Nacional para Fixo'
    elif calltype == LDI:
        return 'Operação de acesso externo à rede \npara ligações internacionais'
