from phonecalls import constants as phonecalls_constants

BASIC_SERVICE = 1
COMMUNICATION_SERVICE = 2
DIVERSE_SERVICE = 3

SERVICE_TYPE_CHOICES = [
    (BASIC_SERVICE, 'Serviços Básicos de Disponibilidade e Contact Center'),
    (COMMUNICATION_SERVICE, 'Serviços de Comunicação'),
    (DIVERSE_SERVICE, 'Serviços Diversos')
]

# No caso da PMF LEVEL1 = aparelhos nivel 1
LEVEL_1_ACCESS_SERVICE = 1
# No caso da PMF Level2 = aparelhos sem fio
LEVEL_2_ACCESS_SERVICE = 2
LEVEL_3_ACCESS_SERVICE = 3
LEVEL_4_ACCESS_SERVICE = 4
LEVEL_5_ACCESS_SERVICE = 5
LEVEL_6_ACCESS_SERVICE = 6
# No caso da PMF WIRELESS_ACCESS_SERVICE = aparelhos DECT base
WIRELESS_ACCESS_SERVICE = 7
SOFTWARE_ACCESS_SERVICE = 8
SOFTWARE_EXTENSION_SERVICE = 9
MO_BASIC_CONTACT_CENTER_PLATFORM = 10
MO_BASIC_RECORDING_PLATFORM = 11
MO_SERVICE_POSITION = 12
MO_SUPERVISOR = 13
MO_REAL_TIME_TRACKING = 14
MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES = 15
MO_RECORDING_POSITION = 16
MO_RECORDING_SUPERVISOR = 17
WIFI_ACCESS_SERVICE = 18
# Servicos novos PMF
MO_Quality = 19
MO_Emotion = 20
MO_TRANSLATION = 21
MO_LEARNING = 22
CHATBOT_LICENSE_SERVICE = 23
CHATBOT_MAINTENANCE_SERVICE = 24

UST_OTHER = 1
KM_OTHER = 2

BASIC_SERVICE_CHOICES = [
    # Serviço de Disponibilização de Acesso a Comunicação Voip
    (LEVEL_1_ACCESS_SERVICE,     'Serviço de Acesso Nivel 1'),
    (LEVEL_2_ACCESS_SERVICE,     'Serviço de Acesso Nivel 2'),
    (LEVEL_3_ACCESS_SERVICE,     'Serviço de Acesso Nivel 3'),
    (LEVEL_4_ACCESS_SERVICE,     'Serviço de Acesso Nivel 4'),
    (LEVEL_5_ACCESS_SERVICE,     'Serviço de Acesso Nivel 5'),
    (LEVEL_6_ACCESS_SERVICE,     'Serviço de Acesso Nivel 6'),
    (WIRELESS_ACCESS_SERVICE,    'Serviço de Acesso sem fio'),
    (SOFTWARE_ACCESS_SERVICE,    'Serviço de acesso via Software'),
    (SOFTWARE_EXTENSION_SERVICE, 'Serviço de Extensão via software'),
    # Serviço de Contact Center
    (MO_BASIC_CONTACT_CENTER_PLATFORM,
     'Gerência e Operação da Plataforma Básica de Contact Center'),
    (MO_BASIC_RECORDING_PLATFORM,
     'Gerência e Operação da Plataforma Básica de Gravação'),
    (MO_SERVICE_POSITION,
     'Gerência e Operação de Posição de Atendimentos'),
    (MO_SUPERVISOR,
     'Gerência e Operação de Supervisor'),
    (MO_REAL_TIME_TRACKING,
     'Gerência e Operação de Acompanhamento em Tempo Real'),
    (MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES,
     'Gerência e Operação de Canal de Atendimento Automático e Mensagens'),
    (MO_RECORDING_POSITION,
     'Gerência e Operação de Posição de Gravação'),
    (MO_RECORDING_SUPERVISOR,
     'Gerência e Operação de Supervisor de Gravação')
]

