import copy
import io
import logging
import os
import re
import string
import sys
import textwrap
from datetime import timedelta
from pathlib import Path
from typing import List

import sublib
from deep_translator import GoogleTranslator

proxy = os.environ.get('HTTP_PROXY', os.environ.get('http_proxy', ''))
proxies = {
    "http": proxy,
    "https": proxy,
}

# https://pypi.org/project/sublib/
# https://pypi.org/project/deep-translator

sample_file = Path(__file__).parent.parent.parent.absolute() / Path('input/1.srt')
sample_str = io.StringIO(textwrap.dedent('''\
    1
    00:00:00,123 --> 00:00:03,456
    Hi there
    
    2
    00:01:04,843 --> 00:01:05,428
    This is an example of a
    subtitle file in SRT format
'''))


def translate_array(texts, source_language='auto', target_language='hu'):
    for i in range(len(texts)):
        text = texts[i]
        if not text or not isinstance(text, str) or not text.strip():
            texts[i] = " zzz "

        if text.isdigit() or all(i in string.punctuation for i in text):
            texts[i] += " zzz "
    retval = GoogleTranslator(source=source_language, target=target_language,
                              proxies=proxies).translate_batch(texts)
    return retval


def split_up_text(text: str, pieces: int = 2) -> List[str]:
    ps = []
    if pieces == 1:
        return [text]
    elif pieces < 1:
        logging.error("pieces error.")
        exit(1)

    l = len(text) / pieces
    optimal_split_positions = [l * x for x in range(1, pieces)]

    indices_object = re.finditer(pattern=r'\w+', string=text)
    indices = [index.start() for index in indices_object]
    if 0 in indices: indices.remove(0)
    for index in indices:
        if text[index] == '-':
            indices.remove('-')
            continue

    def get_optimal_split(where: float, split_points: List[int]):
        minnn = 9999.0
        for split_point in split_points:
            d = abs(where - split_point)
            if d < minnn:
                minnn = d
                min_point = split_point

        split_points.remove(min_point)
        return (min_point, split_points)

    splip_pointssss = []
    for o in optimal_split_positions:
        sp, indices = get_optimal_split(where=o, split_points=indices)
        splip_pointssss.append(sp)

    start_ind = indices[0]
    for i in range(len(indices)):
        ind = indices[i]
        p = text[start_ind:ind]
        if ind - start_ind > l or i - 1 == len(indices):
            ps.append(p.strip())
            start_ind = indices[i]
    ps.append(text[start_ind:].strip())

    logging.info(f"Splitting up '{text}' in {pieces} pieces")
    logging.info(f"{ps}")

    return ps


def translate_subtitle_file(input=sample_file, target_language='hu'):
    translation_char_limit = 4000
    subtitle = sublib.SubRip(input, "utf-8")
    s2 = copy.deepcopy(subtitle)
    general = subtitle.get_general_format()

    def is_end_of_sentence(text: str):
        return text.endswith('.') or text.endswith('?') or text.endswith('!')

    def starts_with_lowercase(text: str):
        first_char = text[0]
        return first_char.isalpha() and first_char.islower()

    translated_all = []
    entries_to_be_translated = []

    entry = {'index_start': 0, 'index_end': 0, 'text': ''}

    # Join entries to sentences.
    for i in range(len(general)):
        start, end, text = general[i]
        text = text.replace('|', ' ').replace('  ', '')
        if len(entry['text']) > 0:
            entry['text'] += ' '
        entry['text'] += text

        if len(general) > i + 1:
            start_next = general[i + 1][0]
        else:
            start_next = end + timedelta(100)

        silence_to_next = start_next - end
        if is_end_of_sentence(text) or silence_to_next.seconds > 1:
            entry['index_end'] = i
            entries_to_be_translated.append(entry)
            entry = {'index_start': i + 1, 'index_end': i + 1, 'text': ''}

    # Split up and translate
    start = 0
    last_i = len(entries_to_be_translated)
    translated_all = []
    for i in range(last_i):
        a = entries_to_be_translated[start:i + 1]
        chars_sum = sum([len(t['text']) for t in a])
        if chars_sum > translation_char_limit - 10 or i == last_i - 1:
            texts = [t['text'] for t in entries_to_be_translated[start:i + 1]]
            td = general[entries_to_be_translated[i]['index_end']][1]
            logging.info("Translating {}...{} ({} characters) {}".format(start, i, chars_sum, td))
            translated = translate_array(texts=texts, target_language='hu')
            translated_all.extend(translated)
            # print(translated)
            start = i + 1

    # Split up sentences (undo #1)
    for i in range(len(entries_to_be_translated)):
        entry = entries_to_be_translated[i]
        text_long = translated_all[i]
        split_pieces = entry['index_end'] - entry['index_start'] + 1
        texts = split_up_text(text=text_long, pieces=split_pieces)
        if len(texts) != split_pieces:
            logging.error("bahh")

        insert_start = entry['index_start']
        insert_end = entry['index_end']
        for i2 in range(insert_end - insert_start + 1):
            iii = insert_start + i2 - 1
            if iii < len(general) - 1:
                general[iii][2] = texts[i2]
            else:
                logging.error("Index overrun.")
                sys.exit(1)

    empty_subtitle = sublib.SubRip()
    with open(input + '.out', 'w', encoding='utf-8') as out:
        out.write(empty_subtitle.set_from_general_format(general))

    return None


if __name__ == "__main__":
    ss = split_up_text("Lksdfj, skl jkljs  joij j ios dfg asdf?", 3)

    logging.basicConfig(level=logging.INFO)
    translate_subtitle_file(input='input/1.srt')



    pass
