from wagtail import hooks
from wagtail.admin.menu import MenuItem

def menu_item(label, url, icon, order):
    def decorator(func):
        @hooks.register('register_admin_menu_item')
        def wrapper():
            return MenuItem(label, url, icon_name=icon, order=order)
        return wrapper
    return decorator

@menu_item("Points", "/cms/snippets/points/point/", "snippet", 100)
def register_points_menu():
    pass

@menu_item("Messages", "/cms/snippets/points/message/", "comment", 101)
def register_messages_menu():
    pass

@menu_item("Geo Pages", "/cms/pages", "doc-full", 90)
def register_geopages_menu():
    pass

@hooks.register('construct_main_menu')
def hide_unwanted_menu_items(request, menu_items):
    unwanted = {'snippets', 'explorer', 'documents', 'images'}
    menu_items[:] = [item for item in menu_items if item.name not in unwanted]