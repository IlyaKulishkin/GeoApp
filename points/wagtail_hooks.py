from wagtail import hooks
from wagtail.admin.menu import MenuItem

@hooks.register('register_admin_menu_item')
def register_point_menu_item():
    return MenuItem(
        "Points",
        "/cms/snippets/points/point/",
        icon_name="snippet",
        order=100
    )

@hooks.register('register_admin_menu_item')
def register_message_menu_item():
    return MenuItem(
        "Messages",
        "/cms/snippets/points/message/",
        icon_name="comment",
        order=101
    )

@hooks.register('register_admin_menu_item')
def register_geopage_menu_item():
    return MenuItem(
        'Geo Pages',
        "/cms/pages",
        icon_name='doc-full',
        order=90
    )

@hooks.register('construct_main_menu')
def hide_unwanted_menu_items(request, menu_items):
    unwanted = {'snippets', 'explorer', 'documents', 'images'}
    menu_items[:] = [item for item in menu_items if item.name not in unwanted]