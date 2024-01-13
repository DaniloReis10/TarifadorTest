IN_CALL = 1
IN_ABANDONED = 2
OUT_CALL = 3
OUT_ABANDONED = 4
INTERNAL = 5
INTERNAL_ABANDONED = 6
CONFERENCE = 7
TRANSFER = 8
BUSY = 9
VACANT = 10
UNCLASSIFIED = 11

PABX = {
    IN_CALL:            [7, 71, 167],
    IN_ABANDONED:       [23, 87],
    OUT_CALL:           [17, 19],
    OUT_ABANDONED:      [28],
    INTERNAL:           [8, 10, 40, 72, 168],
    INTERNAL_ABANDONED: [25, 89],
    CONFERENCE:         [9, 73],
    TRANSFER:           [15, 47, 79, 175],
    BUSY:               [29, 125],
    VACANT:             [30]
}

PABX_CHOICES = [
    (IN_CALL,            'Chamada recebida'),
    (IN_ABANDONED,       'Chamada recebida abandonada'),
    (OUT_CALL,           'Chamada externa'),
    (OUT_ABANDONED,      'Chamada externa abandonada'),
    (INTERNAL,           'Chamada interna'),
    (INTERNAL_ABANDONED, 'Chamada interna abandonada'),
    (CONFERENCE,         'Conferência'),
    (TRANSFER,           'Chamada transferida'),
    (BUSY,               'Número ocupado'),
    (VACANT,             'Número não existe'),
    (UNCLASSIFIED,       'Não classificado')
]

OUTBOUND = '1'
OUTBOUND_CHARGED = '2'
INBOUND = '3'
ALL = '4'

BOUND_CHOICES = [
    (OUTBOUND,         'Originadas'),
    (OUTBOUND_CHARGED, 'Originadas Cobradas'),
    (INBOUND,          'Recebidas'),
    (ALL,              'Todas')
]

VC1 = 1
VC2 = 2
VC3 = 3
LOCAL = 4
LDN = 5
LDI = 6
FREE = 7
UNKNOWN = 8
ADDEDVALUE = 9

CALLTYPE_CHOICES = [
    (VC1,        'Ligações para celular local (VC1)'),
    (VC2,        'Ligações para celular na mesma região (VC2)'),
    (VC3,        'Ligações para celular em outra área (VC3)'),
    (LOCAL,      'Ligações locais para fixo'),
    (LDN,        'Ligações DDD para fixo'),
    (LDI,        'Ligação internacional'),
    (FREE,       'Grátis'),
    (UNKNOWN,    'Desconhecido'),
    (ADDEDVALUE, 'AddedValue')  # TODO
]

UST = 1
KM = 2

OTHERTYPE_CHOICES =[
    (UST, 'Serviços especializados de comunicação VoIP por demanda '),
    (KM, 'Serviço de deslocamento para prestar serviço fora da Região Metropolitana de Fortaleza')
]

REPORT_CALLTYPE_MAP = {
    LOCAL: 'Local Fixo-Fixo Extragrupo',
    VC1:   'Local Fixo-Móvel (VC1)',
    VC2:   'LDN-VC2 Fixo-Móvel',
    VC3:   'LDN-VC3 Fixo-Móvel',
    LDN:   'LDN-fixo/fixo-D1/D2/D3/D4',
    LDI:   'LDI'
}

CRITICAL_SERVICE = 1
PUBLIC_SERVICE = 2
SUPPORT_SERVICE = 3
WIRELINE_PROVIDERS = 4
MOBILE_PROVIDERS = 5
PAY_TV_PROVIDERS = 6
OTHER_SERVICE = 7
UNKNOWN_SERVICE = 8

SERVICE_CHOICES = [
    (CRITICAL_SERVICE,   'Serviços Públicos de Emergência'),
    (PUBLIC_SERVICE,     'Serviços de Utilidade Pública'),
    (SUPPORT_SERVICE,    'Serviços de Apoio a Telefonia'),
    (WIRELINE_PROVIDERS, 'Prestadoras de Telefonia Fixa'),
    (MOBILE_PROVIDERS,   'Prestadoras de Telefonia Celular'),
    (PAY_TV_PROVIDERS,   'Prestadoras de TV por Assinatura'),
    (OTHER_SERVICE,      'Outro Serviço'),
    (UNKNOWN_SERVICE,    'Serviço Desconhecido')
]

