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
        'base', 'mail','sale','account'
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/res_partner_view.xml',
        'views/atmos_sale_schemes_view.xml',
        'views/sale_order_view.xml',
        'views/account_move_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}