from loguru import logger
from aiogram import Router
from aiogram.types import Message, CallbackQuery

router = Router()

@router.message()
async def debug_all_messages(message: Message):
    """Barcha ishlanmagan xabarlarni log qilish"""
    user_id = message.from_user.id
    text = message.text or "[no_text]"
    
    logger.warning("=" * 60)
    logger.warning(f"⚠️  UNHANDLED MESSAGE")
    logger.warning(f"   User: {user_id}")
    logger.warning(f"   Text: '{text}'")
    logger.warning(f"   Content type: {message.content_type}")
    logger.warning("=" * 60)
    
    # User'ga javob beramiz
    await message.answer(
        f"⚠️ Bu xabar ishlanmadi.\n\n"
        f"Text: {text}\n"
        f"Type: {message.content_type}"
    )

@router.callback_query()
async def debug_all_callbacks(callback: CallbackQuery):
    """Barcha ishlanmagan callback'larni log qilish"""
    logger.warning(f"⚠️  UNHANDLED CALLBACK: {callback.data}")
    try:
        await callback.answer("⚠️ Bu callback ishlanmadi")
    except:
        pass