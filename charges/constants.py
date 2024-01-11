from phonecalls import constants as phonecalls_constants

BASIC_SERVICE = 1
COMMUNICATION_SERVICE = 2

SERVICE_TYPE_CHOICES = [
    (BASIC_SERVICE, 'Serviços Básicos de Disponibilidade e Contact Center'),
    (COMMUNICATION_SERVICE, 'Serviços de Comunicação')
]

LEVEL_1_ACCESS_SERVICE = 1
LEVEL_2_ACCESS_SERVICE = 2
LEVEL_3_ACCESS_SERVICE = 3
LEVEL_4_ACCESS_SERVICE = 4
LEVEL_5_ACCESS_SERVICE = 5
LEVEL_6_ACCESS_SERVICE = 6
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

BASIC_SERVICE_MAP = {**BASIC_SERVICE_ACCESS_MAP, **BASIC_SERVICE_MO_MAP}

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
    'LDI'
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

PRICE_FIELDS_CALLTYPE_MAP = {
    phonecalls_constants.LOCAL: 'LOCAL',
    phonecalls_constants.VC1: 'VC1',
    phonecalls_constants.VC2: 'VC2',
    phonecalls_constants.VC3: 'VC3',
    phonecalls_constants.LDN: 'LDN',
    phonecalls_constants.LDI: 'LDI'
}