BASIC_SERVICE_CHOICES_LIST = {
    # Serviço de Disponibilização de Acesso a Comunicação Voip
    LEVEL_1_ACCESS_SERVICE: 'Serviço de Acesso Nivel 1',
    LEVEL_2_ACCESS_SERVICE: 'Serviço de Acesso Nivel 2',
    LEVEL_3_ACCESS_SERVICE: 'Serviço de Acesso Nivel 3',
    LEVEL_4_ACCESS_SERVICE: 'Serviço de Acesso Nivel 4',
    LEVEL_5_ACCESS_SERVICE: 'Serviço de Acesso Nivel 5',
    LEVEL_6_ACCESS_SERVICE: 'Serviço de Acesso Nivel 6',
    WIRELESS_ACCESS_SERVICE: 'Serviço de Acesso sem fio',
    SOFTWARE_ACCESS_SERVICE: 'Serviço de acesso via Software',
    SOFTWARE_EXTENSION_SERVICE: 'Serviço de Extensão via software',
    # Serviço de Contact Center
    MO_BASIC_CONTACT_CENTER_PLATFORM:
     'Gerência e Operação da Plataforma Básica de Contact Center',
    MO_BASIC_RECORDING_PLATFORM:
     'Gerência e Operação da Plataforma Básica de Gravação',
    MO_SERVICE_POSITION:
     'Gerência e Operação de Posição de Atendimentos',
    MO_SUPERVISOR:
     'Gerência e Operação de Supervisor',
    MO_REAL_TIME_TRACKING:
     'Gerência e Operação de Acompanhamento em Tempo Real',
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES:
     'Gerência e Operação de Canal de Atendimento Automático e Mensagens',
    MO_RECORDING_POSITION:
     'Gerência e Operação de Posição de Gravação',
    MO_RECORDING_SUPERVISOR:
     'Gerência e Operação de Supervisor de Gravação'
}

BASIC_SERVICE_CHOICES_NEW = {
    # Serviço de Disponibilização de Acesso a Comunicação Voip
    LEVEL_1_ACCESS_SERVICE:     'Serviço de Acesso VoIP com aparelho 2 SIP e 100 Mb',
    LEVEL_2_ACCESS_SERVICE:     'Serviço de Acesso VoIP com aparelho 2 SIP e 100 MbE PoE',
    LEVEL_3_ACCESS_SERVICE:     'Serviço de Acesso VoIP com aparelho 4 SIP, 1GbE e teclado função',
    LEVEL_4_ACCESS_SERVICE:     'Serviço de Acesso VoIP com aparelho 10 SIP, 1GbE e teclado função',
    LEVEL_5_ACCESS_SERVICE:     'Serviço de Acesso VoIP sem aparelho (aparelho contratante)',
    WIFI_ACCESS_SERVICE:     'Serviço de Acesso VoIP sem fio com aparelho 2 SIP sem fio WiFi',
    WIRELESS_ACCESS_SERVICE:    'Serviço de Acesso com aparelho sem fio com base 2 SIP, 100 MbE e DECT',
    SOFTWARE_ACCESS_SERVICE:    'Serviço de acesso via Software',
    SOFTWARE_EXTENSION_SERVICE: 'Serviço de Extensão via software',
    # Serviço de Contact Center
    MO_BASIC_CONTACT_CENTER_PLATFORM:  'Gerência e Operação da Plataforma Básica de Contact Center',
    MO_BASIC_RECORDING_PLATFORM: 'Gerência e Operação da Plataforma Básica de Gravação',
    MO_SERVICE_POSITION: 'Gerência e Operação de Posição de Atendimentos',
    MO_SUPERVISOR: 'Gerência e Operação de Supervisor',
    MO_REAL_TIME_TRACKING: 'Gerência e Operação de Acompanhamento em Tempo Real',
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES: 'Gerência e Operação de Canal de Atendimento Automático e Mensagens',
    MO_RECORDING_POSITION: 'Gerência e Operação de Posição de Gravação',
    MO_RECORDING_SUPERVISOR: 'Gerência e Operação de Supervisor de Gravação'
}

BASIC_SERVICE_CHOICES_PMF = {
    # Serviço de Disponibilização de Acesso a Comunicação Voip
    LEVEL_1_ACCESS_SERVICE:     'Serviço de Acesso Nivel 1',
    LEVEL_2_ACCESS_SERVICE:     'Serviço de Acesso sem fio',
    WIRELESS_ACCESS_SERVICE:    'Serviço de Acesso com Equipamento DECT',
    # Serviço de Contact Center
    MO_BASIC_CONTACT_CENTER_PLATFORM:  'Gerência e Operação da Plataforma Básica de Contact Center',
    MO_BASIC_RECORDING_PLATFORM: 'Gerência e Operação da Plataforma Básica de Gravação',
    MO_SERVICE_POSITION: 'Gerência e Operação de Posição de Atendimentos',
    MO_SUPERVISOR: 'Gerência e Operação de Supervisor',
    MO_REAL_TIME_TRACKING: 'Gerência e Operação de Acompanhamento em Tempo Real',
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES: 'Gerência e Operação de Canal de Atendimento Automático e Mensagens',
    MO_RECORDING_POSITION: 'Gerência e Operação de Posição de Gravação',
    MO_Quality: 'Gerência e Operação de Qualidade de Gravação',
    MO_Emotion: 'Gerência e Operação de Detecção de Emoção',
    MO_TRANSLATION: 'Gerência e Operação de Tradução para Texto',
    MO_LEARNING: 'Gerência e Operação de Aprendizagem e Avaliação',
    # Serviço de Chatbot
    CHATBOT_LICENSE_SERVICE: 'Assistente Virtual Cognitivo',
    CHATBOT_MAINTENANCE_SERVICE: 'Sustentação e Atualização da Solução de Chatbot'
}

