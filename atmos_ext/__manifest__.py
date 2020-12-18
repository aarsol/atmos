{
    'name': 'ATMOS EXT',
    'version': '1.0',
    'category': 'Sales/CRM',
    'sequence': 4,
    'summary': 'Track leads and close opportunities',
    'author': 'AARSOL',
    'website': 'https://aarsol.com/',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'base', 'mail',
    ],
    'data': [

        'views/res_partner_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}