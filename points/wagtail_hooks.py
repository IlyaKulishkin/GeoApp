from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.rich_text.converters.html_to_contentstate import InlineStyleElementHandler
from wagtail.admin.rich_text.editors.draftail.features import InlineStyleFeature

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


@hooks.register('register_rich_text_features')
def register_underline_feature(features):
    feature_name = 'underline'
    type_ = 'UNDERLINE'

    features.register_editor_plugin(
        'draftail', feature_name, InlineStyleFeature({
            'type': type_,
            'label': 'U',
            'description': 'Подчёркнутый',
            'element': 'u',
        })
    )

    features.register_converter_rule(
        'contentstate', feature_name, {
            'from_database_format': {
                'u': InlineStyleElementHandler(type_),
            },
            'to_database_format': {
                'style_map': {type_: 'u'},
            },
        }
    )


@menu_item("Артефакты", "/cms/snippets/points/artifact/", "code", 102)
def register_artifacts_menu():
    pass