BASIC_SERVICE_ACCESS = [
    LEVEL_1_ACCESS_SERVICE,
    LEVEL_2_ACCESS_SERVICE,
    LEVEL_3_ACCESS_SERVICE,
    LEVEL_4_ACCESS_SERVICE,
    LEVEL_5_ACCESS_SERVICE,
    LEVEL_6_ACCESS_SERVICE,
    WIRELESS_ACCESS_SERVICE,
    SOFTWARE_ACCESS_SERVICE,
    SOFTWARE_EXTENSION_SERVICE
]

BASIC_SERVICE_ACCESS_MAP = {
    'LEVEL_1_ACCESS_SERVICE': 'Serviço de Acesso Nivel 1',
    'LEVEL_2_ACCESS_SERVICE': 'Serviço de Acesso Nivel 2',
    'LEVEL_3_ACCESS_SERVICE': 'Serviço de Acesso Nivel 3',
    'LEVEL_4_ACCESS_SERVICE': 'Serviço de Acesso Nivel 4',
    'LEVEL_5_ACCESS_SERVICE': 'Serviço de Acesso Nivel 5',
    'LEVEL_6_ACCESS_SERVICE': 'Serviço de Acesso Nivel 6',
    'WIRELESS_ACCESS_SERVICE': 'Serviço de Acesso sem fio',
    'SOFTWARE_ACCESS_SERVICE': 'Serviço de acesso via Software',
    'SOFTWARE_EXTENSION_SERVICE': 'Serviço de Extensão via software'
}

BASIC_SERVICE_ACCESS_MAP_NEW = {
    'LEVEL_1_ACCESS_SERVICE': 'Serviço de Acesso VoIP com aparelho 2 SIP e 100 Mb',
    'LEVEL_2_ACCESS_SERVICE': 'Serviço de Acesso VoIP com aparelho 2 SIP e 100 MbE PoE',
    'LEVEL_3_ACCESS_SERVICE': 'Serviço de Acesso VoIP com aparelho 4 SIP, 1GbE e teclado função',
    'LEVEL_4_ACCESS_SERVICE': 'Serviço de Acesso VoIP com aparelho 10 SIP, 1GbE e teclado função',
    'LEVEL_5_ACCESS_SERVICE': 'Serviço de Acesso VoIP sem aparelho (aparelho contratante)',
#    'LEVEL_6_ACCESS_SERVICE': 'Serviço de Acesso VoIP sem fio com aparelho 2 SIP sem fio WiFi',
    'WIRELESS_ACCESS_SERVICE': 'Serviço de Acesso com aparelho sem fio com base 2 SIP, 100 MbE e DECT',
    'SOFTWARE_ACCESS_SERVICE': 'Serviço de acesso via Software',
    'SOFTWARE_EXTENSION_SERVICE': 'Serviço de Extensão via software',
    'WIFI_ACCESS_SERVICE': 'Serviço de Acesso VoIP sem fio com aparelho 2 SIP sem fio WiFi'
}

BASIC_SERVICE_ACCESS_MAP_PMF = {
    'level_1_access_service': 'Serviço de Acesso Nivel 1',
    'level_2_access_service': 'Serviço de Acesso sem fio',
    'wireless_access_service': 'Serviço de Acesso com Equipamento DECT',
}

BASIC_SERVICE_MO = [
    MO_BASIC_CONTACT_CENTER_PLATFORM,
    MO_BASIC_RECORDING_PLATFORM,
    MO_SERVICE_POSITION,
    MO_SUPERVISOR,
    MO_REAL_TIME_TRACKING,
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES,
    MO_RECORDING_POSITION,
    MO_RECORDING_SUPERVISOR
]

BASIC_SERVICE_MO_PMF = [
    MO_BASIC_CONTACT_CENTER_PLATFORM,
    MO_BASIC_RECORDING_PLATFORM,
    MO_SERVICE_POSITION,
    MO_SUPERVISOR,
    MO_REAL_TIME_TRACKING,
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES,
    MO_RECORDING_POSITION,
    MO_Quality,
    MO_Emotion,
    MO_TRANSLATION,
    MO_LEARNING
]

