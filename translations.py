# translations.py

translations = {
    'en': {
        'RDP Server Monitor': 'RDP Server Monitor',
        'Refresh All': 'Refresh All',
        'Configure IT': 'Configure IT',
        'Add Server': 'Add Server',
        'Theme:': 'Theme:',
        'Light': 'Light',
        'Dark': 'Dark',
        'Blue': 'Blue',
        'Loading...': 'Loading...',
        'Select Language': 'Select Language',
        'OK': 'OK',
        # Add more translations here
    },
    'pt': {
        'RDP Server Monitor': 'Monitor de Servidores RDP',
        'Refresh All': 'Atualizar Todos',
        'Configure IT': 'Configurar TI',
        'Add Server': 'Adicionar Servidor',
        'Theme:': 'Tema:',
        'Light': 'Claro',
        'Dark': 'Escuro',
        'Blue': 'Azul',
        'Loading...': 'Carregando...',
        'Select Language': 'Selecionar Idioma',
        'OK': 'OK',
        # Add more translations here
    }
}

class Translator:
    def __init__(self, language):
        self.language = language

    def translate(self, text):
        return translations[self.language].get(text, text)