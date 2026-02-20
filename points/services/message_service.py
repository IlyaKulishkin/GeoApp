from ..models.api import Message, Point

def create_message(*, point_id: int, text: str, author) -> Message:
    """Создаёт сообщение к существующей точке."""
    try:
        point = Point.objects.get(id=point_id)
    except Point.DoesNotExist:
        raise ValueError("Point with this ID does not exist.")
    
    return Message.objects.create(
        point=point,
        text=text,
        author=author
    )