BASIC_SERVICE_CHATBOT_PMF = [
    CHATBOT_LICENSE_SERVICE,
    CHATBOT_MAINTENANCE_SERVICE
]

BASIC_SERVICE_MO_MAP = {
    'MO_BASIC_CONTACT_CENTER_PLATFORM':
        'Gerência e Operação da Plataforma Básica de Contact Center',
    'MO_BASIC_RECORDING_PLATFORM': 'Gerência e Operação da Plataforma Básica de Gravação',
    'MO_SERVICE_POSITION': 'Gerência e Operação de Posição de Atendimentos',
    'MO_SUPERVISOR': 'Gerência e Operação de Supervisor',
    'MO_REAL_TIME_TRACKING': 'Gerência e Operação de Acompanhamento em Tempo Real',
    'MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES':
        'Gerência e Operação de Canal de Atendimento Automático e Mensagens',
    'MO_RECORDING_POSITION': 'Gerência e Operação de Posição de Gravação',
    'MO_RECORDING_SUPERVISOR': 'Gerência e Operação de Supervisor de Gravação'
}

BASIC_SERVICE_MO_MAP_PMF = {
    'mo_basic_contact_center_platform': 'Gerência e Operação da Plataforma Básica de Contact Center',
    'mo_basic_recording_platform': 'Gerência e Operação da Plataforma Básica de Gravação',
    'mo_service_position': 'Gerência e Operação de Posição de Atendimentos',
    'mo_supervisor': 'Gerência e Operação de Supervisor',
    'mo_real_time_tracking': 'Gerência e Operação de Acompanhamento em Tempo Real',
    'mo_auto_answer_channel_and_messages': 'Gerência e Operação de Canal de Atendimento Automático e Mensagens',
    'mo_recording_position': 'Gerência e Operação de Posição de Gravação',
    'mo_quality': 'Gerência e Operação de Qualidade de Gravação',
    'mo_emotion': 'Gerência e Operação de Detecção de Emoção',
    'mo_translation': 'Gerência e Operação de Tradução para Texto',
    'mo_learning': 'Gerência e Operação de Aprendizagem e Avaliação'
}

BASIC_SERVICE_CHATBOT_MAP_PMF = {
    'CHATBOT_LICENSE_SERVICE': 'Assistente Virtual Cognitivo',
    'CHATBOT_MAINTENANCE_SERVICE': 'Sustentação e Atualização da Solução de Chatbot'
}

BASIC_SERVICE_MAP = {**BASIC_SERVICE_ACCESS_MAP, **BASIC_SERVICE_MO_MAP}
BASIC_SERVICE_MAP_NEW = {**BASIC_SERVICE_ACCESS_MAP_NEW, **BASIC_SERVICE_MO_MAP}
BASIC_SERVICE_MAP_PMF = {**BASIC_SERVICE_ACCESS_MAP_PMF, **BASIC_SERVICE_MO_MAP_PMF, **BASIC_SERVICE_CHATBOT_MAP_PMF}

PRICE_FIELDS = [
    'level_1_access_service',
    'level_2_access_service',
    'level_3_access_service',
    'level_4_access_service',
    'level_5_access_service',
    'level_6_access_service',
    'wireless_access_service',
    'software_access_service',
    'software_extension_service',
    'mo_basic_contact_center_platform',
    'mo_basic_recording_platform',
    'mo_service_position',
    'mo_supervisor',
    'mo_real_time_tracking',
    'mo_auto_answer_channel_and_messages',
    'mo_recording_position',
    'mo_recording_supervisor',
    'LOCAL',
    'VC1',
    'VC2',
    'VC3',
    'LDN',
    'LDI',
    'UST',
    'KM'
]

PRICE_FIELDS_BASIC_SERVICE_MAP = {
    LEVEL_1_ACCESS_SERVICE: 'level_1_access_service',
    LEVEL_2_ACCESS_SERVICE: 'level_2_access_service',
    LEVEL_3_ACCESS_SERVICE: 'level_3_access_service',
    LEVEL_4_ACCESS_SERVICE: 'level_4_access_service',
    LEVEL_5_ACCESS_SERVICE: 'level_5_access_service',
    LEVEL_6_ACCESS_SERVICE: 'level_6_access_service',
    WIRELESS_ACCESS_SERVICE: 'wireless_access_service',
    SOFTWARE_ACCESS_SERVICE: 'software_access_service',
    SOFTWARE_EXTENSION_SERVICE: 'software_extension_service',
    MO_BASIC_CONTACT_CENTER_PLATFORM: 'mo_basic_contact_center_platform',
    MO_BASIC_RECORDING_PLATFORM: 'mo_basic_recording_platform',
    MO_SERVICE_POSITION: 'mo_service_position',
    MO_SUPERVISOR: 'mo_supervisor',
    MO_REAL_TIME_TRACKING: 'mo_real_time_tracking',
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES: 'mo_auto_answer_channel_and_messages',
    MO_RECORDING_POSITION: 'mo_recording_position',
    MO_RECORDING_SUPERVISOR: 'mo_recording_supervisor',
}