CRITICAL_NUMBERS = {
    '100': 'Secretaria dos Direitos Humanos',
    '128': 'Serviços de Emergência no Mercosul',
    '129': 'Defensoria Pública',
    '153': 'Guarda Municipal',
    '156': 'PMF - Descarte Lixo',
    '180': 'Central de Atendimento à Mulher',
    # '180': 'Delegacia de Atendimento à Mulher',
    '181': 'Disque Denúncia',
    '185': 'Marinha – Emergências Marítimas / Fluviais',
    '188': 'Centro Val. Vida',
    '190': 'Polícia Militar',
    '191': 'Polícia Rodoviária Federal',
    '192': 'Remoção de Doentes (Ambulâncias - SAMU)',
    '193': 'Corpo de Bombeiros',
    '194': 'Polícia Federal',
    '197': 'Polícia Civil',
    '198': 'Polícia Rodoviária Estadual',
    '199': 'Defesa Civil'
}

PUBLIC_NUMBERS = {
    '115':  'Prestadora de Água e Esgoto',
    '116':  'Prestadora de Energia Elétrica',
    '117':  'Prestadora de Gás Canalizado',
    '118':  'Transporte Público',
    '123':  'Child Helpline',
    '127':  'Ministério Público',
    '130':  'Hora Certa',
    '132':  'Assistência a Dependentes Químicos',
    '1332': 'Anatel',
    '134':  'Despertador Automático',
    '135':  'Ministério da Previdência Social',
    '136':  'Sistema Único de Saúde',
    '138':  'Governo Federal',
    '141':  'Centro de Valorização da Vida',
    '145':  'Banco Central do Brasil',
    '146':  'Receita Federal do Brasil',
    '148':  'Justiça Eleitoral',
    '150':  'Vigilância Sanitária',
    '151':  'Procon',
    '152':  'Ibama',
    '154':  'Detran',
    '155':  'Serviço Estadual',
    '157':  'Informações sobre emprego (SINE)',
    '158':  'Delegacias Regionais do Trabalho',
    '159':  'Poder Judiciário',
    '16':   'Administração Pública Área de Saúde',
    '161':  'Disque Denúncia Atos do Governo',
    '162':  'Ouvidorias Públicas',
    '165':  'Disque Idoso',
    '166':  'ANTT',
    '167':  'Aneel',
    '168':  'Petrobrás (Incidentes)',
    '1746': 'Prefeitura do Rio de Janeiro'
}

SUPPORT_NUMBERS = {
    '102': 'Código de Acesso ao Assinante',
    '142': 'Central de Intermediação de Comunicação Telefônica para pessoas com deficiência '
           'auditiva'
}

WIRELINE_NUMBERS = {
    '10312': 'CTBC TELECOM',
    '10313': 'FONAR',
    '10314': 'BRASIL TELECOM/OI',
    '10315': 'TELEFONICA/VIVO',
    '10317': 'TRANSIT',
    '10318': 'SPIN',
    '10321': 'EMBRATEL',
    '10324': 'DIALDATA',
    '10325': 'GVT',
    '10326': 'IDT',
    '10327': 'AEROTECH',
    '10329': 'T-LESTE',
    '10331': 'OI',
    '10332': 'CONVERGIA',
    '10334': 'ETML',
    '10335': 'EASYTONE',
    '10336': 'DSLI VOX',
    '10337': 'GOLDEN LINE',
    '10338': 'TELECOM SOUTH AMERICA',
    '10339': 'ESPELHINHOS',
    '10341': 'TIM',
    '10342': 'GT GROUP',
    '10343': 'SERCOMTEL',
    '10345': 'GLOBAL CROSSING',
    '10346': 'HOJE',
    '10347': 'BT COMMUNICATIONS',
    '10349': 'CAMBRIDGE',
    '10353': 'OSTARA',
    '10356': 'ESPAS',
    '10357': 'ITA VOICE',
    '10358': 'STELLAR',
    '10361': 'NEXUS',
    '10362': 'OPTION',
    '10363': 'HELLO BRAZIL',
    '10365': 'CGB VOIP',
    '10371': 'DOLLARPHONE',
    '10372': 'LOCAWEB',
    '10373': 'PLUMIUM',
    '10374': 'CABO SERVICOS',
    '10375': 'VIPWAY',
    '10376': 'SMART VOIP',
    '10381': 'DATORA',
    '10385': 'AMERICA NET',
    '10387': 'HIT TELECOM',
    '10389': 'KONECTA',
    '10391': 'FALKLAND',
    '10396': 'AMIGO TELECOM.',
    '10398': 'ALPHA NOBILIS'
}

