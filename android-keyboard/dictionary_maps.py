
vowel_bana_to_komako = {
    "ə̀'": "è'",
    "ə́'": "é'",
    "ə̄'": "ē'",
    "ə̌'": "ě'",
    "ə̂'": "ê'",
}

# Low tone → base vowel / sonorant (duplicate "ù" key removed)
dict_ton_bas = {
    "à": "a",
    "À": "A",
    "ɑ̀": "ɑ",
    "è": "e",
    "È": "E",
    "ɛ̀": "ɛ̀",
    "Ɛ̀": "Ɛ",
    "ə̀": "ə",
    "Ə̀": "Ə",
    "ì": "i",
    "Ì": "I",
    "ò": "o",
    "Ò": "O",
    "ɔ̀": "ɔ",
    "Ɔ̀": "Ɔ",
    "ù": "u",
    "Ù": "U",
    "ʉ̀": "ʉ",
    "ǹ": "n",
    "m̀": "m",
    "ŋ̀": "ŋ",
    "M̀": "M",
    "Ŋ̀": "Ŋ",
    # NFC composes N/n + grave → U+01F8/U+01F9 (Ǹ/ǹ); strip ton bas after normalize
    "ǹ": "n",
    "Ǹ": "N",
}