PRICE_FIELDS_BASIC_SERVICE_MAP_NEW = {
    LEVEL_1_ACCESS_SERVICE: 'level_1_access_service',
    LEVEL_2_ACCESS_SERVICE: 'level_2_access_service',
    LEVEL_3_ACCESS_SERVICE: 'level_3_access_service',
    LEVEL_4_ACCESS_SERVICE: 'level_4_access_service',
    LEVEL_5_ACCESS_SERVICE: 'level_5_access_service',
 #   LEVEL_6_ACCESS_SERVICE: 'level_6_access_service',
    WIRELESS_ACCESS_SERVICE: 'wireless_access_service',
    WIFI_ACCESS_SERVICE: 'wifi_access_service',
    SOFTWARE_ACCESS_SERVICE: 'software_access_service',
    SOFTWARE_EXTENSION_SERVICE: 'software_extension_service',
    MO_BASIC_CONTACT_CENTER_PLATFORM: 'mo_basic_contact_center_platform',
    MO_BASIC_RECORDING_PLATFORM: 'mo_basic_recording_platform',
    MO_SERVICE_POSITION: 'mo_service_position',
    MO_SUPERVISOR: 'mo_supervisor',
    MO_REAL_TIME_TRACKING: 'mo_real_time_tracking',
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES: 'mo_auto_answer_channel_and_messages',
    MO_RECORDING_POSITION: 'mo_recording_position',
    MO_RECORDING_SUPERVISOR: 'mo_recording_supervisor',
}

PRICE_FIELDS_BASIC_SERVICE_MAP_PMF = {
    LEVEL_1_ACCESS_SERVICE: 'level_1_access_service',
    LEVEL_2_ACCESS_SERVICE: 'level_2_access_service',
    WIRELESS_ACCESS_SERVICE: 'wireless_access_service',
    MO_BASIC_CONTACT_CENTER_PLATFORM: 'mo_basic_contact_center_platform',
    MO_BASIC_RECORDING_PLATFORM: 'mo_basic_recording_platform',
    MO_SERVICE_POSITION: 'mo_service_position',
    MO_SUPERVISOR: 'mo_supervisor',
    MO_REAL_TIME_TRACKING: 'mo_real_time_tracking',
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES: 'mo_auto_answer_channel_and_messages',
    MO_RECORDING_POSITION: 'mo_recording_position',
    MO_Quality: 'mo_quality',
    MO_Emotion: 'mo_emotion',
    MO_TRANSLATION: 'mo_translation',
    MO_LEARNING: 'mo_learning',
    CHATBOT_LICENSE_SERVICE: 'CHATBOT_LICENSE_SERVICE',
    CHATBOT_MAINTENANCE_SERVICE: 'CHATBOT_MAINTENANCE_SERVICE'
}


PRICE_FIELDS_CALLTYPE_MAP = {
    phonecalls_constants.LOCAL: 'LOCAL',
    phonecalls_constants.VC1: 'VC1',
    phonecalls_constants.VC2: 'VC2',
    phonecalls_constants.VC3: 'VC3',
    phonecalls_constants.LDN: 'LDN',
    phonecalls_constants.LDI: 'LDI'
}

PRICE_FIELDS_CALLTYPE_MAP_PMF = {
    phonecalls_constants.LOCAL: 'LOCAL',
    phonecalls_constants.VC1: 'VC1',
    phonecalls_constants.VC2: 'VC2_PMF',
    phonecalls_constants.VC3: 'VC3_PMF',
    phonecalls_constants.LDN: 'LDN',
    phonecalls_constants.LDI: 'LDI'
}


PRICE_FIELDS_CALLTYPE_MAP_NEW = {
    phonecalls_constants.LOCAL: 'LOCAL',
    phonecalls_constants.VC1: 'VC1',
    phonecalls_constants.LDN: 'LDN',
    phonecalls_constants.LDI: 'LDI'
}

PRICE_FIELDS_OTHERTYPE_MAP = {
    UST_OTHER: 'UST',
    KM_OTHER: 'KM',
}