MOBILE_NUMBERS = {
    '1050': 'NEXTEL',
    '1051': 'SERCOMTEL',
    '1052': 'CLARO',
    '1053': '14 BRASIL TELECOM',
    '1055': 'CTBC',
    '1056': 'TIM',
    '1057': 'OI',
    '1058': 'VIVO'
}

PAY_TV_NUMBERS = {
    '10600': 'CABO TELECOM',
    '10601': 'BVCi - BOA VISTA TV A CABO',
    '10603': 'SIM TV',
    '10604': 'FLEXTV',
    '10606': 'TVC - TV CABO MOSSORÓ',
    '10607': 'VIAMAX DIGITAL',
    '10611': 'SKY BRASIL',
    '10612': 'CTBC - TV',
    '10613': 'ITAPEMA TV A CABO',
    '10615': 'TELEFONICA TV DIGITAL - BRASIL',
    '10616': 'ORM CABO',
    '10617': 'NET - CATANDUVA/SP',
    '10618': 'TV A CABO - CABONNET',
    '10620': 'TV A CABO SÃO PAULO LTDA',
    '10621': 'NET',
    '10624': 'NET - ANGRA DOS REIS/RJ',
    '10630': 'SUPERTV',
    '10631': 'OI - TV',
    '10637': 'TV UNIÃO - CANAL 56',
    '10643': 'SMTV DIGITAL (SERCOMTEL)',
    '10647': 'TRANSCABO TV - JARAGUÁ/SC',
    '10648': 'TRANSCABO TV - CONCÓRDIA/SC',
    '10649': 'TRANSCABO -  LAGES/SC',
    '10650': 'TRANSCABO - JOAÇABA/SC',
    '10652': 'TVA - BALNEARIO CAMBORIU/SC',
    '10653': 'VIA CABO',
    '10655': 'DTHI - BRASIL',
    '10660': 'NET - Fortaleza/CE NET - BARBALHA/CE NET - CARIRIAÇU/CE NET - CRATO/CE NET - '
             'JUAZEIRO DO NORTE/CE NET - MISSÃO VELHA/CE NET - SOBRAL/CE NET - CAUCAIA/CE',
    '10661': 'ITSA',
    '10666': 'TV CABO SÃO PAULO - CORONEL BARROS/RS TV CABO SÃO PAULO - ENTRE-IJUIS/RS TV CABO '
             'SÃO PAULO - IJUÍ/RS TV CABO SÃO PAULO - SANTA ROSA/RS TV CABO SÃO PAULO - SANTO '
             'ÂNGELO/RS SAT TV A CABO - PERUÍBE/SP',
    '10673': 'NET - BARRO PRETO/BA NET - BUERAREMA/BA NET - CANDEIAS/BA NET - FEIRA DE '
             'SANTANA/BA NET - ILHÉUS/BA NET - ITABUNA/BA NET - ITAJUÍPE/BA NET - ITAPARICA/BA '
             'NET - ITAPE/BA NET - JUAZEIRO/BA NET - LAURO DE FREITAS/BA NET - MADRE DE DEUS/BA '
             'NET - PETROLINA/PE NET - SALINAS DA MARGARIDA/BA NET - SALVADOR/BA NET - SIMÕES '
             'FILHO/BA NET - URUÇUCA/BA NET - VERA CRUZ/BA NET - VITORIA DA CONQUISTA/BA	 106 '
             '+ 71NET - UBATUBA/SP NET - CARAGUATATUBA/SP',
    '10677': 'TVA',
    '10687': 'NET - SÃO JOSÉ/SC',
    '10688': 'JET',
    '10691': 'TVC - NET',
    '10693': 'NET - OSASCO/SP',
    '10695': 'NET - UMUARAMA/PR',
    '10699': 'CLARO TV'
}

PREFIX = {
    '0300': 'Chamadas com tarifa compartilhada',
    '0500': 'Chamadas para doação a instituições de utilidade pública',
    '0800': 'Chamada Grátis - 0800',
    '0900': 'Serviço de valor adicionado',
    '90':   'Chamada a cobrar',
    '9090': 'Chamada a cobrar local'
}

