import emoji
import i18n
from i18n import t as _t

# Устанавливаем язык
i18n.set('locale', 'ru')
# Отключаем требование локали в файле перевода
i18n.set('skip_locale_root_data', True)
i18n.load_path.append('translations')


def t(*args, **kwargs):
    return emoji.emojize(_t(*args, **kwargs), use_aliases=True)