DDD = {
    '11': {'city': 'São Paulo/Guarulhos//Mogi das Cruzes/Suzano/São Bernardo do Campo/Santo '
                   'André/Osasco/Barueri/Taboão da Serra/Jundiaí/Atibaia/Bragança Paulista',
           'state': 'São Paulo'},
    '12': {'city': 'São José dos Campos/Taubaté/Guaratinguetá/Pindamonhangaba/Campos do '
                   'Jordão/Caraguatatuba/Ubatuba',
           'state': 'São Paulo'},
    '13': {'city': 'Santos/São Vicente/Praia Grande/Cubatão/Itanhaém/Peruíbe/Registro',
           'state': 'São Paulo'},
    '14': {'city': 'Bauru/Jaú/Marília/Lençóis Paulista/Lins/Botucatu/Ourinhos/Avaré',
           'state': 'São Paulo'},
    '15': {'city': 'Sorocaba/Itapetininga/Itapeva',
           'state': 'São Paulo'},
    '16': {'city': 'Ribeirão Preto/Franca/São Carlos',
           'state': 'São Paulo'},
    '17': {'city': 'São José do Rio Preto/Barretos/Fernandópolis',
           'state': 'São Paulo'},
    '18': {'city': 'Presidente Prudente/Araçatuba/Birigui/Assis',
           'state': 'São Paulo'},
    '19': {'city': 'Campinas/Piracicaba/Limeira/Americana/Sumaré',
           'state': 'São Paulo'},
    '21': {'city': 'Rio de Janeiro/Niterói/São Gonçalo/Duque de Caxias/Nova Iguaçu',
           'state': 'Rio de Janeiro'},
    '22': {'city': 'Campos dos Goytacazes/Macaé/Cabo Frio/Nova Friburgo',
           'state': 'Rio de Janeiro'},
    '24': {'city': 'Volta Redonda/Barra Mansa/Petrópolis',
           'state': 'Rio de Janeiro'},
    '27': {'city': 'Vitória/Serra/Vila Velha/Linhares',
           'state': 'Espírito Santo'},
    '28': {'city': 'Cachoeiro de Itapemirim',
           'state': 'Espírito Santo'},
    '31': {'city': 'Belo Horizonte/Contagem/Betim',
           'state': 'Minas Gerais'},
    '32': {'city': 'Juiz de Fora/Barbacena',
           'state': 'Minas Gerais'},
    '33': {'city': 'Governador Valadares/Teófilo Otoni/Caratinga/Manhuaçu',
           'state': 'Minas Gerais'},
    '34': {'city': 'Uberlândia/Uberaba/Araguari/Araxá',
           'state': 'Minas Gerais'},
    '35': {'city': 'Passos/Poços de Caldas/Pouso Alegre/Varginha/Itajubá',
           'state': 'Minas Gerais'},
    '37': {'city': 'Divinópolis/Itaúna/Formiga/Capitólio',
           'state': 'Minas Gerais'},
    '38': {'city': 'Montes Claros/Serro/Januária',
           'state': 'Minas Gerais'},
    '41': {'city': 'Curitiba/São José dos Pinhais/Paranaguá',
           'state': 'Paraná'},
    '42': {'city': 'Porto União',
           'state': 'Santa Catarina'},
    '43': {'city': 'Londrina/Arapongas/Assaí/Jacarezinho/Jandaia do Sul',
           'state': 'Paraná'},
    '44': {'city': 'Maringá/Campo Mourão/Astorga',
           'state': 'Paraná'},
    '45': {'city': 'Cascavel/Toledo/Medianeira',
           'state': 'Paraná'},
    '46': {'city': 'Francisco Beltrão/Pato Branco/Palmas/Pinhão',
           'state': 'Paraná'},
    '47': {'city': 'Joinville/Blumenau/Balneário Camboriú',
           'state': 'Santa Catarina'},
    '48': {'city': 'Florianópolis/São José/Criciúma',
           'state': 'Santa Catarina'},
    '49': {'city': 'Chapecó/Lages/Concórdia',
           'state': 'Santa Catarina'},
    '51': {'city': 'Porto Alegre/Canoas/Esteio/Torres',
           'state': 'Rio Grande do Sul'},
    '53': {'city': 'Pelotas/Rio Grande/Bagé/Aceguá/Chuí',
           'state': 'Rio Grande do Sul'},
    '54': {'city': 'Caxias do Sul/Passo Fundo/Vacaria/Veranópolis',
           'state': 'Rio Grande do Sul'},
    '55': {'city': 'Santa Maria/Uruguaiana/Santana do Livramento',
           'state': 'Rio Grande do Sul'},
    '61': {'city': 'Brasília, Luziânia/Valparaíso de Goiás/Formosa',
           'state': 'Distrito Federal/Goiás'},
    '62': {'city': 'Goiânia/Anápolis/Goiás/Pirenópolis',
           'state': 'Goiás'},
    '63': {'city': 'Palmas/Araguaína/Gurupi',
           'state': 'Tocantins'},
    '64': {'city': 'Rio Verde/Jataí/Caldas Novas/Catalão',
           'state': 'Goiás'},
    '65': {'city': 'Cuiabá/Várzea Grande/Cáceres',
           'state': 'Mato Grosso'},
    '66': {'city': 'Rondonópolis/Sinop/Barra do Garças',
           'state': 'Mato Grosso'},
    '67': {'city': 'Campo Grande/Dourados/Corumbá/Três Lagoas',
           'state': 'Mato Grosso do Sul'},
    '68': {'city': 'Rio Branco/Cruzeiro do Sul',
           'state': 'Acre'},
    '69': {'city': 'Porto Velho/Ji-Paraná/Ariquemes',
           'state': 'Rondônia'},
    '71': {'city': 'Salvador/Camaçari/Lauro de Freitas',
           'state': 'Bahia'},
    '73': {'city': 'Itabuna/Ilhéus/Porto Seguro/Jequié',
           'state': 'Bahia'},
    '74': {'city': 'Juazeiro/Xique-Xique',
           'state': 'Bahia'},
    '75': {'city': 'Feira de Santana/Alagoinhas/Lençóis',
           'state': 'Bahia'},
    '77': {'city': 'Vitória da Conquista/Barreiras/Correntina',
           'state': 'Bahia'},
    '79': {'city': 'Aracaju/Lagarto/Itabaiana',
           'state': 'Sergipe'},
    '81': {'city': 'Recife/Jaboatão dos Guararapes/Goiana/Gravatá/Paulista',
           'state': 'Pernambuco'},
    '82': {'city': 'Maceió/Arapiraca/Palmeira dos Índios/Penedo',
           'state': 'Alagoas'},
    '83': {'city': 'João Pessoa/Campina Grande/Patos/Sousa/Cajazeiras',
           'state': 'Paraíba'},
    '84': {'city': 'Natal/Mossoró/Parnamirim/Caicó',
           'state': 'Rio Grande do Norte'},
    '85': {'city': 'Fortaleza/Caucaia/Russas/Maracanaú',
           'state': 'Ceará'},
    '86': {'city': 'Teresina/Parnaíba/Piripiri/Campo Maior/Barras',
           'state': 'Piauí'},
    '87': {'city': 'Petrolina/Salgueiro/Arcoverde',
           'state': 'Pernambuco'},
    '88': {'city': 'Juazeiro do Norte/Crato/Sobral/Itapipoca/Iguatu/Quixadá',
           'state': 'Ceará'},
    '89': {'city': 'Picos/Floriano/Oeiras/São Raimundo Nonato/Corrente',
           'state': 'Piauí'},
    '91': {'city': 'Belém/Ananindeua/Castanhal/Abaetetuba/Bragança',
           'state': 'Pará'},
    '92': {'city': 'Manaus/Iranduba/Parintins/Itacoatiara/Maués/Borba',
           'state': 'Amazonas'},
    '93': {'city': 'Santarém/Altamira/Oriximiná/Itaituba/Jacareacanga',
           'state': 'Pará'},
    '94': {'city': 'Marabá/Tucuruí/Parauapebas/Redenção/Santana do Araguaia',
           'state': 'Pará'},
    '95': {'city': 'Boa Vista/Rorainópolis/Caracaraí/Alto Alegre/Mucajaí',
           'state': 'Roraima'},
    '96': {'city': 'Macapá/Santana/Laranjal do Jari/Oiapoque/Calçoene',
           'state': 'Amapá'},
    '97': {'city': 'Tefé/Coari/Tabatinga/Manicoré/Humaitá/Lábrea',
           'state': 'Amazonas'},
    '98': {'city': 'São Luís/São José de Ribamar/Paço do Lumiar/Pinheiro/Santa Inês',
           'state': 'Maranhão'},
    '99': {'city': 'Imperatriz/Caxias/Timon/Codó/Açailândia',
           'state': 'Maranhão'}
}

DDD_CHOICES = [(ddd, f"{ddd} - {region['state']}") for ddd, region in DDD.items()]
